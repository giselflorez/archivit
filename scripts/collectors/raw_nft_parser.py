#!/usr/bin/env python3
"""
Raw NFT Event Parser - No API Keys Required
Parses NFT data directly from blockchain events without Alchemy enhanced APIs

Tracks:
- NFT mints (Transfer from 0x0)
- NFT transfers between wallets
- Sale prices from transaction values
- Collector addresses (current and historical owners)
- Metadata from IPFS/tokenURI
- Transaction dates and hashes
"""

import os
import json
import requests
import logging
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.multi_provider_web3 import MultiProviderWeb3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ERC-721 Transfer event signature
# Transfer(address indexed from, address indexed to, uint256 indexed tokenId)
ERC721_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# ERC-1155 TransferSingle event signature
ERC1155_TRANSFER_SINGLE_TOPIC = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"

# Null address (mints come from here)
NULL_ADDRESS = "0x0000000000000000000000000000000000000000"

# IPFS gateways for metadata fetching (with failover)
IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
    "https://gateway.pinata.cloud/ipfs/",
    "https://dweb.link/ipfs/",
]

# ERC-721 ABI fragments for tokenURI
ERC721_TOKEN_URI_SIG = "0xc87b56dd"  # tokenURI(uint256)
ERC721_NAME_SIG = "0x06fdde03"       # name()
ERC721_SYMBOL_SIG = "0x95d89b41"     # symbol()
ERC721_OWNER_OF_SIG = "0x6352211e"   # ownerOf(uint256)


class RawNFTParser:
    """
    Parse NFT data directly from blockchain without enhanced APIs

    Features:
    - Get all NFT transfers for a contract or address
    - Detect mints (from null address)
    - Get current owner
    - Fetch metadata from IPFS
    - Calculate sale prices from transaction values
    - Track collector history
    """

    def __init__(self, network: str = 'ethereum'):
        """Initialize with multi-provider RPC client"""
        self.web3 = MultiProviderWeb3(network)
        self.network = network
        self.metadata_cache = {}

    def _pad_address(self, address: str) -> str:
        """Pad address to 32 bytes for topic matching"""
        return "0x" + address.lower().replace("0x", "").zfill(64)

    def _parse_address(self, topic: str) -> str:
        """Parse address from 32-byte topic"""
        return "0x" + topic[-40:]

    def _parse_uint256(self, hex_str: str) -> int:
        """Parse uint256 from hex string"""
        return int(hex_str, 16)

    def _encode_uint256(self, num: int) -> str:
        """Encode uint256 for contract call data"""
        return hex(num)[2:].zfill(64)

    def get_block_timestamp(self, block_number: int) -> Optional[str]:
        """Get timestamp for a block"""
        block = self.web3.get_block(block_number)
        if block and 'timestamp' in block:
            timestamp = block['timestamp']
            if isinstance(timestamp, str):
                timestamp = int(timestamp, 16)
            return datetime.utcfromtimestamp(timestamp).isoformat()
        return None

    def get_nft_transfers(
        self,
        contract_address: str,
        from_block: int = 0,
        to_block: str = 'latest',
        token_id: int = None
    ) -> List[Dict]:
        """
        Get all Transfer events for an NFT contract

        Args:
            contract_address: NFT contract address
            from_block: Starting block (0 for genesis)
            to_block: Ending block ('latest' or block number)
            token_id: Optional specific token ID to filter

        Returns:
            List of transfer records with from, to, tokenId, txHash, blockNumber
        """
        logger.info(f"Fetching transfers for {contract_address} from block {from_block}")

        topics = [ERC721_TRANSFER_TOPIC]

        # Add token_id filter if specified
        if token_id is not None:
            topics.extend([None, None, self._pad_address(hex(token_id))])

        # Get logs in chunks to avoid timeouts
        transfers = []
        current_block = from_block

        # Get latest block if needed
        if to_block == 'latest':
            to_block = self.web3.get_block_number() or current_block + 10000

        # Process in chunks of 500 blocks (public nodes limit to 800-1000)
        chunk_size = 500

        while current_block < to_block:
            end_block = min(current_block + chunk_size, to_block)

            logger.debug(f"Fetching blocks {current_block} to {end_block}")

            logs = self.web3.get_logs(
                from_block=current_block,
                to_block=end_block,
                address=contract_address,
                topics=topics
            )

            if logs:
                for log in logs:
                    transfer = self._parse_transfer_log(log)
                    if transfer:
                        transfers.append(transfer)

            current_block = end_block + 1

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        logger.info(f"Found {len(transfers)} transfers")
        return transfers

    def _parse_transfer_log(self, log: Dict) -> Optional[Dict]:
        """Parse a Transfer event log into structured data"""
        try:
            topics = log.get('topics', [])

            if len(topics) < 4:
                return None

            # Parse addresses and token ID from topics
            from_address = self._parse_address(topics[1])
            to_address = self._parse_address(topics[2])
            token_id = self._parse_uint256(topics[3])

            # Get block number
            block_num = log.get('blockNumber')
            if isinstance(block_num, str):
                block_num = int(block_num, 16)

            return {
                'from_address': from_address,
                'to_address': to_address,
                'token_id': token_id,
                'tx_hash': log.get('transactionHash'),
                'block_number': block_num,
                'log_index': log.get('logIndex'),
                'contract_address': log.get('address'),
                'is_mint': from_address == NULL_ADDRESS,
            }

        except Exception as e:
            logger.warning(f"Failed to parse transfer log: {e}")
            return None

    def get_mints_by_address(
        self,
        creator_address: str,
        from_block: int = 0
    ) -> List[Dict]:
        """
        Get all NFT mints received by an address (creator mints to self)

        This finds NFTs where:
        - Transfer from 0x0 (null address) = mint
        - Transfer to the creator address

        Args:
            creator_address: Address that received mints
            from_block: Starting block

        Returns:
            List of mint records
        """
        logger.info(f"Finding mints to {creator_address}")

        # We need to search broadly since we don't know which contracts
        # This requires knowing the contracts or using indexed events

        # Alternative approach: Get all transfers TO this address from NULL
        topics = [
            ERC721_TRANSFER_TOPIC,
            self._pad_address(NULL_ADDRESS),  # from = null (mint)
            self._pad_address(creator_address)  # to = creator
        ]

        to_block = self.web3.get_block_number() or from_block + 100000

        mints = []
        current_block = from_block
        chunk_size = 50000  # Larger chunks for address search

        while current_block < to_block:
            end_block = min(current_block + chunk_size, to_block)

            logger.debug(f"Searching blocks {current_block} to {end_block}")

            logs = self.web3.get_logs(
                from_block=current_block,
                to_block=end_block,
                topics=topics
            )

            if logs:
                for log in logs:
                    mint = self._parse_transfer_log(log)
                    if mint:
                        mint['is_mint'] = True
                        mints.append(mint)

            current_block = end_block + 1
            time.sleep(0.1)

        logger.info(f"Found {len(mints)} mints to {creator_address}")
        return mints

    def get_token_uri(self, contract_address: str, token_id: int) -> Optional[str]:
        """
        Call tokenURI(uint256) on contract to get metadata URI

        Args:
            contract_address: NFT contract
            token_id: Token ID

        Returns:
            Token URI string (usually IPFS or HTTP URL)
        """
        # Encode call data: tokenURI(uint256)
        call_data = ERC721_TOKEN_URI_SIG + self._encode_uint256(token_id)

        result = self.web3.call_contract(contract_address, call_data)

        if result and result != '0x':
            try:
                # Decode string from ABI encoding
                # Skip first 64 chars (offset) and next 64 chars (length)
                # Then decode hex to string
                hex_data = result[2:]  # Remove 0x

                if len(hex_data) >= 128:
                    # Get string length
                    length = int(hex_data[64:128], 16)
                    # Get string data
                    string_hex = hex_data[128:128 + length * 2]
                    return bytes.fromhex(string_hex).decode('utf-8').strip('\x00')

            except Exception as e:
                logger.warning(f"Failed to decode tokenURI: {e}")

        return None

    def get_current_owner(self, contract_address: str, token_id: int) -> Optional[str]:
        """
        Call ownerOf(uint256) to get current token owner

        Args:
            contract_address: NFT contract
            token_id: Token ID

        Returns:
            Current owner address
        """
        call_data = ERC721_OWNER_OF_SIG + self._encode_uint256(token_id)

        result = self.web3.call_contract(contract_address, call_data)

        if result and len(result) >= 42:
            return self._parse_address(result)

        return None

    @staticmethod
    def _sanitize_ipfs_string(value: str) -> str:
        """
        SECURITY: Sanitize strings from IPFS to prevent XSS.
        Removes script tags, event handlers, and other dangerous content.
        """
        if not isinstance(value, str):
            return value

        import html as html_module

        # First escape HTML entities
        sanitized = html_module.escape(value)

        # Remove any remaining script-like patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'data:text/html',
        ]

        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        return sanitized

    @staticmethod
    def _sanitize_ipfs_metadata(data):
        """
        SECURITY: Recursively sanitize IPFS metadata.
        Sanitizes all string values in dict/list structures.
        """
        if isinstance(data, dict):
            return {k: RawNFTParser._sanitize_ipfs_metadata(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [RawNFTParser._sanitize_ipfs_metadata(item) for item in data]
        elif isinstance(data, str):
            return RawNFTParser._sanitize_ipfs_string(data)
        else:
            return data

    def fetch_ipfs_metadata(self, uri: str) -> Optional[Dict]:
        """
        Fetch metadata from IPFS with gateway failover.
        SECURITY: All returned data is sanitized to prevent XSS.

        Args:
            uri: IPFS URI (ipfs://... or gateway URL)

        Returns:
            Parsed and sanitized JSON metadata
        """
        # Check cache
        if uri in self.metadata_cache:
            return self.metadata_cache[uri]

        # Convert IPFS URI to gateway URL
        if uri.startswith('ipfs://'):
            ipfs_hash = uri.replace('ipfs://', '')
        elif '/ipfs/' in uri:
            ipfs_hash = uri.split('/ipfs/')[-1]
        else:
            # Already an HTTP URL
            try:
                response = requests.get(uri, timeout=10)
                if response.status_code == 200:
                    metadata = response.json()
                    # SECURITY: Sanitize metadata
                    metadata = self._sanitize_ipfs_metadata(metadata)
                    self.metadata_cache[uri] = metadata
                    return metadata
            except:
                pass
            return None

        # Try each IPFS gateway
        for gateway in IPFS_GATEWAYS:
            try:
                url = gateway + ipfs_hash
                logger.debug(f"Trying IPFS gateway: {url}")

                response = requests.get(url, timeout=15)

                if response.status_code == 200:
                    metadata = response.json()
                    # SECURITY: Sanitize metadata
                    metadata = self._sanitize_ipfs_metadata(metadata)
                    self.metadata_cache[uri] = metadata
                    return metadata

            except Exception as e:
                logger.debug(f"Gateway {gateway} failed: {e}")
                continue

        logger.warning(f"All IPFS gateways failed for {uri}")
        return None

    def get_transaction_value(self, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction details including value (for sale price)

        Args:
            tx_hash: Transaction hash

        Returns:
            Dict with value_wei, value_eth, gas_used
        """
        receipt = self.web3.get_transaction_receipt(tx_hash)

        if receipt:
            # Get transaction for value
            tx = self.web3.rpc_call('eth_getTransactionByHash', [tx_hash])

            if tx:
                value_wei = int(tx.get('value', '0x0'), 16)
                gas_used = int(receipt.get('gasUsed', '0x0'), 16)
                gas_price = int(tx.get('gasPrice', '0x0'), 16)

                return {
                    'value_wei': value_wei,
                    'value_eth': value_wei / 1e18,
                    'gas_used': gas_used,
                    'gas_price_gwei': gas_price / 1e9,
                    'tx_fee_eth': (gas_used * gas_price) / 1e18,
                    'from_address': tx.get('from'),
                    'to_address': tx.get('to'),
                }

        return None

    def get_full_nft_data(
        self,
        contract_address: str,
        token_id: int,
        include_transfers: bool = True,
        recent_blocks: int = 50000
    ) -> Dict:
        """
        Get complete data for a single NFT

        Args:
            contract_address: NFT contract
            token_id: Token ID
            include_transfers: Whether to fetch transfer history
            recent_blocks: Only scan this many recent blocks (default 50000 = ~1 week)
                          Set to 0 for full history (slow without API key)

        Returns:
            Complete NFT data including metadata, owner, transfers
        """
        logger.info(f"Getting full data for {contract_address} #{token_id}")

        nft_data = {
            'contract_address': contract_address,
            'token_id': token_id,
            'network': self.network,
        }

        # Get current owner
        owner = self.get_current_owner(contract_address, token_id)
        nft_data['current_owner'] = owner

        # Get tokenURI
        token_uri = self.get_token_uri(contract_address, token_id)
        nft_data['token_uri'] = token_uri

        # Fetch metadata from IPFS
        if token_uri:
            metadata = self.fetch_ipfs_metadata(token_uri)
            if metadata:
                nft_data['name'] = metadata.get('name')
                nft_data['description'] = metadata.get('description')
                nft_data['image'] = metadata.get('image')
                nft_data['attributes'] = metadata.get('attributes', [])
                nft_data['external_url'] = metadata.get('external_url')
                nft_data['animation_url'] = metadata.get('animation_url')
                nft_data['metadata_raw'] = metadata

        # Get transfer history
        if include_transfers:
            # Calculate from_block based on recent_blocks setting
            if recent_blocks > 0:
                current_block = self.web3.get_block_number() or 0
                from_block = max(0, current_block - recent_blocks)
            else:
                from_block = 0

            transfers = self.get_nft_transfers(
                contract_address,
                from_block=from_block,
                token_id=token_id
            )

            nft_data['transfers'] = []
            nft_data['collectors'] = []  # All addresses that owned this NFT

            collectors_seen = set()

            for transfer in transfers:
                # Get timestamp
                timestamp = self.get_block_timestamp(transfer['block_number'])
                transfer['timestamp'] = timestamp

                # Get transaction value (sale price)
                tx_data = self.get_transaction_value(transfer['tx_hash'])
                if tx_data:
                    transfer['value_eth'] = tx_data['value_eth']
                    transfer['is_sale'] = tx_data['value_eth'] > 0
                else:
                    transfer['value_eth'] = 0
                    transfer['is_sale'] = False

                nft_data['transfers'].append(transfer)

                # Track collectors
                if transfer['to_address'] not in collectors_seen:
                    collectors_seen.add(transfer['to_address'])
                    nft_data['collectors'].append({
                        'address': transfer['to_address'],
                        'acquired_block': transfer['block_number'],
                        'acquired_date': timestamp,
                        'acquired_price_eth': transfer['value_eth'] if transfer['is_sale'] else None,
                        'tx_hash': transfer['tx_hash'],
                        'is_current_owner': transfer['to_address'] == owner
                    })

            # Find mint
            mint_transfer = next((t for t in transfers if t['is_mint']), None)
            if mint_transfer:
                nft_data['minter'] = mint_transfer['to_address']
                nft_data['mint_date'] = mint_transfer.get('timestamp')
                nft_data['mint_block'] = mint_transfer['block_number']
                nft_data['mint_tx'] = mint_transfer['tx_hash']

        return nft_data

    def get_collection_stats(self, contract_address: str, sample_size: int = 100) -> Dict:
        """
        Get collection-level statistics

        Args:
            contract_address: NFT contract
            sample_size: Number of recent transfers to analyze

        Returns:
            Collection statistics
        """
        # Get recent transfers
        current_block = self.web3.get_block_number() or 0
        from_block = max(0, current_block - 100000)  # Last ~2 weeks

        transfers = self.get_nft_transfers(
            contract_address,
            from_block=from_block
        )

        # Calculate stats
        unique_tokens = set()
        unique_holders = set()
        total_volume_eth = 0
        sales_count = 0

        for transfer in transfers[-sample_size:]:
            unique_tokens.add(transfer['token_id'])
            unique_holders.add(transfer['to_address'])

            # Get sale value
            tx_data = self.get_transaction_value(transfer['tx_hash'])
            if tx_data and tx_data['value_eth'] > 0:
                total_volume_eth += tx_data['value_eth']
                sales_count += 1

        return {
            'contract_address': contract_address,
            'transfers_analyzed': len(transfers[-sample_size:]),
            'unique_tokens': len(unique_tokens),
            'unique_holders': len(unique_holders),
            'total_volume_eth': total_volume_eth,
            'sales_count': sales_count,
            'avg_sale_price_eth': total_volume_eth / sales_count if sales_count > 0 else 0,
        }


# CLI Interface
if __name__ == '__main__':
    import sys

    parser = RawNFTParser()

    if len(sys.argv) < 2:
        print("""
Raw NFT Parser - No API Keys Required

Usage:
  python raw_nft_parser.py nft <contract> <token_id>     Get full NFT data
  python raw_nft_parser.py transfers <contract>          Get recent transfers
  python raw_nft_parser.py mints <address>               Get mints to address
  python raw_nft_parser.py owner <contract> <token_id>   Get current owner
  python raw_nft_parser.py uri <contract> <token_id>     Get token URI
  python raw_nft_parser.py stats <contract>              Get collection stats

Examples:
  python raw_nft_parser.py nft 0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d 1
  python raw_nft_parser.py transfers 0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d
        """)
        sys.exit(0)

    command = sys.argv[1]

    if command == 'nft':
        if len(sys.argv) < 4:
            print("Usage: python raw_nft_parser.py nft <contract> <token_id>")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        print(f"\nFetching full data for {contract} #{token_id}...")
        print("="*60)

        data = parser.get_full_nft_data(contract, token_id)

        print(f"\nNFT: {data.get('name', 'Unknown')}")
        print(f"Contract: {data['contract_address']}")
        print(f"Token ID: {data['token_id']}")
        print(f"Current Owner: {data.get('current_owner', 'Unknown')}")
        print(f"Minter: {data.get('minter', 'Unknown')}")
        print(f"Mint Date: {data.get('mint_date', 'Unknown')}")
        print(f"Token URI: {data.get('token_uri', 'None')}")

        if data.get('description'):
            print(f"\nDescription: {data['description'][:200]}...")

        if data.get('image'):
            print(f"\nImage: {data['image']}")

        if data.get('transfers'):
            print(f"\n--- Transfer History ({len(data['transfers'])} transfers) ---")
            for t in data['transfers'][:10]:
                sale_str = f" ({t['value_eth']:.4f} ETH)" if t.get('is_sale') else ""
                mint_str = " [MINT]" if t.get('is_mint') else ""
                print(f"  {t.get('timestamp', 'Unknown')} | {t['from_address'][:10]}... → {t['to_address'][:10]}...{sale_str}{mint_str}")

        if data.get('collectors'):
            print(f"\n--- Collectors ({len(data['collectors'])} total) ---")
            for c in data['collectors']:
                current = " [CURRENT]" if c['is_current_owner'] else ""
                price = f" @ {c['acquired_price_eth']:.4f} ETH" if c.get('acquired_price_eth') else ""
                print(f"  {c['address'][:16]}...{price}{current}")

    elif command == 'transfers':
        if len(sys.argv) < 3:
            print("Usage: python raw_nft_parser.py transfers <contract>")
            sys.exit(1)

        contract = sys.argv[2]

        # Get last ~1000 blocks worth
        current_block = parser.web3.get_block_number() or 0
        from_block = max(0, current_block - 1000)

        print(f"\nFetching recent transfers for {contract}...")
        transfers = parser.get_nft_transfers(contract, from_block=from_block)

        print(f"\nFound {len(transfers)} transfers in last ~1000 blocks:")
        for t in transfers[:20]:
            mint_str = " [MINT]" if t.get('is_mint') else ""
            print(f"  #{t['token_id']} | {t['from_address'][:10]}... → {t['to_address'][:10]}...{mint_str}")

    elif command == 'mints':
        if len(sys.argv) < 3:
            print("Usage: python raw_nft_parser.py mints <address>")
            sys.exit(1)

        address = sys.argv[2]

        # Search last 100k blocks
        current_block = parser.web3.get_block_number() or 0
        from_block = max(0, current_block - 100000)

        print(f"\nSearching for mints to {address}...")
        mints = parser.get_mints_by_address(address, from_block=from_block)

        print(f"\nFound {len(mints)} mints:")
        for m in mints[:20]:
            print(f"  Contract: {m['contract_address'][:20]}... | Token #{m['token_id']}")

    elif command == 'owner':
        if len(sys.argv) < 4:
            print("Usage: python raw_nft_parser.py owner <contract> <token_id>")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        owner = parser.get_current_owner(contract, token_id)
        print(f"\nCurrent owner of {contract} #{token_id}:")
        print(f"  {owner}")

    elif command == 'uri':
        if len(sys.argv) < 4:
            print("Usage: python raw_nft_parser.py uri <contract> <token_id>")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        uri = parser.get_token_uri(contract, token_id)
        print(f"\nToken URI for {contract} #{token_id}:")
        print(f"  {uri}")

        if uri:
            print("\nFetching metadata...")
            metadata = parser.fetch_ipfs_metadata(uri)
            if metadata:
                print(json.dumps(metadata, indent=2))

    elif command == 'stats':
        if len(sys.argv) < 3:
            print("Usage: python raw_nft_parser.py stats <contract>")
            sys.exit(1)

        contract = sys.argv[2]

        print(f"\nCalculating stats for {contract}...")
        stats = parser.get_collection_stats(contract)

        print(f"\n--- Collection Stats ---")
        print(f"Transfers Analyzed: {stats['transfers_analyzed']}")
        print(f"Unique Tokens: {stats['unique_tokens']}")
        print(f"Unique Holders: {stats['unique_holders']}")
        print(f"Sales Count: {stats['sales_count']}")
        print(f"Total Volume: {stats['total_volume_eth']:.4f} ETH")
        print(f"Avg Sale Price: {stats['avg_sale_price_eth']:.4f} ETH")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

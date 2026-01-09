#!/usr/bin/env python3
"""
Direct Blockchain Event Parser
Parse NFT mints and transfers directly from blockchain events
NO DEPENDENCY on Alchemy's indexed data - 100% trustless and decentralized
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.multi_provider_web3 import MultiProviderWeb3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlockchainEventParser:
    """
    Parse blockchain events directly without relying on third-party indexing

    This is the MOST decentralized approach:
    - No dependency on Alchemy/Infura indexing
    - Reads raw blockchain data directly
    - Works even if ALL enhanced APIs shut down
    - Only requires basic RPC access (can use public nodes)
    """

    # ERC-721 Transfer event signature
    # Transfer(address indexed from, address indexed to, uint256 indexed tokenId)
    TRANSFER_EVENT_SIGNATURE = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

    # ERC-721 tokenURI function selector
    TOKEN_URI_SELECTOR = '0xc87b56dd'

    def __init__(self, network: str = 'ethereum'):
        """
        Initialize event parser

        Args:
            network: Blockchain network ('ethereum', 'polygon', etc.)
        """
        self.network = network
        self.web3 = MultiProviderWeb3(network)

    def get_nft_mints_from_contract(
        self,
        contract_address: str,
        from_block: int = 0,
        to_block: int = None,
        batch_size: int = 10000
    ) -> List[Dict]:
        """
        Get all NFT mints from a contract by parsing Transfer events

        Mint = Transfer from 0x0000... (null address)

        Args:
            contract_address: NFT contract address
            from_block: Starting block number
            to_block: Ending block number (None = latest)
            batch_size: Process in batches to avoid timeout

        Returns:
            List of mint events
        """
        logger.info(f"Parsing mint events from {contract_address}")

        # Get latest block if not specified
        if to_block is None:
            to_block_num = self.web3.get_block_number()
            if not to_block_num:
                logger.error("Failed to get latest block number")
                return []
            to_block = to_block_num

        mints = []

        # Process in batches to avoid RPC limits
        current_block = from_block

        while current_block <= to_block:
            batch_end = min(current_block + batch_size - 1, to_block)

            logger.info(f"Processing blocks {current_block:,} to {batch_end:,}")

            # Get Transfer events where from=0x0 (mint)
            logs = self.web3.get_logs(
                from_block=current_block,
                to_block=batch_end,
                address=contract_address,
                topics=[
                    self.TRANSFER_EVENT_SIGNATURE,
                    '0x0000000000000000000000000000000000000000000000000000000000000000'  # from=0x0
                ]
            )

            if logs:
                for log in logs:
                    mint = self._parse_transfer_event(log)
                    if mint:
                        mints.append(mint)

            current_block = batch_end + 1

        logger.info(f"Found {len(mints)} mint events")
        return mints

    def get_nft_transfers_for_token(
        self,
        contract_address: str,
        token_id: int,
        from_block: int = 0
    ) -> List[Dict]:
        """
        Get all transfers (including sales) for a specific NFT

        Args:
            contract_address: NFT contract address
            token_id: Token ID
            from_block: Starting block number

        Returns:
            List of transfer events (chronological order)
        """
        logger.info(f"Parsing transfers for {contract_address} #{token_id}")

        # Pad token ID to 32 bytes (64 hex chars)
        token_id_hex = f"0x{token_id:064x}"

        # Get Transfer events for this token
        logs = self.web3.get_logs(
            from_block=from_block,
            to_block='latest',
            address=contract_address,
            topics=[
                self.TRANSFER_EVENT_SIGNATURE,
                None,  # any from address
                None,  # any to address
                token_id_hex  # specific token ID
            ]
        )

        transfers = []
        if logs:
            for log in logs:
                transfer = self._parse_transfer_event(log)
                if transfer:
                    # Get transaction details for price
                    tx_receipt = self.web3.get_transaction_receipt(transfer['tx_hash'])
                    if tx_receipt:
                        # Get transaction value (price in wei)
                        block = self.web3.get_block(transfer['block_number'])
                        if block and 'transactions' in block:
                            for tx in block['transactions']:
                                if tx.get('hash') == transfer['tx_hash']:
                                    transfer['value_wei'] = int(tx.get('value', '0x0'), 16)
                                    break

                    transfers.append(transfer)

        # Sort chronologically
        transfers.sort(key=lambda x: x['block_number'])

        logger.info(f"Found {len(transfers)} transfers")
        return transfers

    def get_token_uri(self, contract_address: str, token_id: int) -> Optional[str]:
        """
        Get tokenURI directly from contract

        Args:
            contract_address: NFT contract address
            token_id: Token ID

        Returns:
            Token URI string or None
        """
        # Encode tokenURI(uint256) call
        token_id_hex = f"{token_id:064x}"
        data = self.TOKEN_URI_SELECTOR + token_id_hex

        # Call contract
        result = self.web3.call_contract(contract_address, data)

        if result and result != '0x':
            return self._decode_string_from_hex(result)

        return None

    def _parse_transfer_event(self, log: Dict) -> Optional[Dict]:
        """
        Parse Transfer event log

        Args:
            log: Raw log entry from eth_getLogs

        Returns:
            Parsed transfer data
        """
        try:
            topics = log.get('topics', [])

            if len(topics) < 3:
                return None

            # Parse topics
            # topics[0] = event signature (already filtered)
            # topics[1] = from address
            # topics[2] = to address
            # topics[3] = token ID (if indexed)

            from_address = '0x' + topics[1][-40:] if len(topics) > 1 else None
            to_address = '0x' + topics[2][-40:] if len(topics) > 2 else None

            # Token ID might be in topics[3] or in data
            token_id = None
            if len(topics) > 3:
                token_id = str(int(topics[3], 16))
            elif log.get('data') and log['data'] != '0x':
                # Parse token ID from data field
                token_id = str(int(log['data'], 16))

            return {
                'contract_address': log.get('address'),
                'from_address': from_address,
                'to_address': to_address,
                'token_id': token_id,
                'tx_hash': log.get('transactionHash'),
                'block_number': int(log.get('blockNumber', '0'), 16),
                'log_index': int(log.get('logIndex', '0'), 16),
            }

        except Exception as e:
            logger.error(f"Error parsing transfer event: {e}")
            return None

    def _decode_string_from_hex(self, hex_data: str) -> Optional[str]:
        """
        Decode string from Ethereum hex response

        Ethereum encodes strings as:
        - 32 bytes: offset to string data
        - 32 bytes: length of string
        - N bytes: actual string data (padded to 32-byte chunks)

        Args:
            hex_data: Hex-encoded response

        Returns:
            Decoded string or None
        """
        if not hex_data or hex_data == '0x':
            return None

        try:
            # Remove '0x' prefix
            hex_data = hex_data[2:] if hex_data.startswith('0x') else hex_data

            # Skip first 64 chars (offset)
            # Next 64 chars are length (in hex)
            length_hex = hex_data[64:128]
            length = int(length_hex, 16)

            # Remaining data is the actual string (hex-encoded)
            string_hex = hex_data[128:128 + (length * 2)]

            # Decode hex to bytes, then to string
            decoded = bytes.fromhex(string_hex).decode('utf-8')

            return decoded

        except Exception as e:
            logger.error(f"Decode error: {e}")
            return None

    def detect_sales_from_transfers(self, transfers: List[Dict]) -> List[Dict]:
        """
        Detect sales by analyzing transfer patterns

        A sale is typically:
        - Transfer from wallet A to wallet B
        - With non-zero transaction value
        - To/from known marketplace contracts (optional filter)

        Args:
            transfers: List of transfer events

        Returns:
            List of likely sales with prices
        """
        sales = []

        MARKETPLACE_ADDRESSES = {
            '0x7be8076f4ea4a4ad08075c2508e481d6c946d12b': 'opensea_v1',  # OpenSea V1
            '0x7f268357a8c2552623316e2562d90e642bb538e5': 'opensea_v2',  # OpenSea V2
            '0xcda72070e455bb31c7690a170224ce43623d0b6f': 'foundation',   # Foundation
            '0x65b49f7aee40347f5a90b714be4ef086f3fe5e2c': 'superrare',    # SuperRare
        }

        for transfer in transfers:
            # Check if from/to involves marketplace
            from_addr = transfer.get('from_address', '').lower()
            to_addr = transfer.get('to_address', '').lower()

            is_marketplace_sale = (
                from_addr in MARKETPLACE_ADDRESSES or
                to_addr in MARKETPLACE_ADDRESSES
            )

            # Check if transaction has value (price)
            value_wei = transfer.get('value_wei', 0)

            if is_marketplace_sale and value_wei > 0:
                sale = transfer.copy()
                sale['sale_type'] = 'marketplace'
                sale['marketplace'] = MARKETPLACE_ADDRESSES.get(from_addr) or MARKETPLACE_ADDRESSES.get(to_addr)
                sale['price_wei'] = value_wei
                sale['price_eth'] = value_wei / 1e18
                sales.append(sale)

        return sales


# CLI interface for testing
if __name__ == '__main__':
    import sys

    parser = BlockchainEventParser('ethereum')

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python blockchain_event_parser.py mints <contract_address> [from_block]")
        print("  python blockchain_event_parser.py transfers <contract_address> <token_id>")
        print("  python blockchain_event_parser.py tokenuri <contract_address> <token_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'mints':
        contract = sys.argv[2]
        from_block = int(sys.argv[3]) if len(sys.argv) > 3 else 0

        print(f"\nParsing mint events from {contract}...")
        mints = parser.get_nft_mints_from_contract(contract, from_block=from_block)

        print(f"\nFound {len(mints)} mints:")
        for mint in mints[:10]:  # Show first 10
            print(f"  Token {mint['token_id']} → {mint['to_address']}")
            print(f"    Block: {mint['block_number']}, TX: {mint['tx_hash']}")

    elif command == 'transfers':
        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        print(f"\nParsing transfers for {contract} #{token_id}...")
        transfers = parser.get_nft_transfers_for_token(contract, token_id)

        print(f"\nFound {len(transfers)} transfers:")
        for i, t in enumerate(transfers):
            print(f"\n{i+1}. Block {t['block_number']}")
            print(f"   {t['from_address']} → {t['to_address']}")
            if 'value_wei' in t and t['value_wei'] > 0:
                print(f"   Value: {t['value_wei'] / 1e18:.4f} ETH")

    elif command == 'tokenuri':
        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        print(f"\nGetting tokenURI for {contract} #{token_id}...")
        token_uri = parser.get_token_uri(contract, token_id)

        if token_uri:
            print(f"Token URI: {token_uri}")
        else:
            print("Failed to get token URI")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

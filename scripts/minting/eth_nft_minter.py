#!/usr/bin/env python3
"""
ETH NFT Minter - Ethereum NFT Minting for ARCHIV-IT NFT-8

Capabilities:
- Mint ERC-721 NFTs to Ethereum mainnet or testnets
- Upload metadata to IPFS via Pinata
- Gas estimation with safety margins
- Transaction signing and broadcasting
- Support for custom contracts and known platforms

SECURITY: Private keys are NEVER logged or stored.
Use environment variables or secure key management.
"""

import os
import json
import time
import hashlib
import requests
import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard ERC-721 ABI for minting
ERC721_MINT_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenURI", "type": "string"}
        ],
        "name": "safeMint",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenId", "type": "uint256"},
            {"name": "tokenURI", "type": "string"}
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# IPFS Gateways for verification
IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://gateway.pinata.cloud/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
]


class IPFSUploader:
    """Upload content to IPFS via Pinata"""

    def __init__(self):
        self.pinata_api_key = os.getenv('PINATA_API_KEY')
        self.pinata_secret = os.getenv('PINATA_SECRET_KEY')
        self.pinata_jwt = os.getenv('PINATA_JWT')

        if not self.pinata_jwt and not (self.pinata_api_key and self.pinata_secret):
            logger.warning("Pinata credentials not found. IPFS upload will fail.")

    def _get_headers(self) -> Dict:
        """Get authorization headers for Pinata"""
        if self.pinata_jwt:
            return {"Authorization": f"Bearer {self.pinata_jwt}"}
        else:
            return {
                "pinata_api_key": self.pinata_api_key,
                "pinata_secret_api_key": self.pinata_secret
            }

    def upload_json(self, data: Dict, name: str = "metadata") -> Optional[str]:
        """
        Upload JSON metadata to IPFS

        Args:
            data: JSON-serializable dict
            name: Name for the pin

        Returns:
            IPFS hash (CID) or None
        """
        try:
            url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

            payload = {
                "pinataContent": data,
                "pinataMetadata": {
                    "name": name,
                    "keyvalues": {
                        "source": "archivit-nft8",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            }

            headers = self._get_headers()
            headers["Content-Type"] = "application/json"

            response = requests.post(url, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result.get('IpfsHash')
                logger.info(f"Uploaded metadata to IPFS: {ipfs_hash}")
                return ipfs_hash
            else:
                logger.error(f"Pinata upload failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"IPFS upload error: {e}")
            return None

    def upload_file(self, file_path: Path, name: str = None) -> Optional[str]:
        """
        Upload file to IPFS

        Args:
            file_path: Path to file
            name: Optional name for the pin

        Returns:
            IPFS hash (CID) or None
        """
        try:
            url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

            name = name or file_path.name

            with open(file_path, 'rb') as f:
                files = {
                    'file': (name, f)
                }

                # Pinata metadata
                pinata_options = json.dumps({
                    "cidVersion": 1
                })
                pinata_metadata = json.dumps({
                    "name": name,
                    "keyvalues": {
                        "source": "archivit-nft8"
                    }
                })

                data = {
                    "pinataOptions": pinata_options,
                    "pinataMetadata": pinata_metadata
                }

                headers = self._get_headers()

                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                    ipfs_hash = result.get('IpfsHash')
                    logger.info(f"Uploaded file to IPFS: {ipfs_hash}")
                    return ipfs_hash
                else:
                    logger.error(f"Pinata file upload failed: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"IPFS file upload error: {e}")
            return None

    def verify_upload(self, ipfs_hash: str) -> bool:
        """Verify content is accessible on IPFS"""
        for gateway in IPFS_GATEWAYS:
            try:
                url = f"{gateway}{ipfs_hash}"
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Verified IPFS content via {gateway}")
                    return True
            except:
                continue

        logger.warning(f"Could not verify IPFS content: {ipfs_hash}")
        return False


class ETHNFTMinter:
    """
    Ethereum NFT Minting Engine

    Supports:
    - Custom ERC-721 contracts
    - Mainnet and testnets (Sepolia, Goerli)
    - Gas estimation with safety margins
    - Transaction tracking
    """

    # Network configurations
    NETWORKS = {
        'ethereum': {
            'chain_id': 1,
            'name': 'Ethereum Mainnet',
            'explorer': 'https://etherscan.io',
            'rpc_urls': [
                "https://cloudflare-eth.com",
                "https://eth.llamarpc.com",
                "https://rpc.ankr.com/eth",
            ]
        },
        'sepolia': {
            'chain_id': 11155111,
            'name': 'Sepolia Testnet',
            'explorer': 'https://sepolia.etherscan.io',
            'rpc_urls': [
                "https://rpc.sepolia.org",
                "https://sepolia.gateway.tenderly.co",
                "https://rpc2.sepolia.org",
            ]
        },
        'base': {
            'chain_id': 8453,
            'name': 'Base Mainnet',
            'explorer': 'https://basescan.org',
            'rpc_urls': [
                "https://mainnet.base.org",
                "https://base.llamarpc.com",
            ]
        },
        'polygon': {
            'chain_id': 137,
            'name': 'Polygon Mainnet',
            'explorer': 'https://polygonscan.com',
            'rpc_urls': [
                "https://polygon-rpc.com",
                "https://rpc.ankr.com/polygon",
            ]
        }
    }

    def __init__(self, network: str = 'ethereum'):
        """
        Initialize minter for specific network

        Args:
            network: 'ethereum', 'sepolia', 'base', 'polygon'
        """
        if network not in self.NETWORKS:
            raise ValueError(f"Unknown network: {network}. Supported: {list(self.NETWORKS.keys())}")

        self.network = network
        self.config = self.NETWORKS[network]
        self.chain_id = self.config['chain_id']

        # Add API key RPCs if available
        self._add_api_rpcs()

        self.ipfs = IPFSUploader()

        logger.info(f"ETHNFTMinter initialized for {self.config['name']}")

    def _add_api_rpcs(self):
        """Add authenticated RPC endpoints if keys available"""
        alchemy_key = os.getenv('ALCHEMY_API_KEY')
        infura_key = os.getenv('INFURA_API_KEY')

        if alchemy_key:
            if self.network == 'ethereum':
                self.config['rpc_urls'].insert(0, f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}")
            elif self.network == 'sepolia':
                self.config['rpc_urls'].insert(0, f"https://eth-sepolia.g.alchemy.com/v2/{alchemy_key}")
            elif self.network == 'polygon':
                self.config['rpc_urls'].insert(0, f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key}")
            elif self.network == 'base':
                self.config['rpc_urls'].insert(0, f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}")

        if infura_key:
            if self.network == 'ethereum':
                self.config['rpc_urls'].insert(1, f"https://mainnet.infura.io/v3/{infura_key}")
            elif self.network == 'sepolia':
                self.config['rpc_urls'].insert(1, f"https://sepolia.infura.io/v3/{infura_key}")

    def _rpc_call(self, method: str, params: List, timeout: int = 30) -> Optional[any]:
        """Make RPC call with failover"""
        for rpc_url in self.config['rpc_urls']:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 1
                }

                response = requests.post(rpc_url, json=payload, timeout=timeout)

                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result:
                        return result['result']
                    elif 'error' in result:
                        logger.warning(f"RPC error from {rpc_url}: {result['error']}")

            except Exception as e:
                logger.debug(f"RPC failed for {rpc_url}: {e}")
                continue

        return None

    def get_gas_price(self) -> Optional[int]:
        """Get current gas price in wei"""
        result = self._rpc_call('eth_gasPrice', [])
        if result:
            return int(result, 16)
        return None

    def get_nonce(self, address: str) -> Optional[int]:
        """Get transaction count (nonce) for address"""
        result = self._rpc_call('eth_getTransactionCount', [address, 'pending'])
        if result:
            return int(result, 16)
        return None

    def get_balance(self, address: str) -> Optional[int]:
        """Get ETH balance in wei"""
        result = self._rpc_call('eth_getBalance', [address, 'latest'])
        if result:
            return int(result, 16)
        return None

    def estimate_gas(self, tx_data: Dict) -> Optional[int]:
        """Estimate gas for transaction"""
        result = self._rpc_call('eth_estimateGas', [tx_data])
        if result:
            return int(result, 16)
        return None

    def send_raw_transaction(self, signed_tx: str) -> Optional[str]:
        """Broadcast signed transaction"""
        result = self._rpc_call('eth_sendRawTransaction', [signed_tx])
        return result

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction receipt"""
        return self._rpc_call('eth_getTransactionReceipt', [tx_hash])

    def prepare_nft_metadata(
        self,
        name: str,
        description: str,
        image_path: Optional[Path] = None,
        image_ipfs: Optional[str] = None,
        attributes: List[Dict] = None,
        external_url: str = None,
        animation_url: str = None
    ) -> Tuple[Optional[str], Dict]:
        """
        Prepare NFT metadata and upload to IPFS

        Args:
            name: NFT name
            description: NFT description
            image_path: Local path to image (will upload to IPFS)
            image_ipfs: Existing IPFS hash for image
            attributes: List of trait dicts [{"trait_type": "...", "value": "..."}]
            external_url: Link to external page
            animation_url: Animation/video URL

        Returns:
            Tuple of (metadata_ipfs_hash, metadata_dict)
        """
        # Upload image if local path provided
        if image_path and not image_ipfs:
            logger.info(f"Uploading image to IPFS: {image_path}")
            image_ipfs = self.ipfs.upload_file(image_path)
            if not image_ipfs:
                logger.error("Failed to upload image to IPFS")
                return None, {}

        # Build metadata following OpenSea/ERC-721 standard
        metadata = {
            "name": name,
            "description": description,
            "image": f"ipfs://{image_ipfs}" if image_ipfs else None,
            "attributes": attributes or [],
        }

        if external_url:
            metadata["external_url"] = external_url

        if animation_url:
            metadata["animation_url"] = animation_url

        # Add ARCHIV-IT provenance
        metadata["properties"] = {
            "created_by": "ARCHIV-IT NFT-8",
            "created_at": datetime.utcnow().isoformat(),
            "sovereignty": "user-owned"
        }

        # Upload metadata to IPFS
        logger.info("Uploading metadata to IPFS...")
        metadata_hash = self.ipfs.upload_json(metadata, name=f"metadata_{name}")

        if metadata_hash:
            # Verify upload
            self.ipfs.verify_upload(metadata_hash)
            return metadata_hash, metadata

        return None, metadata

    def build_mint_transaction(
        self,
        contract_address: str,
        to_address: str,
        token_uri: str,
        from_address: str,
        gas_limit: int = None,
        gas_price: int = None,
        max_priority_fee: int = None
    ) -> Optional[Dict]:
        """
        Build mint transaction data

        Args:
            contract_address: NFT contract address
            to_address: Recipient address
            token_uri: IPFS URI for metadata (ipfs://...)
            from_address: Sender address
            gas_limit: Optional gas limit override
            gas_price: Optional gas price override
            max_priority_fee: Optional priority fee (for EIP-1559)

        Returns:
            Transaction dict ready for signing
        """
        try:
            # Encode safeMint(address to, string tokenURI) function call
            # Function selector: keccak256("safeMint(address,string)")[:4]
            function_selector = "0xd204c45e"  # safeMint(address,string)

            # Encode parameters
            # address (32 bytes, padded)
            to_padded = to_address.lower().replace('0x', '').zfill(64)

            # string offset (points to where string data starts)
            # First param is 32 bytes, so string starts at offset 64 (0x40)
            string_offset = "0000000000000000000000000000000000000000000000000000000000000040"

            # string length
            token_uri_bytes = token_uri.encode('utf-8')
            string_length = hex(len(token_uri_bytes))[2:].zfill(64)

            # string data (padded to 32-byte boundary)
            string_hex = token_uri_bytes.hex()
            padding_needed = (32 - (len(token_uri_bytes) % 32)) % 32
            string_padded = string_hex + ('00' * padding_needed)

            # Combine
            data = function_selector + to_padded + string_offset + string_length + string_padded

            # Get nonce
            nonce = self.get_nonce(from_address)
            if nonce is None:
                logger.error("Failed to get nonce")
                return None

            # Get gas price if not provided
            if not gas_price:
                gas_price = self.get_gas_price()
                if gas_price:
                    # Add 10% safety margin
                    gas_price = int(gas_price * 1.1)

            # Estimate gas if not provided
            tx_for_estimate = {
                'from': from_address,
                'to': contract_address,
                'data': data
            }

            if not gas_limit:
                estimated = self.estimate_gas(tx_for_estimate)
                if estimated:
                    # Add 20% safety margin for NFT mints
                    gas_limit = int(estimated * 1.2)
                else:
                    # Fallback for NFT mint
                    gas_limit = 200000

            # Build transaction
            tx = {
                'nonce': nonce,
                'to': contract_address,
                'value': 0,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'data': data,
                'chainId': self.chain_id
            }

            logger.info(f"Built mint transaction:")
            logger.info(f"  To contract: {contract_address}")
            logger.info(f"  Recipient: {to_address}")
            logger.info(f"  Token URI: {token_uri}")
            logger.info(f"  Gas limit: {gas_limit:,}")
            logger.info(f"  Gas price: {gas_price / 1e9:.2f} gwei")
            logger.info(f"  Estimated cost: {(gas_limit * gas_price) / 1e18:.6f} ETH")

            return tx

        except Exception as e:
            logger.error(f"Failed to build transaction: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def sign_transaction(self, tx: Dict, private_key: str) -> Optional[str]:
        """
        Sign transaction with private key

        SECURITY: Private key is used only in memory, never logged or stored.

        Args:
            tx: Transaction dict
            private_key: Private key (with or without 0x prefix)

        Returns:
            Signed transaction hex string
        """
        try:
            # Import web3 for signing (required dependency)
            from eth_account import Account
            from eth_account.signers.local import LocalAccount

            # Ensure private key has 0x prefix
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key

            # Create account from private key
            account: LocalAccount = Account.from_key(private_key)

            logger.info(f"Signing transaction from: {account.address}")

            # Sign transaction
            signed = account.sign_transaction(tx)

            # Return raw transaction hex
            return signed.raw_transaction.hex()

        except ImportError:
            logger.error("eth-account package required. Install with: pip install eth-account")
            return None
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            return None

    def mint_nft(
        self,
        contract_address: str,
        to_address: str,
        name: str,
        description: str,
        image_path: Path = None,
        image_ipfs: str = None,
        attributes: List[Dict] = None,
        private_key: str = None,
        dry_run: bool = False
    ) -> Dict:
        """
        Complete NFT minting flow

        Args:
            contract_address: ERC-721 contract address
            to_address: Recipient address
            name: NFT name
            description: NFT description
            image_path: Local image path (will upload to IPFS)
            image_ipfs: Existing IPFS hash for image
            attributes: NFT attributes/traits
            private_key: Private key for signing (env var MINTER_PRIVATE_KEY used if not provided)
            dry_run: If True, prepare but don't broadcast

        Returns:
            Result dict with tx_hash, metadata, etc.
        """
        result = {
            'success': False,
            'network': self.network,
            'contract': contract_address,
            'recipient': to_address,
            'name': name,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # Step 1: Prepare and upload metadata
            logger.info("Step 1: Preparing NFT metadata...")
            metadata_hash, metadata = self.prepare_nft_metadata(
                name=name,
                description=description,
                image_path=image_path,
                image_ipfs=image_ipfs,
                attributes=attributes
            )

            if not metadata_hash:
                result['error'] = "Failed to upload metadata to IPFS"
                return result

            result['metadata_ipfs'] = metadata_hash
            result['metadata'] = metadata
            result['token_uri'] = f"ipfs://{metadata_hash}"

            # Step 2: Get private key
            if not private_key:
                private_key = os.getenv('MINTER_PRIVATE_KEY')

            if not private_key:
                result['error'] = "No private key provided. Set MINTER_PRIVATE_KEY env var."
                return result

            # Get from_address from private key
            from eth_account import Account
            account = Account.from_key(private_key if private_key.startswith('0x') else '0x' + private_key)
            from_address = account.address

            result['from_address'] = from_address

            # Step 3: Check balance
            logger.info("Step 2: Checking wallet balance...")
            balance = self.get_balance(from_address)
            if balance:
                result['balance_eth'] = balance / 1e18
                logger.info(f"Wallet balance: {result['balance_eth']:.6f} ETH")

            # Step 4: Build transaction
            logger.info("Step 3: Building mint transaction...")
            tx = self.build_mint_transaction(
                contract_address=contract_address,
                to_address=to_address,
                token_uri=result['token_uri'],
                from_address=from_address
            )

            if not tx:
                result['error'] = "Failed to build transaction"
                return result

            result['transaction'] = {
                'nonce': tx['nonce'],
                'gas_limit': tx['gas'],
                'gas_price_gwei': tx['gasPrice'] / 1e9,
                'estimated_cost_eth': (tx['gas'] * tx['gasPrice']) / 1e18
            }

            if dry_run:
                logger.info("DRY RUN - Transaction not broadcast")
                result['dry_run'] = True
                result['success'] = True
                return result

            # Step 5: Sign transaction
            logger.info("Step 4: Signing transaction...")
            signed_tx = self.sign_transaction(tx, private_key)

            if not signed_tx:
                result['error'] = "Failed to sign transaction"
                return result

            # Step 6: Broadcast transaction
            logger.info("Step 5: Broadcasting transaction...")
            tx_hash = self.send_raw_transaction(signed_tx)

            if not tx_hash:
                result['error'] = "Failed to broadcast transaction"
                return result

            result['tx_hash'] = tx_hash
            result['explorer_url'] = f"{self.config['explorer']}/tx/{tx_hash}"

            logger.info(f"Transaction broadcast: {tx_hash}")
            logger.info(f"Explorer: {result['explorer_url']}")

            # Step 7: Wait for confirmation (optional)
            logger.info("Step 6: Waiting for confirmation...")
            for i in range(30):  # Wait up to 5 minutes
                receipt = self.get_transaction_receipt(tx_hash)
                if receipt:
                    result['block_number'] = int(receipt['blockNumber'], 16)
                    result['gas_used'] = int(receipt['gasUsed'], 16)
                    result['status'] = 'success' if receipt['status'] == '0x1' else 'failed'
                    result['success'] = receipt['status'] == '0x1'

                    logger.info(f"Transaction confirmed in block {result['block_number']}")
                    logger.info(f"Gas used: {result['gas_used']:,}")
                    break

                time.sleep(10)
            else:
                result['status'] = 'pending'
                result['success'] = True  # Tx was broadcast successfully
                logger.info("Transaction pending confirmation")

            return result

        except Exception as e:
            logger.error(f"Minting failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            result['error'] = str(e)
            return result


def mint_masters_visualization(dry_run: bool = True) -> Dict:
    """
    Mint the 22 NORTHSTAR Masters visualization as an NFT

    This is a special function for minting the ARCHIV-IT Masters visualization.
    """
    minter = ETHNFTMinter(network='ethereum')

    # Masters visualization metadata
    attributes = [
        {"trait_type": "Type", "value": "Interactive Visualization"},
        {"trait_type": "Masters Count", "value": 22},
        {"trait_type": "Feminine Masters", "value": 9},
        {"trait_type": "Masculine Masters", "value": 13},
        {"trait_type": "Technology", "value": "Three.js WebGL"},
        {"trait_type": "Platform", "value": "ARCHIV-IT"},
        {"trait_type": "Sovereignty", "value": "User-Owned"},
    ]

    # The visualization HTML could be uploaded to IPFS
    viz_path = Path("public/masters_point_cloud_v3_spectral.html")

    result = minter.mint_nft(
        contract_address=os.getenv('NFT_CONTRACT_ADDRESS', ''),  # User must provide
        to_address=os.getenv('MINTER_ADDRESS', ''),  # User must provide
        name="22 NORTHSTAR Masters - Spectral Visualization",
        description="Interactive 4D visualization of the 22 NORTHSTAR Masters in spectral space. "
                   "9 feminine and 13 masculine masters represented as constellation nodes. "
                   "Created with ARCHIV-IT - Local-First User-Sovereign Data Platform.",
        image_path=None,  # Would need a preview image
        attributes=attributes,
        dry_run=dry_run
    )

    return result


# CLI Interface
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("""
ETH NFT Minter - ARCHIV-IT NFT-8

Usage:
  python eth_nft_minter.py test              Test IPFS upload
  python eth_nft_minter.py balance <addr>    Check wallet balance
  python eth_nft_minter.py gas               Get current gas price
  python eth_nft_minter.py mint-masters      Mint Masters visualization (dry run)
  python eth_nft_minter.py mint-masters --live   Actually mint (requires config)

Environment Variables:
  PINATA_JWT           - Pinata JWT for IPFS uploads
  PINATA_API_KEY       - Alternative: Pinata API key
  PINATA_SECRET_KEY    - Alternative: Pinata secret
  MINTER_PRIVATE_KEY   - Private key for signing (KEEP SECRET!)
  MINTER_ADDRESS       - Your wallet address
  NFT_CONTRACT_ADDRESS - ERC-721 contract to mint on
  ALCHEMY_API_KEY      - Optional: Alchemy RPC key
  INFURA_API_KEY       - Optional: Infura RPC key
        """)
        sys.exit(0)

    command = sys.argv[1]

    if command == 'test':
        print("\nTesting IPFS Upload...")
        uploader = IPFSUploader()

        test_data = {
            "name": "Test NFT",
            "description": "Testing ARCHIV-IT NFT-8 IPFS upload",
            "test": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        ipfs_hash = uploader.upload_json(test_data, "test_upload")

        if ipfs_hash:
            print(f"Upload successful: ipfs://{ipfs_hash}")
            print(f"Gateway URL: https://ipfs.io/ipfs/{ipfs_hash}")

            # Verify
            if uploader.verify_upload(ipfs_hash):
                print("Verification: PASSED")
            else:
                print("Verification: PENDING (may take a few minutes)")
        else:
            print("Upload failed. Check Pinata credentials.")

    elif command == 'balance':
        if len(sys.argv) < 3:
            print("Usage: python eth_nft_minter.py balance <address>")
            sys.exit(1)

        address = sys.argv[2]
        minter = ETHNFTMinter('ethereum')

        balance = minter.get_balance(address)
        if balance is not None:
            print(f"\nAddress: {address}")
            print(f"Balance: {balance / 1e18:.6f} ETH")
        else:
            print("Failed to get balance")

    elif command == 'gas':
        minter = ETHNFTMinter('ethereum')

        gas_price = minter.get_gas_price()
        if gas_price:
            print(f"\nCurrent Gas Price:")
            print(f"  {gas_price / 1e9:.2f} gwei")
            print(f"  {gas_price} wei")

            # Estimate mint cost
            typical_mint_gas = 150000
            cost_eth = (typical_mint_gas * gas_price) / 1e18
            print(f"\nEstimated NFT mint cost (~150k gas):")
            print(f"  {cost_eth:.6f} ETH")
        else:
            print("Failed to get gas price")

    elif command == 'mint-masters':
        live = '--live' in sys.argv

        print("\n" + "="*60)
        print("ARCHIV-IT NFT-8 - Mint Masters Visualization")
        print("="*60)

        if not live:
            print("\nDRY RUN MODE - No transaction will be broadcast")
            print("Use --live flag to actually mint")

        result = mint_masters_visualization(dry_run=not live)

        print("\nResult:")
        print(json.dumps(result, indent=2, default=str))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

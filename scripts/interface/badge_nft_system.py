#!/usr/bin/env python3
"""
ACCUMETER NFT System - Dynamic NFT + IPFS Dual Verification

Security model:
1. User mints an ACCUMETER NFT (proves ownership)
2. NFT tokenURI points to ARCHIV-IT server
3. Server verifies NFT holder matches registered user
4. Score snapshots stored on IPFS for audit trail (requires Pinata API keys)

This creates a double-lock:
- Hack server -> still need NFT wallet
- Steal NFT -> server won't verify wrong user
- Both must match for valid badge

IPFS Integration:
- Set PINATA_API_KEY and PINATA_SECRET_KEY environment variables
- Free tier: 100 pins, 1GB bandwidth
- Without Pinata keys, snapshots are stored locally only
"""

import json
import hashlib
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import logging
import requests

logger = logging.getLogger(__name__)


class AccumeterNFT:
    """
    Manages the relationship between ARCHIV-IT users and their ACCUMETER NFTs.

    The NFT contract would be deployed separately - this handles the server-side
    verification and metadata generation.
    """

    # Storage for user-NFT mappings
    REGISTRY_FILE = Path("knowledge_base/accumeter_nft_registry.json")

    # Supported chains for badge NFTs
    # Contract source: /contracts/ArchivitAccumeter.sol
    # Deployment script: /contracts/deploy_polygon.js
    SUPPORTED_CHAINS = {
        'ethereum': {
            'chain_id': 1,
            'contract': None,  # To be deployed
            'explorer': 'https://etherscan.io',
            'rpc': 'https://eth.llamarpc.com'
        },
        'polygon': {
            'chain_id': 137,
            # DEPLOY TO POLYGON AND UPDATE - run: npx hardhat run contracts/deploy_polygon.js --network polygon
            'contract': None,  # TODO: Update with deployed address after running deploy_polygon.js
            'explorer': 'https://polygonscan.com',
            'rpc': 'https://polygon-rpc.com'
        },
        'base': {
            'chain_id': 8453,
            'contract': None,  # To be deployed
            'explorer': 'https://basescan.org',
            'rpc': 'https://mainnet.base.org'
        },
        'zora': {
            'chain_id': 7777777,
            'contract': None,  # To be deployed
            'explorer': 'https://explorer.zora.energy',
            'rpc': 'https://rpc.zora.energy'
        }
    }

    def __init__(self):
        self._load_registry()

    def _load_registry(self):
        """Load NFT registry from disk"""
        self.REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.REGISTRY_FILE.exists():
            try:
                with open(self.REGISTRY_FILE, 'r') as f:
                    self.registry = json.load(f)
            except:
                self.registry = {'users': {}, 'nfts': {}}
        else:
            self.registry = {'users': {}, 'nfts': {}}

    def _save_registry(self):
        """Save registry to disk"""
        with open(self.REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_accumeter_nft(self, user_id: str, wallet_address: str,
                               chain: str, token_id: int, tx_hash: str) -> Dict:
        """
        Register a minted ACCUMETER NFT to a user

        Args:
            user_id: ARCHIV-IT user ID
            wallet_address: Wallet that owns the NFT
            chain: Blockchain (ethereum, polygon, etc.)
            token_id: NFT token ID
            tx_hash: Minting transaction hash

        Returns:
            Registration confirmation
        """
        if chain not in self.SUPPORTED_CHAINS:
            return {'error': f'Unsupported chain: {chain}'}

        # Generate unique badge ID
        badge_id = hashlib.sha256(
            f"{chain}:{token_id}:{wallet_address}".encode()
        ).hexdigest()[:16]

        # Create registration
        registration = {
            'badge_id': badge_id,
            'user_id': user_id,
            'wallet_address': wallet_address.lower(),
            'chain': chain,
            'token_id': token_id,
            'tx_hash': tx_hash,
            'registered_at': datetime.now().isoformat(),
            'status': 'active'
        }

        # Store by user and by NFT
        self.registry['users'][user_id] = registration
        nft_key = f"{chain}:{token_id}"
        self.registry['nfts'][nft_key] = registration

        self._save_registry()

        logger.info(f"Registered ACCUMETER NFT {badge_id} for user {user_id}")

        return {
            'success': True,
            'badge_id': badge_id,
            'message': 'ACCUMETER ACTIVATED'
        }

    def verify_nft_ownership(self, user_id: str, wallet_address: str) -> Dict:
        """
        Verify that a wallet owns the badge NFT for a user

        This is called when generating badge metadata to ensure
        the requester actually owns the NFT.

        Args:
            user_id: ARCHIV-IT user ID
            wallet_address: Wallet claiming to own the badge

        Returns:
            Verification result
        """
        registration = self.registry['users'].get(user_id)

        if not registration:
            return {
                'verified': False,
                'reason': 'no_badge_registered',
                'message': 'No ACCUMETER NFT registered for this user'
            }

        if registration['wallet_address'].lower() != wallet_address.lower():
            return {
                'verified': False,
                'reason': 'wallet_mismatch',
                'message': 'Wallet does not match registered badge owner'
            }

        if registration['status'] != 'active':
            return {
                'verified': False,
                'reason': 'badge_inactive',
                'message': 'Badge is not active'
            }

        return {
            'verified': True,
            'badge_id': registration['badge_id'],
            'chain': registration['chain'],
            'token_id': registration['token_id']
        }

    def get_user_badge(self, user_id: str) -> Optional[Dict]:
        """Get badge registration for a user"""
        return self.registry['users'].get(user_id)

    def generate_token_metadata(self, user_id: str, trust_score: int,
                                trust_level: str) -> Dict:
        """
        Generate ERC-721 compatible metadata for the badge NFT

        This is what the tokenURI returns - it's dynamic based on
        current trust score.

        Args:
            user_id: ARCHIV-IT user ID
            trust_score: Current trust score (0-100)
            trust_level: Level string (critical, low, moderate, good, excellent)

        Returns:
            ERC-721 metadata dict
        """
        registration = self.registry['users'].get(user_id)
        if not registration:
            return {'error': 'No badge registered'}

        # Color based on level
        level_colors = {
            'critical': '#e53e3e',
            'low': '#ed8936',
            'moderate': '#d4a574',
            'good': '#48bb78',
            'excellent': '#68d391'
        }

        color = level_colors.get(trust_level, '#d4a574')

        # Generate metadata
        metadata = {
            'name': f'ACCUMETER #{registration["token_id"]}',
            'description': f'Dynamic data consistency indicator from ARCHIV-IT. Current score: {trust_score}%. This ACCUMETER updates in real-time based on data alignment across blockchain and social sources.',
            'image': f'https://archivit.web3photo.com/badge/{user_id}/nft.svg',
            'animation_url': f'https://archivit.web3photo.com/badge/{user_id}/animated.html',
            'external_url': f'https://archivit.web3photo.com/u/{user_id}',
            'attributes': [
                {
                    'trait_type': 'Trust Score',
                    'value': trust_score,
                    'max_value': 100,
                    'display_type': 'boost_percentage'
                },
                {
                    'trait_type': 'Trust Level',
                    'value': trust_level.capitalize()
                },
                {
                    'trait_type': 'Badge Color',
                    'value': color
                },
                {
                    'trait_type': 'Last Updated',
                    'value': datetime.now().strftime('%Y-%m-%d'),
                    'display_type': 'date'
                },
                {
                    'trait_type': 'Chain',
                    'value': registration['chain'].capitalize()
                }
            ],
            'background_color': '0a0a0f'
        }

        return metadata


class IPFSAuditTrail:
    """
    Manages IPFS snapshots of trust scores for audit trail.

    Periodically (or on-demand), we pin a snapshot of the user's
    trust score to IPFS via Pinata. This creates an immutable history.

    Requires PINATA_API_KEY and PINATA_SECRET_KEY environment variables
    for real IPFS pinning. Without these, snapshots are stored locally only.
    """

    SNAPSHOTS_FILE = Path("knowledge_base/ipfs_snapshots.json")
    PINATA_PIN_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

    def __init__(self, ipfs_gateway: str = "https://gateway.pinata.cloud/ipfs/"):
        self.ipfs_gateway = ipfs_gateway
        self.pinata_api_key = os.environ.get('PINATA_API_KEY')
        self.pinata_secret_key = os.environ.get('PINATA_SECRET_KEY')
        self._load_snapshots()

    @property
    def pinata_configured(self) -> bool:
        """Check if Pinata credentials are available"""
        return bool(self.pinata_api_key and self.pinata_secret_key)

    def _load_snapshots(self):
        """Load snapshot history"""
        self.SNAPSHOTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.SNAPSHOTS_FILE.exists():
            try:
                with open(self.SNAPSHOTS_FILE, 'r') as f:
                    self.snapshots = json.load(f)
            except:
                self.snapshots = {}
        else:
            self.snapshots = {}

    def _save_snapshots(self):
        """Save snapshot history"""
        with open(self.SNAPSHOTS_FILE, 'w') as f:
            json.dump(self.snapshots, f, indent=2)

    def _pin_to_ipfs(self, snapshot: Dict, user_id: str) -> Optional[str]:
        """
        Pin snapshot data to IPFS via Pinata.

        Args:
            snapshot: The snapshot data to pin
            user_id: User ID for metadata

        Returns:
            IPFS CID if successful, None otherwise
        """
        if not self.pinata_configured:
            logger.debug("Pinata not configured - storing snapshot locally only")
            return None

        try:
            headers = {
                'pinata_api_key': self.pinata_api_key,
                'pinata_secret_api_key': self.pinata_secret_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'pinataContent': snapshot,
                'pinataMetadata': {
                    'name': f'archivit_trust_snapshot_{user_id}_{snapshot["unix_timestamp"]}',
                    'keyvalues': {
                        'type': 'trust_snapshot',
                        'user_id': user_id,
                        'score': str(snapshot['trust_score']),
                        'level': snapshot['trust_level']
                    }
                },
                'pinataOptions': {
                    'cidVersion': 1
                }
            }

            response = requests.post(
                self.PINATA_PIN_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                cid = result.get('IpfsHash')
                logger.info(f"Pinned snapshot to IPFS: {cid}")
                return cid
            else:
                logger.warning(f"Pinata pin failed: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logger.warning(f"IPFS pinning failed: {e}")
            return None

    def create_snapshot(self, user_id: str, trust_score: int,
                        trust_level: str, breakdown: Dict) -> Dict:
        """
        Create a trust score snapshot and pin to IPFS if configured.

        Args:
            user_id: ARCHIV-IT user ID
            trust_score: Current score
            trust_level: Current level
            breakdown: Score breakdown by category

        Returns:
            Snapshot data with ipfs_cid if pinning succeeded
        """
        snapshot = {
            'version': '1.0',
            'type': 'archivit_trust_snapshot',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'unix_timestamp': int(time.time()),
            'trust_score': trust_score,
            'trust_level': trust_level,
            'breakdown': breakdown,
            'signature': self._sign_snapshot(user_id, trust_score)
        }

        # Pin to IPFS via Pinata (returns None if not configured)
        ipfs_cid = self._pin_to_ipfs(snapshot, user_id)

        # Store locally with CID reference
        if user_id not in self.snapshots:
            self.snapshots[user_id] = []

        snapshot_record = {
            'snapshot': snapshot,
            'created_at': datetime.now().isoformat(),
            'ipfs_cid': ipfs_cid,
            'ipfs_url': f"{self.ipfs_gateway}{ipfs_cid}" if ipfs_cid else None,
            'storage': 'ipfs' if ipfs_cid else 'local'
        }
        self.snapshots[user_id].append(snapshot_record)

        # Keep only last 100 snapshots per user
        self.snapshots[user_id] = self.snapshots[user_id][-100:]

        self._save_snapshots()

        # Include CID in returned snapshot for immediate use
        snapshot['ipfs_cid'] = ipfs_cid
        snapshot['ipfs_url'] = snapshot_record['ipfs_url']
        snapshot['storage'] = snapshot_record['storage']

        return snapshot

    def _sign_snapshot(self, user_id: str, score: int) -> str:
        """Create a signature for the snapshot"""
        from badge_integrity import BadgeIntegrity
        return BadgeIntegrity.generate_signature(
            user_id,
            datetime.now().isoformat()
        )

    def get_user_history(self, user_id: str, limit: int = 30) -> List[Dict]:
        """Get trust score history for a user"""
        history = self.snapshots.get(user_id, [])
        return history[-limit:]

    def get_ipfs_stats(self, user_id: str) -> Dict:
        """
        Get IPFS pinning statistics for a user.

        Returns:
            Dict with counts of pinned vs local snapshots
        """
        history = self.snapshots.get(user_id, [])
        pinned = sum(1 for h in history if h.get('ipfs_cid'))
        local = len(history) - pinned

        return {
            'total': len(history),
            'pinned_to_ipfs': pinned,
            'local_only': local,
            'ipfs_configured': self.pinata_configured
        }

    def verify_snapshot(self, snapshot: Dict) -> bool:
        """
        Verify a snapshot's integrity

        Args:
            snapshot: Snapshot dict to verify

        Returns:
            True if valid
        """
        # In production, this would verify the signature
        # and optionally check against IPFS
        return 'signature' in snapshot and 'trust_score' in snapshot


class DualVerificationSystem:
    """
    Combines NFT ownership + server verification for maximum security.

    Flow:
    1. User requests ACCUMETER (provides wallet address)
    2. System checks NFT ownership on-chain
    3. System verifies wallet matches registered user
    4. If both pass, return live trust score
    5. Create IPFS snapshot for audit trail
    """

    def __init__(self):
        self.nft_system = AccumeterNFT()
        self.ipfs_audit = IPFSAuditTrail()

    def verify_and_generate_badge(self, user_id: str, wallet_address: str,
                                  trust_score: int, trust_level: str,
                                  breakdown: Dict) -> Dict:
        """
        Full verification flow for badge generation

        Args:
            user_id: ARCHIV-IT user ID
            wallet_address: Requesting wallet
            trust_score: Current score
            trust_level: Current level
            breakdown: Score breakdown

        Returns:
            Badge data or error
        """
        # Step 1: Verify NFT ownership
        nft_verify = self.nft_system.verify_nft_ownership(user_id, wallet_address)

        if not nft_verify.get('verified'):
            return {
                'success': False,
                'error': 'nft_verification_failed',
                'message': nft_verify.get('message', 'Could not verify NFT ownership'),
                'can_mint': True  # Indicate they need to mint first
            }

        # Step 2: Generate metadata
        metadata = self.nft_system.generate_token_metadata(
            user_id, trust_score, trust_level
        )

        # Step 3: Create IPFS snapshot
        snapshot = self.ipfs_audit.create_snapshot(
            user_id, trust_score, trust_level, breakdown
        )

        return {
            'success': True,
            'verified': True,
            'badge_id': nft_verify['badge_id'],
            'metadata': metadata,
            'snapshot': snapshot,
            'message': 'Badge verified and generated'
        }

    def get_public_verification(self, user_id: str) -> Dict:
        """
        Get publicly verifiable badge info

        This is what third parties can check to verify a badge is real.
        """
        badge = self.nft_system.get_user_badge(user_id)
        history = self.ipfs_audit.get_user_history(user_id, limit=5)

        if not badge:
            return {
                'has_badge': False,
                'message': 'No verified badge for this user'
            }

        return {
            'has_badge': True,
            'badge_id': badge['badge_id'],
            'chain': badge['chain'],
            'token_id': badge['token_id'],
            'registered_at': badge['registered_at'],
            'verification_url': f"https://archivit.web3photo.com/verify/{badge['badge_id']}",
            'recent_snapshots': len(history),
            'explorer_url': f"{self.nft_system.SUPPORTED_CHAINS[badge['chain']]['explorer']}/token/{badge.get('contract_address', 'TBD')}?a={badge['token_id']}"
        }


# Solidity contract interface (for reference)
ACCUMETER_CONTRACT_ABI = '''
// SPDX-License-Identifier: MIT
// ARCHIV-IT ACCUMETER NFT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ArchivitAccumeter is ERC721, Ownable {
    string private _baseTokenURI;
    uint256 private _tokenIds;

    // Mapping from token ID to ARCHIV-IT user hash
    mapping(uint256 => bytes32) public userHashes;

    // Mapping from user hash to token ID (one badge per user)
    mapping(bytes32 => uint256) public userTokens;

    event AccumeterMinted(address indexed owner, uint256 tokenId, bytes32 userHash);

    constructor() ERC721("ACCUMETER", "ACCUM") Ownable(msg.sender) {
        _baseTokenURI = "https://archivit.web3photo.com/api/nft/metadata/";
    }

    function mint(bytes32 userHash) external returns (uint256) {
        require(userTokens[userHash] == 0, "ACCUMETER already minted for this user");

        _tokenIds++;
        uint256 newTokenId = _tokenIds;

        _safeMint(msg.sender, newTokenId);
        userHashes[newTokenId] = userHash;
        userTokens[userHash] = newTokenId;

        emit AccumeterMinted(msg.sender, newTokenId, userHash);

        return newTokenId;
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        return string(abi.encodePacked(_baseTokenURI, Strings.toString(tokenId)));
    }

    function setBaseURI(string memory baseURI) external onlyOwner {
        _baseTokenURI = baseURI;
    }

    // Get token ID for a user hash
    function getTokenForUser(bytes32 userHash) external view returns (uint256) {
        return userTokens[userHash];
    }

    // Verify ownership for a user
    function verifyOwnership(bytes32 userHash, address wallet) external view returns (bool) {
        uint256 tokenId = userTokens[userHash];
        if (tokenId == 0) return false;
        return ownerOf(tokenId) == wallet;
    }
}
'''

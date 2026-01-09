# ARCHIV-IT ACCUMETER Smart Contracts

This directory contains the ERC-721 smart contract and deployment scripts for the ARCHIV-IT ACCUMETER NFT system.

## Overview

The ACCUMETER NFT is a dynamic badge that represents a user's data consistency score within the ARCHIV-IT system. Each NFT:

- Links to a unique ARCHIV-IT user via a `userHash` (keccak256 of user ID)
- Returns dynamic metadata via tokenURI pointing to the ARCHIV-IT server
- Enforces one NFT per user (cannot mint duplicate badges)
- Provides on-chain verification of ownership

## Contract: ArchivitAccumeter.sol

### Key Functions

| Function | Description |
|----------|-------------|
| `mint(bytes32 userHash)` | Mint new ACCUMETER NFT for a user |
| `verifyOwnership(bytes32 userHash, address wallet)` | Check if wallet owns the badge for a user |
| `tokenURI(uint256 tokenId)` | Returns metadata URL: `https://archivit.web3photo.com/api/nft/metadata/{tokenId}` |
| `getTokenForUser(bytes32 userHash)` | Get token ID for a user hash |
| `hasMinted(bytes32 userHash)` | Check if user already has an ACCUMETER |

### Events

- `AccumeterMinted(address owner, uint256 tokenId, bytes32 userHash)` - Emitted on mint

## Prerequisites

1. **Node.js** (v18+ recommended)
2. **Hardhat** development environment
3. **Wallet with MATIC** (for Polygon deployment)
4. **API Keys** (for contract verification)

## Setup

### 1. Install Dependencies

From the project root directory:

```bash
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox @openzeppelin/contracts dotenv
```

### 2. Initialize Hardhat

```bash
npx hardhat init
# Select "Create a JavaScript project"
```

### 3. Configure Environment

Create `.env` file in project root:

```env
# Polygon Mainnet
POLYGON_RPC_URL=https://polygon-rpc.com
# Or use Alchemy: https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY

# Polygon Mumbai Testnet
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com

# Deployer wallet (KEEP SECRET - never commit!)
PRIVATE_KEY=your_private_key_here

# For contract verification
POLYGONSCAN_API_KEY=your_polygonscan_api_key
```

### 4. Configure Hardhat

Update `hardhat.config.js`:

```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    polygon: {
      url: process.env.POLYGON_RPC_URL || "https://polygon-rpc.com",
      chainId: 137,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    mumbai: {
      url: process.env.MUMBAI_RPC_URL || "https://rpc-mumbai.maticvigil.com",
      chainId: 80001,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }
  },
  etherscan: {
    apiKey: {
      polygon: process.env.POLYGONSCAN_API_KEY,
      polygonMumbai: process.env.POLYGONSCAN_API_KEY
    }
  }
};
```

### 5. Move Contract and Script

```bash
# Create Hardhat directories if needed
mkdir -p contracts scripts

# Contract is already at contracts/ArchivitAccumeter.sol
# Move deployment script to scripts folder
cp contracts/deploy_polygon.js scripts/deploy_polygon.js
```

## Deployment

### Testnet (Mumbai) - Recommended First

```bash
# Get testnet MATIC from faucet: https://faucet.polygon.technology/

npx hardhat run scripts/deploy_polygon.js --network mumbai
```

### Mainnet (Polygon)

```bash
# Ensure wallet has MATIC for gas (0.1+ MATIC recommended)

npx hardhat run scripts/deploy_polygon.js --network polygon
```

### Expected Output

```
============================================================
ARCHIV-IT ACCUMETER NFT - Deployment Script
============================================================

Network: polygon
Chain ID: 137
Deployer: 0x...

Deploying ArchivitAccumeter contract...

------------------------------------------------------------
DEPLOYMENT SUCCESSFUL
------------------------------------------------------------

Contract Address: 0x1234567890abcdef...
Owner: 0x...
Transaction Hash: 0x...
```

## Post-Deployment

### 1. Update badge_nft_system.py

After deployment, update the contract address in `/scripts/interface/badge_nft_system.py`:

```python
SUPPORTED_CHAINS = {
    'polygon': {
        'chain_id': 137,
        'contract': '0xYOUR_DEPLOYED_ADDRESS',  # <-- Update this
        'explorer': 'https://polygonscan.com',
        'rpc': 'https://polygon-rpc.com'
    },
    ...
}
```

### 2. Verify on Polygonscan

If auto-verification failed during deployment:

```bash
npx hardhat verify --network polygon CONTRACT_ADDRESS OWNER_ADDRESS
```

### 3. Test Minting

Use Polygonscan's "Write Contract" feature or create a test script:

```javascript
// test_mint.js
const userHash = ethers.keccak256(ethers.toUtf8Bytes("test_user_123"));
const tx = await contract.mint(userHash);
console.log("Minted token:", tx);
```

## Security Considerations

1. **Private Key Security**: Never commit `.env` or private keys to git
2. **Owner Privileges**: Only the contract owner can update the base URI
3. **One NFT per User**: The contract enforces this on-chain
4. **Dual Verification**: On-chain ownership + off-chain server registration

## Gas Estimates

| Operation | Estimated Gas | ~Cost at 50 gwei |
|-----------|---------------|------------------|
| Deploy | ~2,500,000 | ~0.125 MATIC |
| Mint | ~150,000 | ~0.0075 MATIC |
| Transfer | ~65,000 | ~0.00325 MATIC |

## Contract ABI

After compilation, find the ABI at:
```
artifacts/contracts/ArchivitAccumeter.sol/ArchivitAccumeter.json
```

Key ABI for frontend integration:

```javascript
const ABI = [
  "function mint(bytes32 userHash) external returns (uint256)",
  "function verifyOwnership(bytes32 userHash, address wallet) external view returns (bool)",
  "function tokenURI(uint256 tokenId) public view returns (string memory)",
  "function getTokenForUser(bytes32 userHash) external view returns (uint256)",
  "function hasMinted(bytes32 userHash) external view returns (bool)",
  "function ownerOf(uint256 tokenId) public view returns (address)",
  "function totalSupply() external view returns (uint256)",
  "event AccumeterMinted(address indexed owner, uint256 indexed tokenId, bytes32 indexed userHash)"
];
```

## Supported Networks

| Network | Chain ID | Status | Contract |
|---------|----------|--------|----------|
| Polygon Mainnet | 137 | Ready to Deploy | TBD |
| Polygon Mumbai | 80001 | Ready to Deploy | TBD |
| Ethereum | 1 | Planned | TBD |
| Base | 8453 | Planned | TBD |
| Zora | 7777777 | Planned | TBD |

## Troubleshooting

### "Insufficient funds"
Ensure deployer wallet has enough MATIC. Get testnet MATIC from [Polygon Faucet](https://faucet.polygon.technology/).

### "Already Verified" error
Contract is already verified on Polygonscan - this is not an error.

### Compilation errors with OpenZeppelin
Ensure you have the correct OpenZeppelin version:
```bash
npm install @openzeppelin/contracts@5.0.0
```

### RPC timeout
Try alternative RPC endpoints:
- Polygon: `https://polygon.llamarpc.com`
- Mumbai: `https://polygon-mumbai-bor.publicnode.com`

## License

MIT License - See LICENSE file in project root.

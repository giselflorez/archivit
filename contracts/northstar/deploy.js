#!/usr/bin/env node
/**
 * NORTHSTAR PRINCIPALS EXPERIENCE - Deployment Script
 * ====================================================
 *
 * This script handles the complete deployment process:
 * 1. Upload to Arweave (permanent storage)
 * 2. Upload to IPFS (backup)
 * 3. Deploy smart contract
 * 4. Mint genesis token
 * 5. Create Token Bound Account
 *
 * Prerequisites:
 * - Node.js 18+
 * - Funded Ethereum wallet
 * - Environment variables configured
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Load content hashes
const hashes = JSON.parse(fs.readFileSync(
  path.join(__dirname, 'content_hashes.json'),
  'utf8'
));

console.log(`
╔════════════════════════════════════════════════════════════════╗
║     NORTHSTAR PRINCIPALS EXPERIENCE - DEPLOYMENT SEQUENCE      ║
╠════════════════════════════════════════════════════════════════╣
║  22 Masters / 100 Truths / Infinite Connections / Forever      ║
╚════════════════════════════════════════════════════════════════╝
`);

console.log('Content Hash (SHA256):');
console.log(`  ${hashes.sha256}`);
console.log('');
console.log('Visualization Hash (Keccak256):');
console.log(`  ${hashes.keccak256}`);
console.log('');

// Check for required environment variables
const requiredEnvVars = [
  'PRIVATE_KEY',
  'ETHERSCAN_API_KEY'
];

const missingVars = requiredEnvVars.filter(v => !process.env[v]);

if (missingVars.length > 0) {
  console.log('⚠️  Missing environment variables:');
  missingVars.forEach(v => console.log(`   - ${v}`));
  console.log('');
  console.log('Create a .env file with:');
  console.log(`
PRIVATE_KEY=your_wallet_private_key
ETHERSCAN_API_KEY=your_etherscan_api_key
ALCHEMY_API_KEY=your_alchemy_api_key (optional)
  `);
  console.log('');
  console.log('Or export them in your shell:');
  console.log('  export PRIVATE_KEY="0x..."');
  console.log('');
}

console.log(`
═══════════════════════════════════════════════════════════════
                    DEPLOYMENT STEPS
═══════════════════════════════════════════════════════════════

STEP 1: Upload to Arweave (Permanent Storage)
─────────────────────────────────────────────
Option A - Using Bundlr CLI:
  npm install -g @bundlr-network/client
  bundlr fund 0.1 -h https://node1.bundlr.network -w wallet.json -c ethereum
  bundlr upload scripts/interface/templates/masters_point_cloud_v3_spectral.html \\
    -h https://node1.bundlr.network -w wallet.json -c ethereum \\
    --tags "Content-Type" "text/html" \\
    --tags "App-Name" "NORTHSTAR-PRINCIPALS"

Option B - Using ArDrive (Web UI):
  1. Go to https://app.ardrive.io
  2. Connect wallet
  3. Upload: scripts/interface/templates/masters_point_cloud_v3_spectral.html
  4. Note the ar:// URI

Option C - Using Irys (formerly Bundlr) Web:
  1. Go to https://irys.xyz
  2. Connect wallet
  3. Upload file
  4. Note the ar:// URI


STEP 2: Upload to IPFS (Backup)
───────────────────────────────
Option A - Using Pinata (Recommended):
  1. Go to https://pinata.cloud
  2. Create account / Sign in
  3. Upload: scripts/interface/templates/masters_point_cloud_v3_spectral.html
  4. Note the ipfs:// CID

Option B - Using local IPFS:
  ipfs add scripts/interface/templates/masters_point_cloud_v3_spectral.html


STEP 3: Deploy Smart Contract
─────────────────────────────
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install OpenZeppelin
forge install OpenZeppelin/openzeppelin-contracts

# Compile
forge build

# Deploy to Sepolia (test first!)
forge create --rpc-url https://sepolia.infura.io/v3/YOUR_KEY \\
  --private-key $PRIVATE_KEY \\
  --etherscan-api-key $ETHERSCAN_API_KEY \\
  --verify \\
  contracts/northstar/NORTHSTAR_PRINCIPALS.sol:NorthstarPrincipals \\
  --constructor-args YOUR_ADDRESS "[]"


STEP 4: Mint Genesis Token
──────────────────────────
After deployment, call mintGenesis with:
  - contentHash: ${hashes.sha256}
  - visualizationHash: ${hashes.keccak256}
  - arweaveURI: ar://[YOUR_ARWEAVE_TX_ID]
  - ipfsURI: ipfs://[YOUR_IPFS_CID]

Using cast (Foundry):
  cast send CONTRACT_ADDRESS \\
    "mintGenesis(bytes32,bytes32,string,string)" \\
    ${hashes.sha256} \\
    ${hashes.keccak256} \\
    "ar://YOUR_TX_ID" \\
    "ipfs://YOUR_CID" \\
    --private-key $PRIVATE_KEY \\
    --rpc-url https://sepolia.infura.io/v3/YOUR_KEY


STEP 5: Create Token Bound Account (ERC-6551)
─────────────────────────────────────────────
# Registry address (same on all EVM chains)
REGISTRY=0x000000006551c19487814612e58FE06813775758

# Standard implementation
IMPLEMENTATION=0x55266d75D1a14E4572138116aF39863Ed6596E7F

cast send $REGISTRY \\
  "createAccount(address,bytes32,uint256,address,uint256)" \\
  $IMPLEMENTATION \\
  0x0000000000000000000000000000000000000000000000000000000000000000 \\
  1 \\
  CONTRACT_ADDRESS \\
  0 \\
  --private-key $PRIVATE_KEY \\
  --rpc-url YOUR_RPC_URL


═══════════════════════════════════════════════════════════════
                    QUICK START COMMANDS
═══════════════════════════════════════════════════════════════

# Full deployment in one go (after setting up .env):

# 1. Compile contract
forge build

# 2. Deploy to testnet
forge script scripts/Deploy.s.sol --rpc-url sepolia --broadcast --verify

# 3. After testing, deploy to mainnet
forge script scripts/Deploy.s.sol --rpc-url mainnet --broadcast --verify

═══════════════════════════════════════════════════════════════
`);

// Create Foundry config if it doesn't exist
const foundryConfig = `[profile.default]
src = "contracts"
out = "out"
libs = ["lib"]
optimizer = true
optimizer_runs = 10000

[rpc_endpoints]
mainnet = "\${MAINNET_RPC_URL}"
sepolia = "\${SEPOLIA_RPC_URL}"
base = "\${BASE_RPC_URL}"

[etherscan]
mainnet = { key = "\${ETHERSCAN_API_KEY}" }
sepolia = { key = "\${ETHERSCAN_API_KEY}" }
`;

const foundryPath = path.join(__dirname, '../../foundry.toml');
if (!fs.existsSync(foundryPath)) {
  fs.writeFileSync(foundryPath, foundryConfig);
  console.log('Created foundry.toml configuration');
}

console.log(`
═══════════════════════════════════════════════════════════════
                         READY TO DEPLOY
═══════════════════════════════════════════════════════════════

Your NORTHSTAR PRINCIPALS EXPERIENCE is ready for blockchain!

Content Hash: ${hashes.sha256.slice(0, 20)}...
File Size: ${(hashes.size_bytes / 1024).toFixed(1)} KB

Next steps:
1. Upload to Arweave (get ar:// URI)
2. Upload to IPFS (get ipfs:// CID)
3. Deploy contract
4. Mint genesis token
5. Create Token Bound Account

The 22 Masters await their eternal blockchain home.

SO MOTE IT BE
═══════════════════════════════════════════════════════════════
`);

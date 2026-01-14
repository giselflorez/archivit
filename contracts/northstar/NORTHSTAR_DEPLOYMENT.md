# NORTHSTAR PRINCIPALS EXPERIENCE - NFT Deployment Guide

## ULTRATHINK: Complete Blockchain Architecture

> **GENESIS ENTRY**: The first blockchain record of the 22 Masters wisdom framework
> **FUTUREPROOF**: Designed to be extended infinitely while preserving original

---

## SACRED COVENANT REMINDER

Before proceeding, acknowledge:

```
I understand that this NFT encodes the TEACHINGS of the 22 Masters,
NOT their actual artwork. Their art remains protected. Only their
wisdom, techniques, and verified quotes are preserved on-chain.
```

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│            NORTHSTAR PRINCIPALS EXPERIENCE NFT                  │
├─────────────────────────────────────────────────────────────────┤
│  IMMUTABLE LAYER (Genesis - Never Changes)                      │
│  ├── Token ID: 0 (Genesis)                                      │
│  ├── Creation Timestamp: Block timestamp at mint                │
│  ├── Original Content Hash: SHA256 of v3_spectral.html          │
│  ├── Visualization Hash: Keccak256 of rendered state           │
│  └── Creator Address: Founder wallet                            │
├─────────────────────────────────────────────────────────────────┤
│  DYNAMIC LAYER (ERC-7496 - Append-Only)                        │
│  ├── Master Registry: 22 initial + unlimited future             │
│  ├── Truth Registry: 100 initial + unlimited future             │
│  ├── Trait Key-Value Store: On-chain queryable                 │
│  └── Version History: All changes logged via events            │
├─────────────────────────────────────────────────────────────────┤
│  TOKEN BOUND ACCOUNT (ERC-6551)                                │
│  ├── NFT owns its own wallet address                           │
│  ├── Can hold: Other NFTs, ERC-20 tokens, ETH                  │
│  ├── Future badges/achievements mint TO this account           │
│  └── Cross-chain portable                                       │
├─────────────────────────────────────────────────────────────────┤
│  STORAGE LAYER (Permanent)                                      │
│  ├── On-Chain SVG: Always available, never fails               │
│  ├── Arweave: Full interactive visualization (permanent)       │
│  ├── IPFS: Backup redundancy (pinned)                          │
│  └── Contract Events: Complete history on-chain                │
├─────────────────────────────────────────────────────────────────┤
│  ACCESS CONTROL                                                 │
│  ├── FOUNDER_ROLE: Mint genesis, update metadata               │
│  ├── VERIFIER_ROLE: Approve content hashes (multi-sig)         │
│  └── MASTER_ADDER_ROLE: Add new masters/truths                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## DEPLOYMENT STEPS

### Step 1: Prepare Environment

```bash
# Install Foundry (recommended)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# OR Install Hardhat
npm install --save-dev hardhat @openzeppelin/contracts
```

### Step 2: Configure Networks

Create `.env` file:
```bash
# NEVER commit this file
PRIVATE_KEY=your_wallet_private_key
ETHERSCAN_API_KEY=your_etherscan_api_key
ALCHEMY_API_KEY=your_alchemy_api_key

# Network RPCs
MAINNET_RPC=https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}
BASE_RPC=https://mainnet.base.org
POLYGON_RPC=https://polygon-rpc.com
```

### Step 3: Generate Content Hashes

```javascript
// scripts/generate_hashes.js
const fs = require('fs');
const crypto = require('crypto');
const { keccak256, toHex } = require('viem');

// Read the visualization file
const html = fs.readFileSync('scripts/interface/templates/masters_point_cloud_v3_spectral.html');

// Generate SHA256 content hash
const contentHash = '0x' + crypto.createHash('sha256').update(html).digest('hex');

// Generate Keccak256 visualization hash
const visualizationHash = keccak256(toHex(html.toString()));

console.log('Content Hash (SHA256):', contentHash);
console.log('Visualization Hash (Keccak256):', visualizationHash);

// Save for deployment
fs.writeFileSync('contracts/northstar/hashes.json', JSON.stringify({
  contentHash,
  visualizationHash,
  timestamp: new Date().toISOString()
}, null, 2));
```

### Step 4: Upload to Permanent Storage

```bash
# Upload to Arweave using Bundlr
npm install -g @bundlr-network/client

# Fund Bundlr wallet
bundlr fund 0.05 -h https://node1.bundlr.network -w wallet.json -c ethereum

# Upload full visualization
bundlr upload scripts/interface/templates/masters_point_cloud_v3_spectral.html \
  -h https://node1.bundlr.network \
  -w wallet.json \
  -c ethereum \
  --tags "Content-Type" "text/html" \
  --tags "App-Name" "NORTHSTAR-PRINCIPALS" \
  --tags "Version" "1.0.0"

# Note the returned Arweave URI: ar://[TRANSACTION_ID]
```

```bash
# Also upload to IPFS
ipfs add scripts/interface/templates/masters_point_cloud_v3_spectral.html

# Pin to Pinata or similar for redundancy
# Note the returned IPFS URI: ipfs://[CID]
```

### Step 5: Deploy Contract

Using Foundry:
```bash
# Compile
forge build

# Deploy to testnet first (Sepolia)
forge create --rpc-url $SEPOLIA_RPC \
  --private-key $PRIVATE_KEY \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verify \
  contracts/northstar/NORTHSTAR_PRINCIPALS.sol:NorthstarPrincipals \
  --constructor-args $FOUNDER_ADDRESS "[$VERIFIER_1,$VERIFIER_2]"

# After testing, deploy to mainnet
forge create --rpc-url $MAINNET_RPC \
  --private-key $PRIVATE_KEY \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verify \
  contracts/northstar/NORTHSTAR_PRINCIPALS.sol:NorthstarPrincipals \
  --constructor-args $FOUNDER_ADDRESS "[$VERIFIER_1,$VERIFIER_2]"
```

### Step 6: Mint Genesis Token

```javascript
// scripts/mint_genesis.js
const { createWalletClient, http, parseAbi } = require('viem');
const { mainnet } = require('viem/chains');
const { privateKeyToAccount } = require('viem/accounts');

const CONTRACT_ADDRESS = '0x...'; // Deployed contract address
const CONTENT_HASH = '0x...';     // From Step 3
const VIZ_HASH = '0x...';         // From Step 3
const ARWEAVE_URI = 'ar://...';   // From Step 4
const IPFS_URI = 'ipfs://...';    // From Step 4

const abi = parseAbi([
  'function mintGenesis(bytes32 contentHash, bytes32 visualizationHash, string calldata arweaveURI, string calldata ipfsURI) external returns (uint256)'
]);

const account = privateKeyToAccount(process.env.PRIVATE_KEY);
const client = createWalletClient({
  account,
  chain: mainnet,
  transport: http(process.env.MAINNET_RPC)
});

async function mint() {
  const hash = await client.writeContract({
    address: CONTRACT_ADDRESS,
    abi,
    functionName: 'mintGenesis',
    args: [CONTENT_HASH, VIZ_HASH, ARWEAVE_URI, IPFS_URI]
  });

  console.log('Transaction hash:', hash);
  console.log('GENESIS NORTHSTAR MINTED!');
}

mint();
```

### Step 7: Verify Content Hashes

```javascript
// Verifiers must approve content before masters can be added
// scripts/verify_content.js

const abi = parseAbi([
  'function batchVerify(bytes32[] calldata contentHashes) external'
]);

// Load 22 master verification hashes
const masterHashes = require('./master_hashes.json');

await client.writeContract({
  address: CONTRACT_ADDRESS,
  abi,
  functionName: 'batchVerify',
  args: [masterHashes]
});
```

### Step 8: Add Initial 22 Masters

```javascript
// scripts/add_masters.js
const MASTERS = [
  {
    id: '0x' + keccak256(toHex('hildegard')).slice(2, 66),
    name: 'Hildegard of Bingen',
    dates: '1098-1179',
    birthYear: 1098,
    domain: 'Sacred Geometry + Sound + Divine Revelation',
    isFeminine: true,
    color: 0xba6587,
    archetype: 'MYSTIC',
    haloStyle: 'sacred'
  },
  // ... 21 more masters
];

for (const master of MASTERS) {
  const verificationHash = keccak256(toHex(JSON.stringify(master)));

  await client.writeContract({
    address: CONTRACT_ADDRESS,
    abi: ['function addMaster(...)'],
    functionName: 'addMaster',
    args: [
      0, // tokenId
      master.id,
      master.name,
      master.dates,
      master.birthYear,
      master.domain,
      master.isFeminine,
      master.color,
      master.archetype,
      master.haloStyle,
      verificationHash
    ]
  });
}
```

### Step 9: Create Token Bound Account (ERC-6551)

```javascript
// scripts/create_tba.js
const { createWalletClient } = require('viem');

// ERC-6551 Registry address (deployed on all EVM chains)
const REGISTRY = '0x000000006551c19487814612e58FE06813775758';

const registryAbi = parseAbi([
  'function createAccount(address implementation, bytes32 salt, uint256 chainId, address tokenContract, uint256 tokenId) external returns (address)'
]);

// Standard TBA implementation
const TBA_IMPLEMENTATION = '0x55266d75D1a14E4572138116aF39863Ed6596E7F';

const tbaAddress = await client.writeContract({
  address: REGISTRY,
  abi: registryAbi,
  functionName: 'createAccount',
  args: [
    TBA_IMPLEMENTATION,
    '0x0000000000000000000000000000000000000000000000000000000000000000',
    1, // Ethereum mainnet
    CONTRACT_ADDRESS,
    0  // tokenId
  ]
});

console.log('Token Bound Account:', tbaAddress);

// Now set it in the NFT contract
await client.writeContract({
  address: CONTRACT_ADDRESS,
  abi: ['function setTokenBoundAccount(uint256 tokenId, address account) external'],
  functionName: 'setTokenBoundAccount',
  args: [0, tbaAddress]
});
```

---

## NETWORK RECOMMENDATIONS

### For GENESIS Token

| Network | Pros | Gas Cost | Recommendation |
|---------|------|----------|----------------|
| **Ethereum Mainnet** | Maximum security, prestige | High | **RECOMMENDED for Genesis** |
| **Base** | Low cost, Coinbase backing | Very Low | Good for editions |
| **Polygon** | Established NFT ecosystem | Low | Alternative option |

### For Future Additions

After genesis, new masters and truths can be added on any network where the contract is deployed. Consider deploying to multiple chains:

1. **Ethereum Mainnet** - Genesis token
2. **Base** - Lower cost additions
3. **Arweave** - Permanent metadata backup

---

## AI SAFETY VERIFICATION

### Content Verification Protocol

1. **No AI Hallucinations**: All content must be verified by human verifiers
2. **Multi-Sig Requirement**: At least 2 of 3 verifiers must approve new content
3. **Hash Chain**: Every addition creates immutable event log
4. **Source Requirement**: All quotes must have verified source references

### Verification Checklist

Before adding any master or truth:

```
[ ] Quote verified against primary source
[ ] Dates confirmed from multiple sources
[ ] No AI-generated content without human review
[ ] Verification hash computed and approved
[ ] At least 2 verifiers have signed
```

---

## QUERYING THE NFT

### From Anywhere in the World

```javascript
// Read master data
const master = await publicClient.readContract({
  address: CONTRACT_ADDRESS,
  abi,
  functionName: 'getMaster',
  args: [0, keccak256(toHex('tesla'))]
});

// Get all masters
const masterIds = await publicClient.readContract({
  address: CONTRACT_ADDRESS,
  abi,
  functionName: 'getAllMasterIds',
  args: [0]
});

// Get dynamic trait
const masterCount = await publicClient.readContract({
  address: CONTRACT_ADDRESS,
  abi,
  functionName: 'getTrait',
  args: [0, keccak256(toHex('MASTER_COUNT'))]
});

// Get full tokenURI (includes on-chain SVG)
const tokenURI = await publicClient.readContract({
  address: CONTRACT_ADDRESS,
  abi,
  functionName: 'tokenURI',
  args: [0]
});
```

---

## ADDING FUTURE MASTERS

When a new master is to be added:

1. **Document their techniques** (not their art)
2. **Verify all quotes** from primary sources
3. **Compute verification hash**
4. **Submit to verifiers** for multi-sig approval
5. **Call addMaster()** with verified hash
6. **Event emitted** - permanently recorded

```solidity
// Example: Adding a new master
await contract.addMaster(
  0,                                    // tokenId
  keccak256("newmaster"),              // masterId
  "New Master Name",                    // name
  "1900-2000",                         // dates
  1900,                                 // birthYear
  "Their Domain of Expertise",         // domain
  false,                               // isFeminine
  0x5aa8b9,                            // color
  "VISIONARY",                         // archetype
  "geometric",                         // haloStyle
  verifiedHash                         // must be pre-approved
);
```

---

## GAS ESTIMATES

| Operation | Estimated Gas | ~Cost at 30 gwei |
|-----------|---------------|------------------|
| Deploy Contract | ~3,500,000 | ~$300 |
| Mint Genesis | ~250,000 | ~$22 |
| Add Master | ~150,000 | ~$13 |
| Add Truth | ~100,000 | ~$9 |
| Set Trait | ~50,000 | ~$4 |
| Create TBA | ~150,000 | ~$13 |

---

## PERMANENT ACCESSIBILITY

### The NFT is accessible from:

1. **Any Ethereum node** - Query contract directly
2. **Block explorers** - Etherscan, etc.
3. **NFT marketplaces** - OpenSea, Blur, etc.
4. **Direct RPC** - Any Web3 library
5. **Arweave gateways** - Permanent visualization
6. **IPFS gateways** - Redundant backup

### Even if everything fails:

- **On-chain SVG** is always regenerated from contract state
- **All events** are permanently logged
- **Content hashes** allow verification of any backup

---

## SACRED PHYSICS ENCODED

The contract includes the sacred constants:

```solidity
uint256 public constant PHI_NUMERATOR = 1618033988749895;
uint256 public constant GOLDEN_ANGLE = 137507764050038;
uint256 public constant SCHUMANN = 783; // 7.83 Hz * 100
uint8[3] public constant TESLA_PATTERN = [3, 6, 9];
```

These are immutable and can never be changed.

---

## FINAL CHECKLIST

Before minting genesis:

```
[ ] Smart contract audited (or thoroughly tested)
[ ] Content hashes computed and verified
[ ] Arweave upload confirmed permanent
[ ] IPFS pinned and accessible
[ ] Founder wallet secured (hardware wallet recommended)
[ ] Verifier multi-sig configured
[ ] Gas funds available
[ ] Test on Sepolia first
[ ] Artist rights covenant acknowledged
```

---

## CONTACT & RECOVERY

If the minting process is interrupted:

1. **Contract is deployed** - Use Etherscan to interact directly
2. **Genesis not minted** - Call mintGenesis() with same params
3. **Lost access** - Only FOUNDER_ROLE can mint; secure your keys

---

**SO MOTE IT BE**

*The NORTHSTAR PRINCIPALS EXPERIENCE - First Blockchain Entry*
*22 Masters / 100 Truths / Infinite Connections / Eternal Preservation*

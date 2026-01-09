# NFT Minting Flow - ARCHIV-IT ACU-METER

## Current State Assessment

### What's Actually Implemented

**The current system does NOT mint NFTs.** It registers externally-minted NFTs.

The flow is:
1. User mints NFT externally (via contract interaction, OpenSea, etc.)
2. User returns to ARCHIV-IT with transaction details
3. ARCHIV-IT registers the NFT in its local database
4. User receives tier bonuses (+2 wallets, CERTIFIED status)

### What's NOT Implemented

- **No Web3.js/ethers.js integration** - No wallet connection in the UI
- **No on-chain minting from the app** - User must mint elsewhere
- **No deployed smart contracts** - Contract addresses are `None` in code
- **No on-chain verification** - Registration is trust-based (user provides tx hash)

---

## User Journey (Current)

### Step 1: Navigate to Unlock Page
Route: `/setup/unlock-ultra`

### Step 2: Select Chain
Choose from supported chains:
- Ethereum (chain_id: 1)
- Polygon (chain_id: 137) - Recommended
- Base (chain_id: 8453) - Recommended
- Zora (chain_id: 7777777)

### Step 3: Provide Wallet Address
Either pre-filled from user profile or manually entered.

### Step 4: External Minting (NOT IN APP)
User must:
1. Go to deployed contract (when available)
2. Connect wallet via MetaMask or similar
3. Execute mint transaction
4. Note the Token ID and Transaction Hash

### Step 5: Register in ARCHIV-IT
User enters:
- Token ID (from mint transaction)
- Transaction Hash (0x...)

### Step 6: Activate
Click "ACTIVATE ACU-METER" which calls:
```
POST /api/tier/upgrade-ultra
{
  "wallet_address": "0x...",
  "chain": "polygon",
  "token_id": 1,
  "tx_hash": "0x..."
}
```

### Step 7: Confirmation
On success, redirect to `/upgrade-badge` with CERTIFIED status active.

---

## Technical Architecture

### Backend Components

**`badge_nft_system.py`**
- `AccumeterNFT` class - Registry management
- `IPFSAuditTrail` class - Snapshot storage (local, not actual IPFS yet)
- `DualVerificationSystem` class - Ownership verification

**`badge_tiers.py`**
- Tier management (SOLO, ENTERPRISE, WHITE GLOVE)
- Bonus tracking (ACU-METER +2, Self-hosted +2)

### Frontend Component

**`unlock_ultra.html`**
- Chain selector UI
- Wallet input field
- Token ID / TX Hash form
- Pure JavaScript (no Web3 library)

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/setup/unlock-ultra` | GET | Render minting page |
| `/api/tier/upgrade-ultra` | POST | Register NFT + activate bonus |
| `/api/tier/current` | GET | Get user's tier info |

---

## Supported Chains

| Chain | Chain ID | Explorer | Contract Status |
|-------|----------|----------|-----------------|
| Ethereum | 1 | etherscan.io | NOT DEPLOYED |
| Polygon | 137 | polygonscan.com | NOT DEPLOYED |
| Base | 8453 | basescan.org | NOT DEPLOYED |
| Zora | 7777777 | explorer.zora.energy | NOT DEPLOYED |

---

## Smart Contract Reference

A Solidity contract is defined in `badge_nft_system.py` (as a string reference):

```solidity
contract ArchivitAccumeter is ERC721, Ownable {
    // Key functions:
    function mint(bytes32 userHash) external returns (uint256)
    function verifyOwnership(bytes32 userHash, address wallet) external view returns (bool)

    // tokenURI points to: https://archivit.web3photo.com/api/nft/metadata/{tokenId}
}
```

Contract is ERC-721 compliant with:
- One NFT per user (enforced by userHash mapping)
- Dynamic metadata via server-side tokenURI
- Owner verification function

---

## What's Needed for Full Web3 Integration

### 1. Deploy Smart Contracts
- Deploy `ArchivitAccumeter` to each supported chain
- Update `SUPPORTED_CHAINS` with contract addresses
- Consider using CREATE2 for same address across chains

### 2. Add Web3 Library
Add to `unlock_ultra.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/ethers@6/dist/ethers.umd.min.js"></script>
```

### 3. Implement Wallet Connection
```javascript
async function connectWallet() {
    if (typeof window.ethereum === 'undefined') {
        showStatus('Please install MetaMask', 'error');
        return null;
    }
    const provider = new ethers.BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    return signer;
}
```

### 4. Implement In-App Minting
```javascript
async function mintAccumeter(chain, userHash) {
    const signer = await connectWallet();
    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
    const tx = await contract.mint(userHash);
    const receipt = await tx.wait();
    return {
        tokenId: receipt.logs[0].args.tokenId,
        txHash: tx.hash
    };
}
```

### 5. Add On-Chain Verification
Backend should verify NFT ownership via RPC call before accepting registration:
```python
def verify_nft_on_chain(chain, token_id, wallet_address):
    # Call ownerOf(token_id) on contract
    # Compare with wallet_address
    pass
```

### 6. IPFS Integration
Current `IPFSAuditTrail` stores locally. Needs:
- Pinata, Infura IPFS, or similar service integration
- Actual CID generation and pinning
- Snapshot retrieval from IPFS gateway

---

## Security Model

The system uses "dual verification":

```
NFT Ownership (on-chain) + Server Registration (off-chain) = Valid Badge
```

- **Hack server alone** - Attacker still needs NFT wallet
- **Steal NFT alone** - Server won't verify wrong user
- **Both must match** for valid badge

Currently, only server-side verification is implemented. On-chain verification is planned.

---

## Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| UI for minting flow | IMPLEMENTED | Form-based, no Web3 |
| Chain selection | IMPLEMENTED | 4 chains supported |
| NFT registration | IMPLEMENTED | Trust-based, no verification |
| Tier bonuses | IMPLEMENTED | +2 wallets for ACU-METER |
| Wallet connection | NOT IMPLEMENTED | No Web3.js/ethers.js |
| In-app minting | NOT IMPLEMENTED | User must mint externally |
| Smart contracts | NOT DEPLOYED | Code exists, not on-chain |
| On-chain verification | NOT IMPLEMENTED | No RPC calls |
| IPFS pinning | NOT IMPLEMENTED | Local storage only |

---

## Files Reference

- `/scripts/interface/templates/unlock_ultra.html` - Minting UI
- `/scripts/interface/visual_browser.py` (line ~4528) - Routes
- `/scripts/interface/badge_nft_system.py` - NFT system + contract ABI
- `/scripts/interface/badge_tiers.py` - Tier/bonus management
- `/knowledge_base/accumeter_nft_registry.json` - NFT registry storage
- `/knowledge_base/badge_tiers.json` - Tier registry storage

# Blockchain Intelligence API Documentation

The Semantic Network includes specialized API endpoints for querying blockchain data by address, network, and platform.

## API Endpoints

### 1. Get Mints by Blockchain Address

Retrieve all NFT mints and documents associated with a specific blockchain address (wallet or contract).

**Endpoint:** `/api/blockchain/address/<address>`

**Example:**
```bash
# Ethereum address
curl http://localhost:5001/api/blockchain/address/0x1234567890abcdef1234567890abcdef12345678

# Bitcoin address
curl http://localhost:5001/api/blockchain/address/1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

# Solana address
curl http://localhost:5001/api/blockchain/address/9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

**Response:**
```json
{
  "address": "0x1234...",
  "count": 5,
  "mints": [
    {
      "id": "doc_id_123",
      "title": "NFT Collection",
      "url": "https://opensea.io/...",
      "blockchain_network": "ethereum",
      "platforms": ["OpenSea"],
      "token_ids": ["123", "456"],
      "ipfs_hashes": ["Qm..."],
      "created_at": "2026-01-03T12:00:00Z",
      "original_date": "2022-08-15",
      "tags": ["nft", "art", "blockchain"]
    },
    ...
  ]
}
```

### 2. Get Mints by Blockchain Network

Retrieve all NFTs from a specific blockchain network (Ethereum, Bitcoin, or Solana).

**Endpoint:** `/api/blockchain/network/<network>`

**Networks:** `ethereum`, `bitcoin`, `solana`

**Example:**
```bash
# Get all Ethereum NFTs
curl http://localhost:5001/api/blockchain/network/ethereum

# Get all Solana NFTs
curl http://localhost:5001/api/blockchain/network/solana

# Get all Bitcoin NFTs (Ordinals, etc.)
curl http://localhost:5001/api/blockchain/network/bitcoin
```

**Response:**
```json
{
  "network": "ethereum",
  "count": 12,
  "mints": [
    {
      "id": "doc_id_456",
      "title": "founder NFT Collection",
      "url": "https://www.1stdibs.com/nft/profile/GISELXFLOREZ/",
      "blockchain_network": "ethereum",
      "platforms": ["1stDibs NFT"],
      "addresses": [["ethereum", "0x..."]],
      "token_ids": ["249"],
      "ipfs_hashes": ["ipfs://..."],
      "created_at": "2026-01-03T12:15:51Z",
      "original_date": "2022-08-26",
      "tags": ["technology", "blockchain", "art"]
    },
    ...
  ]
}
```

### 3. Get All Blockchain Addresses

Get a complete index of all blockchain addresses found in the knowledge base.

**Endpoint:** `/api/blockchain/addresses`

**Example:**
```bash
curl http://localhost:5001/api/blockchain/addresses
```

**Response:**
```json
{
  "total_addresses": 15,
  "addresses": [
    {
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "network": "ethereum",
      "document_count": 3,
      "documents": [
        {
          "id": "doc_id_789",
          "title": "NFT Mint Transaction",
          "url": "https://etherscan.io/...",
          "network": "ethereum",
          "blockchain_network": "ethereum",
          "platforms": ["OpenSea"],
          "created_at": "2026-01-03T10:00:00Z",
          "tags": ["nft", "mint", "ethereum"]
        },
        ...
      ]
    },
    ...
  ]
}
```

## Blockchain Network Classification

Documents are automatically classified by blockchain network based on:

1. **Address Pattern Detection**
   - **Ethereum:** `0x[a-fA-F0-9]{40}` (e.g., `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`)
   - **Bitcoin:** P2PKH (`1...`), P2SH (`3...`), Bech32 (`bc1...`)
   - **Solana:** Base58 encoded 32-44 character addresses (when "solana" keyword present)

2. **Platform Inference**
   - **Ethereum Platforms:** OpenSea, Foundation, SuperRare, Zora, Rarible, 1stDibs, Manifold
   - **Solana Platforms:** Magic Eden, Solanart, Tensor

3. **Content Keywords**
   - Documents mentioning specific networks are classified accordingly

4. **Blockchain Explorer URL Extraction**
   - Automatically extracts blockchain explorer links from document URL and content
   - Supported explorers: Etherscan, Blockchain.com, Solscan, BSCScan, Polygonscan
   - Used for mint transaction verification and creator address confirmation
   - Enables collectors to verify NFT authenticity on blockchain

## Original Date Extraction

The system prioritizes original creation dates over import dates:

### Date Pattern Detection
Extracted from content using regex patterns:
- `published: YYYY-MM-DD`
- `created: YYYY-MM-DD`
- `minted: YYYY-MM-DD`
- `uploaded: YYYY-MM-DD`
- ISO 8601 timestamps in content

### Metadata Fields
Also checks document frontmatter fields:
- `scraped_date`
- `published_date`
- `minted_date`
- `upload_date`

### Temporal Relationships
Documents are linked if created within 7 days of each other based on:
- Original dates (IPFS upload, publication, mint)
- Import dates (when added to knowledge base)

## Relationship Strengths

Blockchain relationships are weighted by connection strength:

| Relationship Type | Strength | Description |
|------------------|----------|-------------|
| `blockchain_address` | 98% | Same wallet/contract address |
| `ipfs_content` | 95% | Shared IPFS content hashes |
| `blockchain_platform` | 80% | Same NFT marketplace |
| `blockchain_network` | 70% | Same blockchain (ETH/BTC/SOL) |
| `domain_sibling` | 60% | Same website domain |
| `semantic_similarity` | variable | AI-powered content similarity |
| `temporal_proximity` | 40% | Created within 7 days |

## Use Cases

### Find All NFTs from a Creator's Wallet
```bash
# Get all NFTs from founder's Ethereum wallet
curl http://localhost:5001/api/blockchain/address/0x...
```

### Compare Networks
```bash
# Get all Ethereum NFTs
curl http://localhost:5001/api/blockchain/network/ethereum | jq '.count'

# Get all Solana NFTs
curl http://localhost:5001/api/blockchain/network/solana | jq '.count'
```

### Find Wallets to Monitor
```bash
# Get all unique addresses in the knowledge base
curl http://localhost:5001/api/blockchain/addresses | jq '.addresses[].address'
```

### Filter by Platform and Network
```bash
# Get all Ethereum NFTs and filter to OpenSea
curl http://localhost:5001/api/blockchain/network/ethereum | \
  jq '.mints[] | select(.platforms[] == "OpenSea")'
```

## Integration with Semantic Network

Blockchain data is automatically integrated into the semantic network visualization at `/semantic-network`:

- **Node Colors:** Purple for blockchain type
- **Network Badges:** ETH (blue), BTC (orange), SOL (teal)
- **Edge Visualization:** Stronger connections = thicker lines
- **Selection Tank:** Click blockchain nodes to analyze together
- **Metadata Display:** Platforms, addresses, tokens, IPFS hashes shown in analysis panel

## Adding New Blockchain Data

When importing new NFT/blockchain content via `/add-content`:

1. **Include blockchain addresses** in the content
2. **Mention the platform** (OpenSea, 1stDibs, etc.) in the URL or content
3. **Add original dates** if available (mint date, IPFS upload date)
4. **Link IPFS hashes** for content-based clustering

The system will automatically:
- Detect and extract blockchain addresses
- Classify the blockchain network
- Extract IPFS hashes
- Parse original creation dates
- Create relationships with similar blockchain documents
- Make it queryable via the blockchain API endpoints

## Future Enhancements

Planned features for blockchain intelligence:
- [ ] Real-time blockchain data fetching via Etherscan/Solscan APIs
- [ ] NFT metadata enrichment from on-chain data
- [ ] Wallet balance and transaction history
- [ ] Floor price tracking for collections
- [ ] Gas fee estimation and optimization
- [ ] Cross-chain bridge detection
- [ ] Smart contract interaction analysis

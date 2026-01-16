# Foundation Blockchain Query Setup

Get actual IPFS metadata and full-resolution images directly from the Ethereum blockchain for your Foundation NFTs.

---

## Quick Setup (5 minutes)

### Step 1: Get Free Alchemy API Key

Alchemy provides free Ethereum blockchain access (300M compute units/month - plenty for NFT queries).

1. **Visit:** https://www.alchemy.com/
2. **Sign up** (free account)
3. **Create an app:**
   - Click "Create App"
   - Name: "Founder NFT Query"
   - Network: **Ethereum Mainnet**
   - Free tier is perfect!

4. **Copy API key:**
   - Click on your app
   - Click "API Key"
   - Copy the key

5. **Add to `.env` file:**
   ```bash
   ALCHEMY_API_KEY=your-key-here
   ```

That's it! You're ready to query blockchain NFT data.

---

## Usage

### Query Foundation NFT from Blockchain

When you have a Foundation NFT and want the **actual IPFS metadata** (not just what's on the web page):

```bash
source venv/bin/activate

python scripts/collectors/foundation_blockchain_query.py \
  knowledge_base/processed/about_web_imports/web_af21bdaef6e4_*.md
```

**The tool will:**
1. Ask for the token ID (visible on Foundation page)
2. Query Ethereum blockchain for tokenURI
3. Fetch IPFS metadata JSON
4. Download optimized preview image (max 1200px)
5. Add clickable IPFS links to your document

**Result:**
```markdown
## Blockchain NFT

### Glitter of Hard Knocks

**Contract:** `0x8740EEf45Def23A94Bed5b9793c6d1A9b7dC1ebf`
**Token ID:** 5
**Network:** Ethereum Mainnet

**Description:** A photographic exploration of light and movement...

**Preview Image:**

![Glitter of Hard Knocks](../../knowledge_base/media/nft/af21bdaef6e4/nft_5_preview.jpg)

*Optimized preview: 245,789 bytes (saved 88% vs. original 2,047,653 bytes)*

**Full Resolution (IPFS):** `ipfs://QmXyZ123abc456...`

*Access original: [ipfs.io](https://ipfs.io/ipfs/QmXyZ123...) | [Pinata](https://gateway.pinata.cloud/ipfs/QmXyZ123...)*

---
```

Now you have **clickable IPFS links** to access full-resolution originals anytime!

---

## How It Works

### Traditional Web Scraping Limitations

When you scrape a Foundation profile page, you get:
- ✓ NFT thumbnails (compressed CDN images)
- ✓ Titles and descriptions (if visible)
- ✗ IPFS metadata URIs (stored on blockchain, not in HTML)
- ✗ Original full-resolution images
- ✗ Blockchain attributes

### Blockchain Query Advantages

By querying the smart contract directly:
- ✅ **tokenURI** - Official IPFS metadata location
- ✅ **Full metadata JSON** - Name, description, attributes, traits
- ✅ **Original IPFS image** - Full resolution (download preview)
- ✅ **Provenance** - Contract address, token ID, network
- ✅ **Permanent links** - IPFS URIs that work forever

---

## Finding Token IDs

### Method 1: From Foundation URL

Foundation NFT page URLs contain the token ID:

```
https://foundation.app/@founder/~/5
                                    ↑
                                 token ID
```

Or collection page:
```
https://foundation.app/collections/glitter-of-hard-knocks
```
(View the page, click on specific NFT to see token ID in URL)

### Method 2: From Page Content

Token IDs are often visible on the NFT page:
- "Edition 5/5"
- "#5" in title
- Token metadata panel

### Method 3: From Etherscan

1. Go to Foundation contract on Etherscan:
   ```
   https://etherscan.io/address/0x8740EEf45Def23A94Bed5b9793c6d1A9b7dC1ebf
   ```

2. Click "Tracker" tab
3. Search for your NFT by name
4. Token ID shown in results

---

## Foundation Contract Addresses

The tool automatically uses these Foundation contracts:

**Foundation V1 (Legacy):**
```
0x3B3ee1931Dc30C1957379FAc9aba94D1C48a5405
```

**Foundation V2 (World) - Current:**
```
0x8740EEf45Def23A94Bed5b9793c6d1A9b7dC1ebf
```

Most recent NFTs use V2 (World).

---

## Example Workflow

### 1. Import Foundation Profile

Via web interface:
```
http://localhost:5000
→ + Import
→ URL: https://foundation.app/@founder
→ ✓ Extract Images
→ Import
```

This gets:
- Profile info
- Bio/description
- Thumbnail images
- **No IPFS metadata yet**

### 2. Query Blockchain for IPFS Data

```bash
source venv/bin/activate

python scripts/collectors/foundation_blockchain_query.py \
  knowledge_base/processed/about_web_imports/web_XXXXX.md
```

When prompted, enter token ID (e.g., `5`)

This adds:
- ✅ IPFS metadata URI
- ✅ Full NFT description
- ✅ Attributes/traits
- ✅ Preview image from IPFS
- ✅ Clickable links to full-resolution original

### 3. View Enhanced Document

Open your document to see:
- Original web-scraped content
- **New "Blockchain NFT" section** with IPFS links
- Preview image
- Links to download full resolution

Click IPFS links anytime to access originals!

---

## Costs & Limits

### Alchemy Free Tier

- **300M compute units/month**
- **1 tokenURI query ≈ 1,000 compute units**
- **You can query ~300,000 NFTs/month** (way more than needed!)

### IPFS Fetching

- **FREE** (decentralized network)
- Gateways: ipfs.io, Pinata, Cloudflare
- No API key required

### Preview Images

- Downloaded from IPFS (free)
- Resized to max 1200px locally
- Saves 70-90% storage vs. full resolution
- Full originals always accessible via IPFS links

**Total cost: $0**

---

## Troubleshooting

### "No ALCHEMY_API_KEY found in .env"

**Solution:** Add API key to `.env` file:
```bash
ALCHEMY_API_KEY=your-key-here
```

Make sure `.env` is in project root directory.

### "Could not fetch token URI from blockchain"

**Possible causes:**
- Wrong token ID
- NFT doesn't exist
- Wrong contract address

**Solutions:**
1. Verify token ID from Foundation page URL
2. Check if NFT is on V1 or V2 contract
3. Try different token ID

### "Could not fetch metadata from IPFS"

**Causes:**
- IPFS content not pinned
- Temporary gateway outage

**Solutions:**
1. Try again (IPFS may be propagating)
2. Check different IPFS gateway manually
3. Metadata URI might not be IPFS (some use Arweave)

### "No response from blockchain"

**Causes:**
- API key invalid
- Rate limit exceeded
- Network issue

**Solutions:**
1. Check API key is correct
2. Wait a minute (rate limit resets)
3. Check Alchemy dashboard for usage

---

## Advanced: Batch Query Multiple NFTs

To query multiple Foundation NFTs at once, modify the script or create a loop:

```bash
# Query tokens 1-10
for token_id in {1..10}; do
  echo "Token ID: $token_id" | python scripts/collectors/foundation_blockchain_query.py \
    knowledge_base/processed/about_web_imports/web_af21bdaef6e4_*.md
  sleep 1  # Be polite to API
done
```

---

## Future Enhancements

Planned features:

- [ ] Auto-detect token IDs from Foundation page content
- [ ] Query all NFTs from profile automatically
- [ ] Support for other chains (Polygon, Tezos, Solana)
- [ ] Collection-level queries
- [ ] Historical sales data
- [ ] Rarity scoring

---

## Why This Matters

**Web scraping** gets you:
- Thumbnails (200-500 KB, compressed)
- Visible page content
- No provenance

**Blockchain querying** gets you:
- Original IPFS metadata (immutable)
- Full-resolution images (2-10 MB)
- Smart contract provenance
- Permanent decentralized links

**Your knowledge base becomes Web3-native!** 🚀

---

**Last updated:** 2026-01-03

# Multi-Wallet System - ARCHIV-IT by WEB3GISEL

## Overview

The ARCHIV-IT by WEB3GISEL supports **multiple wallet addresses** under a single artist profile, allowing organized data storage across different wallets. Perfect for managing multiple wallets, marketplaces, or project identities while keeping everything under one artist profile.

## Key Features

### 1. Artist Profile with Multiple Wallets
- One artist profile per installation (FREE tier)
- Up to 3 wallet addresses per artist profile
- Dedicated subfolder structure per wallet address
- Separate NFT data and media files per wallet
- All data queryable under one unified artist identity

### 2. Automatic Organization
When you add wallet addresses:
1. **First address:** Artist profile created with custom name
2. **Folders created automatically:**
   - `knowledge_base/processed/artist_{folder_name}/wallet_{address}/`
   - `knowledge_base/media/artist_{folder_name}/wallet_{address}/`
3. **Blockchain scrape initiated** for each wallet address
4. **Subsequent addresses:** New wallet subfolders created under existing artist
5. **All data** stored in wallet-specific subfolders within artist folder

### 3. Wallet Management
- View all wallet addresses under your artist profile
- Filter NFTs by specific wallet
- Unified view across all wallets
- Add/remove wallets (up to 3 total)

## How It Works

### During Setup

**Step 3: Add Wallet Addresses**

**First Wallet Address:**
You provide:
- **Artist Name:** Display name (e.g., "GiselX", "My Art Project")
- **Wallet Address:** Ethereum minting address (0x...)
- **Wallet Label:** Optional label (e.g., "Primary Wallet")

**Second & Third Wallet Addresses:**
You provide:
- **Wallet Address:** Ethereum minting address (0x...)
- **Wallet Label:** Optional label (e.g., "Foundation Wallet", "OpenSea Wallet")
- Artist name is NOT asked again (addresses added to existing artist)

**What Happens:**
1. System creates artist profile with sanitized folder name (first address only)
   - "GiselX" → `artist_giselx`
   - "My Art Project" → `artist_my_art_project`

2. Creates wallet subfolder structure:
   ```
   knowledge_base/
   ├── processed/
   │   └── artist_giselx/
   │       ├── wallet_0xabc123.../     # First wallet's markdown files
   │       ├── wallet_0xdef456.../     # Second wallet's markdown files
   │       └── wallet_0x789abc.../     # Third wallet's markdown files
   └── media/
       └── artist_giselx/
           ├── wallet_0xabc123.../     # First wallet's images/videos
           ├── wallet_0xdef456.../     # Second wallet's images/videos
           └── wallet_0x789abc.../     # Third wallet's images/videos
   ```

3. Triggers blockchain scraper with wallet-specific folder parameter

4. All NFTs minted by each address → stored in that wallet's subfolder

### Folder Structure

**Example with 1 artist and 3 wallet addresses:**
```
knowledge_base/
├── processed/
│   └── artist_giselx/
│       ├── wallet_0xabc123.../
│       │   ├── nft_token_1234.md
│       │   ├── nft_token_5678.md
│       │   └── collection_metadata.md
│       ├── wallet_0xdef456.../
│       │   ├── nft_token_9999.md
│       │   └── nft_token_8888.md
│       └── wallet_0x789abc.../
│           └── nft_token_7777.md
└── media/
    └── artist_giselx/
        ├── wallet_0xabc123.../
        │   ├── image_1234.jpg
        │   └── image_5678.png
        ├── wallet_0xdef456.../
        │   ├── image_9999.jpg
        │   └── image_8888.png
        └── wallet_0x789abc.../
            └── image_7777.png
```

## Database Schema

### Artist Profiles Table
```sql
CREATE TABLE artist_profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    artist_name TEXT,           -- Display name
    folder_name TEXT UNIQUE,    -- Sanitized folder name
    bio TEXT,                   -- Optional bio
    is_current BOOLEAN,         -- Currently viewing this artist
    is_active BOOLEAN,          -- Active/inactive
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Minting Addresses Table (Updated)
```sql
CREATE TABLE minting_addresses (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    artist_profile_id INTEGER,  -- Linked to artist profile
    address TEXT,
    network TEXT,
    label TEXT,
    is_primary BOOLEAN,
    created_at TIMESTAMP
);
```

## API Methods

### Create Artist Profile
```python
from scripts.interface.user_config_db import UserConfigDB

user_db = UserConfigDB()
artist_id = user_db.create_artist_profile(
    user_id=1,
    artist_name="GiselX",
    folder_name="giselx",  # Optional, auto-generated if not provided
    bio="Digital artist exploring Web3"
)
```

### Get Current Artist
```python
artist = user_db.get_current_artist()
# Returns: {'id': 1, 'artist_name': 'GiselX', 'folder_name': 'giselx', ...}
```

### Get All Artists
```python
artists = user_db.get_all_artists()
# Returns list of all active artist profiles with address counts
```

### Switch Artist
```python
user_db.switch_artist(artist_id=2)
# UI now shows data for artist #2
```

### Get Artist Folder Path
```python
folder = user_db.get_artist_folder_path(artist_id=1)
# Returns: "artist_giselx"
```

## Adding More Wallets Later

After initial setup, you can add more wallet addresses (up to 3 total) to your artist profile:

```python
from scripts.interface.user_config_db import UserConfigDB
from scripts.interface.setup_routes import trigger_blockchain_scrape

user_db = UserConfigDB()
user = user_db.get_primary_user()

# Get existing artist profile
artist = user_db.get_current_artist(user['id'])

# Add new wallet to existing artist (no artist_name needed)
success = user_db.add_minting_address(
    user['id'],
    '0xYourNewAddress',
    network='ethereum',
    label='Foundation Wallet',
    artist_id=artist['id']  # Link to existing artist
)

if success:
    # Get wallet-specific folder path
    wallet_folder = user_db.get_wallet_folder_path(address='0xYourNewAddress')

    # Trigger blockchain scrape for new wallet
    trigger_blockchain_scrape(
        '0xYourNewAddress',
        'ethereum',
        wallet_folder
    )
```

## Blockchain Scraper Integration

The blockchain scraper (`ethereum_tracker.py`) accepts `--artist-folder` parameter with wallet subfolder:

```bash
python scripts/collectors/ethereum_tracker.py \
  --address 0xYourAddress \
  --network ethereum \
  --sync-type full \
  --artist-folder artist_giselx/wallet_0xYourAddress
```

**What it does:**
- Scrapes NFTs minted by `0xYourAddress`
- Saves markdown files to `knowledge_base/processed/artist_giselx/wallet_0xYourAddress/`
- Downloads images to `knowledge_base/media/artist_giselx/wallet_0xYourAddress/`
- Links NFTs to artist profile and specific wallet address in database

## Collection Detection

The "COLLECTED" badge system works across all your wallet addresses:

1. System queries blockchain for current NFT owner
2. Compares owner to **all wallet addresses** in your artist profile
3. If owner ≠ any of your wallet addresses:
   - Badge shows "✓ COLLECTED"
   - Tooltip displays current owner address
4. If owner = one of your wallet addresses:
   - No badge (you still own it)
   - Can identify which specific wallet owns it

## Licensing Tiers

The system supports three licensing tiers:

### FREE Tier (Current Implementation)
- 1 artist profile per installation
- Up to 3 wallet addresses per artist
- Full blockchain tracking and scraping
- NFT collection detection
- Complete knowledge base features
- Self-service setup

### ENTERPRISE Tier
- Up to 5 artist profiles
- Each artist can have 3 wallet addresses (15 wallets total)
- Dedicated customer service
- Walkthroughs and onboarding assistance
- Priority support
- Multi-artist analytics dashboard

### WHITE LABEL Tier
- Custom pricing upon request
- Custom builds tailored to your needs
- Monthly white-label updates
- Custom branding and theming
- Dedicated development resources
- Enterprise-level SLA

### Multi-Artist Features (Enterprise/White Label)
- Switch between artists in navigation
- View all artists on dashboard
- Compare NFT sales across artists
- Cross-artist analytics
- Shared collector tracking
- Multi-artist exhibitions
- Edit artist profiles
- Manage per-artist settings

## Usage Examples

### Setup Wizard Flow
```
1. Enter email → Confirm email

2. Add first wallet (creates artist profile):
   - Artist Name: "GiselX"
   - Address: 0xABC...
   - Label: "Primary Wallet"
   → Creates artist_giselx/wallet_0xABC... folder
   → Scrapes blockchain for 0xABC...

3. Add second wallet (to same artist):
   - Address: 0xDEF...
   - Label: "Foundation Wallet"
   → Creates artist_giselx/wallet_0xDEF... folder
   → Scrapes blockchain for 0xDEF...

4. Add third wallet (to same artist):
   - Address: 0x123...
   - Label: "OpenSea Wallet"
   → Creates artist_giselx/wallet_0x123... folder
   → Scrapes blockchain for 0x123...
```

### Viewing Wallet Data
```python
# Get current artist
artist = user_db.get_current_artist()
print(f"Viewing: {artist['artist_name']}")

# Get all wallet addresses for this artist
addresses = user_db.get_minting_addresses(artist['user_id'])
for addr in addresses:
    wallet_folder = user_db.get_wallet_folder_path(address_id=addr['id'])
    print(f"Wallet: {addr['address'][:10]}... → {wallet_folder}")
```

### Blockchain Scraping Per Wallet
```bash
# Scrape for first wallet
python scripts/collectors/ethereum_tracker.py \
  --address 0xABC... \
  --artist-folder artist_giselx/wallet_0xABC...

# Scrape for second wallet
python scripts/collectors/ethereum_tracker.py \
  --address 0xDEF... \
  --artist-folder artist_giselx/wallet_0xDEF...

# Scrape for third wallet
python scripts/collectors/ethereum_tracker.py \
  --address 0x123... \
  --artist-folder artist_giselx/wallet_0x123...
```

## Benefits

### Organization
- Clean separation of data per wallet address
- Easy to find NFTs from specific wallets
- No mixing of different marketplace mints
- Unified view across all your wallets

### Scalability
- Support multiple wallets/marketplaces
- Ready for multi-artist enterprise deployment
- Can manage multiple identities under one profile

### Data Integrity
- Each wallet's data isolated in subfolders
- Independent blockchain scraping per wallet
- Separate media libraries per wallet
- All queryable under one artist profile

### Future-Proof
- Foundation for multi-artist comparison (Enterprise tier)
- Ready for multi-user expansion
- Supports complex organizational structures
- Easy to upgrade from FREE → ENTERPRISE → WHITE LABEL

## Migration from Root Folders

If you already have data in the root folders without wallet subfolders, you can migrate:

```python
from pathlib import Path
import shutil

# Create artist profile for existing data
user_db = UserConfigDB()
user = user_db.get_primary_user()

# Get or create artist
artist = user_db.get_current_artist(user['id'])
if not artist:
    artist_id = user_db.create_artist_profile(
        user['id'],
        "Main Artist",
        "main_artist"
    )

# Add your main wallet address
user_db.add_minting_address(
    user['id'],
    "0xYourMainAddress",
    network='ethereum',
    label='Primary Wallet',
    artist_id=artist['id']
)

# Get wallet folder path
wallet_folder = user_db.get_wallet_folder_path(address='0xYourMainAddress')

# Move existing files to wallet subfolder
old_processed = Path("knowledge_base/processed")
new_processed = Path(f"knowledge_base/processed/{wallet_folder}")
new_processed.mkdir(parents=True, exist_ok=True)

for file in old_processed.glob("*.md"):
    if not "artist_" in str(file.parent):
        shutil.move(str(file), str(new_processed / file.name))

# Same for media files
old_media = Path("knowledge_base/media")
new_media = Path(f"knowledge_base/media/{wallet_folder}")
new_media.mkdir(parents=True, exist_ok=True)

for file in old_media.rglob("*"):
    if file.is_file() and not "artist_" in str(file.parent):
        rel_path = file.relative_to(old_media)
        new_file = new_media / rel_path
        new_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(new_file))
```

## Troubleshooting

### Wallet folders not created
- Check permissions on `knowledge_base/` directory
- Verify artist profile and addresses created in database:
  ```sql
  sqlite3 db/user_config.db "SELECT * FROM artist_profiles"
  sqlite3 db/user_config.db "SELECT * FROM minting_addresses"
  ```

### Blockchain scrape not using wallet folder
- Check scraper logs for `--artist-folder` parameter
- Verify parameter includes wallet subfolder: `artist_name/wallet_address`
- Check folder exists before scraping

### Can't add more wallets
- Verify you haven't reached the 3-wallet limit (FREE tier)
- Check license configuration in database
- Ensure artist profile exists

### Data in wrong folder
- Check which wallet is being scraped
- Verify `wallet_folder` path passed to scraper
- Check scraper uses correct artist/wallet subfolder path

### Setup wizard keeps asking for artist name
- This is normal for the first wallet address only
- For 2nd and 3rd wallets, artist name field should be hidden
- Check that addresses already exist in database

## Next Steps

1. **Complete setup** with first wallet address (creates artist profile)
2. **Add more wallets** if using multiple addresses (up to 3 total)
3. **Run blockchain scrapes** for each wallet
4. **View unified data** across all wallets under one artist
5. **Consider upgrading** to ENTERPRISE tier for multi-artist support

The multi-wallet system provides a foundation for professional, scalable NFT portfolio management across multiple wallet addresses and marketplaces while maintaining a unified artist identity.

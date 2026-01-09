# ARCHIV-IT by WEB3GISEL - Setup Wizard

## Overview

The ARCHIV-IT by WEB3GISEL now includes a first-time setup wizard that guides new users through configuring their personal research vault.

## Features

### 1. Email Collection & Confirmation
- Users provide their email address for system access
- Optional marketing opt-in for feature updates
- Email confirmation with 6-digit code
- Privacy-focused: all data stored locally

### 2. Minting Address Configuration
- Add up to 3 Ethereum wallet addresses used for minting NFTs
- Addresses are used to identify which NFTs are "collected" (owned by others)
- Each address can have a custom label
- **Automatic blockchain scrape** triggered when adding an address

### 3. NFT Collection Detection
- System queries blockchain APIs to get current owner of each NFT
- Compares current owner to your minting addresses
- Green "COLLECTED" badge appears on NFTs owned by others
- Full wallet address displayed in metadata panel

## Setup Process

### Step 1: Email Registration
1. Enter your email address
2. Choose whether to receive update notifications
3. Click "Continue"

### Step 2: Email Confirmation
1. Check console output for 6-digit confirmation code
2. Enter the code in the setup wizard
3. Click "Verify Email"

**Note:** Email integration is currently console-based. To enable SMTP:
- Add to `.env`:
  ```
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  ```

### Step 3: Minting Addresses
1. Enter your Ethereum wallet address (0x...)
2. Optional: Add a label (e.g., "Primary Wallet", "Foundation Address")
3. Click "Add Address"
4. **Automatic blockchain scrape begins** for this address
5. Repeat for up to 3 addresses total
6. Click "Continue to Archive"

### Step 4: Complete Setup
- Setup is marked as complete
- Minting addresses are synced to blockchain tracking database
- User is redirected to main archive interface

## Technical Details

### Database Schema

**user_config.db**
- `user_config` - User email, confirmation status, setup progress
- `minting_addresses` - Up to 3 addresses per user, network, labels
- `setup_steps` - Track progress through setup wizard

### Files Created

1. `/scripts/interface/user_config_db.py` - User configuration database manager
2. `/scripts/interface/setup_routes.py` - Flask routes for setup wizard
3. `/scripts/interface/templates/setup_wizard.html` - Setup UI
4. `/db/user_config.db` - SQLite database (auto-created on first run)

### Integration Points

**visual_browser.py:**
- Middleware checks if setup is complete before allowing access
- Redirects to `/setup` if not configured
- Uses minting addresses for NFT collection detection

**Blockchain Scraper:**
- Automatically triggered when minting address is added
- Runs in background to populate NFT database
- Syncs with blockchain APIs (Etherscan, Alchemy)

## Required API Keys

For full functionality, add to `.env`:

```bash
# Blockchain APIs (for NFT owner lookup)
ALCHEMY_API_KEY=your_alchemy_key
ETHERSCAN_API_KEY=your_etherscan_key

# Email (optional, for SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password

# Flask session secret
FLASK_SECRET_KEY=random-secret-key-here
```

## Accessing Setup After Completion

If you need to modify minting addresses after initial setup:

```python
from scripts.interface.user_config_db import UserConfigDB

user_db = UserConfigDB()
user = user_db.get_primary_user()

# Add new address
user_db.add_minting_address(
    user['id'],
    '0xYourNewAddress',
    network='ethereum',
    label='New Wallet'
)

# Sync to blockchain database
user_db.sync_minting_addresses_to_blockchain_db()
```

## Marketing & Privacy

- **Email storage:** Local only, never sent to external services
- **Marketing opt-in:** Can be disabled by setting `marketing_opt_in = FALSE` in database
- **Mailing list export:** Query `user_config` table where `marketing_opt_in = TRUE`
- **Data privacy:** All user data stored locally in SQLite databases

## For Enterprise Version (Future)

The system is designed to support multiple artist directories:

1. **Multi-tenant setup:**
   - Each artist has their own user config
   - Separate minting addresses per artist
   - Filter NFTs by creator/artist
   - Compare collections across multiple artists

2. **Planned features:**
   - Artist switching in UI
   - Cross-artist analytics
   - Shared collector tracking
   - Multi-artist exhibitions/collections

## How Setup Works

### First Time Only
The setup wizard **only runs once**:
- After completing setup, `setup_completed = 1` is saved in database
- On reload, middleware checks this flag and allows normal access
- Setup wizard won't show again unless you reset

### What Gets Saved
When you complete setup:
- Email and confirmation status → `db/user_config.db`
- Minting addresses (up to 3) → `db/user_config.db`
- Setup completion flag → `db/user_config.db`
- Synced minting addresses → `db/blockchain_tracking.db`

## Resetting Setup

### Quick Reset (Setup Wizard Only)
To restart the setup wizard without losing your data:

```bash
python scripts/reset_setup.py
```

This deletes **only** `db/user_config.db`, so you'll go through setup again but keep:
- ✅ Knowledge base files
- ✅ Media files
- ✅ Blockchain data
- ✅ Sales analytics
- ✅ Collections

### Full Reset (Complete Fresh Start)
To delete **everything** and start from scratch:

```bash
python scripts/reset_setup.py --full
```

This will ask for confirmation before deleting:
- ❌ User configuration database
- ❌ Blockchain tracking database
- ❌ Sales analytics database
- ❌ Collections database
- ❌ Knowledge base files (scraped content)
- ❌ Media files (images, videos)
- ❌ Embeddings index

**Skip confirmation prompts:**
```bash
python scripts/reset_setup.py --full --yes
```

### Manual Reset
If you prefer to do it manually:

**Setup wizard only:**
```bash
rm db/user_config.db
```

**Complete reset:**
```bash
rm db/user_config.db
rm db/blockchain_tracking.db
rm db/sales_analytics.db
rm db/collections.db
rm -rf knowledge_base/processed/*
rm -rf knowledge_base/media/*
rm -rf knowledge_base/embeddings/*
```

## Troubleshooting

### Setup loop (keeps redirecting to /setup)
- Check `db/user_config.db` exists
- Verify `setup_completed = 1` in `user_config` table
- Run: `sqlite3 db/user_config.db "SELECT * FROM user_config"`
- If missing, run reset script

### Confirmation code not showing
- Check console output where Flask server is running
- Code is printed to stdout for development
- Enable SMTP to send real emails

### Blockchain scrape not working
- Verify `/scripts/collectors/ethereum_tracker.py` exists
- Check Etherscan/Alchemy API keys in `.env`
- Check `db/blockchain_tracking.db` for scraped NFTs

### Collection badge not appearing
- Ensure NFT current owner differs from minting addresses
- Check blockchain API keys are configured
- Verify minting addresses are lowercase in database

### Want to add more minting addresses later
You can modify minting addresses after setup:
```python
from scripts.interface.user_config_db import UserConfigDB

user_db = UserConfigDB()
user = user_db.get_primary_user()

# Add new address (up to 3 total)
user_db.add_minting_address(
    user['id'],
    '0xYourNewAddress',
    network='ethereum',
    label='New Wallet'
)

# Trigger blockchain scrape
from scripts.interface.setup_routes import trigger_blockchain_scrape
trigger_blockchain_scrape('0xYourNewAddress', 'ethereum')

# Sync to blockchain database
user_db.sync_minting_addresses_to_blockchain_db()
```

## Usage Example

```bash
# First time running the app
python scripts/interface/visual_browser.py

# Browser redirects to http://localhost:5000/setup
# Follow 4-step wizard:
# 1. Enter email
# 2. Confirm with code from console
# 3. Add minting addresses (triggers NFT scrape)
# 4. Complete setup

# System now tracks:
# - Which NFTs you minted
# - Current owners of each NFT
# - "COLLECTED" badge on NFTs owned by others
```

## Next Steps

After setup is complete:
1. Import content via `/add-content`
2. View NFTs in `/visual-translator`
3. Track blockchain activity in `/blockchain-tracker`
4. Analyze sales in `/sales-analytics`
5. Build knowledge network in `/semantic-network`

# Reset Guide - ARCHIV-IT by WEB3GISEL

## Quick Reference

### The Setup Wizard Only Runs ONCE ✅
- After you complete setup, the wizard won't show again
- Reloading the website goes straight to your archive
- Your configuration is saved in `db/user_config.db`

### Want to Start Fresh?

**Two reset options:**

## Option 1: Reset Setup Only (Keep Your Data)

```bash
python scripts/reset_setup.py
```

**What this does:**
- ✅ Restarts the setup wizard
- ✅ Keeps all your knowledge base files
- ✅ Keeps all your media files
- ✅ Keeps blockchain data
- ✅ Keeps sales analytics

**Use this when:**
- You want to change your email
- You want to add different minting addresses
- You want to go through setup again
- Testing the setup flow

---

## Option 2: Complete Reset (Delete Everything)

```bash
python scripts/reset_setup.py --full
```

**What this does:**
- ❌ Deletes user configuration
- ❌ Deletes blockchain tracking database
- ❌ Deletes sales analytics database
- ❌ Asks before deleting knowledge base files
- ❌ Asks before deleting media files
- ❌ Deletes embeddings index

**Use this when:**
- You want a completely fresh start
- You're switching to a different project
- You want to clear all data

**Skip confirmations (dangerous!):**
```bash
python scripts/reset_setup.py --full --yes
```

---

## Manual Reset (If Needed)

**Setup only:**
```bash
rm db/user_config.db
```

**Everything:**
```bash
rm db/user_config.db
rm db/blockchain_tracking.db
rm db/sales_analytics.db
rm db/collections.db
rm -rf knowledge_base/processed/*
rm -rf knowledge_base/media/*
rm -rf knowledge_base/embeddings/*
```

---

## After Reset

1. Start the server:
   ```bash
   python scripts/interface/visual_browser.py
   ```

2. Visit: http://localhost:5000

3. You'll see the setup wizard again!

---

## What Files to Delete for Different Scenarios

### Just want new minting addresses?
**Don't delete anything!** You can add/modify addresses after setup:
```python
python
from scripts.interface.user_config_db import UserConfigDB
user_db = UserConfigDB()
user = user_db.get_primary_user()
user_db.add_minting_address(user['id'], '0xNewAddress', label='New Wallet')
```

### Want to re-import blockchain data?
```bash
rm db/blockchain_tracking.db
# Then run blockchain scraper again
```

### Want to clear scraped content but keep user config?
```bash
rm -rf knowledge_base/processed/*
rm -rf knowledge_base/media/*
# Setup wizard won't run again
```

### Want to test setup wizard again?
```bash
python scripts/reset_setup.py
# Quick and safe!
```

### Nuclear option (start completely fresh)?
```bash
python scripts/reset_setup.py --full --yes
# Deletes EVERYTHING
```

---

## Files That Store Your Setup

| File | What It Stores |
|------|----------------|
| `db/user_config.db` | Email, minting addresses, setup completion |
| `db/blockchain_tracking.db` | Scraped NFT data, tracked addresses |
| `db/sales_analytics.db` | Sales data, collectors |
| `db/collections.db` | Collection hierarchies |
| `knowledge_base/processed/` | Scraped markdown files |
| `knowledge_base/media/` | Images, videos, audio files |
| `knowledge_base/embeddings/` | Search index |

---

## Pro Tips

- **Backup before full reset:** Copy the `db/` folder to save your data
- **Test setup wizard:** Use `python scripts/reset_setup.py` to test without losing data
- **Add addresses later:** You don't need to reset to add more minting addresses
- **Marketing list:** Query `user_config` table to export emails where `marketing_opt_in = TRUE`

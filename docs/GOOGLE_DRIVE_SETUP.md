# Google Drive Automation Setup Guide

Complete guide to setting up automated file collection from Google Drive.

---

## Overview

The Google Drive automation system allows you to:
- Upload files to a specific Google Drive folder ("WEB3GISELAUTOMATE")
- Automatically download and process them (PDFs, images, text files)
- Extract text content using OCR and PDF parsers
- Add content to your personal knowledge base
- Search across all uploaded files

---

## Prerequisites

1. Google account with Google Drive access
2. Python environment with dependencies installed
3. Git repository initialized

---

## Part 1: Google Cloud Project Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Project name: `ARCHIV-IT` (or your choice)
4. Click "Create"

### Step 2: Enable Google Drive API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and click "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Click "Configure Consent Screen"
   - Select "External" (unless you have Google Workspace)
   - Click "Create"
   - Fill in:
     - App name: `ARCHIV-IT`
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip this (click "Save and Continue")
   - Test users: Add your Gmail address
   - Click "Save and Continue"

4. Back to "Create OAuth client ID":
   - Application type: **Desktop app**
   - Name: `Drive Automation Desktop Client`
   - Click "Create"

5. **Download credentials:**
   - Click the download button (⬇) next to your newly created OAuth 2.0 Client ID
   - Save the JSON file

### Step 4: Install Credentials

1. Rename the downloaded file to `google_drive_credentials.json`
2. Move it to your project:
   ```bash
   mv ~/Downloads/client_secret_*.json /Users/onthego/+NEWPROJ/config/google_drive_credentials.json
   ```

3. Verify it's in place:
   ```bash
   ls -l config/google_drive_credentials.json
   ```

---

## Part 2: Install Dependencies

Install the Google Drive API libraries:

```bash
cd /Users/onthego/+NEWPROJ
source venv/bin/activate
pip install -r requirements.txt
```

This will install:
- `google-auth` - Authentication
- `google-auth-oauthlib` - OAuth flow
- `google-auth-httplib2` - HTTP transport
- `google-api-python-client` - Drive API client

---

## Part 3: First-Time Authentication

### Test Connection

Run the test command to authenticate:

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/drive_collector.py --test
```

**What happens:**
1. A browser window will open
2. Sign in with your Google account
3. Google will show a warning "Google hasn't verified this app"
   - Click "Advanced"
   - Click "Go to ARCHIV-IT (unsafe)" (it's your own app)
4. Click "Allow" to grant access
5. You'll see "The authentication flow has completed"
6. Close the browser

**Terminal output:**
```
✓ Connection successful!

Your Google Drive folders:
  - My Folder 1
  - My Folder 2
  - ...
```

A token file will be created at: `config/google_drive_token.json`

**Important:** This token allows the script to access your Drive without asking again.

---

## Part 4: Create the Watch Folder

The automation looks for a folder named **"WEB3GISELAUTOMATE"** in your Google Drive.

### Option A: Let the Script Create It

Run the collector once:

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/drive_collector.py
```

It will create the folder if it doesn't exist.

### Option B: Create Manually

1. Go to [Google Drive](https://drive.google.com)
2. Click "New" → "Folder"
3. Name it exactly: `WEB3GISELAUTOMATE`
4. Click "Create"

---

## Part 5: Upload Your First File

### Test Upload

1. Go to Google Drive
2. Navigate to the "WEB3GISELAUTOMATE" folder
3. Click "New" → "File upload"
4. Upload a test file (PDF, image, or text file)

### Run Collection

```bash
cd /Users/onthego/+NEWPROJ
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/drive_collector.py
```

**What happens:**
1. Script connects to Google Drive
2. Finds the "WEB3GISELAUTOMATE" folder
3. Lists all files in it
4. Downloads each file
5. Creates metadata markdown files
6. Moves processed files to a "Processed" subfolder

**Output:**
```
============================================================
Google Drive Collection - Folder: WEB3GISELAUTOMATE
============================================================

Authenticating with Google Drive...
✓ Connected to Google Drive

✓ Found folder: WEB3GISELAUTOMATE

Found 1 file(s) to process

============================================================
Processing: my-document.pdf
============================================================

Filename: my-document.pdf
Type: application/pdf
Size: 125,432 bytes
Modified: 2026-01-01T10:30:00.000Z
Category: file_general
Doc ID: a1b2c3d4e5f6

Downloading file...
✓ Downloaded to: knowledge_base/attachments/a1b2c3d4e5f6/my-document.pdf
  Raw metadata saved to: knowledge_base/raw/drive_files/drive_a1b2c3d4e5f6_20260101_103045.json
  Markdown saved to: knowledge_base/processed/about_file_general/drive_a1b2c3d4e5f6_20260101_103045.md

Moving file to 'Processed' folder...
✓ Moved to processed folder

✓ Successfully processed file
```

---

## Part 6: Full Automation Pipeline

### Manual Run (Recommended for Testing)

Process files and update embeddings:

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
```

**Pipeline steps:**
1. Collect files from Drive
2. Process file content (extract text)
3. Update embeddings index
4. Commit to git

### Options

**Skip git commit:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py --no-commit
```

**Only collect files (no processing):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py --collect-only
```

---

## Part 7: Daily Automation (Optional)

### Option A: Manual Daily Run

Simply run this command once per day:

```bash
cd /Users/onthego/+NEWPROJ && source venv/bin/activate && KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
```

### Option B: Cron Job (macOS/Linux)

Add to crontab to run daily at 9 AM:

```bash
crontab -e
```

Add this line:
```
0 9 * * * cd /Users/onthego/+NEWPROJ && source venv/bin/activate && KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py >> logs/drive_automation.log 2>&1
```

Create logs directory first:
```bash
mkdir -p /Users/onthego/+NEWPROJ/logs
```

### Option C: Launch Agent (macOS)

Create: `~/Library/LaunchAgents/com.giselx.drive.automation.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.giselx.drive.automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/onthego/+NEWPROJ/venv/bin/python</string>
        <string>/Users/onthego/+NEWPROJ/scripts/orchestration/drive_automation.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/onthego/+NEWPROJ</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/onthego/+NEWPROJ/logs/drive_automation.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/onthego/+NEWPROJ/logs/drive_automation.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>KMP_DUPLICATE_LIB_OK</key>
        <string>TRUE</string>
    </dict>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.giselx.drive.automation.plist
```

---

## Part 8: Supported File Types

### Currently Supported

| Type | Extensions | Processing Method |
|------|-----------|-------------------|
| PDFs | .pdf | Text extraction (pdfplumber or PyPDF2) |
| Images | .png, .jpg, .jpeg | OCR with pytesseract (if installed) |
| Text | .txt, .md | Direct text read |
| Documents | .doc, .docx | Metadata only (content extraction not yet implemented) |

### PDF Processing

Two methods (automatic fallback):
1. **pdfplumber** (preferred) - Better text formatting
2. **PyPDF2** (fallback) - Basic text extraction

### Image Processing (OCR)

Requires **Tesseract OCR** to be installed:

```bash
# macOS
brew install tesseract

# Verify
tesseract --version
```

Without Tesseract, images will be saved with metadata only.

---

## Part 9: Workflow

### Daily Usage

1. **Upload files to Drive:**
   - Go to Google Drive
   - Open "WEB3GISELAUTOMATE" folder
   - Upload PDFs, images, or text files
   - Can upload multiple files at once

2. **Run automation:**
   ```bash
   cd /Users/onthego/+NEWPROJ
   source venv/bin/activate
   KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
   ```

3. **Search your knowledge:**
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "topic from uploaded file"
   ```

### File Organization

After processing, files are moved to:
- **In Drive:** `WEB3GISELAUTOMATE/Processed/` folder
- **Local:** `knowledge_base/attachments/<doc-id>/filename`

Metadata and extracted content:
- **Raw:** `knowledge_base/raw/drive_files/`
- **Processed:** `knowledge_base/processed/about_<category>/`

---

## Part 10: Troubleshooting

### "Credentials file not found"

**Error:**
```
FileNotFoundError: Credentials file not found: config/google_drive_credentials.json
```

**Fix:**
1. Make sure you downloaded OAuth credentials from Google Cloud Console
2. Rename to `google_drive_credentials.json`
3. Move to `config/` directory

### "Access denied" or "Invalid credentials"

**Fix:**
1. Delete token file: `rm config/google_drive_token.json`
2. Run test again: `python scripts/collectors/drive_collector.py --test`
3. Re-authenticate in browser

### "Folder not found"

**Error:**
```
Folder 'WEB3GISELAUTOMATE' not found
```

**Fix:**
1. The script will create it automatically, OR
2. Create it manually in Google Drive (exact name)

### "No files found"

**Possible causes:**
- No files uploaded to the folder yet
- Files already processed (check "Processed" subfolder)
- Unsupported file types

**Fix:**
Upload a test PDF or image to the folder

### OCR not working for images

**Error:**
```
OCR error: pytesseract is not installed
```

**Fix:**
```bash
brew install tesseract
pip install pytesseract
```

### OpenMP library error

**Error:**
```
OMP: Error #15: Initializing libomp.dylib
```

**Fix:**
Always use `KMP_DUPLICATE_LIB_OK=TRUE` before Python commands

---

## Part 11: Configuration

Edit `config/settings.json` to customize:

```json
{
  "google_drive": {
    "enabled": true,
    "watch_folder_name": "WEB3GISELAUTOMATE",
    "poll_interval_seconds": 300,
    "move_processed_files": true,
    "processed_folder_name": "Processed",
    "supported_file_types": ["pdf", "png", "jpg", "jpeg", "txt", "md"],
    "save_files_dir": "knowledge_base/attachments",
    "credentials_file": "config/google_drive_credentials.json",
    "token_file": "config/google_drive_token.json"
  }
}
```

**Options:**
- `enabled` - Turn automation on/off
- `watch_folder_name` - Name of folder to monitor
- `move_processed_files` - Move files after processing (recommended)
- `processed_folder_name` - Where to move processed files
- `supported_file_types` - File extensions to process

---

## Part 12: Security

### Credentials Safety

**Protected files (gitignored):**
- `config/google_drive_credentials.json` - OAuth client secrets
- `config/google_drive_token.json` - Your access token
- `.env` - API keys

**Never commit these to git!**

Check `.gitignore` includes:
```
config/google_drive_credentials.json
config/google_drive_token.json
config/*.json
.env
```

### Token Refresh

The token automatically refreshes when expired. No manual action needed.

### Revoking Access

To revoke Drive access:
1. Go to [Google Account > Security > Third-party apps](https://myaccount.google.com/permissions)
2. Find "ARCHIV-IT"
3. Click "Remove access"
4. Delete local token: `rm config/google_drive_token.json`

---

## Part 13: Mobile Upload (Bonus)

### Upload from Phone

1. Install Google Drive app on your phone
2. Sign in with same Google account
3. Navigate to "WEB3GISELAUTOMATE" folder
4. Tap "+" → Upload
5. Select photos, PDFs, or files
6. Files will be processed next time automation runs

**Perfect for:**
- Photos of notes, sketches, whiteboards
- Screenshots
- PDFs from email
- Quick voice memos (as audio files, metadata only)

---

## Quick Reference

### First-time setup:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test connection (authenticate)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/drive_collector.py --test

# 3. Upload a test file to Drive folder "WEB3GISELAUTOMATE"

# 4. Run first collection
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
```

### Daily usage:
```bash
# Upload files to Google Drive → "WEB3GISELAUTOMATE" folder

# Then run:
cd /Users/onthego/+NEWPROJ
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
```

### Search:
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "your query"
```

---

## Next Steps

1. ✅ Set up Google Cloud project and credentials
2. ✅ Install dependencies
3. ✅ Authenticate with test run
4. ✅ Upload test file
5. ✅ Run automation pipeline
6. ✅ Search for uploaded content
7. 🔄 Set up daily automation (optional)

---

**Need help?** Check the main README.md or review error messages carefully.

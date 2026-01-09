# Gmail Email Collector Setup Guide

This guide explains how to set up the Gmail Email Collector for ARCHIV-IT. The collector automatically retrieves email attachments from messages matching a specific subject filter.

## Overview

The Email Collector uses Gmail API with OAuth 2.0 authentication to:
- Search for emails with a specific subject (default: `WEB3GISELAUTOMATE`)
- Extract PDF and image attachments
- Process attachments through the appropriate processors
- Store processed content in the knowledge base

## Prerequisites

- Python 3.8 or higher
- Google Cloud account
- Gmail account
- Required Python packages (already in requirements.txt):
  - `google-auth-oauthlib`
  - `google-auth-httplib2`
  - `google-api-python-client`

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** at the top of the page
3. Click **New Project**
4. Enter a project name (e.g., "ARCHIV-IT Email Collector")
5. Click **Create**

## Step 2: Enable the Gmail API

1. In your Google Cloud project, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on **Gmail API**
4. Click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** (unless you have a Google Workspace account)
3. Click **Create**
4. Fill in the required fields:
   - **App name**: ARCHIV-IT Email Collector
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click **Save and Continue**
6. On the Scopes page, click **Add or Remove Scopes**
7. Find and select `https://www.googleapis.com/auth/gmail.readonly`
8. Click **Update** then **Save and Continue**
9. On the Test users page:
   - Click **Add Users**
   - Add your Gmail address
   - Click **Save and Continue**
10. Click **Back to Dashboard**

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Desktop app** as the application type
4. Enter a name (e.g., "ARCHIV-IT Desktop Client")
5. Click **Create**
6. Click **Download JSON** to download your credentials
7. Save the file as `config/gmail_credentials.json` in your ARCHIV-IT directory

## Step 5: Configure ARCHIV-IT

### Option A: Web Interface Setup

1. Start the ARCHIV-IT server:
   ```bash
   python scripts/interface/visual_browser.py
   ```

2. Navigate to `http://localhost:5000/email-setup`

3. Upload your `credentials.json` file

4. Configure the subject filter (default: `WEB3GISELAUTOMATE`)

5. Click **Test Gmail Connection** to authorize

6. A browser window will open for Google OAuth

7. Sign in and grant permissions

### Option B: Command Line Setup

1. Place your credentials file at `config/gmail_credentials.json`

2. Run the collector with test flag:
   ```bash
   cd scripts
   python -m collectors.email_collector --oauth --test
   ```

3. Follow the OAuth flow in your browser

4. The token will be saved at `config/gmail_token.json`

## Step 6: Usage

### Automatic Sync via Web Interface

1. Go to `/email-setup`
2. Configure subject filter if needed
3. Click **Sync Now**

### API Endpoints

**Trigger Email Sync**
```http
POST /api/email/sync
Content-Type: application/json

{
    "subject_filter": "WEB3GISELAUTOMATE",
    "max_results": 50
}
```

**Get Sync Status**
```http
GET /api/email/status
```

**Test Connection**
```http
POST /api/email/test
```

**Update Configuration**
```http
POST /api/email/config
Content-Type: application/json

{
    "enabled": true,
    "subject_filter": "WEB3GISELAUTOMATE",
    "max_results": 50
}
```

### Command Line Usage

```bash
# Test connection
python -m collectors.email_collector --oauth --test

# Sync with default settings
python -m collectors.email_collector --oauth

# Custom subject filter
python -m collectors.email_collector --oauth --subject "MY_CUSTOM_SUBJECT"

# Limit results
python -m collectors.email_collector --oauth --max-results 10
```

## Configuration Options

Add these to `config/settings.json`:

```json
{
    "gmail": {
        "enabled": true,
        "credentials_file": "config/gmail_credentials.json",
        "token_file": "config/gmail_token.json",
        "subject_filter": "WEB3GISELAUTOMATE",
        "max_results": 50,
        "save_attachments_dir": "knowledge_base/media/email_attachments"
    }
}
```

## Supported Attachment Types

The collector processes these file types:

| Extension | Type | Processor |
|-----------|------|-----------|
| `.pdf` | PDF | PDF text extraction |
| `.png` | Image | OCR (if available) |
| `.jpg/.jpeg` | Image | OCR (if available) |
| `.gif` | Image | OCR (if available) |
| `.webp` | Image | OCR (if available) |
| `.txt` | Text | Direct read |
| `.md` | Markdown | Direct read |

Other attachment types are logged and skipped.

## How It Works

1. **Search**: The collector searches Gmail for messages matching the subject filter that have attachments

2. **Extract**: For each matching message, supported attachments are downloaded

3. **Process**: Each attachment is processed:
   - PDFs: Text is extracted using pdfplumber or PyPDF2
   - Images: Metadata extracted; OCR if pytesseract available
   - Text files: Content read directly

4. **Store**: Processed content is saved to the knowledge base:
   - Raw data: `knowledge_base/raw/email_attachments/`
   - Markdown: `knowledge_base/processed/about_[category]/`
   - Attachments: `knowledge_base/media/email_attachments/`

## Email Workflow Example

1. Send an email to yourself (or have someone send to you) with:
   - Subject containing `WEB3GISELAUTOMATE`
   - PDF or image attachments

2. Run sync from the web interface or API

3. Attachments are processed and added to your knowledge base

4. Search for the content using the ARCHIV-IT search

## Troubleshooting

### "Gmail OAuth libraries not available"

Install the required packages:
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "Credentials not found"

Ensure `config/gmail_credentials.json` exists and contains valid OAuth credentials.

### "Token expired"

Delete `config/gmail_token.json` and re-authenticate.

### "Access denied"

1. Ensure your email is added as a test user in OAuth consent screen
2. Check that Gmail API is enabled
3. Verify the scopes include `gmail.readonly`

### "Quota exceeded"

Gmail API has usage limits. Wait a few minutes and try again.

## Security Notes

- OAuth tokens are stored locally in `config/gmail_token.json`
- Credentials are stored locally in `config/gmail_credentials.json`
- Never commit these files to version control
- The collector only requests read-only access to Gmail
- No email content is sent to external servers

## Legacy IMAP Mode

For backwards compatibility, the collector also supports IMAP with app passwords:

1. Set environment variables:
   ```bash
   GMAIL_EMAIL=your@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   ```

2. Run without `--oauth` flag:
   ```bash
   python -m collectors.email_collector --test
   ```

Note: OAuth is recommended over app passwords for better security.

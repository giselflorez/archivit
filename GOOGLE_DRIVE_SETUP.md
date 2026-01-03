# Google Drive Setup Guide

## Issue
Your Google Drive collector is configured but the API is not enabled for your project.

## Quick Fix - Enable Google Drive API

### Step 1: Enable the API
Visit this URL to enable the Google Drive API for your project:
```
https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=889962217438
```

1. Click the **"Enable"** button
2. Wait a few seconds for the API to activate
3. You should see "API enabled" status

### Step 2: Test the Connection
After enabling the API, test the connection:

```bash
cd /Users/onthego/+NEWPROJ
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/drive_collector.py --test
```

You should see:
- ✓ Connection successful!
- Your Google Drive folders listed

### Step 3: Run the Collector
Once the API is enabled, run the collector to sync files:

```bash
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
```

## What Was Fixed

The collector now **recursively searches all subdirectories** in your Drive folder:
```
WEB3AUTOMATE/               ← Your folder (ID: 11cv5o0ZbcVH3wTlIyx6eClKAh1kqCekM)
├── subfolder1/
│   ├── file1.pdf          ← Will now be found
│   └── file2.jpg
├── subfolder2/
│   └── nested/
│       └── file3.txt      ← Even nested files will be found
└── file_at_root.pdf       ← Already was finding these
```

## Configuration

Your Drive settings in `config/settings.json`:
```json
{
  "google_drive": {
    "enabled": true,
    "watch_folder_name": "WEB3AUTOMATE",
    "watch_folder_id": "11cv5o0ZbcVH3wTlIyx6eClKAh1kqCekM",
    "move_processed_files": true,
    "processed_folder_name": "Processed",
    "supported_file_types": ["pdf", "png", "jpg", "jpeg", "txt", "md", "doc", "docx"]
  }
}
```

## How It Works Now

1. **Scans recursively**: Finds all subdirectories in WEB3AUTOMATE folder
2. **Discovers all files**: Searches each subdirectory for supported file types
3. **Downloads files**: Saves to `knowledge_base/attachments/{doc_id}/`
4. **Processes content**: Extracts text from PDFs, OCR from images
5. **Moves to Processed**: Moves files to "Processed" subfolder after import
6. **Updates embeddings**: Makes files searchable

## Supported File Types

The collector will find and process:
- **PDFs**: Text extraction
- **Images**: JPG, PNG (OCR with tesseract if installed)
- **Documents**: DOC, DOCX
- **Text**: TXT, MD

## Manual Run Commands

### Full automation (recommended)
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
```

### Just collect files (no processing)
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/drive_collector.py
```

### Collect without git commit
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py --no-commit
```

## Troubleshooting

### "API not enabled" error
- Make sure you clicked Enable at the URL above
- Wait 1-2 minutes after enabling for it to propagate
- Try the test command again

### "No files found"
- Check that files are in subdirectories of the WEB3AUTOMATE folder
- Make sure files are supported types (pdf, jpg, png, txt, md, doc, docx)
- Files may have already been moved to "Processed" subfolder

### "Permission denied"
- Re-authenticate by deleting `config/google_drive_token.json`
- Run the collector again - it will prompt for login

### Files already processed
If files were already moved to "Processed" folder:
- They won't be re-imported (this is by design)
- Move them back to WEB3AUTOMATE folder if you want to re-import
- Or disable `move_processed_files` in settings.json

## Next Steps

1. ✅ **Enable the API** at the URL above
2. ✅ **Test connection** with `--test` flag
3. ✅ **Run collector** with `drive_automation.py`
4. Check `knowledge_base/processed/` for imported files
5. Search for them at http://localhost:5001

The collector is now ready to find all files in your entire Drive folder tree!

#!/bin/bash
# Quick script to process uploaded files

UPLOAD_FOLDER="$HOME/Desktop/WEB3AUTOMATE_UPLOAD"

echo "=================================================="
echo "Processing files from: $UPLOAD_FOLDER"
echo "=================================================="
echo ""

cd /Users/onthego/+NEWPROJ
source venv/bin/activate

# Check if there are any files
if [ -z "$(ls -A "$UPLOAD_FOLDER" 2>/dev/null)" ]; then
    echo "No files found in upload folder."
    echo ""
    echo "To upload files:"
    echo "1. Go to: https://drive.google.com/drive/folders/11cv5o0ZbcVH3wTlIyx6eClKAh1kqCekM"
    echo "2. Download files from your WEB3AUTOMATE folder"
    echo "3. Drop them in: $UPLOAD_FOLDER"
    echo "4. Run this script again"
    exit 0
fi

echo "Found files:"
ls -1 "$UPLOAD_FOLDER"
echo ""

# Process all files
echo "Processing..."
KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/attachment_processor.py "$UPLOAD_FOLDER"/* --parent-id web3automate

echo ""
echo "Updating search index..."
KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/embeddings_generator.py --update

echo ""
echo "Moving processed files to archive..."
mkdir -p "$UPLOAD_FOLDER/processed"
mv "$UPLOAD_FOLDER"/* "$UPLOAD_FOLDER/processed/" 2>/dev/null

echo ""
echo "=================================================="
echo "✓ Processing complete!"
echo "=================================================="
echo ""
echo "Search your files:"
echo "  KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py \"your query\""

#!/bin/bash
# Download Buckminster Fuller "Everything I Know" (1975)
# 42 hours across 12 parts from Archive.org

DOWNLOAD_DIR="/Users/onthego/ARCHIVIT_01/northstar_knowledge_bank/videos/downloads/Fuller_Everything_I_Know"
mkdir -p "$DOWNLOAD_DIR"

echo "=== DOWNLOADING FULLER 'EVERYTHING I KNOW' (42 HOURS) ==="
echo "This is a large download (~26GB total). Parts download sequentially."
echo ""

# Download all 12 parts
for PART in $(seq -w 1 12); do
    echo "--- Downloading Part $PART of 12 ---"
    IDENTIFIER="buckminsterfullereverythingiknow${PART}"

    # Get the main video file (usually the largest mp4)
    curl -s "https://archive.org/metadata/${IDENTIFIER}" | \
    python3 -c "
import json, sys
d = json.load(sys.stdin)
# Find largest mp4 file
mp4s = [(f['name'], int(f.get('size', 0))) for f in d['files'] if f['name'].endswith('.mp4')]
if mp4s:
    mp4s.sort(key=lambda x: x[1], reverse=True)
    print(mp4s[0][0])
" > /tmp/fuller_file_${PART}.txt

    FILENAME=$(cat /tmp/fuller_file_${PART}.txt 2>/dev/null)

    if [ -n "$FILENAME" ]; then
        OUTPUT_FILE="${DOWNLOAD_DIR}/Fuller_Part${PART}.mp4"
        if [ ! -f "$OUTPUT_FILE" ]; then
            echo "Downloading: $FILENAME"
            curl -L -o "$OUTPUT_FILE" "https://archive.org/download/${IDENTIFIER}/${FILENAME}" --progress-bar
            echo "Part $PART complete."
        else
            echo "Part $PART already exists, skipping."
        fi
    else
        echo "Warning: Could not find video file for Part $PART"
    fi
    echo ""
done

echo "=== DOWNLOAD COMPLETE ==="
echo "Location: $DOWNLOAD_DIR"
ls -lh "$DOWNLOAD_DIR"

#!/bin/bash
# REVERT SCRIPT - Restore DOC-8 to pre-ULTRATHINK state
# Run this script if you don't like the design changes

BACKUP_DIR="$(dirname "$0")"
PROJECT_DIR="/Users/onthego/ARCHIVIT_01"

echo "Reverting DOC-8 to pre-ULTRATHINK state..."

# Restore files
cp "$BACKUP_DIR/doc8_archivist.html" "$PROJECT_DIR/scripts/interface/templates/doc8_archivist.html"
cp "$BACKUP_DIR/team_gallery.html" "$PROJECT_DIR/scripts/interface/templates/team_gallery.html"
cp "$BACKUP_DIR/nft8_collector.html" "$PROJECT_DIR/scripts/interface/templates/nft8_collector.html"

echo "Done! Files restored from backup."
echo "Refresh http://localhost:5001/doc8 to see the original version."

#!/bin/bash
# ═══════════════════════════════════════════════════════════
#         ARCHIV-IT - Create Clean Tester Package
# ═══════════════════════════════════════════════════════════
# This script creates a clean zip for testers WITHOUT modifying
# your working copy. Your data stays intact.
# ═══════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="ARCHIVIT_BETA_${TIMESTAMP}"
TEMP_DIR="/tmp/${PACKAGE_NAME}"
OUTPUT_ZIP="${SCRIPT_DIR}/${PACKAGE_NAME}.zip"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "         Creating Clean Tester Package"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────
# Step 1: Copy project to temp location
# ─────────────────────────────────────────────────────────────
echo "[1/5] Copying project..."
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy everything except venv and large generated folders
rsync -a --progress \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='*.zip' \
    "$SCRIPT_DIR/" "$TEMP_DIR/"

echo "      Done"

# ─────────────────────────────────────────────────────────────
# Step 2: Remove security-sensitive files
# ─────────────────────────────────────────────────────────────
echo "[2/5] Removing sensitive files..."

# API keys and OAuth tokens
rm -f "$TEMP_DIR/.env"
rm -f "$TEMP_DIR/config/google_drive_token.json"
rm -f "$TEMP_DIR/config/google_drive_credentials.json"
rm -f "$TEMP_DIR/config/gmail_credentials.json" 2>/dev/null || true
rm -f "$TEMP_DIR/config/gmail_token.json" 2>/dev/null || true

echo "      Removed: .env, OAuth tokens"

# ─────────────────────────────────────────────────────────────
# Step 3: Remove personal data
# ─────────────────────────────────────────────────────────────
echo "[3/5] Removing personal data..."

# Knowledge base (your personal archive)
rm -rf "$TEMP_DIR/knowledge_base/raw/"*
rm -rf "$TEMP_DIR/knowledge_base/processed/"*
rm -rf "$TEMP_DIR/knowledge_base/media/"*
rm -rf "$TEMP_DIR/knowledge_base/attachments/"*
rm -f "$TEMP_DIR/knowledge_base/training_data.json"

# Databases (your personal data)
rm -f "$TEMP_DIR/db/"*.db
rm -rf "$TEMP_DIR/db/txtai_index/"*
rm -rf "$TEMP_DIR/db/chroma/"*
rm -rf "$TEMP_DIR/db/visual_cache/"*

# Config with personal data
rm -f "$TEMP_DIR/config/ignored_drive_files.json"
rm -f "$TEMP_DIR/config/email_sync_status.json" 2>/dev/null || true

# Reset usage tracking
echo '{"requests_today": 0, "requests_this_month": 0, "last_reset_date": "", "last_reset_month": "", "tier": "free_tier"}' > "$TEMP_DIR/config/usage_tracking.json"

echo "      Removed: knowledge_base/*, db/*.db, personal configs"

# ─────────────────────────────────────────────────────────────
# Step 4: Remove internal dev docs
# ─────────────────────────────────────────────────────────────
echo "[4/5] Removing internal docs..."

# Agent/dev docs
rm -f "$TEMP_DIR/AGENT_HANDOFF.md"
rm -f "$TEMP_DIR/AGENT_INSTRUCTIONS.md"
rm -f "$TEMP_DIR/CLAUDE_SESSIONS.md"
rm -f "$TEMP_DIR/PROJECT_STATE.md"
rm -f "$TEMP_DIR/STRATEGIC_ANALYSIS.md"
rm -rf "$TEMP_DIR/sessions/"

# Dev summaries
rm -f "$TEMP_DIR/DEDUPLICATION_COMPLETE.md"
rm -f "$TEMP_DIR/NFT_SCRAPER_SYSTEM_SUMMARY.md"
rm -f "$TEMP_DIR/SUPERRARE_SCRAPER_FIX.md"
rm -f "$TEMP_DIR/VISUAL_TRANSLATOR_REDESIGN_SUMMARY.md"
rm -f "$TEMP_DIR/VISUAL_TRANSLATOR_V2_REDESIGN.md"
rm -f "$TEMP_DIR/PROJECT_BIBLE.md"

# Security/internal docs (not for testers)
rm -f "$TEMP_DIR/docs/SPATIAL_SECURITY_THREAT_MODEL.md"
rm -f "$TEMP_DIR/docs/SECURITY_AUDIT_TRACKER.md"

# Internal specs (legal, protection)
rm -f "$TEMP_DIR/ARCHIV-IT_IP_Legal_DocumentationWEB3GISEL.txt"
rm -f "$TEMP_DIR/ARCHIV-IT_DESCRIPTION_WEB3GISEL.txt"
rm -f "$TEMP_DIR/ARCHIV-IT_Product_Documentation.txt"
rm -f "$TEMP_DIR/ARCHIV-IT_Technical_Specification.txt"
rm -f "$TEMP_DIR/PROTECTION_README.md"
rm -f "$TEMP_DIR/QUICK_PROTECTION_GUIDE.md"
rm -f "$TEMP_DIR/ANTI_AI_PROTECTION_SUMMARY.md"
rm -f "$TEMP_DIR/RESET_GUIDE.md"

# Misc dev files
rm -f "$TEMP_DIR/CONVERSATION_BACKUP.md" 2>/dev/null || true
rm -f "$TEMP_DIR/test_upload.txt" 2>/dev/null || true
# Remove test/demo HTML files but KEEP tester documentation
rm -f "$TEMP_DIR/test_centered.html" 2>/dev/null || true
rm -f "$TEMP_DIR/test_layout.html" 2>/dev/null || true
rm -f "$TEMP_DIR/filter_design_demo.html" 2>/dev/null || true
rm -f "$TEMP_DIR/filter_system_iterations.html" 2>/dev/null || true
rm -f "$TEMP_DIR/database_overview_demo.html" 2>/dev/null || true
rm -f "$TEMP_DIR/=1.0.0" 2>/dev/null || true
rm -rf "$TEMP_DIR/scrape-nft" 2>/dev/null || true
rm -rf "$TEMP_DIR/deduplicate-kb" 2>/dev/null || true

# Remove this script from the package
rm -f "$TEMP_DIR/create_tester_package.sh"

echo "      Removed: agent docs, dev notes, internal specs"

# ─────────────────────────────────────────────────────────────
# Step 5: Create empty folder structure
# ─────────────────────────────────────────────────────────────
echo "[5/5] Creating folder structure..."

# Ensure folders exist for testers
mkdir -p "$TEMP_DIR/knowledge_base/raw"
mkdir -p "$TEMP_DIR/knowledge_base/processed"
mkdir -p "$TEMP_DIR/knowledge_base/media"
mkdir -p "$TEMP_DIR/knowledge_base/attachments"
mkdir -p "$TEMP_DIR/db/txtai_index"
mkdir -p "$TEMP_DIR/db/chroma"
mkdir -p "$TEMP_DIR/db/visual_cache"

# Add .gitkeep files
touch "$TEMP_DIR/knowledge_base/raw/.gitkeep"
touch "$TEMP_DIR/knowledge_base/processed/.gitkeep"
touch "$TEMP_DIR/knowledge_base/media/.gitkeep"
touch "$TEMP_DIR/db/.gitkeep"

echo "      Created empty folders"

# ─────────────────────────────────────────────────────────────
# Create ZIP
# ─────────────────────────────────────────────────────────────
echo ""
echo "Creating zip..."

cd /tmp
zip -r "$OUTPUT_ZIP" "$PACKAGE_NAME" -x "*.DS_Store" -x "*__pycache__*"

# Cleanup temp
rm -rf "$TEMP_DIR"

# ─────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────
ZIP_SIZE=$(du -h "$OUTPUT_ZIP" | cut -f1)

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "                    PACKAGE CREATED"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  File: $OUTPUT_ZIP"
echo "  Size: $ZIP_SIZE"
echo ""
echo "  Share this zip with testers!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

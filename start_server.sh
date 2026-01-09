#!/bin/bash
# ═══════════════════════════════════════════════════════════
#                 ARCHIV-IT SERVER
# ═══════════════════════════════════════════════════════════

# Get script directory (works from anywhere)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Kill any existing process on port 5001
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 1

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: venv not found. Run ./install.sh first"
    exit 1
fi

# macOS compatibility
export KMP_DUPLICATE_LIB_OK=TRUE

# Start server
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "                   ARCHIV-IT SERVER"
echo "═══════════════════════════════════════════════════════════"
echo ""
# Get local IP for network access
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "your-ip")
echo "  LOCAL:   http://localhost:5001"
echo "  NETWORK: http://${LOCAL_IP}:5001  (iPad/other devices)"
echo ""
echo "  Visualizations:"
echo "    /semantic-network       - 3D force-directed graph"
echo "    /edition-constellation  - Spatial edition collector analysis"
echo "    /provenance-arteries    - Blockchain bloodflow visualization"
echo "    /tag-cloud              - Tag network visualization"
echo "    /point-cloud            - 5 paradigm visualizers"
echo ""
echo "  Features:"
echo "    /visual-translator      - AI-powered image analysis"
echo "    /add-content            - Import from URLs"
echo "    /blockchain-tracker     - NFT provenance tracking"
echo "    /data-source-manager    - Unified data control"
echo "    /verified-social        - Verified social prototype"
echo ""
echo "  Press Ctrl+C to stop"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

python scripts/interface/visual_browser.py

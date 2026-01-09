#!/bin/bash
# ═══════════════════════════════════════════════════════════
#                 ARCHIV-IT INSTALLER
# ═══════════════════════════════════════════════════════════

set -e

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "              ARCHIV-IT INSTALLER"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Get script directory (works even if called from elsewhere)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ─────────────────────────────────────────────────────────────
# 1. Check Python
# ─────────────────────────────────────────────────────────────
echo "[1/4] Checking Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "      Found Python $PYTHON_VERSION"
else
    echo "      ERROR: Python 3 not found"
    echo ""
    echo "      Install Python from: https://www.python.org/downloads/"
    exit 1
fi

# ─────────────────────────────────────────────────────────────
# 2. Create Virtual Environment
# ─────────────────────────────────────────────────────────────
echo "[2/4] Setting up virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "      Created venv/"
else
    echo "      venv/ already exists"
fi

source venv/bin/activate

# ─────────────────────────────────────────────────────────────
# 3. Install Dependencies
# ─────────────────────────────────────────────────────────────
echo "[3/4] Installing dependencies (this may take a few minutes)..."

pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "      Done"

# ─────────────────────────────────────────────────────────────
# 4. Create .env if missing
# ─────────────────────────────────────────────────────────────
echo "[4/4] Checking configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "      Created .env from template"
        echo "      (Edit .env to add your API keys - optional)"
    else
        touch .env
        echo "      Created empty .env"
    fi
else
    echo "      .env exists"
fi

# ─────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "              INSTALLATION COMPLETE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Start the server:"
echo "     ./start_server.sh"
echo ""
echo "  2. Open in browser:"
echo "     http://localhost:5001"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

#!/usr/bin/env python3
"""
WSGI entry point for cloud deployment
"""
import os
import sys
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(scripts_dir))

# Import the app
from interface.visual_browser import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

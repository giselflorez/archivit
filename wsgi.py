#!/usr/bin/env python3
"""
WSGI entry point for cloud deployment
Sets up Python path correctly before importing the app
"""
import os
import sys
from pathlib import Path

# Set up paths BEFORE any app imports
project_root = Path(__file__).parent
scripts_dir = project_root / "scripts"

# Add both project root and scripts to path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(scripts_dir))

# Set working directory
os.chdir(scripts_dir / "interface")

# Now import the app
from interface.visual_browser import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

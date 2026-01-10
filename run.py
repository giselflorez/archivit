#!/usr/bin/env python3
import os
import sys
from pathlib import Path

print("=== run.py starting ===", flush=True)

# Set up paths
project_root = Path(__file__).parent
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(scripts_dir))

# Get port from environment
port = int(os.environ.get("PORT", 5001))
print(f"Starting Flask on port {port}", flush=True)

# Import and run app
from interface.visual_browser import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

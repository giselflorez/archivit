#!/usr/bin/env python3
import os
import sys
from pathlib import Path

print("=== run.py starting ===")
print(f"PORT env var: {os.environ.get('PORT', 'NOT SET')}")

# Set up paths
project_root = Path(__file__).parent
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(scripts_dir))

# Get port from environment
port = int(os.environ.get("PORT", 5001))
print(f"Using port: {port}")

# Import and run app
from interface.visual_browser import app

if __name__ == "__main__":
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        "bind": f"0.0.0.0:{port}",
        "workers": 2,
        "timeout": 120,
    }

    print(f"Starting on port {port}")
    StandaloneApplication(app, options).run()

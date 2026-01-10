#!/usr/bin/env python3
import os
import sys
from pathlib import Path

print("=== run.py starting ===", flush=True)

# Get port from environment FIRST
port = int(os.environ.get("PORT", 5001))
print(f"Will use port {port}", flush=True)

# Minimal Flask app to test deployment
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>ARCHIVIT - Deployment Test OK</h1><p>Basic Flask is working. Full app loading next...</p>"

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    print(f"Starting minimal Flask on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False)

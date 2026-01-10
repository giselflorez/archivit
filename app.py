import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>ARCHIVIT</h1><p>Deployment working!</p>"

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

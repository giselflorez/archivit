import os
import sys
import logging
from flask import Flask, render_template, request, session, redirect, url_for

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Try to import markdown, fall back gracefully
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')

logger.info(f"Starting app - BASE_DIR: {BASE_DIR}")
logger.info(f"Template dir exists: {os.path.exists(TEMPLATE_DIR)}")
logger.info(f"Docs dir exists: {os.path.exists(DOCS_DIR)}")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'archivit-counsel-2026-secure-key')
logger.info("Flask app created successfully")

# Access code for legal counsel (can be changed via Railway environment variable)
COUNSEL_ACCESS_CODE = os.environ.get('COUNSEL_ACCESS_CODE', 'ARCHIVIT-COUNSEL-2026')

def render_markdown(filepath):
    """Safely render markdown file to HTML"""
    if not os.path.exists(filepath):
        return f"<p>File not found: {filepath}</p>"
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        if HAS_MARKDOWN:
            return markdown.markdown(content, extensions=['tables', 'fenced_code'])
        else:
            return f"<pre>{content}</pre>"
    except Exception as e:
        return f"<p>Error reading file: {e}</p>"

@app.route("/")
def home():
    try:
        return render_template("team_gallery.html")
    except Exception as e:
        return "<h1>ARCHIVIT</h1><p>Deployment working!</p>"

@app.route("/health")
def health():
    return "OK"

@app.route("/debug")
def debug():
    """Debug endpoint to diagnose deployment issues"""
    import json
    info = {
        "base_dir": BASE_DIR,
        "template_dir": TEMPLATE_DIR,
        "docs_dir": DOCS_DIR,
        "template_exists": os.path.exists(TEMPLATE_DIR),
        "docs_exists": os.path.exists(DOCS_DIR),
        "templates_contents": os.listdir(TEMPLATE_DIR) if os.path.exists(TEMPLATE_DIR) else [],
        "docs_contents": os.listdir(DOCS_DIR)[:10] if os.path.exists(DOCS_DIR) else [],
        "has_markdown": HAS_MARKDOWN,
        "python_version": sys.version,
        "cwd": os.getcwd()
    }
    return f"<pre>{json.dumps(info, indent=2)}</pre>"

@app.route("/counsel", methods=["GET", "POST"])
def counsel_login():
    """Password-protected entry point for legal counsel documents"""
    error = None

    if request.method == "POST":
        code = request.form.get("access_code", "").strip()
        if code == COUNSEL_ACCESS_CODE:
            session['counsel_authenticated'] = True
            return redirect(url_for('counsel_documents'))
        else:
            error = "Invalid access code. Please try again."

    try:
        return render_template("counsel_login.html", error=error)
    except Exception as e:
        return f"<h1>Template Error</h1><p>{e}</p><p>Template dir: {TEMPLATE_DIR}</p>"

@app.route("/counsel/documents")
def counsel_documents():
    """Display legal counsel documents - requires authentication"""
    if not session.get('counsel_authenticated'):
        return redirect(url_for('counsel_login'))

    legal_briefing = render_markdown(os.path.join(DOCS_DIR, 'LEGAL_COUNSEL_BRIEFING.md'))
    for_the_people = render_markdown(os.path.join(DOCS_DIR, 'FOR_THE_PEOPLE.md'))
    release_checklist = render_markdown(os.path.join(DOCS_DIR, 'RELEASE_CHECKLIST.md'))

    try:
        return render_template(
            "counsel_documents.html",
            legal_briefing=legal_briefing,
            for_the_people=for_the_people,
            release_checklist=release_checklist
        )
    except Exception as e:
        return f"<h1>Template Error</h1><p>{e}</p>"

@app.route("/counsel/logout")
def counsel_logout():
    """Log out from counsel area"""
    session.pop('counsel_authenticated', None)
    return redirect(url_for('counsel_login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

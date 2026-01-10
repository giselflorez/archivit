import os
from flask import Flask, render_template, request, session, redirect, url_for
import markdown

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'archivit-counsel-2026-secure-key')

# Access code for legal counsel - CHANGE THIS before sharing with lawyer
COUNSEL_ACCESS_CODE = "ARCHIVIT-COUNSEL-2026"

@app.route("/")
def home():
    return "<h1>ARCHIVIT</h1><p>Deployment working!</p>"

@app.route("/health")
def health():
    return "OK"

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

    return render_template("counsel_login.html", error=error)

@app.route("/counsel/documents")
def counsel_documents():
    """Display legal counsel documents - requires authentication"""
    if not session.get('counsel_authenticated'):
        return redirect(url_for('counsel_login'))

    # Load the legal briefing document
    legal_briefing = ""
    briefing_path = os.path.join(os.path.dirname(__file__), 'docs', 'LEGAL_COUNSEL_BRIEFING.md')
    if os.path.exists(briefing_path):
        with open(briefing_path, 'r') as f:
            legal_briefing = markdown.markdown(f.read(), extensions=['tables', 'fenced_code'])

    # Load the public manifesto
    for_the_people = ""
    people_path = os.path.join(os.path.dirname(__file__), 'docs', 'FOR_THE_PEOPLE.md')
    if os.path.exists(people_path):
        with open(people_path, 'r') as f:
            for_the_people = markdown.markdown(f.read(), extensions=['tables', 'fenced_code'])

    # Load release checklist
    release_checklist = ""
    checklist_path = os.path.join(os.path.dirname(__file__), 'docs', 'RELEASE_CHECKLIST.md')
    if os.path.exists(checklist_path):
        with open(checklist_path, 'r') as f:
            release_checklist = markdown.markdown(f.read(), extensions=['tables', 'fenced_code'])

    return render_template(
        "counsel_documents.html",
        legal_briefing=legal_briefing,
        for_the_people=for_the_people,
        release_checklist=release_checklist
    )

@app.route("/counsel/logout")
def counsel_logout():
    """Log out from counsel area"""
    session.pop('counsel_authenticated', None)
    return redirect(url_for('counsel_login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

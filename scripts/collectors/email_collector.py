#!/usr/bin/env python3
"""
Email Collector - Automatically collect emails with subject "WEB3GISELAUTOMATE"
"""
import imaplib
import email
from email.header import decode_header
import os
import json
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import yaml
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def generate_id(email_subject, sender, date):
    """Generate a unique ID based on email metadata"""
    content = f"{email_subject}_{sender}_{date}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def determine_subject(email_body, email_subject):
    """Determine the subject category based on email content"""
    combined_text = f"{email_subject} {email_body}".lower()

    if "giselxflorez" in combined_text:
        return "giselxflorez"
    elif "giselx" in combined_text:
        return "giselx"
    elif "gisel" in combined_text:
        return "gisel_florez"
    else:
        return "email_general"

def extract_tags(email_body, email_subject):
    """Extract relevant tags from email content"""
    tags = ["email", "automated"]

    combined_text = f"{email_subject} {email_body}".lower()

    tag_keywords = {
        'art': ['art', 'artwork', 'creative', 'artist'],
        'blockchain': ['blockchain', 'crypto', 'nft', 'web3'],
        'digital_identity': ['identity', 'digital', 'online', 'persona'],
        'philosophy': ['philosophy', 'thought', 'concept', 'idea'],
        'technology': ['tech', 'technology', 'digital', 'innovation'],
        'project': ['project', 'work', 'collaboration'],
        'research': ['research', 'study', 'analysis']
    }

    for tag, keywords in tag_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            tags.append(tag)

    return list(set(tags))  # Remove duplicates

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def decode_email_header(header):
    """Decode email header"""
    if header is None:
        return ""

    decoded_parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            decoded_parts.append(str(part))
    return ''.join(decoded_parts)

def connect_to_gmail():
    """Connect to Gmail via IMAP"""
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        raise ValueError("GMAIL_EMAIL and GMAIL_APP_PASSWORD must be set in .env file")

    config = load_config()
    imap_server = config['email']['imap_server']
    imap_port = config['email']['imap_port']

    print(f"Connecting to {imap_server}:{imap_port}...")

    # Connect to Gmail
    imap = imaplib.IMAP4_SSL(imap_server, imap_port)
    imap.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)

    print(f"✓ Connected as {GMAIL_EMAIL}")
    return imap

def search_emails(imap, subject_filter):
    """Search for unread emails with specific subject"""
    # Select inbox
    imap.select("INBOX")

    # Search for unread emails with subject
    search_criteria = f'(SUBJECT "{subject_filter}")'
    status, messages = imap.search(None, search_criteria)

    if status != "OK":
        print("No emails found")
        return []

    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} email(s) with subject '{subject_filter}'")

    return email_ids

def parse_email_message(msg):
    """Extract email components"""
    email_data = {
        'subject': decode_email_header(msg['subject']),
        'from': decode_email_header(msg['from']),
        'to': decode_email_header(msg['to']),
        'date': msg['date'],
        'body': '',
        'body_html': '',
        'attachments': []
    }

    # Extract body
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Get body
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    email_data['body'] += body
                except:
                    pass

            elif content_type == "text/html" and "attachment" not in content_disposition:
                try:
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    email_data['body_html'] += html_body
                except:
                    pass

            # Get attachments
            elif "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    email_data['attachments'].append({
                        'filename': decode_email_header(filename),
                        'content': part.get_payload(decode=True),
                        'content_type': content_type
                    })
    else:
        # Not multipart
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            email_data['body'] = body
        except:
            pass

    # If no plain text body, convert HTML to text
    if not email_data['body'] and email_data['body_html']:
        email_data['body'] = clean_html(email_data['body_html'])

    return email_data

def save_attachments(attachments, parent_id):
    """Save email attachments to filesystem"""
    config = load_config()
    attachments_dir = Path(config['email']['save_attachments_dir'])
    attachments_dir.mkdir(parents=True, exist_ok=True)

    saved_attachments = []

    for attachment in attachments:
        filename = attachment['filename']
        content = attachment['content']

        # Create subdirectory for this email
        email_dir = attachments_dir / parent_id
        email_dir.mkdir(exist_ok=True)

        # Save file
        filepath = email_dir / filename
        with open(filepath, 'wb') as f:
            f.write(content)

        saved_attachments.append({
            'filename': filename,
            'filepath': str(filepath),
            'content_type': attachment['content_type'],
            'size': len(content)
        })

        print(f"  Saved attachment: {filename} ({len(content)} bytes)")

    return saved_attachments

def create_markdown(email_data, doc_id, subject_category, saved_attachments):
    """Convert email to markdown with frontmatter"""
    now = datetime.now()
    tags = extract_tags(email_data['body'], email_data['subject'])

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'email',
        'type': 'email_entry',
        'created_at': now.isoformat(),
        'sender': email_data['from'],
        'subject': email_data['subject'],
        'received_date': email_data['date'],
        'has_attachments': len(saved_attachments) > 0,
        'attachment_count': len(saved_attachments),
        'tags': tags
    }

    # Clean subject for title (remove the filter keyword)
    title = email_data['subject'].replace('WEB3GISELAUTOMATE', '').strip(' -')
    if not title:
        title = "Email Entry"

    # Create markdown body
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# Email: {title}

## From
{email_data['from']}

## Date
{email_data['date']}

## Subject
{email_data['subject']}

## Content
{email_data['body'].strip()}

"""

    # Add attachments section if any
    if saved_attachments:
        md_content += "## Attachments\n"
        for i, att in enumerate(saved_attachments, 1):
            md_content += f"{i}. **{att['filename']}** ({att['content_type']}, {att['size']:,} bytes)\n"
            md_content += f"   - Saved to: `{att['filepath']}`\n"
            md_content += f"   - Will be processed separately\n\n"

    md_content += f"## Related Topics\n- Search for more about: {subject_category}\n"

    return md_content

def save_email(markdown_content, raw_data, subject_category, doc_id):
    """Save email as knowledge base entry"""
    # Save raw email data
    raw_dir = Path("knowledge_base/raw/emails")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"email_{doc_id}_{timestamp}.json"
    raw_filepath = raw_dir / raw_filename

    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"Raw email saved to: {raw_filepath}")

    # Save processed markdown
    processed_dir = Path(f"knowledge_base/processed/about_{subject_category}")
    processed_dir.mkdir(parents=True, exist_ok=True)

    md_filename = f"email_{doc_id}_{timestamp}.md"
    md_filepath = processed_dir / md_filename

    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Markdown saved to: {md_filepath}")

    return str(md_filepath)

def mark_as_read(imap, email_id):
    """Mark email as read"""
    imap.store(email_id, '+FLAGS', '\\Seen')

def collect_emails():
    """Main email collection function"""
    config = load_config()

    if not config['email']['enabled']:
        print("Email collection is disabled in config")
        return []

    subject_filter = config['email']['subject_filter']
    mark_read = config['email']['mark_as_read']

    print(f"\n{'='*60}")
    print(f"Email Collection - Subject: {subject_filter}")
    print(f"{'='*60}\n")

    # Connect to Gmail
    imap = connect_to_gmail()

    # Search for emails
    email_ids = search_emails(imap, subject_filter)

    if not email_ids:
        print("No new emails to process")
        imap.logout()
        return []

    processed_emails = []

    # Process each email
    for email_id in email_ids:
        try:
            print(f"\n{'='*60}")
            print(f"Processing email ID: {email_id.decode()}")
            print(f"{'='*60}\n")

            # Fetch email
            status, msg_data = imap.fetch(email_id, "(RFC822)")

            if status != "OK":
                print(f"Failed to fetch email {email_id}")
                continue

            # Parse email
            msg = email.message_from_bytes(msg_data[0][1])
            email_data = parse_email_message(msg)

            # Generate doc ID
            doc_id = generate_id(
                email_data['subject'],
                email_data['from'],
                email_data['date']
            )

            # Determine subject category
            subject_category = determine_subject(
                email_data['body'],
                email_data['subject']
            )

            print(f"From: {email_data['from']}")
            print(f"Subject: {email_data['subject']}")
            print(f"Date: {email_data['date']}")
            print(f"Attachments: {len(email_data['attachments'])}")
            print(f"Category: {subject_category}")
            print(f"Doc ID: {doc_id}")

            # Save attachments
            saved_attachments = []
            if email_data['attachments']:
                print(f"\nSaving {len(email_data['attachments'])} attachment(s)...")
                saved_attachments = save_attachments(email_data['attachments'], doc_id)

            # Create markdown
            markdown = create_markdown(email_data, doc_id, subject_category, saved_attachments)

            # Save email
            filepath = save_email(markdown, email_data, subject_category, doc_id)

            # Mark as read
            if mark_read:
                mark_as_read(imap, email_id)
                print("✓ Marked as read")

            processed_emails.append({
                'id': doc_id,
                'filepath': filepath,
                'subject': email_data['subject'],
                'from': email_data['from'],
                'attachments': saved_attachments
            })

            print(f"✓ Successfully processed email")

        except Exception as e:
            print(f"Error processing email {email_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Logout
    imap.logout()

    print(f"\n{'='*60}")
    print(f"Email Collection Complete")
    print(f"Processed: {len(processed_emails)} email(s)")
    print(f"{'='*60}\n")

    return processed_emails

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Collect emails from Gmail inbox")
    parser.add_argument('--test', action='store_true', help='Test connection only')

    args = parser.parse_args()

    if args.test:
        # Test connection
        try:
            imap = connect_to_gmail()
            print("✓ Connection successful!")
            imap.logout()
        except Exception as e:
            print(f"✗ Connection failed: {e}")
        return

    # Collect emails
    emails = collect_emails()

    if emails:
        print("\nCollected emails:")
        for email_info in emails:
            print(f"  - {email_info['subject']} (ID: {email_info['id']})")

if __name__ == "__main__":
    main()

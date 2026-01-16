#!/usr/bin/env python3
"""
Email Collector - Automatically collect emails with subject "WEB3GISELAUTOMATE"
Supports both Gmail OAuth 2.0 (preferred) and IMAP with App Password (legacy)
"""
import imaplib
import email
from email.header import decode_header
import os
import io
import json
import base64
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import yaml
from bs4 import BeautifulSoup

# Gmail OAuth imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_OAUTH_AVAILABLE = True
except ImportError:
    GMAIL_OAUTH_AVAILABLE = False

# Gmail API Scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Supported attachment types for processing
SUPPORTED_ATTACHMENT_TYPES = {
    'pdf': 'pdf',
    'png': 'image',
    'jpg': 'image',
    'jpeg': 'image',
    'gif': 'image',
    'webp': 'image',
    'txt': 'text',
    'md': 'text'
}

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

    if "founder" in combined_text:
        return "founder"
    elif "founder" in combined_text:
        return "founder"
    elif "founder" in combined_text:
        return "founder"
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

class EmailCollector:
    """
    Gmail OAuth 2.0 based email collector for ARCHIV-IT knowledge base.
    Provides secure authentication and attachment processing.
    """

    def __init__(self, credentials_path=None):
        """
        Initialize the email collector with OAuth credentials.

        Args:
            credentials_path: Path to Gmail OAuth credentials JSON file
        """
        self.config = load_config()
        email_config = self.config.get('gmail', {})

        self.credentials_path = Path(credentials_path or email_config.get(
            'credentials_file', 'config/gmail_credentials.json'))
        self.token_path = Path(email_config.get(
            'token_file', 'config/gmail_token.json'))
        self.subject_filter = email_config.get('subject_filter', 'WEB3GISELAUTOMATE')
        self.save_dir = Path(email_config.get(
            'save_attachments_dir', 'knowledge_base/media/email_attachments'))
        self.max_results = email_config.get('max_results', 50)
        self.service = None
        self.last_sync = None
        self.sync_stats = {
            'messages_found': 0,
            'attachments_processed': 0,
            'errors': []
        }

    def connect(self):
        """
        Establish connection to Gmail via OAuth 2.0.

        Returns:
            Gmail API service object
        """
        if not GMAIL_OAUTH_AVAILABLE:
            raise ImportError(
                "Gmail OAuth libraries not available. "
                "Install with: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )

        creds = None

        # Load existing token if available
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), GMAIL_SCOPES)

        # Refresh or get new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.credentials_path}\n"
                        "Please download your Gmail API credentials from Google Cloud Console.\n"
                        "See documentation at /docs/EMAIL_COLLECTOR_SETUP.md for instructions."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), GMAIL_SCOPES)

                # Try to run local server, fallback to console if needed
                try:
                    print("\nOpening browser for Gmail authentication...")
                    print("If browser doesn't open, you'll see a URL to copy manually.\n")
                    creds = flow.run_local_server(port=0, open_browser=True)
                except Exception as e:
                    print(f"\nCouldn't open browser automatically: {e}")
                    print("\nPlease visit this URL to authenticate:")
                    print("-" * 70)
                    creds = flow.run_console()
                    print("-" * 70)

            # Save credentials for next run
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        return self.service

    def search_messages(self, subject_filter=None, max_results=None):
        """
        Search for emails matching subject filter.

        Args:
            subject_filter: Subject line to filter by (default: WEB3GISELAUTOMATE)
            max_results: Maximum number of messages to return

        Returns:
            List of message dictionaries with id and threadId
        """
        if not self.service:
            self.connect()

        filter_text = subject_filter or self.subject_filter
        limit = max_results or self.max_results

        query = f'subject:{filter_text} has:attachment'
        print(f"Searching Gmail for: {query}")

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()

            messages = results.get('messages', [])
            self.sync_stats['messages_found'] = len(messages)

            print(f"Found {len(messages)} matching message(s)")
            return messages

        except HttpError as error:
            error_msg = f"Gmail API error: {error}"
            print(error_msg)
            self.sync_stats['errors'].append(error_msg)
            return []

    def get_message(self, message_id):
        """
        Get full message details by ID.

        Args:
            message_id: Gmail message ID

        Returns:
            Full message object
        """
        if not self.service:
            self.connect()

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            return message

        except HttpError as error:
            error_msg = f"Failed to get message {message_id}: {error}"
            print(error_msg)
            self.sync_stats['errors'].append(error_msg)
            return None

    def extract_attachments(self, message_id):
        """
        Extract all supported attachments from a message.

        Args:
            message_id: Gmail message ID

        Returns:
            List of attachment dictionaries with metadata and data
        """
        if not self.service:
            self.connect()

        message = self.get_message(message_id)
        if not message:
            return []

        attachments = []
        payload = message.get('payload', {})

        # Get message metadata
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

        def process_parts(parts, parent_message_id):
            """Recursively process message parts to find attachments"""
            extracted = []

            for part in parts:
                filename = part.get('filename', '')
                mime_type = part.get('mimeType', '')
                body = part.get('body', {})

                # Check for nested parts
                if 'parts' in part:
                    extracted.extend(process_parts(part['parts'], parent_message_id))

                # Check if this part is an attachment
                if filename:
                    extension = Path(filename).suffix.lower().lstrip('.')

                    if extension in SUPPORTED_ATTACHMENT_TYPES:
                        attachment_id = body.get('attachmentId')

                        if attachment_id:
                            try:
                                # Download attachment
                                att = self.service.users().messages().attachments().get(
                                    userId='me',
                                    messageId=parent_message_id,
                                    id=attachment_id
                                ).execute()

                                data = base64.urlsafe_b64decode(att['data'])

                                extracted.append({
                                    'filename': filename,
                                    'mime_type': mime_type,
                                    'size': body.get('size', len(data)),
                                    'data': data,
                                    'extension': extension,
                                    'file_type': SUPPORTED_ATTACHMENT_TYPES[extension],
                                    'message_id': parent_message_id,
                                    'subject': subject,
                                    'from': from_email,
                                    'date': date
                                })
                                print(f"  Found attachment: {filename} ({len(data):,} bytes)")

                            except HttpError as error:
                                error_msg = f"Failed to download attachment {filename}: {error}"
                                print(f"  {error_msg}")
                                self.sync_stats['errors'].append(error_msg)
                    else:
                        print(f"  Skipping unsupported file type: {filename}")

            return extracted

        # Process message parts
        parts = payload.get('parts', [])
        if parts:
            attachments = process_parts(parts, message_id)
        elif payload.get('filename'):
            # Single-part message with attachment
            attachments = process_parts([payload], message_id)

        return attachments

    def process_attachment(self, attachment):
        """
        Process an attachment through the appropriate processor.

        Args:
            attachment: Attachment dictionary with data and metadata

        Returns:
            Result dictionary with processed file info
        """
        filename = attachment['filename']
        file_type = attachment['file_type']
        data = attachment['data']
        message_id = attachment['message_id']

        # Generate unique ID
        doc_id = generate_id(filename, message_id)

        # Create save directory
        save_path = self.save_dir / doc_id
        save_path.mkdir(parents=True, exist_ok=True)

        # Save attachment to disk
        local_filepath = save_path / filename
        with open(local_filepath, 'wb') as f:
            f.write(data)

        print(f"  Saved to: {local_filepath}")

        # Process based on file type
        content = ""
        metadata = {}

        try:
            if file_type == 'pdf':
                from processors.attachment_processor import process_pdf
                content, metadata = process_pdf(str(local_filepath))
                print(f"  Extracted {len(content)} characters from PDF")

            elif file_type == 'image':
                from processors.attachment_processor import process_image
                content, metadata = process_image(str(local_filepath))
                print(f"  Processed image: {metadata.get('width', 0)}x{metadata.get('height', 0)}")

            elif file_type == 'text':
                from processors.attachment_processor import process_text_file
                content, metadata = process_text_file(str(local_filepath))
                print(f"  Read {metadata.get('lines', 0)} lines of text")

        except ImportError as e:
            metadata['error'] = f"Processor not available: {e}"
            print(f"  Warning: {metadata['error']}")

        except Exception as e:
            metadata['error'] = f"Processing error: {e}"
            print(f"  Warning: {metadata['error']}")

        # Determine subject category
        subject_category = determine_subject(content, filename)
        tags = extract_tags(content, filename)

        # Create markdown
        markdown = self._create_attachment_markdown(
            attachment=attachment,
            doc_id=doc_id,
            content=content,
            metadata=metadata,
            local_filepath=str(local_filepath),
            subject_category=subject_category,
            tags=tags
        )

        # Save to knowledge base
        saved_path = self._save_attachment_to_kb(
            markdown=markdown,
            raw_data=attachment,
            doc_id=doc_id,
            subject_category=subject_category
        )

        self.sync_stats['attachments_processed'] += 1

        return {
            'id': doc_id,
            'filepath': saved_path,
            'filename': filename,
            'local_path': str(local_filepath),
            'content_length': len(content),
            'file_type': file_type,
            'subject': subject_category
        }

    def _create_attachment_markdown(self, attachment, doc_id, content, metadata,
                                     local_filepath, subject_category, tags):
        """Create markdown with frontmatter for email attachment"""
        now = datetime.now()

        frontmatter = {
            'id': doc_id,
            'source': 'gmail',
            'type': f"email_attachment_{attachment['file_type']}",
            'created_at': now.isoformat(),
            'filename': attachment['filename'],
            'filepath': local_filepath,
            'file_type': attachment['file_type'],
            'file_size': attachment['size'],
            'mime_type': attachment['mime_type'],
            'email_subject': attachment['subject'],
            'email_from': attachment['from'],
            'email_date': attachment['date'],
            'message_id': attachment['message_id'],
            'extraction_metadata': metadata,
            'tags': tags
        }

        title = Path(attachment['filename']).stem.replace('_', ' ').replace('-', ' ').title()

        md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# Email Attachment: {title}

## File Information
- **Filename:** {attachment['filename']}
- **Type:** {attachment['file_type']}
- **Size:** {attachment['size']:,} bytes
- **MIME Type:** {attachment['mime_type']}

## Email Metadata
- **Subject:** {attachment['subject']}
- **From:** {attachment['from']}
- **Date:** {attachment['date']}

## Local Path
`{local_filepath}`

"""

        if metadata:
            md_content += "## Extraction Details\n"
            for key, value in metadata.items():
                if value is not None and value != '':
                    md_content += f"- **{key.replace('_', ' ').title()}:** {value}\n"
            md_content += "\n"

        if content:
            md_content += "## Extracted Content\n\n"
            md_content += content + "\n\n"
        else:
            md_content += "## Extracted Content\n\n"
            md_content += "*No text content could be extracted from this file.*\n\n"
            if metadata.get('error'):
                md_content += f"**Error:** {metadata['error']}\n\n"

        md_content += f"## Related Topics\n- Search for more about: {subject_category}\n"

        return md_content

    def _save_attachment_to_kb(self, markdown, raw_data, doc_id, subject_category):
        """Save email attachment as knowledge base entry"""
        # Save raw data (without binary content)
        raw_dir = Path("knowledge_base/raw/email_attachments")
        raw_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_filename = f"email_{doc_id}_{timestamp}.json"
        raw_filepath = raw_dir / raw_filename

        # Create serializable copy of raw_data (remove binary data)
        serializable_data = {k: v for k, v in raw_data.items() if k != 'data'}
        serializable_data['data_saved_separately'] = True

        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"  Raw metadata saved to: {raw_filepath}")

        # Save processed markdown
        processed_dir = Path(f"knowledge_base/processed/about_{subject_category}")
        processed_dir.mkdir(parents=True, exist_ok=True)

        md_filename = f"email_{doc_id}_{timestamp}.md"
        md_filepath = processed_dir / md_filename

        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"  Markdown saved to: {md_filepath}")

        return str(md_filepath)

    def sync(self, subject_filter=None, max_results=None):
        """
        Main sync function: search -> extract -> process.

        Args:
            subject_filter: Override subject filter for this sync
            max_results: Override max results for this sync

        Returns:
            List of processed attachment results
        """
        print(f"\n{'='*60}")
        print(f"Gmail Email Collection (OAuth) - Subject: {subject_filter or self.subject_filter}")
        print(f"{'='*60}\n")

        # Reset stats
        self.sync_stats = {
            'messages_found': 0,
            'attachments_processed': 0,
            'errors': []
        }

        # Ensure connection
        if not self.service:
            print("Connecting to Gmail via OAuth...")
            self.connect()
            print("Connected successfully\n")

        # Search for messages
        messages = self.search_messages(subject_filter, max_results)

        if not messages:
            print("No matching messages found")
            return []

        processed_attachments = []

        # Process each message
        for msg in messages:
            try:
                message_id = msg['id']
                print(f"\nProcessing message: {message_id}")

                # Extract attachments
                attachments = self.extract_attachments(message_id)

                # Process each attachment
                for attachment in attachments:
                    try:
                        result = self.process_attachment(attachment)
                        if result:
                            processed_attachments.append(result)
                    except Exception as e:
                        error_msg = f"Error processing {attachment.get('filename', 'unknown')}: {e}"
                        print(f"  {error_msg}")
                        self.sync_stats['errors'].append(error_msg)

            except Exception as e:
                error_msg = f"Error processing message {msg['id']}: {e}"
                print(error_msg)
                self.sync_stats['errors'].append(error_msg)
                continue

        # Update last sync time
        self.last_sync = datetime.now().isoformat()

        # Save sync status
        self._save_sync_status()

        print(f"\n{'='*60}")
        print(f"Gmail Collection Complete")
        print(f"Messages Found: {self.sync_stats['messages_found']}")
        print(f"Attachments Processed: {self.sync_stats['attachments_processed']}")
        if self.sync_stats['errors']:
            print(f"Errors: {len(self.sync_stats['errors'])}")
        print(f"{'='*60}\n")

        return processed_attachments

    def _save_sync_status(self):
        """Save sync status to config file"""
        status_file = Path("config/email_sync_status.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)

        status = {
            'last_sync': self.last_sync,
            'subject_filter': self.subject_filter,
            'stats': self.sync_stats
        }

        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

    def get_status(self):
        """
        Get current sync status.

        Returns:
            Dictionary with sync status info
        """
        status_file = Path("config/email_sync_status.json")

        if status_file.exists():
            with open(status_file, 'r') as f:
                return json.load(f)

        return {
            'last_sync': None,
            'subject_filter': self.subject_filter,
            'stats': {
                'messages_found': 0,
                'attachments_processed': 0,
                'errors': []
            }
        }

    def test_connection(self):
        """
        Test Gmail OAuth connection and return status.

        Returns:
            Dictionary with connection test results
        """
        try:
            service = self.connect()

            # Get user profile to verify connection
            profile = service.users().getProfile(userId='me').execute()

            return {
                'success': True,
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal')
            }

        except FileNotFoundError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'credentials_not_found'
            }

        except HttpError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'api_error'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'unknown'
            }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Collect emails from Gmail inbox")
    parser.add_argument('--test', action='store_true', help='Test connection only')
    parser.add_argument('--oauth', action='store_true', help='Use OAuth authentication (recommended)')
    parser.add_argument('--subject', type=str, default=None, help='Subject filter override')
    parser.add_argument('--max-results', type=int, default=None, help='Maximum messages to process')
    parser.add_argument('--credentials', type=str, default=None, help='Path to Gmail OAuth credentials')

    args = parser.parse_args()

    # Use OAuth collector if specified or if app password not available
    if args.oauth or (not GMAIL_EMAIL or not GMAIL_APP_PASSWORD):
        if not GMAIL_OAUTH_AVAILABLE:
            print("Gmail OAuth libraries not available.")
            print("Install with: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return

        collector = EmailCollector(credentials_path=args.credentials)

        if args.test:
            print("Testing Gmail OAuth connection...")
            result = collector.test_connection()

            if result['success']:
                print(f"\nConnection successful!")
                print(f"  Email: {result['email']}")
                print(f"  Total Messages: {result['messages_total']:,}")
                print(f"  Total Threads: {result['threads_total']:,}")
            else:
                print(f"\nConnection failed!")
                print(f"  Error Type: {result['error_type']}")
                print(f"  Error: {result['error']}")
            return

        # Run OAuth sync
        results = collector.sync(
            subject_filter=args.subject,
            max_results=args.max_results
        )

        if results:
            print("\nProcessed attachments:")
            for result in results:
                print(f"  - {result['filename']}: {result['content_length']} chars (ID: {result['id']})")
    else:
        # Legacy IMAP mode
        if args.test:
            try:
                imap = connect_to_gmail()
                print("Connection successful!")
                imap.logout()
            except Exception as e:
                print(f"Connection failed: {e}")
            return

        # Collect emails via IMAP
        emails = collect_emails()

        if emails:
            print("\nCollected emails:")
            for email_info in emails:
                print(f"  - {email_info['subject']} (ID: {email_info['id']})")


if __name__ == "__main__":
    main()

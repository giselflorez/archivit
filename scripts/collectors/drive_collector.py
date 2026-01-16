#!/usr/bin/env python3
"""
Google Drive Collector - Automatically collect files from Google Drive folder
"""
import os
import io
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import yaml

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/drive']

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def generate_id(filename, modified_time):
    """Generate a unique ID based on file metadata"""
    content = f"{filename}_{modified_time}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def determine_subject(filename, content_preview=""):
    """Determine the subject category based on filename and content"""
    combined_text = f"{filename} {content_preview}".lower()

    if "founder" in combined_text:
        return "founder"
    elif "founder" in combined_text:
        return "founder"
    elif "founder" in combined_text:
        return "founder"
    else:
        return "file_general"

def extract_tags(filename, content_preview=""):
    """Extract relevant tags from filename and content"""
    tags = ["google_drive", "automated"]

    combined_text = f"{filename} {content_preview}".lower()

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

def get_drive_service():
    """Authenticate and return Google Drive service"""
    config = load_config()
    creds = None

    token_file = Path(config['google_drive']['token_file'])
    credentials_file = Path(config['google_drive']['credentials_file'])

    # The token file stores the user's access and refresh tokens
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_file.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {credentials_file}\n"
                    "Please download your Google Drive API credentials and save them to this location.\n"
                    "See documentation for setup instructions."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES)

            # Try to run local server, fallback to console if needed
            try:
                print("\nOpening browser for authentication...")
                print("If browser doesn't open, you'll see a URL to copy manually.\n")
                creds = flow.run_local_server(port=0, open_browser=True)
            except Exception as e:
                print(f"\nCouldn't open browser automatically: {e}")
                print("\nPlease visit this URL to authenticate:")
                print("-" * 70)
                creds = flow.run_console()
                print("-" * 70)

        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def find_folder(service, folder_name):
    """Find folder by name in Google Drive"""
    try:
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        folders = results.get('files', [])
        if not folders:
            return None

        return folders[0]['id']

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def create_folder(service, folder_name, parent_id=None):
    """Create a new folder in Google Drive"""
    try:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()

        return folder.get('id')

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def list_subdirectories(service, folder_id, visited=None):
    """Recursively list all subdirectories in a folder"""
    if visited is None:
        visited = set()

    if folder_id in visited:
        return []

    visited.add(folder_id)
    subdirs = [folder_id]  # Include the root folder itself

    try:
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=100
        ).execute()

        folders = results.get('files', [])

        for folder in folders:
            print(f"  Found subdirectory: {folder['name']}")
            # Recursively get subdirectories
            subdirs.extend(list_subdirectories(service, folder['id'], visited))

        return subdirs

    except HttpError as error:
        print(f"An error occurred listing subdirectories: {error}")
        return subdirs

def list_files_in_folder(service, folder_id, supported_types, recursive=True):
    """List all supported files in a folder (optionally recursive)"""
    all_files = []

    try:
        # Get all folders to search (including subdirectories if recursive)
        if recursive:
            print(f"\nScanning folder and all subdirectories recursively...")
            folder_ids = list_subdirectories(service, folder_id)
            print(f"Found {len(folder_ids)} folder(s) to scan (including root)\n")
        else:
            folder_ids = [folder_id]

        # Build MIME type query
        mime_queries = []
        for file_type in supported_types:
            if file_type == 'pdf':
                mime_queries.append("mimeType='application/pdf'")
            elif file_type in ['jpg', 'jpeg']:
                mime_queries.append("mimeType='image/jpeg'")
            elif file_type == 'png':
                mime_queries.append("mimeType='image/png'")
            elif file_type == 'txt':
                mime_queries.append("mimeType='text/plain'")
            elif file_type == 'md':
                mime_queries.append("mimeType='text/markdown'")
            elif file_type == 'doc':
                mime_queries.append("mimeType='application/msword'")
            elif file_type == 'docx':
                mime_queries.append("mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'")

        mime_query = " or ".join(mime_queries)

        # Search each folder
        for fid in folder_ids:
            query = f"'{fid}' in parents and ({mime_query}) and trashed=false"

            results = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, modifiedTime, size)',
                orderBy='modifiedTime desc',
                pageSize=100
            ).execute()

            files = results.get('files', [])
            if files:
                print(f"  Found {len(files)} file(s) in folder")
                all_files.extend(files)

        return all_files

    except HttpError as error:
        print(f"An error occurred: {error}")
        return all_files

def download_file(service, file_id, destination_path):
    """Download a file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        # Write to file
        with open(destination_path, 'wb') as f:
            f.write(file_content.getvalue())

        return True

    except HttpError as error:
        print(f"An error occurred downloading file: {error}")
        return False

def move_file(service, file_id, new_parent_id, old_parent_id):
    """Move a file to a different folder"""
    try:
        service.files().update(
            fileId=file_id,
            addParents=new_parent_id,
            removeParents=old_parent_id,
            fields='id, parents'
        ).execute()
        return True

    except HttpError as error:
        print(f"An error occurred moving file: {error}")
        return False

def create_markdown(file_data, doc_id, subject_category, file_path):
    """Convert file metadata to markdown with frontmatter"""
    now = datetime.now()
    tags = extract_tags(file_data['name'])

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'google_drive',
        'type': 'drive_file',
        'created_at': now.isoformat(),
        'filename': file_data['name'],
        'mime_type': file_data['mimeType'],
        'modified_time': file_data['modifiedTime'],
        'file_size': file_data.get('size', 0),
        'tags': tags
    }

    # Create markdown body
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# File: {file_data['name']}

## File Information
- **Type:** {file_data['mimeType']}
- **Size:** {int(file_data.get('size', 0)):,} bytes
- **Modified:** {file_data['modifiedTime']}
- **Source:** Google Drive

## Local Path
`{file_path}`

## Content
This file will be processed separately by the attachment processor.

## Related Topics
- Search for more about: {subject_category}
"""

    return md_content

def save_file(markdown_content, raw_data, subject_category, doc_id):
    """Save file metadata as knowledge base entry"""
    # Save raw file data
    raw_dir = Path("knowledge_base/raw/drive_files")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"drive_{doc_id}_{timestamp}.json"
    raw_filepath = raw_dir / raw_filename

    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"  Raw metadata saved to: {raw_filepath}")

    # Save processed markdown
    processed_dir = Path(f"knowledge_base/processed/about_{subject_category}")
    processed_dir.mkdir(parents=True, exist_ok=True)

    md_filename = f"drive_{doc_id}_{timestamp}.md"
    md_filepath = processed_dir / md_filename

    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  Markdown saved to: {md_filepath}")

    return str(md_filepath)

def collect_files():
    """Main file collection function"""
    config = load_config()

    if not config['google_drive']['enabled']:
        print("Google Drive collection is disabled in config")
        return []

    folder_name = config['google_drive']['watch_folder_name']
    folder_id_config = config['google_drive'].get('watch_folder_id')
    processed_folder_name = config['google_drive']['processed_folder_name']
    move_processed = config['google_drive']['move_processed_files']
    supported_types = config['google_drive']['supported_file_types']
    save_dir = Path(config['google_drive']['save_files_dir'])

    print(f"\n{'='*60}")
    print(f"Google Drive Collection - Folder: {folder_name}")
    if folder_id_config:
        print(f"Folder ID: {folder_id_config}")
    print(f"{'='*60}\n")

    # Get Drive service
    print("Authenticating with Google Drive...")
    service = get_drive_service()
    print("✓ Connected to Google Drive\n")

    # Use configured folder ID if available, otherwise search by name
    if folder_id_config:
        print(f"Using configured folder ID: {folder_id_config}")
        folder_id = folder_id_config
    else:
        # Find watch folder by name
        print(f"Looking for folder: {folder_name}")
        folder_id = find_folder(service, folder_name)

        if not folder_id:
            print(f"Folder '{folder_name}' not found. Creating it...")
            folder_id = create_folder(service, folder_name)
            if folder_id:
                print(f"✓ Created folder: {folder_name}")
                print(f"  Please upload files to this folder and run again.")
                return []
            else:
                print("Failed to create folder")
                return []

    print(f"✓ Found folder: {folder_name}\n")

    # Get processed folder (create if needed and if we're moving files)
    processed_folder_id = None
    if move_processed:
        processed_folder_id = find_folder(service, processed_folder_name)
        if not processed_folder_id:
            print(f"Creating '{processed_folder_name}' folder...")
            processed_folder_id = create_folder(service, processed_folder_name, folder_id)
            if processed_folder_id:
                print(f"✓ Created '{processed_folder_name}' subfolder\n")

    # List files in folder
    files = list_files_in_folder(service, folder_id, supported_types)

    if not files:
        print("No new files to process")
        return []

    print(f"Found {len(files)} file(s) to process\n")

    processed_files = []

    # Process each file
    for file_data in files:
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {file_data['name']}")
            print(f"{'='*60}\n")

            # Generate doc ID
            doc_id = generate_id(file_data['name'], file_data['modifiedTime'])

            # Determine subject category
            subject_category = determine_subject(file_data['name'])

            print(f"Filename: {file_data['name']}")
            print(f"Type: {file_data['mimeType']}")
            print(f"Size: {int(file_data.get('size', 0)):,} bytes")
            print(f"Modified: {file_data['modifiedTime']}")
            print(f"Category: {subject_category}")
            print(f"Doc ID: {doc_id}")

            # Create save directory
            save_dir.mkdir(parents=True, exist_ok=True)
            file_save_dir = save_dir / doc_id
            file_save_dir.mkdir(exist_ok=True)

            # Download file
            print(f"\nDownloading file...")
            local_filepath = file_save_dir / file_data['name']
            if download_file(service, file_data['id'], local_filepath):
                print(f"✓ Downloaded to: {local_filepath}")
            else:
                print(f"✗ Failed to download file")
                continue

            # Create markdown
            markdown = create_markdown(file_data, doc_id, subject_category, str(local_filepath))

            # Save file metadata
            filepath = save_file(markdown, file_data, subject_category, doc_id)

            # Move to processed folder
            if move_processed and processed_folder_id:
                print(f"\nMoving file to '{processed_folder_name}' folder...")
                if move_file(service, file_data['id'], processed_folder_id, folder_id):
                    print(f"✓ Moved to processed folder")
                else:
                    print(f"✗ Failed to move file")

            processed_files.append({
                'id': doc_id,
                'filepath': filepath,
                'filename': file_data['name'],
                'local_path': str(local_filepath)
            })

            print(f"\n✓ Successfully processed file")

        except Exception as e:
            print(f"Error processing file {file_data['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*60}")
    print(f"Google Drive Collection Complete")
    print(f"Processed: {len(processed_files)} file(s)")
    print(f"{'='*60}\n")

    return processed_files

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Collect files from Google Drive folder")
    parser.add_argument('--test', action='store_true', help='Test connection only')

    args = parser.parse_args()

    if args.test:
        # Test connection
        try:
            service = get_drive_service()
            print("✓ Connection successful!")

            # List folders
            results = service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()

            folders = results.get('files', [])
            if folders:
                print("\nYour Google Drive folders:")
                for folder in folders:
                    print(f"  - {folder['name']}")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
        return

    # Collect files
    files = collect_files()

    if files:
        print("\nCollected files:")
        for file_info in files:
            print(f"  - {file_info['filename']} (ID: {file_info['id']})")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Attachment Processor - Extract content from files (PDFs, images, text)
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
import yaml

# PDF processing
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def generate_id(filename, parent_id):
    """Generate a unique ID for attachment"""
    content = f"{filename}_{parent_id}_{datetime.now().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def determine_file_type(filepath):
    """Determine file type from extension"""
    extension = Path(filepath).suffix.lower().lstrip('.')

    type_mapping = {
        'pdf': 'pdf',
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image',
        'gif': 'image',
        'txt': 'text',
        'md': 'text',
        'doc': 'document',
        'docx': 'document'
    }

    return type_mapping.get(extension, 'unknown')

def process_pdf(filepath):
    """Extract text from PDF file"""
    text_content = ""
    metadata = {
        'pages': 0,
        'method': None,
        'error': None
    }

    # Try pdfplumber first (better formatting)
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(filepath) as pdf:
                metadata['pages'] = len(pdf.pages)
                metadata['method'] = 'pdfplumber'

                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n\n"

                # Extract metadata if available
                if pdf.metadata:
                    metadata['pdf_metadata'] = {
                        k: str(v) for k, v in pdf.metadata.items() if v is not None
                    }

                return text_content.strip(), metadata
        except Exception as e:
            metadata['error'] = f"pdfplumber error: {str(e)}"

    # Fallback to PyPDF2
    if PYPDF2_AVAILABLE:
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata['pages'] = len(pdf_reader.pages)
                metadata['method'] = 'PyPDF2'

                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n\n"

                # Extract metadata
                if pdf_reader.metadata:
                    metadata['pdf_metadata'] = {
                        k.lstrip('/'): str(v) for k, v in pdf_reader.metadata.items() if v is not None
                    }

                return text_content.strip(), metadata
        except Exception as e:
            metadata['error'] = f"PyPDF2 error: {str(e)}"

    # If both failed
    if not text_content:
        metadata['error'] = "No PDF libraries available or extraction failed"

    return text_content.strip(), metadata

def process_image(filepath):
    """Extract text from image using OCR"""
    text_content = ""
    metadata = {
        'width': 0,
        'height': 0,
        'format': None,
        'ocr_available': OCR_AVAILABLE,
        'error': None
    }

    if not PIL_AVAILABLE:
        metadata['error'] = "PIL not available"
        return text_content, metadata

    try:
        # Open image and get basic info
        with Image.open(filepath) as img:
            metadata['width'] = img.width
            metadata['height'] = img.height
            metadata['format'] = img.format

            # Try OCR if available
            if OCR_AVAILABLE:
                try:
                    text_content = pytesseract.image_to_string(img)
                    metadata['method'] = 'pytesseract'
                except Exception as e:
                    metadata['error'] = f"OCR error: {str(e)}"
            else:
                metadata['error'] = "OCR not available (pytesseract not installed)"

    except Exception as e:
        metadata['error'] = f"Image processing error: {str(e)}"

    return text_content.strip(), metadata

def process_text_file(filepath):
    """Read plain text file"""
    text_content = ""
    metadata = {
        'encoding': 'utf-8',
        'lines': 0,
        'error': None
    }

    try:
        # Try UTF-8 first
        with open(filepath, 'r', encoding='utf-8') as f:
            text_content = f.read()
            metadata['lines'] = len(text_content.split('\n'))
    except UnicodeDecodeError:
        # Fallback to latin-1
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                text_content = f.read()
                metadata['encoding'] = 'latin-1'
                metadata['lines'] = len(text_content.split('\n'))
        except Exception as e:
            metadata['error'] = f"Encoding error: {str(e)}"
    except Exception as e:
        metadata['error'] = f"Read error: {str(e)}"

    return text_content.strip(), metadata

def extract_tags(content, filename):
    """Extract relevant tags from content"""
    tags = ["attachment", "processed"]

    combined_text = f"{filename} {content}".lower()

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

    return list(set(tags))

def determine_subject(content, filename):
    """Determine subject category from content"""
    combined_text = f"{filename} {content}".lower()

    if "founder" in combined_text:
        return "founder"
    elif "founder" in combined_text:
        return "founder"
    elif "founder" in combined_text:
        return "founder"
    else:
        return "file_general"

def create_markdown(filepath, content, metadata, parent_id, subject_category):
    """Create markdown with frontmatter for processed attachment"""
    now = datetime.now()
    filename = Path(filepath).name
    file_type = determine_file_type(filepath)
    doc_id = generate_id(filename, parent_id)

    tags = extract_tags(content, filename)

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'attachment',
        'type': f'attachment_{file_type}',
        'created_at': now.isoformat(),
        'parent_id': parent_id,
        'filename': filename,
        'filepath': str(filepath),
        'file_type': file_type,
        'file_size': Path(filepath).stat().st_size if Path(filepath).exists() else 0,
        'extraction_metadata': metadata,
        'tags': tags
    }

    # Create title from filename
    title = Path(filename).stem.replace('_', ' ').replace('-', ' ').title()

    # Create markdown body
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# Attachment: {title}

## File Information
- **Filename:** {filename}
- **Type:** {file_type}
- **Size:** {frontmatter['file_size']:,} bytes
- **Parent Document:** {parent_id}

"""

    # Add extraction metadata
    if metadata:
        md_content += "## Extraction Details\n"
        for key, value in metadata.items():
            if value is not None and value != '':
                md_content += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        md_content += "\n"

    # Add content
    if content:
        md_content += "## Extracted Content\n\n"
        md_content += content + "\n\n"
    else:
        md_content += "## Extracted Content\n\n"
        md_content += "*No text content could be extracted from this file.*\n\n"
        if metadata.get('error'):
            md_content += f"**Error:** {metadata['error']}\n\n"

    md_content += f"## Related Topics\n- Search for more about: {subject_category}\n"

    return md_content, doc_id

def save_attachment(markdown_content, raw_data, subject_category, doc_id):
    """Save attachment as knowledge base entry"""
    # Save raw attachment data
    raw_dir = Path("knowledge_base/raw/attachments")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"attachment_{doc_id}_{timestamp}.json"
    raw_filepath = raw_dir / raw_filename

    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)

    # Save processed markdown
    processed_dir = Path(f"knowledge_base/processed/about_{subject_category}")
    processed_dir.mkdir(parents=True, exist_ok=True)

    md_filename = f"attachment_{doc_id}_{timestamp}.md"
    md_filepath = processed_dir / md_filename

    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return str(md_filepath)

def process_file(filepath, parent_id="unknown"):
    """Main function to process a file and extract content"""
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return None

    print(f"\nProcessing file: {filepath.name}")

    file_type = determine_file_type(filepath)
    print(f"File type: {file_type}")

    # Process based on type
    content = ""
    metadata = {}

    if file_type == 'pdf':
        print("Extracting PDF content...")
        content, metadata = process_pdf(filepath)
    elif file_type == 'image':
        print("Processing image...")
        content, metadata = process_image(filepath)
    elif file_type == 'text':
        print("Reading text file...")
        content, metadata = process_text_file(filepath)
    else:
        print(f"Unsupported file type: {file_type}")
        metadata = {'error': 'Unsupported file type'}

    # Determine subject
    subject_category = determine_subject(content, filepath.name)

    # Create markdown
    markdown, doc_id = create_markdown(
        filepath,
        content,
        metadata,
        parent_id,
        subject_category
    )

    # Prepare raw data
    raw_data = {
        'filename': filepath.name,
        'filepath': str(filepath),
        'file_type': file_type,
        'file_size': filepath.stat().st_size,
        'parent_id': parent_id,
        'content_preview': content[:500] if content else None,
        'metadata': metadata
    }

    # Save
    saved_path = save_attachment(markdown, raw_data, subject_category, doc_id)

    print(f"✓ Saved to: {saved_path}")
    print(f"✓ Extracted {len(content)} characters")

    return {
        'id': doc_id,
        'filepath': saved_path,
        'filename': filepath.name,
        'content_length': len(content),
        'subject': subject_category
    }

def process_multiple_files(file_list, parent_id="batch"):
    """Process multiple files at once"""
    results = []

    print(f"\n{'='*60}")
    print(f"Processing {len(file_list)} file(s)")
    print(f"{'='*60}")

    for filepath in file_list:
        try:
            result = process_file(filepath, parent_id)
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"Processed {len(results)}/{len(file_list)} file(s)")
    print(f"{'='*60}\n")

    return results

def main():
    """Main function for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Process attachments and extract content")
    parser.add_argument('files', nargs='+', help='Files to process')
    parser.add_argument('--parent-id', default='manual', help='Parent document ID')

    args = parser.parse_args()

    results = process_multiple_files(args.files, args.parent_id)

    if results:
        print("\nProcessed files:")
        for result in results:
            print(f"  - {result['filename']}: {result['content_length']} chars (ID: {result['id']})")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Text Processor - Clean and normalize markdown content
"""
import re
import yaml
from pathlib import Path
from bs4 import BeautifulSoup

def clean_html(text):
    """Remove HTML tags and clean text"""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def normalize_whitespace(text):
    """Normalize whitespace in text"""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with max 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing whitespace from lines
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    return text.strip()

def extract_frontmatter(content):
    """
    Extract YAML frontmatter from markdown content

    Returns:
        tuple: (frontmatter_dict, body_content)
    """
    if not content.startswith('---'):
        return {}, content

    # Split by frontmatter delimiters
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return frontmatter, body
    except yaml.YAMLError as e:
        print(f"Error parsing YAML frontmatter: {e}")
        return {}, content

def validate_frontmatter(frontmatter):
    """
    Validate and normalize frontmatter fields

    Args:
        frontmatter: Dictionary of frontmatter fields

    Returns:
        dict: Validated frontmatter
    """
    required_fields = ['id', 'source', 'type', 'created_at']

    for field in required_fields:
        if field not in frontmatter:
            print(f"Warning: Missing required field '{field}' in frontmatter")

    # Ensure tags is a list
    if 'tags' in frontmatter and not isinstance(frontmatter['tags'], list):
        frontmatter['tags'] = [frontmatter['tags']]

    # Ensure urls is a list
    if 'urls' in frontmatter and not isinstance(frontmatter['urls'], list):
        frontmatter['urls'] = [frontmatter['urls']]

    return frontmatter

def clean_markdown_content(content):
    """Clean and normalize markdown content"""
    # Clean HTML
    content = clean_html(content)

    # Normalize whitespace
    content = normalize_whitespace(content)

    # Fix markdown headers (ensure space after #)
    content = re.sub(r'^(#{1,6})([^ #])', r'\1 \2', content, flags=re.MULTILINE)

    # Fix markdown lists (ensure space after bullet)
    content = re.sub(r'^([-*+])([^ ])', r'\1 \2', content, flags=re.MULTILINE)

    return content

def process_markdown_file(filepath):
    """
    Process a single markdown file

    Args:
        filepath: Path to markdown file

    Returns:
        str: Processed markdown content
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter and body
    frontmatter, body = extract_frontmatter(content)

    # Validate frontmatter
    frontmatter = validate_frontmatter(frontmatter)

    # Clean body content
    body = clean_markdown_content(body)

    # Reconstruct document
    processed = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

{body}
"""
    return processed

def process_text_to_markdown(text, metadata=None):
    """
    Convert plain text to markdown with frontmatter

    Args:
        text: Plain text content
        metadata: Optional metadata dictionary

    Returns:
        str: Markdown formatted text
    """
    # Clean text
    clean_text = clean_markdown_content(text)

    # Create default metadata if not provided
    if metadata is None:
        metadata = {}

    # Create frontmatter
    frontmatter_yaml = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)

    # Create markdown document
    markdown = f"""---
{frontmatter_yaml}---

{clean_text}
"""
    return markdown

def main():
    """Main function for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Process and clean markdown files")
    parser.add_argument('input', type=str, help='Input markdown file')
    parser.add_argument('--output', '-o', type=str, help='Output file (optional)')
    args = parser.parse_args()

    # Process file
    processed = process_markdown_file(args.input)

    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(processed)
        print(f"Processed file saved to: {args.output}")
    else:
        print(processed)

if __name__ == "__main__":
    main()

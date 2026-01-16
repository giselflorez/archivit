#!/usr/bin/env python3
"""
Perplexity Collector - Search Perplexity API for information about gisel/founder/founder
"""
import os
import json
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
import yaml
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def generate_id(query):
    """Generate a unique ID based on query and timestamp"""
    timestamp = datetime.now().isoformat()
    content = f"{query}_{timestamp}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def determine_subject(query):
    """Determine the subject based on the query"""
    query_lower = query.lower()
    if "founder" in query_lower:
        return "founder"
    elif "founder" in query_lower:
        return "founder"
    elif "founder" in query_lower:
        return "founder"
    else:
        return "general"

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def query_perplexity(query, api_key):
    """
    Query the Perplexity API

    Args:
        query: Search query string
        api_key: Perplexity API key

    Returns:
        dict: API response
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "temperature": 0.2,
        "stream": False
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Perplexity API: {e}")
        return None

def extract_content(api_response):
    """Extract content and citations from API response"""
    if not api_response or 'choices' not in api_response:
        return None, None

    message = api_response['choices'][0]['message']
    content = message.get('content', '')
    citations = api_response.get('citations', [])

    return content, citations

def create_markdown(query, content, citations, doc_id, subject):
    """
    Create markdown document with YAML frontmatter

    Args:
        query: Original search query
        content: Main content from Perplexity
        citations: List of source URLs
        doc_id: Unique document ID
        subject: Subject category

    Returns:
        str: Formatted markdown document
    """
    now = datetime.now()

    # Clean content
    clean_content = clean_html(content)

    # Extract key points (first 3 sentences or paragraphs)
    paragraphs = [p.strip() for p in clean_content.split('\n') if p.strip()]
    key_points = paragraphs[:3] if len(paragraphs) >= 3 else paragraphs

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'perplexity',
        'type': 'query_result',
        'created_at': now.isoformat(),
        'query': query,
        'subject': subject,
        'tags': extract_tags(query, subject),
        'urls': citations[:5] if citations else []  # Top 5 citations
    }

    # Create markdown body
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# {query.title()}

## Summary
Query: "{query}"
Found {len(citations) if citations else 0} sources

## Content
{clean_content}

## Key Points
{chr(10).join(f'- {point}' for point in key_points)}

## Sources
{chr(10).join(f'- [{i+1}]({url})' for i, url in enumerate(citations[:10])) if citations else '- No sources available'}

## Related Topics
- Search for more about: {subject}
"""

    return md_content

def extract_tags(query, subject):
    """Extract relevant tags from query and subject"""
    tags = [subject]

    query_lower = query.lower()
    tag_keywords = {
        'art': ['art', 'artwork', 'creative', 'artist'],
        'blockchain': ['blockchain', 'crypto', 'nft', 'web3'],
        'digital_identity': ['identity', 'digital', 'online', 'persona'],
        'philosophy': ['philosophy', 'thought', 'concept', 'idea'],
        'technology': ['tech', 'technology', 'digital', 'innovation']
    }

    for tag, keywords in tag_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            tags.append(tag)

    return list(set(tags))  # Remove duplicates

def save_raw_response(query, response, subject):
    """Save raw API response as JSON"""
    base_path = Path("knowledge_base/raw")
    base_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{subject}_{timestamp}.json"
    filepath = base_path / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)

    print(f"Raw response saved to: {filepath}")
    return filepath

def save_markdown(markdown_content, subject, doc_id):
    """Save processed markdown file"""
    base_path = Path(f"knowledge_base/processed/about_{subject}")
    base_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{doc_id}_{timestamp}.md"
    filepath = base_path / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Markdown saved to: {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser(description="Collect information from Perplexity API")
    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--queries', '-qs', nargs='+', help='Multiple search queries')

    args = parser.parse_args()

    if not PERPLEXITY_API_KEY:
        print("Error: PERPLEXITY_API_KEY not found in .env file")
        return 1

    # Collect queries
    queries = []
    if args.query:
        queries.append(args.query)
    if args.queries:
        queries.extend(args.queries)

    if not queries:
        print("No queries provided. Use --query or --queries")
        return 1

    # Process each query
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Processing query: {query}")
        print(f"{'='*60}\n")

        # Query Perplexity
        response = query_perplexity(query, PERPLEXITY_API_KEY)
        if not response:
            print(f"Failed to get response for query: {query}")
            continue

        # Extract content
        content, citations = extract_content(response)
        if not content:
            print(f"No content found for query: {query}")
            continue

        # Generate IDs and determine subject
        doc_id = generate_id(query)
        subject = determine_subject(query)

        # Save raw response
        save_raw_response(query, response, subject)

        # Create and save markdown
        markdown = create_markdown(query, content, citations, doc_id, subject)
        save_markdown(markdown, subject, doc_id)

        print(f"✓ Successfully processed query: {query}")
        print(f"  Subject: {subject}")
        print(f"  Document ID: {doc_id}")
        print(f"  Citations: {len(citations) if citations else 0}")

    print(f"\n{'='*60}")
    print(f"Completed processing {len(queries)} queries")
    print(f"{'='*60}\n")

    return 0

if __name__ == "__main__":
    exit(main())

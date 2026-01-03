#!/usr/bin/env python3
"""
Visual Translator - OCR and AI Vision Analysis for Images

Extracts text from images using Tesseract OCR and generates detailed
descriptions using Claude's vision capabilities.
"""
import os
import sys
import base64
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Image processing
from PIL import Image
import pytesseract

# Claude API
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not available. Vision analysis will be disabled.")

# Load environment variables
load_dotenv()

# Cache directory for analysis results
CACHE_DIR = Path("db/visual_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_image_hash(image_path: Path) -> str:
    """Generate hash of image file for caching"""
    with open(image_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def load_cached_analysis(image_path: Path) -> Optional[Dict]:
    """Load cached analysis if available and not expired"""
    try:
        img_hash = get_image_hash(image_path)
        cache_file = CACHE_DIR / f"{img_hash}.json"

        if not cache_file.exists():
            return None

        with open(cache_file, 'r') as f:
            cached = json.load(f)

        # Check cache age (90 days default)
        cache_date = datetime.fromisoformat(cached.get('cached_at', ''))
        age_days = (datetime.now() - cache_date).days

        if age_days > 90:
            return None

        return cached.get('analysis')
    except Exception as e:
        print(f"Warning: Could not load cache: {e}")
        return None


def save_to_cache(image_path: Path, analysis: Dict):
    """Save analysis results to cache"""
    try:
        img_hash = get_image_hash(image_path)
        cache_file = CACHE_DIR / f"{img_hash}.json"

        cache_data = {
            'image_path': str(image_path),
            'cached_at': datetime.now().isoformat(),
            'analysis': analysis
        }

        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save to cache: {e}")


def extract_text_from_image(
    image_path: Path,
    lang: str = 'eng',
    preprocess: bool = True
) -> Dict:
    """
    Extract text from image using Tesseract OCR

    Args:
        image_path: Path to image file
        lang: Language code for OCR (eng, spa, fra, etc.)
        preprocess: Apply image preprocessing for better OCR

    Returns:
        dict with:
            - text: Extracted text
            - confidence: OCR confidence score (0-100)
            - language: Detected language
            - error: Error message if failed
    """
    result = {
        'text': '',
        'confidence': 0,
        'language': lang,
        'error': None
    }

    try:
        # Open image
        img = Image.open(image_path)

        # Preprocessing for better OCR
        if preprocess:
            # Convert to RGB if needed
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Convert to grayscale
            img = img.convert('L')

            # Enhance contrast (optional, can improve OCR)
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)

        # Extract text with detailed data
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

        # Get full text
        text = pytesseract.image_to_string(img, lang=lang)
        result['text'] = text.strip()

        # Calculate average confidence
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        if confidences:
            result['confidence'] = sum(confidences) / len(confidences)

        # Mark as successful if we got any text
        if result['text']:
            result['has_text'] = True
        else:
            result['has_text'] = False
            result['error'] = "No text detected in image"

    except Exception as e:
        result['error'] = str(e)
        result['has_text'] = False
        print(f"OCR Error for {image_path}: {e}")

    return result


def encode_image_base64(image_path: Path, max_size: int = 2048) -> str:
    """
    Encode image to base64 for API transmission

    Args:
        image_path: Path to image
        max_size: Maximum dimension (width or height) in pixels

    Returns:
        Base64 encoded image string
    """
    img = Image.open(image_path)

    # Resize if too large
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Convert to RGB if needed
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')

    # Save to bytes
    from io import BytesIO
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_bytes = buffer.getvalue()

    # Encode to base64
    return base64.b64encode(img_bytes).decode('utf-8')


def describe_image_with_claude(
    image_path: Path,
    api_key: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 1000
) -> Dict:
    """
    Generate detailed image description using Claude's vision API

    Args:
        image_path: Path to image file
        api_key: Anthropic API key (optional, uses env var if not provided)
        model: Claude model to use
        max_tokens: Maximum tokens in response

    Returns:
        dict with:
            - description: Detailed narrative description
            - tags: List of detected visual elements
            - scene_type: Type of scene (photo, sketch, diagram, etc.)
            - detected_objects: List of main objects
            - has_text_visual: Whether text is visible in image (from vision)
            - error: Error message if failed
    """
    result = {
        'description': '',
        'tags': [],
        'scene_type': '',
        'detected_objects': [],
        'has_text_visual': False,
        'error': None
    }

    if not ANTHROPIC_AVAILABLE:
        result['error'] = "Anthropic package not installed"
        return result

    try:
        # Get API key
        if not api_key:
            api_key = os.getenv('ANTHROPIC_API_KEY')

        if not api_key:
            result['error'] = "No API key provided"
            return result

        # Initialize client
        client = Anthropic(api_key=api_key)

        # Encode image
        img_base64 = encode_image_base64(image_path)

        # Get file extension for media type
        ext = image_path.suffix.lower()
        media_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/jpeg')

        # Create prompt for detailed analysis
        prompt = """Analyze this image in detail and provide:

1. A comprehensive description of what you see (2-3 sentences)
2. The type of image (photo, sketch, diagram, screenshot, artwork, etc.)
3. Main objects or elements present (as a list)
4. Relevant tags or keywords (as a list)
5. Whether there is any visible text in the image (yes/no)

Format your response as JSON with these fields:
{
  "description": "detailed description here",
  "scene_type": "photo/sketch/diagram/etc",
  "detected_objects": ["object1", "object2"],
  "tags": ["tag1", "tag2"],
  "has_text": true/false
}

Be specific and detailed, especially for artistic or technical content."""

        # Make API call
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Parse response
        response_text = message.content[0].text

        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)

        if json_match:
            vision_data = json.loads(json_match.group())
            result['description'] = vision_data.get('description', '')
            result['scene_type'] = vision_data.get('scene_type', '')
            result['detected_objects'] = vision_data.get('detected_objects', [])
            result['tags'] = vision_data.get('tags', [])
            result['has_text_visual'] = vision_data.get('has_text', False)
        else:
            # Fallback: use full response as description
            result['description'] = response_text

    except Exception as e:
        result['error'] = str(e)
        print(f"Claude Vision Error for {image_path}: {e}")

    return result


def analyze_image(
    image_path: Path,
    api_key: Optional[str] = None,
    skip_vision: bool = False,
    use_cache: bool = True
) -> Dict:
    """
    Complete image analysis: OCR + Vision AI

    Args:
        image_path: Path to image file
        api_key: Anthropic API key (optional)
        skip_vision: Skip Claude vision analysis (OCR only)
        use_cache: Use cached results if available

    Returns:
        dict with complete analysis results
    """
    # Check cache first
    if use_cache:
        cached = load_cached_analysis(image_path)
        if cached:
            print(f"✓ Using cached analysis for {image_path.name}")
            return cached

    analysis = {
        'image_path': str(image_path),
        'analyzed_at': datetime.now().isoformat(),
        'ocr': None,
        'vision': None,
        'status': 'success'
    }

    print(f"Analyzing: {image_path.name}")

    # Run OCR
    print("  → Running OCR...")
    ocr_result = extract_text_from_image(image_path)
    analysis['ocr'] = ocr_result

    if ocr_result.get('has_text'):
        print(f"  ✓ OCR: Found {len(ocr_result['text'])} characters (confidence: {ocr_result['confidence']:.1f}%)")
    else:
        print("  - No text detected")

    # Run vision analysis
    if not skip_vision:
        print("  → Running Claude vision analysis...")
        vision_result = describe_image_with_claude(image_path, api_key)
        analysis['vision'] = vision_result

        if vision_result.get('description'):
            print(f"  ✓ Vision: {vision_result['description'][:80]}...")
        elif vision_result.get('error'):
            print(f"  ✗ Vision failed: {vision_result['error']}")
            analysis['status'] = 'partial'
    else:
        print("  - Skipping vision analysis")

    # Save to cache
    if use_cache and analysis['status'] == 'success':
        save_to_cache(image_path, analysis)

    return analysis


def batch_analyze_images(
    image_paths: List[Path],
    api_key: Optional[str] = None,
    skip_vision: bool = False,
    rate_limit_delay: float = 1.0
) -> List[Dict]:
    """
    Analyze multiple images with rate limiting

    Args:
        image_paths: List of image paths to analyze
        api_key: Anthropic API key
        skip_vision: Skip vision analysis (OCR only)
        rate_limit_delay: Delay between API calls in seconds

    Returns:
        List of analysis results
    """
    import time

    results = []
    total = len(image_paths)

    print(f"\n{'='*60}")
    print(f"Batch Analyzing {total} Images")
    print(f"{'='*60}\n")

    for i, img_path in enumerate(image_paths, 1):
        print(f"[{i}/{total}] ", end='')

        result = analyze_image(img_path, api_key, skip_vision)
        results.append(result)

        # Rate limiting
        if not skip_vision and i < total:
            time.sleep(rate_limit_delay)

    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    with_text = sum(1 for r in results if r.get('ocr', {}).get('has_text'))

    print(f"\n{'='*60}")
    print(f"Batch Complete: {successful}/{total} successful")
    print(f"Images with text: {with_text}")
    print(f"{'='*60}\n")

    return results


def main():
    """CLI for testing visual translator"""
    import argparse

    parser = argparse.ArgumentParser(description='Visual Translator - Image Analysis')
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('--skip-vision', action='store_true', help='Skip Claude vision analysis (OCR only)')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')

    args = parser.parse_args()

    img_path = Path(args.image)

    if not img_path.exists():
        print(f"Error: Image not found: {img_path}")
        return 1

    # Analyze
    result = analyze_image(
        img_path,
        skip_vision=args.skip_vision,
        use_cache=not args.no_cache
    )

    # Display results
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)

    if result.get('ocr'):
        ocr = result['ocr']
        print(f"\n📝 OCR Results:")
        print(f"   Has Text: {ocr.get('has_text', False)}")
        if ocr.get('text'):
            print(f"   Confidence: {ocr.get('confidence', 0):.1f}%")
            print(f"   Text:\n   {ocr['text'][:200]}")

    if result.get('vision'):
        vision = result['vision']
        print(f"\n👁️  Vision Analysis:")
        print(f"   Description: {vision.get('description', 'N/A')}")
        print(f"   Scene Type: {vision.get('scene_type', 'N/A')}")
        print(f"   Objects: {', '.join(vision.get('detected_objects', []))}")
        print(f"   Tags: {', '.join(vision.get('tags', []))}")

    print("\n" + "="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

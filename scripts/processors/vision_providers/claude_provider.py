#!/usr/bin/env python3
"""
Claude Vision Provider
Vision analysis using Anthropic's Claude API
"""

import os
import base64
import json
import re
import logging
import time
from pathlib import Path
from typing import Dict, Optional, List
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

from .base import (
    VisionProvider,
    VisionProviderNotAvailableError,
    VisionProviderTimeoutError,
    VisionProviderQuotaError
)

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic package not installed")


class ClaudeProvider(VisionProvider):
    """Claude vision analysis provider"""

    def __init__(self, model: str = 'claude-3-5-haiku-20241022', config: Optional[Dict] = None):
        """
        Initialize Claude provider

        Args:
            model: Claude model to use
            config: Provider configuration
        """
        self.model = model or 'claude-3-5-haiku-20241022'
        self.config = config or {}
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        self.client = None

        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

    def is_available(self) -> bool:
        """Check if Claude provider is ready"""
        return ANTHROPIC_AVAILABLE and self.api_key is not None and self.client is not None

    def get_provider_name(self) -> str:
        return 'claude'

    def get_model_name(self) -> str:
        return self.model

    def get_cost_estimate(self, num_images: int) -> float:
        """
        Estimate cost for processing images

        Claude pricing (as of 2026):
        - Haiku: ~$0.003 per image
        - Sonnet: ~$0.015 per image
        - Opus: ~$0.075 per image
        """
        cost_per_image = {
            'claude-3-5-haiku-20241022': 0.003,
            'claude-3-haiku-20240307': 0.003,
            'claude-3-5-sonnet-20241022': 0.015,
            'claude-3-sonnet-20240229': 0.015,
            'claude-3-opus-20240229': 0.075,
        }.get(self.model, 0.003)

        return num_images * cost_per_image

    def warm_up(self):
        """Verify API connection"""
        if not self.is_available():
            raise VisionProviderNotAvailableError(
                "Claude provider not available. Check ANTHROPIC_API_KEY."
            )

    def _encode_image_base64(self, image_path: Path, max_size: int = 2048) -> str:
        """
        Encode image to base64 for API transmission

        Args:
            image_path: Path to image
            max_size: Maximum dimension in pixels

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
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        img_bytes = buffer.getvalue()

        # Encode to base64
        return base64.b64encode(img_bytes).decode('utf-8')

    def analyze_image(self, image_path: Path, prompt: Optional[str] = None) -> Dict:
        """
        Analyze image using Claude Vision API

        Args:
            image_path: Path to image file
            prompt: Optional custom prompt

        Returns:
            Analysis results dict
        """
        if not self.is_available():
            return {
                'description': '',
                'tags': [],
                'scene_type': '',
                'detected_objects': [],
                'has_text': False,
                'confidence': 0.0,
                'provider': 'claude',
                'model': self.model,
                'processing_time': 0.0,
                'error': 'Claude provider not available'
            }

        start_time = time.time()

        try:
            # Encode image
            img_base64 = self._encode_image_base64(image_path)

            # Get file extension for media type
            ext = image_path.suffix.lower()
            media_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(ext, 'image/jpeg')

            # Use custom prompt or default
            if not prompt:
                prompt = """Analyze this image in detail and provide:

1. A comprehensive description of what you see (2-3 sentences)
2. The type of image (photo, sketch, diagram, screenshot, artwork, NFT, etc.)
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
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
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
            json_match = re.search(r'\{[\s\S]*\}', response_text)

            result = {
                'description': '',
                'tags': [],
                'scene_type': '',
                'detected_objects': [],
                'has_text': False,
                'confidence': 0.9,  # Claude typically has high confidence
                'provider': 'claude',
                'model': self.model,
                'processing_time': time.time() - start_time,
                'error': None
            }

            if json_match:
                vision_data = json.loads(json_match.group())
                result['description'] = vision_data.get('description', '')
                result['scene_type'] = vision_data.get('scene_type', '')
                result['detected_objects'] = vision_data.get('detected_objects', [])
                result['tags'] = vision_data.get('tags', [])
                result['has_text'] = vision_data.get('has_text', False)
            else:
                # Fallback: use full response as description
                result['description'] = response_text
                result['confidence'] = 0.7  # Lower confidence for non-JSON response

            logger.info(f"Claude analyzed {image_path.name} in {result['processing_time']:.2f}s")
            return result

        except Exception as e:
            error_msg = str(e)

            # Detect specific error types
            if 'rate_limit' in error_msg.lower() or 'quota' in error_msg.lower():
                raise VisionProviderQuotaError(f"Claude API quota exceeded: {error_msg}")
            elif 'timeout' in error_msg.lower():
                raise VisionProviderTimeoutError(f"Claude API timeout: {error_msg}")

            logger.error(f"Claude vision error for {image_path.name}: {error_msg}")

            return {
                'description': '',
                'tags': [],
                'scene_type': '',
                'detected_objects': [],
                'has_text': False,
                'confidence': 0.0,
                'provider': 'claude',
                'model': self.model,
                'processing_time': time.time() - start_time,
                'error': error_msg
            }

    def batch_analyze(self, image_paths: List[Path], prompt: Optional[str] = None) -> List[Dict]:
        """
        Analyze multiple images with rate limiting

        Args:
            image_paths: List of image paths
            prompt: Optional custom prompt

        Returns:
            List of analysis results
        """
        results = []

        for i, image_path in enumerate(image_paths):
            result = self.analyze_image(image_path, prompt)
            results.append(result)

            # Rate limiting (except for last image)
            if i < len(image_paths) - 1:
                time.sleep(self.rate_limit_delay)

        return results

    def get_capabilities(self) -> Dict:
        """Get Claude provider capabilities"""
        return {
            'supports_ocr': True,
            'supports_objects': True,
            'supports_scenes': True,
            'supports_batch': True,
            'supports_custom_prompts': True,
            'max_image_size_mb': 5,
            'supported_formats': ['jpg', 'jpeg', 'png', 'gif', 'webp']
        }

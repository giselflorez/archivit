#!/usr/bin/env python3
"""
Vision Provider Base Interface
Abstract base class for all vision analysis providers (Claude, local models, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from pathlib import Path


class VisionProvider(ABC):
    """Abstract base class for vision analysis providers"""

    @abstractmethod
    def analyze_image(self, image_path: Path, prompt: Optional[str] = None) -> Dict:
        """
        Analyze image and return structured results

        Args:
            image_path: Path to image file
            prompt: Optional custom prompt for analysis

        Returns:
            Dict with analysis results:
            {
                'description': str,          # Main description
                'tags': List[str],           # Detected tags/labels
                'scene_type': str,           # Scene classification
                'detected_objects': List[str],  # Objects found
                'has_text': bool,            # Text detected
                'text_content': str,         # OCR text (if available)
                'confidence': float,         # Confidence score (0-1)
                'provider': str,             # Provider name
                'model': str,                # Model name
                'processing_time': float,    # Time in seconds
                'error': Optional[str]       # Error message if failed
            }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is ready to use

        Returns:
            True if provider can analyze images, False otherwise
        """
        pass

    @abstractmethod
    def get_cost_estimate(self, num_images: int) -> float:
        """
        Return estimated cost for processing images

        Args:
            num_images: Number of images to process

        Returns:
            Estimated cost in USD
        """
        pass

    @abstractmethod
    def warm_up(self):
        """
        Pre-load model into memory (if applicable)

        For cloud providers: verify API key
        For local models: load model weights into GPU/CPU
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get provider name

        Returns:
            Provider name (e.g., 'claude', 'local')
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get current model name

        Returns:
            Model name (e.g., 'claude-3-5-haiku', 'moondream-2b')
        """
        pass

    def batch_analyze(self, image_paths: List[Path], prompt: Optional[str] = None) -> List[Dict]:
        """
        Analyze multiple images (default implementation processes one by one)

        Override this method in provider implementations for optimized batch processing

        Args:
            image_paths: List of image file paths
            prompt: Optional custom prompt for all images

        Returns:
            List of analysis results
        """
        results = []
        for image_path in image_paths:
            result = self.analyze_image(image_path, prompt)
            results.append(result)
        return results

    def get_capabilities(self) -> Dict:
        """
        Get provider capabilities

        Returns:
            Dict with capability flags:
            {
                'supports_ocr': bool,
                'supports_objects': bool,
                'supports_scenes': bool,
                'supports_batch': bool,
                'supports_custom_prompts': bool,
                'max_image_size_mb': int,
                'supported_formats': List[str]
            }
        """
        return {
            'supports_ocr': False,
            'supports_objects': False,
            'supports_scenes': False,
            'supports_batch': False,
            'supports_custom_prompts': False,
            'max_image_size_mb': 10,
            'supported_formats': ['jpg', 'jpeg', 'png', 'webp']
        }


class VisionProviderError(Exception):
    """Base exception for vision provider errors"""
    pass


class VisionProviderNotAvailableError(VisionProviderError):
    """Raised when provider is not available (missing API key, model not loaded, etc.)"""
    pass


class VisionProviderTimeoutError(VisionProviderError):
    """Raised when provider times out"""
    pass


class VisionProviderQuotaError(VisionProviderError):
    """Raised when provider quota is exceeded"""
    pass

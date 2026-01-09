#!/usr/bin/env python3
"""
Local Vision Provider
Vision analysis using local models (Moondream, BLIP-2, LLaVA, etc.)
Zero-cost alternative to Claude Vision API
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List
from PIL import Image

from .base import (
    VisionProvider,
    VisionProviderNotAvailableError
)

logger = logging.getLogger(__name__)

# Try to import transformers and torch
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch/transformers not installed - local models unavailable")


class LocalProvider(VisionProvider):
    """Local vision model provider (Moondream, BLIP-2, etc.)"""

    SUPPORTED_MODELS = {
        'moondream-0.5b': {
            'hf_repo': 'vikhyatk/moondream2',
            'variant': '0.5b',
            'vram_mb': 1000,
            'quality_score': 0.60,
            'revision': '2024-08-26'
        },
        'moondream-2b': {
            'hf_repo': 'vikhyatk/moondream2',
            'variant': '2b',
            'vram_mb': 3000,
            'quality_score': 0.70,
            'revision': '2024-08-26'
        }
    }

    def __init__(self, model: str = 'moondream-2b', config: Optional[Dict] = None):
        """
        Initialize local vision provider

        Args:
            model: Model name (e.g., 'moondream-2b')
            config: Provider configuration
        """
        self.model_name = model or 'moondream-2b'
        self.config = config or {}
        self.model = None
        self.tokenizer = None
        self.device = None
        self.loaded = False

        # Get model info
        self.model_info = self.SUPPORTED_MODELS.get(self.model_name)

        if not self.model_info:
            logger.warning(f"Unknown model: {self.model_name}, defaulting to moondream-2b")
            self.model_name = 'moondream-2b'
            self.model_info = self.SUPPORTED_MODELS['moondream-2b']

        # Check if torch is available
        if not TORCH_AVAILABLE:
            logger.error("PyTorch not installed - local models unavailable")
            return

        # Detect device
        self.device = self._get_optimal_device()
        logger.info(f"Local provider will use device: {self.device}")

    def _get_optimal_device(self) -> str:
        """Auto-detect best available device"""
        if not TORCH_AVAILABLE:
            return 'cpu'

        # Check for CUDA (NVIDIA GPU)
        if torch.cuda.is_available():
            logger.info("CUDA GPU detected")
            return 'cuda'

        # Check for MPS (Apple Silicon GPU)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Apple Silicon GPU detected")
            return 'mps'

        # Fallback to CPU
        logger.info("Using CPU (no GPU detected)")
        return 'cpu'

    def is_available(self) -> bool:
        """Check if local provider can run"""
        return TORCH_AVAILABLE

    def get_provider_name(self) -> str:
        return 'local'

    def get_model_name(self) -> str:
        return self.model_name

    def get_cost_estimate(self, num_images: int) -> float:
        """Local models are free (zero cost)"""
        return 0.0

    def warm_up(self):
        """Load model into memory"""
        if not self.is_available():
            raise VisionProviderNotAvailableError(
                "PyTorch not installed. Run: pip install torch transformers"
            )

        if self.loaded:
            logger.info(f"Model {self.model_name} already loaded")
            return

        logger.info(f"Loading {self.model_name} model...")
        start_time = time.time()

        try:
            # Model cache directory
            cache_dir = Path("db/vision_models")
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Load Moondream model
            hf_repo = self.model_info['hf_repo']
            revision = self.model_info.get('revision', 'main')

            logger.info(f"Downloading/loading from HuggingFace: {hf_repo}")

            # Load model with trust_remote_code for Moondream
            self.model = AutoModelForCausalLM.from_pretrained(
                hf_repo,
                trust_remote_code=True,
                cache_dir=str(cache_dir),
                revision=revision,
                torch_dtype=torch.float16 if self.device in ['cuda', 'mps'] else torch.float32,
                device_map=self.device if self.device == 'cuda' else None
            )

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                hf_repo,
                trust_remote_code=True,
                cache_dir=str(cache_dir),
                revision=revision
            )

            # Move to device if not CUDA (CUDA uses device_map)
            if self.device != 'cuda':
                self.model = self.model.to(self.device)

            self.model.eval()  # Set to evaluation mode
            self.loaded = True

            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise VisionProviderNotAvailableError(f"Model loading failed: {e}")

    def analyze_image(self, image_path: Path, prompt: Optional[str] = None) -> Dict:
        """
        Analyze image using local model

        Args:
            image_path: Path to image file
            prompt: Optional custom prompt (default: "Describe this image in detail")

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
                'provider': 'local',
                'model': self.model_name,
                'processing_time': 0.0,
                'error': 'PyTorch not installed'
            }

        # Lazy load model on first use
        if not self.loaded:
            try:
                self.warm_up()
            except Exception as e:
                return {
                    'description': '',
                    'tags': [],
                    'scene_type': '',
                    'detected_objects': [],
                    'has_text': False,
                    'confidence': 0.0,
                    'provider': 'local',
                    'model': self.model_name,
                    'processing_time': 0.0,
                    'error': f'Model loading failed: {str(e)}'
                }

        start_time = time.time()

        try:
            # Load image
            image = Image.open(image_path).convert('RGB')

            # Use custom prompt or default
            if not prompt:
                prompt = "Describe this image in detail, including the main subjects, scene type, and any notable elements or text."

            # Encode image and generate description
            # Moondream-specific inference
            enc_image = self.model.encode_image(image)

            # Generate description
            description = self.model.answer_question(
                enc_image,
                prompt,
                self.tokenizer
            )

            # Parse description to extract structured data
            # For Moondream, we get a text description - try to extract structure
            tags = []
            scene_type = 'unknown'
            detected_objects = []

            # Simple heuristic parsing (can be improved)
            desc_lower = description.lower()

            # Detect scene type
            if any(word in desc_lower for word in ['photo', 'photograph', 'picture']):
                scene_type = 'photo'
            elif any(word in desc_lower for word in ['drawing', 'sketch', 'illustration']):
                scene_type = 'artwork'
            elif any(word in desc_lower for word in ['screenshot', 'interface', 'ui']):
                scene_type = 'screenshot'
            elif any(word in desc_lower for word in ['diagram', 'chart', 'graph']):
                scene_type = 'diagram'

            # Extract potential objects (simple noun extraction)
            # This is very basic - in production would use NLP
            common_objects = [
                'person', 'people', 'face', 'building', 'car', 'tree', 'sky',
                'water', 'text', 'logo', 'animal', 'food', 'device', 'screen'
            ]
            detected_objects = [obj for obj in common_objects if obj in desc_lower]

            # Extract basic tags
            tags = detected_objects[:5]  # Use detected objects as tags

            # Check for text
            has_text = 'text' in desc_lower or 'writing' in desc_lower or 'letters' in desc_lower

            processing_time = time.time() - start_time

            result = {
                'description': description,
                'tags': tags,
                'scene_type': scene_type,
                'detected_objects': detected_objects,
                'has_text': has_text,
                'confidence': self.model_info['quality_score'],
                'provider': 'local',
                'model': self.model_name,
                'processing_time': processing_time,
                'error': None
            }

            logger.info(f"Local model analyzed {image_path.name} in {processing_time:.2f}s")
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Local inference error for {image_path.name}: {error_msg}")

            return {
                'description': '',
                'tags': [],
                'scene_type': '',
                'detected_objects': [],
                'has_text': False,
                'confidence': 0.0,
                'provider': 'local',
                'model': self.model_name,
                'processing_time': time.time() - start_time,
                'error': error_msg
            }

    def batch_analyze(self, image_paths: List[Path], prompt: Optional[str] = None) -> List[Dict]:
        """
        Analyze multiple images (can be optimized for batch processing)

        Args:
            image_paths: List of image paths
            prompt: Optional custom prompt

        Returns:
            List of analysis results
        """
        # For now, process sequentially
        # TODO: Implement true batch processing with batched inference
        results = []

        for image_path in image_paths:
            result = self.analyze_image(image_path, prompt)
            results.append(result)

        return results

    def get_capabilities(self) -> Dict:
        """Get local provider capabilities"""
        return {
            'supports_ocr': False,  # Basic - depends on model
            'supports_objects': True,
            'supports_scenes': True,
            'supports_batch': True,
            'supports_custom_prompts': True,
            'max_image_size_mb': 10,
            'supported_formats': ['jpg', 'jpeg', 'png', 'webp']
        }

    def unload_model(self):
        """Unload model from memory to free resources"""
        if self.loaded:
            logger.info(f"Unloading model {self.model_name}")
            del self.model
            del self.tokenizer

            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.model = None
            self.tokenizer = None
            self.loaded = False

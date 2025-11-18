"""
Vision Language Model (VLM) Engine for Brochure Analysis

Supports:
- Ollama (local LLaVA, Bakllava, etc.)
- Gemini API (Google)
- Multi-modal understanding and structured extraction
"""

import os
import json
import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List, Dict, Optional
import logging
from PIL import Image
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VLMEngine(ABC):
    """Abstract base class for Vision Language Models."""

    def __init__(self, model_name: str = None):
        """
        Initialize VLM engine.

        Args:
            model_name: Model identifier
        """
        self.model_name = model_name
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def analyze_image(
        self,
        image: Union[str, Path, Image.Image],
        prompt: str = None,
        temperature: float = 0.1
    ) -> Dict:
        """
        Analyze image and extract information.

        Args:
            image: Image to analyze
            prompt: Custom prompt for the model
            temperature: Sampling temperature

        Returns:
            Dictionary with analysis results
        """
        pass

    def load_image(self, image: Union[str, Path, Image.Image]) -> Image.Image:
        """Load image from various formats."""
        if isinstance(image, (str, Path)):
            return Image.open(image).convert('RGB')
        elif isinstance(image, Image.Image):
            return image.convert('RGB')
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

    @staticmethod
    def encode_image_base64(image: Image.Image) -> str:
        """Encode PIL Image to base64 string."""
        import io
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')


class OllamaVLM(VLMEngine):
    """
    Ollama Vision Language Model.

    Supports local models like LLaVA, Bakllava, etc.
    """

    def __init__(
        self,
        model_name: str = "llava:latest",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama VLM.

        Args:
            model_name: Ollama model name (llava, bakllava, etc.)
            base_url: Ollama server URL
        """
        super().__init__(model_name)
        self.base_url = base_url.rstrip('/')

        try:
            import requests
            self.requests = requests
            # Test connection
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Connected to Ollama at {self.base_url}")
            else:
                logger.warning(f"Ollama server responded with status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
            raise

    def analyze_image(
        self,
        image: Union[str, Path, Image.Image],
        prompt: str = None,
        temperature: float = 0.1
    ) -> Dict:
        """
        Analyze image using Ollama VLM.

        Args:
            image: Image to analyze
            prompt: Custom analysis prompt
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Dictionary with extracted information
        """
        # Load and encode image
        img = self.load_image(image)
        img_base64 = self.encode_image_base64(img)

        # Default prompt for brochure analysis
        if prompt is None:
            prompt = self._get_default_prompt()

        # Call Ollama API
        try:
            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [img_base64],
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                },
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # Parse response
            return self._parse_response(result.get('response', ''))

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return {"error": str(e), "deals": []}

    def _get_default_prompt(self) -> str:
        """Get default prompt for brochure analysis."""
        return """Analyze this supermarket brochure image and extract all product deals.

For each product deal, identify:
- Product name
- Original price (if shown)
- Discounted/sale price
- Discount percentage (if shown)
- Valid dates (if shown)

Return the information in JSON format as a list of deals:
{
  "deals": [
    {
      "product_name": "Product Name",
      "original_price": 10.99,
      "discounted_price": 7.99,
      "discount_percentage": 27,
      "valid_from": "2024-11-01",
      "valid_to": "2024-11-07"
    }
  ]
}

Only return valid JSON, no additional text."""

    def _parse_response(self, response_text: str) -> Dict:
        """Parse VLM response to extract structured data."""
        try:
            # Try to find JSON in response
            import re

            # Look for JSON block
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data

            # If no JSON found, return raw response
            return {"raw_response": response_text, "deals": []}

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {"raw_response": response_text, "deals": []}


class GeminiVLM(VLMEngine):
    """
    Google Gemini Vision API.

    Requires API key: export GEMINI_API_KEY=your_key
    """

    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        api_key: str = None
    ):
        """
        Initialize Gemini VLM.

        Args:
            model_name: Gemini model name
            api_key: Google API key (or set GEMINI_API_KEY env var)
        """
        super().__init__(model_name)

        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        try:
            import google.generativeai as genai
            self.genai = genai
            genai.configure(api_key=self.api_key)

            # Initialize model
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Initialized Gemini model: {model_name}")

        except ImportError:
            logger.error("google-generativeai not installed. Install with: pip install google-generativeai")
            raise

    def analyze_image(
        self,
        image: Union[str, Path, Image.Image],
        prompt: str = None,
        temperature: float = 0.1
    ) -> Dict:
        """
        Analyze image using Gemini Vision API.

        Args:
            image: Image to analyze
            prompt: Custom analysis prompt
            temperature: Sampling temperature

        Returns:
            Dictionary with extracted information
        """
        # Load image
        img = self.load_image(image)

        # Default prompt
        if prompt is None:
            prompt = self._get_default_prompt()

        try:
            # Generate content
            response = self.model.generate_content(
                [prompt, img],
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 2048,
                }
            )

            # Parse response
            return self._parse_response(response.text)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {"error": str(e), "deals": []}

    def _get_default_prompt(self) -> str:
        """Get default prompt for brochure analysis."""
        return """Analyze this supermarket brochure and extract all product deals.

For each deal, provide:
- product_name: Name of the product
- original_price: Original price (number, or null)
- discounted_price: Sale price (number)
- discount_percentage: Discount % (number, or null)
- valid_from: Start date (YYYY-MM-DD, or null)
- valid_to: End date (YYYY-MM-DD, or null)

Return ONLY a valid JSON object in this exact format:
{
  "deals": [
    {
      "product_name": "Example Product",
      "original_price": 10.99,
      "discounted_price": 7.99,
      "discount_percentage": 27,
      "valid_from": "2024-11-01",
      "valid_to": "2024-11-07"
    }
  ]
}

Important: Return ONLY the JSON, no markdown, no explanation."""

    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini response."""
        try:
            import re

            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*', '', response_text)
            text = re.sub(r'```\s*', '', text)

            # Find JSON
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data

            return {"raw_response": response_text, "deals": []}

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON: {e}")
            return {"raw_response": response_text, "deals": []}


def create_vlm_engine(
    engine_type: str = "ollama",
    model_name: str = None,
    **kwargs
) -> VLMEngine:
    """
    Factory function to create VLM engine.

    Args:
        engine_type: Type of VLM ('ollama' or 'gemini')
        model_name: Model name (optional, uses defaults)
        **kwargs: Additional engine-specific arguments

    Returns:
        VLMEngine instance

    Examples:
        >>> vlm = create_vlm_engine('ollama', model_name='llava:latest')
        >>> vlm = create_vlm_engine('gemini', api_key='your-key')
    """
    engine_type = engine_type.lower()

    if engine_type == 'ollama':
        model_name = model_name or "llava:latest"
        return OllamaVLM(model_name=model_name, **kwargs)

    elif engine_type == 'gemini':
        model_name = model_name or "gemini-1.5-flash"
        return GeminiVLM(model_name=model_name, **kwargs)

    else:
        raise ValueError(f"Unknown VLM engine: {engine_type}. Choose 'ollama' or 'gemini'")


def main():
    """Command-line interface for VLM extraction."""
    import argparse

    parser = argparse.ArgumentParser(description='Extract information from brochures using VLM')
    parser.add_argument('image', help='Brochure image path')
    parser.add_argument('--engine', choices=['ollama', 'gemini'], default='ollama')
    parser.add_argument('--model', help='Model name')
    parser.add_argument('--prompt', help='Custom prompt')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--api-key', help='API key (for Gemini)')

    args = parser.parse_args()

    # Create VLM engine
    kwargs = {}
    if args.api_key:
        kwargs['api_key'] = args.api_key

    vlm = create_vlm_engine(
        engine_type=args.engine,
        model_name=args.model,
        **kwargs
    )

    # Analyze image
    logger.info(f"Analyzing {args.image} with {args.engine}...")
    result = vlm.analyze_image(args.image, prompt=args.prompt)

    # Print results
    print("\nExtracted Deals:")
    print("=" * 80)

    if 'deals' in result:
        for i, deal in enumerate(result['deals'], 1):
            print(f"\n{i}. {deal.get('product_name', 'Unknown')}")
            if deal.get('discounted_price'):
                print(f"   Price: €{deal['discounted_price']}")
            if deal.get('discount_percentage'):
                print(f"   Discount: {deal['discount_percentage']}%")
            if deal.get('valid_to'):
                print(f"   Valid until: {deal['valid_to']}")
    else:
        print(json.dumps(result, indent=2))

    # Save to file
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {args.output}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

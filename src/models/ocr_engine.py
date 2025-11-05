"""
OCR Engine for Brochure Text Extraction

Supports multiple OCR backends:
- Tesseract OCR
- PaddleOCR
- EasyOCR
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCREngine(ABC):
    """
    Abstract base class for OCR engines.

    All OCR engines should inherit from this class and implement
    the extract_text method.
    """

    def __init__(self, languages: List[str] = None):
        """
        Initialize OCR engine.

        Args:
            languages: List of language codes (e.g., ['de', 'en'])
        """
        self.languages = languages or ['de', 'en']
        logger.info(f"Initialized {self.__class__.__name__} with languages: {self.languages}")

    @abstractmethod
    def extract_text(
        self,
        image: Union[str, Path, Image.Image, np.ndarray]
    ) -> List[Dict]:
        """
        Extract text from image.

        Args:
            image: Image as path, PIL Image, or numpy array

        Returns:
            List of dictionaries containing:
                - text: Extracted text
                - bbox: Bounding box coordinates [x1, y1, x2, y2]
                - confidence: Confidence score (0-1)
        """
        pass

    def load_image(self, image: Union[str, Path, Image.Image, np.ndarray]) -> np.ndarray:
        """
        Load image and convert to numpy array.

        Args:
            image: Image in various formats

        Returns:
            Image as numpy array (RGB)
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image)

        if isinstance(image, Image.Image):
            image = np.array(image)

        # Ensure RGB format
        if len(image.shape) == 2:  # Grayscale
            image = np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:  # RGBA
            image = image[:, :, :3]

        return image


class TesseractOCR(OCREngine):
    """
    Tesseract OCR engine wrapper.

    Requires tesseract to be installed on the system.
    """

    def __init__(self, languages: List[str] = None, config: str = None):
        """
        Initialize Tesseract OCR.

        Args:
            languages: List of language codes
            config: Tesseract configuration string (e.g., '--psm 6')
        """
        super().__init__(languages)
        self.config = config or '--psm 6'

        try:
            import pytesseract
            self.pytesseract = pytesseract
            logger.info("Tesseract OCR initialized successfully")
        except ImportError:
            logger.error("pytesseract not installed. Install with: pip install pytesseract")
            raise

    def extract_text(
        self,
        image: Union[str, Path, Image.Image, np.ndarray]
    ) -> List[Dict]:
        """
        Extract text using Tesseract.

        Args:
            image: Input image

        Returns:
            List of extracted text regions with bounding boxes
        """
        img_array = self.load_image(image)
        img_pil = Image.fromarray(img_array)

        # Run Tesseract
        lang_string = '+'.join(self.languages)

        # Get detailed results with bounding boxes
        data = self.pytesseract.image_to_data(
            img_pil,
            lang=lang_string,
            config=self.config,
            output_type=self.pytesseract.Output.DICT
        )

        results = []
        n_boxes = len(data['text'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:  # Skip empty detections
                continue

            # Extract bounding box
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            bbox = [x, y, x + w, y + h]

            # Extract confidence (convert from 0-100 to 0-1)
            confidence = float(data['conf'][i]) / 100.0 if data['conf'][i] != -1 else 0.0

            results.append({
                'text': text,
                'bbox': bbox,
                'confidence': confidence
            })

        logger.info(f"Tesseract extracted {len(results)} text regions")
        return results


class PaddleOCR(OCREngine):
    """
    PaddleOCR engine wrapper.

    PaddleOCR is a deep learning-based OCR tool with good accuracy.
    """

    def __init__(
        self,
        languages: List[str] = None,
        use_gpu: bool = False,
        det_db_thresh: float = 0.3
    ):
        """
        Initialize PaddleOCR.

        Args:
            languages: List of language codes
            use_gpu: Whether to use GPU acceleration
            det_db_thresh: Detection threshold for text regions
        """
        super().__init__(languages)
        self.use_gpu = use_gpu
        self.det_db_thresh = det_db_thresh

        try:
            from paddleocr import PaddleOCR as PaddleOCRBackend

            # Map language codes
            lang_map = {
                'de': 'german',
                'en': 'en',
                'fr': 'french',
                'es': 'spanish'
            }
            paddle_lang = lang_map.get(self.languages[0], 'en')

            self.ocr = PaddleOCRBackend(
                use_angle_cls=True,
                lang=paddle_lang,
                use_gpu=use_gpu,
                det_db_thresh=det_db_thresh,
                show_log=False
            )
            logger.info(f"PaddleOCR initialized with language: {paddle_lang}, GPU: {use_gpu}")
        except ImportError:
            logger.error("paddleocr not installed. Install with: pip install paddleocr")
            raise

    def extract_text(
        self,
        image: Union[str, Path, Image.Image, np.ndarray]
    ) -> List[Dict]:
        """
        Extract text using PaddleOCR.

        Args:
            image: Input image

        Returns:
            List of extracted text regions with bounding boxes
        """
        img_array = self.load_image(image)

        # Run PaddleOCR
        result = self.ocr.ocr(img_array, cls=True)

        results = []

        if result and result[0]:
            for line in result[0]:
                # PaddleOCR returns: [bbox_points, (text, confidence)]
                bbox_points, (text, confidence) = line

                # Convert bbox points to [x1, y1, x2, y2]
                x_coords = [p[0] for p in bbox_points]
                y_coords = [p[1] for p in bbox_points]
                bbox = [
                    int(min(x_coords)),
                    int(min(y_coords)),
                    int(max(x_coords)),
                    int(max(y_coords))
                ]

                results.append({
                    'text': text,
                    'bbox': bbox,
                    'confidence': float(confidence)
                })

        logger.info(f"PaddleOCR extracted {len(results)} text regions")
        return results


class EasyOCR(OCREngine):
    """
    EasyOCR engine wrapper.

    EasyOCR is a PyTorch-based OCR with support for many languages.
    """

    def __init__(
        self,
        languages: List[str] = None,
        gpu: bool = False
    ):
        """
        Initialize EasyOCR.

        Args:
            languages: List of language codes
            gpu: Whether to use GPU acceleration
        """
        super().__init__(languages)
        self.gpu = gpu

        try:
            import easyocr

            self.reader = easyocr.Reader(
                self.languages,
                gpu=gpu
            )
            logger.info(f"EasyOCR initialized with languages: {self.languages}, GPU: {gpu}")
        except ImportError:
            logger.error("easyocr not installed. Install with: pip install easyocr")
            raise

    def extract_text(
        self,
        image: Union[str, Path, Image.Image, np.ndarray]
    ) -> List[Dict]:
        """
        Extract text using EasyOCR.

        Args:
            image: Input image

        Returns:
            List of extracted text regions with bounding boxes
        """
        img_array = self.load_image(image)

        # Run EasyOCR
        result = self.reader.readtext(img_array)

        results = []

        for detection in result:
            # EasyOCR returns: (bbox_points, text, confidence)
            bbox_points, text, confidence = detection

            # Convert bbox points to [x1, y1, x2, y2]
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            bbox = [
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords))
            ]

            results.append({
                'text': text,
                'bbox': bbox,
                'confidence': float(confidence)
            })

        logger.info(f"EasyOCR extracted {len(results)} text regions")
        return results


def create_ocr_engine(
    engine_type: str = 'paddleocr',
    languages: List[str] = None,
    **kwargs
) -> OCREngine:
    """
    Factory function to create OCR engine.

    Args:
        engine_type: Type of OCR engine ('tesseract', 'paddleocr', 'easyocr')
        languages: List of language codes
        **kwargs: Additional arguments for specific engines

    Returns:
        OCREngine instance
    """
    engine_type = engine_type.lower()

    if engine_type == 'tesseract':
        return TesseractOCR(languages=languages, **kwargs)
    elif engine_type == 'paddleocr':
        return PaddleOCR(languages=languages, **kwargs)
    elif engine_type == 'easyocr':
        return EasyOCR(languages=languages, **kwargs)
    else:
        raise ValueError(f"Unknown OCR engine: {engine_type}")


def main():
    """Command-line interface for OCR extraction."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Extract text from brochure images using OCR')
    parser.add_argument('image', help='Input image file')
    parser.add_argument('--engine', choices=['tesseract', 'paddleocr', 'easyocr'],
                        default='paddleocr', help='OCR engine to use')
    parser.add_argument('--languages', nargs='+', default=['de', 'en'],
                        help='Languages to recognize')
    parser.add_argument('--gpu', action='store_true', help='Use GPU acceleration')
    parser.add_argument('--output', help='Output JSON file for results')

    args = parser.parse_args()

    # Create OCR engine
    ocr = create_ocr_engine(
        engine_type=args.engine,
        languages=args.languages,
        use_gpu=args.gpu,
        gpu=args.gpu
    )

    # Extract text
    logger.info(f"Processing {args.image}")
    results = ocr.extract_text(args.image)

    # Print results
    print(f"\nExtracted {len(results)} text regions:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['text']}")
        print(f"   BBox: {result['bbox']}")
        print(f"   Confidence: {result['confidence']:.2f}\n")

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_path}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

"""Models Module for Brochure Information Extraction"""

from .ocr_engine import OCREngine, TesseractOCR, PaddleOCR, EasyOCR

__all__ = ['OCREngine', 'TesseractOCR', 'PaddleOCR', 'EasyOCR']

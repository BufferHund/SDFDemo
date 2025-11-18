"""
Entity Extraction and Post-processing Module

Extracts structured information from OCR results and model predictions:
- Product names
- Prices (original and discounted)
- Discount percentages
- Valid dates
- Store information
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Deal:
    """Structured deal information."""
    product_name: str
    original_price: Optional[float] = None
    discounted_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    store: Optional[str] = None
    location: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'product_name': self.product_name,
            'original_price': self.original_price,
            'discounted_price': self.discounted_price,
            'discount_percentage': self.discount_percentage,
            'valid_from': self.valid_from,
            'valid_to': self.valid_to,
            'store': self.store,
            'location': self.location,
            'confidence': self.confidence
        }


class PriceExtractor:
    """Extract and parse price information."""

    # German and English price patterns
    PRICE_PATTERNS = [
        r'(\d+[,\.]\d{2})\s*€',  # 1.99€, 1,99€
        r'€\s*(\d+[,\.]\d{2})',  # €1.99, €1,99
        r'(\d+[,\.]\d{2})\s*EUR',  # 1.99EUR
        r'(\d+[,\.]\d{2})\s*euro',  # 1.99euro (case insensitive)
        r'(\d+[,\.]\d{2})',  # 1.99, 1,99 (fallback)
    ]

    @staticmethod
    def extract_price(text: str) -> Optional[float]:
        """
        Extract price from text.

        Args:
            text: Text containing price

        Returns:
            Price as float or None
        """
        text = text.strip()

        for pattern in PriceExtractor.PRICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1)
                # Normalize decimal separator
                price_str = price_str.replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    continue

        return None

    @staticmethod
    def extract_discount_percentage(text: str) -> Optional[float]:
        """
        Extract discount percentage from text.

        Args:
            text: Text containing discount percentage

        Returns:
            Discount percentage or None
        """
        # Patterns: -20%, 20% off, -20 %, etc.
        patterns = [
            r'-?\s*(\d+)\s*%',
            r'(\d+)\s*%\s*off',
            r'(\d+)\s*%\s*rabatt',  # German
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None


class DateExtractor:
    """Extract and parse date information."""

    # German date patterns
    DATE_PATTERNS = [
        # DD.MM.YYYY
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        # DD.MM.YY
        r'(\d{1,2})\.(\d{1,2})\.(\d{2})',
        # DD.MM. (without year)
        r'(\d{1,2})\.(\d{1,2})\.',
    ]

    # German month names
    MONTH_NAMES_DE = {
        'januar': 1, 'jan': 1,
        'februar': 2, 'feb': 2,
        'märz': 3, 'mär': 3,
        'april': 4, 'apr': 4,
        'mai': 5,
        'juni': 6, 'jun': 6,
        'juli': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'oktober': 10, 'okt': 10,
        'november': 11, 'nov': 11,
        'dezember': 12, 'dez': 12,
    }

    @staticmethod
    def extract_date(text: str) -> Optional[str]:
        """
        Extract date from text.

        Args:
            text: Text containing date

        Returns:
            Date in ISO format (YYYY-MM-DD) or None
        """
        current_year = datetime.now().year

        for pattern in DateExtractor.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    day = int(match.group(1))
                    month = int(match.group(2))

                    # Get year
                    if len(match.groups()) >= 3:
                        year_str = match.group(3)
                        if len(year_str) == 2:
                            year = 2000 + int(year_str)
                        else:
                            year = int(year_str)
                    else:
                        year = current_year

                    # Validate date
                    date = datetime(year, month, day)
                    return date.strftime('%Y-%m-%d')

                except (ValueError, IndexError):
                    continue

        return None

    @staticmethod
    def extract_date_range(text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract date range from text.

        Args:
            text: Text containing date range (e.g., "01.11. bis 07.11.2024")

        Returns:
            Tuple of (start_date, end_date) in ISO format
        """
        # Pattern for date ranges
        range_patterns = [
            r'(\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})?)\s*(?:bis|to|-)\s*(\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})?)',
            r'gültig\s*(?:vom|von)\s*(\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})?)\s*(?:bis)\s*(\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})?)',
        ]

        for pattern in range_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_date = DateExtractor.extract_date(match.group(1))
                end_date = DateExtractor.extract_date(match.group(2))
                return start_date, end_date

        return None, None


class EntityExtractor:
    """
    Extract structured deals from OCR results and model predictions.
    """

    def __init__(self):
        self.price_extractor = PriceExtractor()
        self.date_extractor = DateExtractor()

    def extract_from_entities(
        self,
        entities: List[Dict],
        image_metadata: Optional[Dict] = None
    ) -> List[Deal]:
        """
        Extract structured deals from entity list.

        Args:
            entities: List of entities from model prediction
                [{"type": "PRODUCT", "text": "...", "bbox": [...], "confidence": ...}, ...]
            image_metadata: Optional metadata (store, location, dates)

        Returns:
            List of Deal objects
        """
        # Group entities by proximity (same deal)
        deals = []

        # Extract entities by type
        products = [e for e in entities if e['type'] == 'PRODUCT']
        prices = [e for e in entities if e['type'] == 'PRICE']
        discount_prices = [e for e in entities if e['type'] == 'DISCOUNT_PRICE']
        discount_percents = [e for e in entities if e['type'] == 'DISCOUNT_PERCENT']

        # Match entities to create deals
        for product in products:
            deal = Deal(
                product_name=product['text'],
                confidence=product.get('confidence', 1.0)
            )

            # Find closest price (by spatial proximity)
            closest_price = self._find_closest_entity(product, prices)
            if closest_price:
                deal.original_price = self.price_extractor.extract_price(closest_price['text'])

            # Find closest discount price
            closest_discount = self._find_closest_entity(product, discount_prices)
            if closest_discount:
                deal.discounted_price = self.price_extractor.extract_price(closest_discount['text'])

            # Find closest discount percentage
            closest_percent = self._find_closest_entity(product, discount_percents)
            if closest_percent:
                deal.discount_percentage = self.price_extractor.extract_discount_percentage(
                    closest_percent['text']
                )

            # Calculate missing values
            if deal.original_price and deal.discounted_price and not deal.discount_percentage:
                deal.discount_percentage = (
                    (deal.original_price - deal.discounted_price) / deal.original_price * 100
                )

            if deal.original_price and deal.discount_percentage and not deal.discounted_price:
                deal.discounted_price = deal.original_price * (1 - deal.discount_percentage / 100)

            # Add metadata
            if image_metadata:
                deal.store = image_metadata.get('store')
                deal.location = image_metadata.get('location')
                deal.valid_from = image_metadata.get('valid_from')
                deal.valid_to = image_metadata.get('valid_to')

            deals.append(deal)

        return deals

    def extract_from_ocr(
        self,
        ocr_results: List[Dict],
        image_metadata: Optional[Dict] = None
    ) -> List[Deal]:
        """
        Extract deals from raw OCR results (without model predictions).

        Uses heuristics to identify products and prices.

        Args:
            ocr_results: OCR results [{"text": ..., "bbox": ..., "confidence": ...}, ...]
            image_metadata: Optional metadata

        Returns:
            List of Deal objects
        """
        deals = []

        # Simple heuristic: any text near a price is likely a product
        for i, result in enumerate(ocr_results):
            text = result['text']

            # Check if this is a price
            price = self.price_extractor.extract_price(text)
            if price:
                # Look for product name nearby
                product_name = self._find_product_near_price(i, ocr_results)

                if product_name:
                    deal = Deal(
                        product_name=product_name,
                        discounted_price=price,
                        confidence=result.get('confidence', 1.0)
                    )

                    if image_metadata:
                        deal.store = image_metadata.get('store')
                        deal.location = image_metadata.get('location')
                        deal.valid_from = image_metadata.get('valid_from')
                        deal.valid_to = image_metadata.get('valid_to')

                    deals.append(deal)

        return deals

    def _find_closest_entity(
        self,
        entity: Dict,
        candidates: List[Dict],
        max_distance: float = 200.0
    ) -> Optional[Dict]:
        """Find the closest entity by spatial distance."""
        if not candidates:
            return None

        entity_center = self._get_bbox_center(entity['bbox'])
        best_candidate = None
        best_distance = max_distance

        for candidate in candidates:
            candidate_center = self._get_bbox_center(candidate['bbox'])
            distance = self._euclidean_distance(entity_center, candidate_center)

            if distance < best_distance:
                best_distance = distance
                best_candidate = candidate

        return best_candidate

    def _find_product_near_price(
        self,
        price_idx: int,
        ocr_results: List[Dict],
        search_radius: int = 3
    ) -> Optional[str]:
        """Find product name near a price."""
        # Look at nearby text (before the price)
        start_idx = max(0, price_idx - search_radius)

        for i in range(start_idx, price_idx):
            text = ocr_results[i]['text']

            # Skip if it looks like a price or number
            if self.price_extractor.extract_price(text):
                continue

            if re.match(r'^\d+$', text.strip()):
                continue

            # If it has letters and is substantial, likely a product name
            if len(text.strip()) > 2 and re.search(r'[a-zA-ZäöüÄÖÜß]', text):
                return text

        return None

    @staticmethod
    def _get_bbox_center(bbox: List[int]) -> Tuple[float, float]:
        """Get center point of bounding box."""
        x = (bbox[0] + bbox[2]) / 2
        y = (bbox[1] + bbox[3]) / 2
        return x, y

    @staticmethod
    def _euclidean_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

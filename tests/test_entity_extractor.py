"""Tests for entity extraction module."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.entity_extractor import (
    PriceExtractor,
    DateExtractor,
    EntityExtractor,
    Deal
)


class TestPriceExtractor:
    """Test price extraction."""

    def test_extract_price_euro_symbol(self):
        assert PriceExtractor.extract_price("1.99€") == 1.99
        assert PriceExtractor.extract_price("€2.50") == 2.50

    def test_extract_price_comma_separator(self):
        assert PriceExtractor.extract_price("1,99€") == 1.99
        assert PriceExtractor.extract_price("12,50 EUR") == 12.50

    def test_extract_price_no_symbol(self):
        assert PriceExtractor.extract_price("3.99") == 3.99

    def test_extract_price_invalid(self):
        assert PriceExtractor.extract_price("kein Preis") is None
        assert PriceExtractor.extract_price("") is None

    def test_extract_discount_percentage(self):
        assert PriceExtractor.extract_discount_percentage("-20%") == 20.0
        assert PriceExtractor.extract_discount_percentage("30% off") == 30.0
        assert PriceExtractor.extract_discount_percentage("15% rabatt") == 15.0

    def test_extract_discount_percentage_invalid(self):
        assert PriceExtractor.extract_discount_percentage("kein Rabatt") is None


class TestDateExtractor:
    """Test date extraction."""

    def test_extract_date_full(self):
        result = DateExtractor.extract_date("01.11.2024")
        assert result == "2024-11-01"

    def test_extract_date_short_year(self):
        result = DateExtractor.extract_date("15.12.24")
        assert result == "2024-12-15"

    def test_extract_date_no_year(self):
        result = DateExtractor.extract_date("25.12.")
        # Should use current year
        assert result is not None
        assert "-12-25" in result

    def test_extract_date_invalid(self):
        assert DateExtractor.extract_date("kein Datum") is None
        assert DateExtractor.extract_date("32.13.2024") is None

    def test_extract_date_range(self):
        start, end = DateExtractor.extract_date_range("01.11. bis 07.11.2024")
        assert start is not None
        assert end == "2024-11-07"

    def test_extract_date_range_german(self):
        start, end = DateExtractor.extract_date_range("gültig vom 01.11.2024 bis 15.11.2024")
        assert start == "2024-11-01"
        assert end == "2024-11-15"


class TestEntityExtractor:
    """Test entity extraction."""

    def test_find_closest_entity(self):
        extractor = EntityExtractor()

        entity = {"bbox": [100, 100, 200, 150]}
        candidates = [
            {"bbox": [250, 100, 350, 150]},  # Close
            {"bbox": [500, 500, 600, 600]},  # Far
        ]

        result = extractor._find_closest_entity(entity, candidates)
        assert result == candidates[0]

    def test_find_closest_entity_max_distance(self):
        extractor = EntityExtractor()

        entity = {"bbox": [100, 100, 200, 150]}
        candidates = [{"bbox": [1000, 1000, 1100, 1150]}]  # Too far

        result = extractor._find_closest_entity(entity, candidates, max_distance=100)
        assert result is None

    def test_extract_from_entities_complete_deal(self):
        extractor = EntityExtractor()

        entities = [
            {"type": "PRODUCT", "text": "Milch", "bbox": [100, 100, 200, 150], "confidence": 0.9},
            {"type": "PRICE", "text": "2.99€", "bbox": [250, 100, 300, 150], "confidence": 0.95},
            {"type": "DISCOUNT_PRICE", "text": "1.99€", "bbox": [350, 100, 400, 150], "confidence": 0.93},
        ]

        deals = extractor.extract_from_entities(entities)

        assert len(deals) == 1
        assert deals[0].product_name == "Milch"
        assert deals[0].original_price == 2.99
        assert deals[0].discounted_price == 1.99


class TestDeal:
    """Test Deal dataclass."""

    def test_deal_to_dict(self):
        deal = Deal(
            product_name="Test Product",
            original_price=10.0,
            discounted_price=7.99,
            discount_percentage=20.0
        )

        result = deal.to_dict()

        assert result["product_name"] == "Test Product"
        assert result["original_price"] == 10.0
        assert result["discounted_price"] == 7.99
        assert result["discount_percentage"] == 20.0
        assert result["confidence"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

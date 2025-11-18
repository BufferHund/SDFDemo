"""Data Collection Module for Supermarket Brochures"""

from .base_scraper import BaseScraper
from .aldi_scraper import AldiScraper, AldiSuedScraper, AldiNordScraper
from .rewe_scraper import ReweScraper
from .lidl_scraper import LidlScraper
from .edeka_scraper import EdekaScraper

__all__ = [
    'BaseScraper',
    'AldiScraper',
    'AldiSuedScraper',
    'AldiNordScraper',
    'ReweScraper',
    'LidlScraper',
    'EdekaScraper'
]

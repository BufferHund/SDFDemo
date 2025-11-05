"""Data Collection Module for Supermarket Brochures"""

from .base_scraper import BaseScraper
from .aldi_scraper import AldiScraper
from .rewe_scraper import ReweScraper

__all__ = ['BaseScraper', 'AldiScraper', 'ReweScraper']

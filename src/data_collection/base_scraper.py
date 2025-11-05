"""
Base Scraper Class for Supermarket Brochures
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseScraper(ABC):
    """
    Abstract base class for supermarket brochure scrapers.

    Each supermarket has different website structure, so subclasses
    must implement the scraping logic specific to each retailer.
    """

    def __init__(
        self,
        supermarket_name: str,
        base_url: str,
        output_dir: str = "data/raw",
        metadata_dir: str = "data/metadata",
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize the base scraper.

        Args:
            supermarket_name: Name of the supermarket (e.g., "aldi_sued")
            base_url: Base URL of the supermarket's brochure page
            output_dir: Directory to save downloaded files
            metadata_dir: Directory to save metadata JSON files
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.supermarket_name = supermarket_name
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.metadata_dir = Path(metadata_dir)
        self.timeout = timeout
        self.retry_attempts = retry_attempts

        self.logger = logging.getLogger(f"{__name__}.{supermarket_name}")

        # Create output directories
        self.pdf_dir = self.output_dir / "pdfs" / supermarket_name
        self.image_dir = self.output_dir / "images" / supermarket_name
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a web page and return BeautifulSoup object.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(f"Fetching {url} (attempt {attempt + 1}/{self.retry_attempts})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                self.logger.warning(f"Failed to fetch {url}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"All attempts failed for {url}")
                    return None

    def download_file(self, url: str, output_path: Path) -> bool:
        """
        Download a file from URL to output path.

        Args:
            url: URL of the file
            output_path: Path where to save the file

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(f"Downloading {url} to {output_path}")
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()

                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                self.logger.info(f"Successfully downloaded {output_path}")
                return True
            except requests.RequestException as e:
                self.logger.warning(f"Failed to download {url}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.logger.error(f"All attempts failed for {url}")
                    return False

    def save_metadata(self, metadata: Dict, filename: str):
        """
        Save metadata to JSON file.

        Args:
            metadata: Dictionary containing metadata
            filename: Name of the output JSON file
        """
        output_path = self.metadata_dir / f"{self.supermarket_name}_{filename}"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, ensure_ascii=False, fp=f)
        self.logger.info(f"Saved metadata to {output_path}")

    @abstractmethod
    def get_brochure_urls(self) -> List[Dict[str, str]]:
        """
        Get list of brochure URLs from the supermarket website.

        Must be implemented by subclasses.

        Returns:
            List of dictionaries containing:
                - url: URL of the brochure
                - title: Title of the brochure
                - valid_from: Start date of validity
                - valid_to: End date of validity
                - type: 'pdf' or 'image'
        """
        pass

    @abstractmethod
    def download_brochure(self, brochure_info: Dict[str, str]) -> bool:
        """
        Download a single brochure.

        Must be implemented by subclasses.

        Args:
            brochure_info: Dictionary with brochure information

        Returns:
            True if successful, False otherwise
        """
        pass

    def run(self) -> Dict[str, any]:
        """
        Run the complete scraping process.

        Returns:
            Dictionary with summary statistics
        """
        self.logger.info(f"Starting scraper for {self.supermarket_name}")
        start_time = datetime.now()

        # Get list of brochures
        brochures = self.get_brochure_urls()
        self.logger.info(f"Found {len(brochures)} brochures")

        # Download each brochure
        success_count = 0
        failed_count = 0

        for i, brochure in enumerate(brochures, 1):
            self.logger.info(f"Processing brochure {i}/{len(brochures)}: {brochure.get('title', 'Unknown')}")
            if self.download_brochure(brochure):
                success_count += 1
            else:
                failed_count += 1

            # Be polite - don't hammer the server
            time.sleep(1)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        summary = {
            'supermarket': self.supermarket_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'total_brochures': len(brochures),
            'successful_downloads': success_count,
            'failed_downloads': failed_count
        }

        # Save summary
        self.save_metadata(summary, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        self.logger.info(f"Scraping complete: {success_count} successful, {failed_count} failed")
        return summary

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

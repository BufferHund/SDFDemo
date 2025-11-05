"""
Aldi Supermarket Brochure Scraper
"""

import re
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from .base_scraper import BaseScraper


class AldiScraper(BaseScraper):
    """
    Scraper for Aldi Süd and Aldi Nord brochures.

    Aldi provides brochures in PDF format on their websites:
    - Aldi Süd: https://prospekt.aldi-sued.de/
    - Aldi Nord: https://www.aldi-nord.de/prospekte/
    """

    def __init__(self, variant: str = "sued", **kwargs):
        """
        Initialize Aldi scraper.

        Args:
            variant: "sued" for Aldi Süd or "nord" for Aldi Nord
            **kwargs: Additional arguments passed to BaseScraper
        """
        if variant.lower() not in ["sued", "nord"]:
            raise ValueError("variant must be 'sued' or 'nord'")

        self.variant = variant.lower()

        if self.variant == "sued":
            base_url = "https://prospekt.aldi-sued.de/"
            name = "aldi_sued"
        else:
            base_url = "https://www.aldi-nord.de/prospekte/aldi-aktuell.html"
            name = "aldi_nord"

        super().__init__(
            supermarket_name=name,
            base_url=base_url,
            **kwargs
        )

    def get_brochure_urls(self) -> List[Dict[str, str]]:
        """
        Get list of brochure URLs from Aldi website.

        Returns:
            List of dictionaries with brochure information
        """
        brochures = []

        # Fetch main page
        soup = self.fetch_page(self.base_url)
        if not soup:
            self.logger.error("Failed to fetch main page")
            return brochures

        if self.variant == "sued":
            # Aldi Süd structure
            # Look for PDF links in the page
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))

            for link in pdf_links:
                href = link.get('href')
                if not href.startswith('http'):
                    href = f"https://prospekt.aldi-sued.de{href}"

                # Try to extract title and dates
                title = link.get_text(strip=True) or link.get('title', 'Aldi Süd Prospekt')

                brochures.append({
                    'url': href,
                    'title': title,
                    'type': 'pdf',
                    'valid_from': None,
                    'valid_to': None
                })

        else:
            # Aldi Nord structure
            # Similar approach but adjusted for Aldi Nord's page structure
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))

            for link in pdf_links:
                href = link.get('href')
                if not href.startswith('http'):
                    href = f"https://www.aldi-nord.de{href}"

                title = link.get_text(strip=True) or link.get('title', 'Aldi Nord Prospekt')

                brochures.append({
                    'url': href,
                    'title': title,
                    'type': 'pdf',
                    'valid_from': None,
                    'valid_to': None
                })

        # If no PDFs found via parsing, try alternative methods
        if not brochures:
            self.logger.warning("No PDFs found via parsing. You may need to inspect the website structure manually.")
            # Could add Selenium-based scraping here for dynamic content

        return brochures

    def download_brochure(self, brochure_info: Dict[str, str]) -> bool:
        """
        Download a single Aldi brochure.

        Args:
            brochure_info: Dictionary with brochure information

        Returns:
            True if successful, False otherwise
        """
        url = brochure_info['url']
        title = brochure_info['title']

        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.pdf"

        output_path = self.pdf_dir / filename

        # Download the file
        success = self.download_file(url, output_path)

        if success:
            # Save metadata for this brochure
            metadata = {
                'filename': filename,
                'original_url': url,
                'title': title,
                'download_date': datetime.now().isoformat(),
                'supermarket': self.supermarket_name,
                'valid_from': brochure_info.get('valid_from'),
                'valid_to': brochure_info.get('valid_to'),
                'file_size_bytes': output_path.stat().st_size
            }

            metadata_filename = f"{Path(filename).stem}.json"
            self.save_metadata(metadata, metadata_filename)

        return success


class AldiSuedScraper(AldiScraper):
    """Convenience class for Aldi Süd."""
    def __init__(self, **kwargs):
        super().__init__(variant="sued", **kwargs)


class AldiNordScraper(AldiScraper):
    """Convenience class for Aldi Nord."""
    def __init__(self, **kwargs):
        super().__init__(variant="nord", **kwargs)

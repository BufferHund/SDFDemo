"""
REWE Supermarket Brochure Scraper
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from .base_scraper import BaseScraper


class ReweScraper(BaseScraper):
    """
    Scraper for REWE brochures.

    REWE brochures are location-specific and may require market ID.
    URL pattern: https://www.rewe.de/angebote
    """

    def __init__(self, market_id: Optional[str] = None, **kwargs):
        """
        Initialize REWE scraper.

        Args:
            market_id: Optional REWE market ID for location-specific offers
            **kwargs: Additional arguments passed to BaseScraper
        """
        self.market_id = market_id

        if market_id:
            base_url = f"https://www.rewe.de/angebote?marketId={market_id}"
        else:
            base_url = "https://www.rewe.de/angebote"

        super().__init__(
            supermarket_name="rewe",
            base_url=base_url,
            **kwargs
        )

    def get_brochure_urls(self) -> List[Dict[str, str]]:
        """
        Get list of brochure URLs from REWE website.

        Returns:
            List of dictionaries with brochure information
        """
        brochures = []

        # Fetch main page
        soup = self.fetch_page(self.base_url)
        if not soup:
            self.logger.error("Failed to fetch main page")
            return brochures

        # Look for brochure/flyer links
        # REWE may have PDF links or image-based brochures
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))

        for link in pdf_links:
            href = link.get('href')
            if not href.startswith('http'):
                href = f"https://www.rewe.de{href}"

            title = link.get_text(strip=True) or link.get('title', 'REWE Angebote')

            # Try to extract validity dates from nearby text
            valid_from, valid_to = self._extract_dates(link.parent.get_text() if link.parent else '')

            brochures.append({
                'url': href,
                'title': title,
                'type': 'pdf',
                'valid_from': valid_from,
                'valid_to': valid_to
            })

        # Also look for image-based brochures
        img_containers = soup.find_all(['div', 'article'], class_=re.compile(r'(flyer|brochure|angebot)', re.IGNORECASE))

        for container in img_containers:
            # Look for images
            img = container.find('img')
            if img:
                src = img.get('src') or img.get('data-src')
                if src:
                    if not src.startswith('http'):
                        src = f"https://www.rewe.de{src}"

                    title = img.get('alt') or container.get_text(strip=True) or 'REWE Angebote'
                    valid_from, valid_to = self._extract_dates(container.get_text())

                    brochures.append({
                        'url': src,
                        'title': title,
                        'type': 'image',
                        'valid_from': valid_from,
                        'valid_to': valid_to
                    })

        if not brochures:
            self.logger.warning("No brochures found. REWE website may have changed structure or require JavaScript rendering.")

        return brochures

    def _extract_dates(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract validity dates from text.

        Args:
            text: Text that may contain dates

        Returns:
            Tuple of (valid_from, valid_to) as ISO date strings or None
        """
        # Common German date patterns
        # e.g., "Gültig von 30.10. bis 04.11.2024"
        date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})?'
        matches = re.findall(date_pattern, text)

        if len(matches) >= 2:
            # First date is valid_from
            day1, month1, year1 = matches[0]
            day2, month2, year2 = matches[1]

            # If year is missing, use current year
            current_year = datetime.now().year
            year1 = year1 or str(current_year)
            year2 = year2 or str(current_year)

            try:
                valid_from = f"{year1}-{month1.zfill(2)}-{day1.zfill(2)}"
                valid_to = f"{year2}-{month2.zfill(2)}-{day2.zfill(2)}"
                return valid_from, valid_to
            except ValueError:
                pass

        return None, None

    def download_brochure(self, brochure_info: Dict[str, str]) -> bool:
        """
        Download a single REWE brochure.

        Args:
            brochure_info: Dictionary with brochure information

        Returns:
            True if successful, False otherwise
        """
        url = brochure_info['url']
        title = brochure_info['title']
        file_type = brochure_info['type']

        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Determine extension
        if file_type == 'pdf':
            extension = '.pdf'
            output_dir = self.pdf_dir
        else:
            # Detect image extension from URL
            if '.jpg' in url.lower() or '.jpeg' in url.lower():
                extension = '.jpg'
            elif '.png' in url.lower():
                extension = '.png'
            else:
                extension = '.jpg'  # default
            output_dir = self.image_dir

        filename = f"{safe_title}_{timestamp}{extension}"
        output_path = output_dir / filename

        # Download the file
        success = self.download_file(url, output_path)

        if success:
            # Save metadata
            metadata = {
                'filename': filename,
                'original_url': url,
                'title': title,
                'download_date': datetime.now().isoformat(),
                'supermarket': self.supermarket_name,
                'market_id': self.market_id,
                'valid_from': brochure_info.get('valid_from'),
                'valid_to': brochure_info.get('valid_to'),
                'file_size_bytes': output_path.stat().st_size,
                'file_type': file_type
            }

            metadata_filename = f"{Path(filename).stem}.json"
            self.save_metadata(metadata, metadata_filename)

        return success

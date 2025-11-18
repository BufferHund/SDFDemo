"""
Edeka Supermarket Brochure Scraper
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from .base_scraper import BaseScraper


class EdekaScraper(BaseScraper):
    """
    Scraper for Edeka brochures.

    Edeka provides market-specific brochures.
    Each market has its own page with local offers.
    """

    def __init__(self, market_url: Optional[str] = None, **kwargs):
        """
        Initialize Edeka scraper.

        Args:
            market_url: URL of a specific Edeka market
                       e.g., "https://www.edeka.de/eh/s%C3%BCdwest/edeka-walter/..."
            **kwargs: Additional arguments for BaseScraper
        """
        self.market_url = market_url

        if market_url:
            base_url = market_url
        else:
            base_url = "https://www.edeka.de/"

        super().__init__(
            supermarket_name="edeka",
            base_url=base_url,
            **kwargs
        )

    def get_brochure_urls(self) -> List[Dict[str, str]]:
        """
        Get list of brochure URLs from Edeka website.

        Returns:
            List of dictionaries with brochure information
        """
        brochures = []

        # Fetch main page or market page
        soup = self.fetch_page(self.base_url)
        if not soup:
            self.logger.error("Failed to fetch main page")
            return brochures

        # Look for "Prospekte" or "Angebote" links
        prospekt_links = soup.find_all(
            'a',
            href=re.compile(r'(prospekt|angebot|handzettel)', re.IGNORECASE)
        )

        for link in prospekt_links:
            href = link.get('href')
            if not href:
                continue

            if not href.startswith('http'):
                href = f"https://www.edeka.de{href}"

            # Get title
            title = link.get_text(strip=True) or 'Edeka Angebote'

            # Visit the link to find actual brochures
            brochure_page = self.fetch_page(href)
            if brochure_page:
                # Look for PDF links
                pdf_links = brochure_page.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))

                for pdf_link in pdf_links:
                    pdf_href = pdf_link.get('href')
                    if not pdf_href.startswith('http'):
                        pdf_href = f"https://www.edeka.de{pdf_href}"

                    pdf_title = pdf_link.get_text(strip=True) or title

                    brochures.append({
                        'url': pdf_href,
                        'title': pdf_title,
                        'type': 'pdf',
                        'valid_from': None,
                        'valid_to': None
                    })

                # Also look for image-based brochures
                img_containers = brochure_page.find_all(
                    ['div', 'article'],
                    class_=re.compile(r'(flyer|brochure|prospekt)', re.IGNORECASE)
                )

                for container in img_containers:
                    img = container.find('img')
                    if img:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            if not src.startswith('http'):
                                src = f"https://www.edeka.de{src}"

                            img_title = img.get('alt') or title

                            brochures.append({
                                'url': src,
                                'title': img_title,
                                'type': 'image',
                                'valid_from': None,
                                'valid_to': None
                            })

        if not brochures:
            self.logger.warning(
                "No brochures found. Edeka website may require JavaScript or "
                "a specific market URL. Try providing a market_url parameter."
            )

        return brochures

    def download_brochure(self, brochure_info: Dict[str, str]) -> bool:
        """
        Download a single Edeka brochure.

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

        # Determine extension and output directory
        if file_type == 'pdf':
            extension = '.pdf'
            output_dir = self.pdf_dir
        else:
            # Detect image extension from URL
            if '.png' in url.lower():
                extension = '.png'
            elif '.webp' in url.lower():
                extension = '.webp'
            else:
                extension = '.jpg'
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
                'market_url': self.market_url,
                'valid_from': brochure_info.get('valid_from'),
                'valid_to': brochure_info.get('valid_to'),
                'file_size_bytes': output_path.stat().st_size,
                'file_type': file_type
            }

            metadata_filename = f"{Path(filename).stem}.json"
            self.save_metadata(metadata, metadata_filename)

        return success


def scrape_multiple_markets(market_urls: List[str], **kwargs) -> List[Dict]:
    """
    Scrape brochures from multiple Edeka markets.

    Args:
        market_urls: List of Edeka market URLs
        **kwargs: Additional arguments for EdekaScraper

    Returns:
        List of summary dictionaries
    """
    summaries = []

    for market_url in market_urls:
        scraper = EdekaScraper(market_url=market_url, **kwargs)
        summary = scraper.run()
        summaries.append(summary)
        scraper.close()

    return summaries

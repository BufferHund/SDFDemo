"""
Lidl Supermarket Brochure Scraper
"""

import re
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from .base_scraper import BaseScraper


class LidlScraper(BaseScraper):
    """
    Scraper for Lidl brochures.

    Lidl provides digital brochures on their website.
    URL: https://www.lidl.de/l/prospekte
    """

    def __init__(self, **kwargs):
        """Initialize Lidl scraper."""
        base_url = "https://www.lidl.de/l/prospekte"

        super().__init__(
            supermarket_name="lidl",
            base_url=base_url,
            **kwargs
        )

    def get_brochure_urls(self) -> List[Dict[str, str]]:
        """
        Get list of brochure URLs from Lidl website.

        Returns:
            List of dictionaries with brochure information
        """
        brochures = []

        # Fetch main prospekte page
        soup = self.fetch_page(self.base_url)
        if not soup:
            self.logger.error("Failed to fetch main page")
            return brochures

        # Look for brochure/flyer containers
        # Lidl uses dynamic loading, so we may need Selenium for full functionality
        # For now, try to find static content

        # Look for links to brochure pages
        brochure_links = soup.find_all('a', href=re.compile(r'/l/prospekte/.*'))

        for link in brochure_links:
            href = link.get('href')
            if not href:
                continue

            if not href.startswith('http'):
                href = f"https://www.lidl.de{href}"

            # Get title
            title_elem = link.find(['h2', 'h3', 'h4', 'span'])
            title = title_elem.get_text(strip=True) if title_elem else 'Lidl Prospekt'

            # Try to extract dates from href or nearby text
            valid_from, valid_to = self._extract_dates_from_url(href)

            # Check if this is a detail page we should visit
            if '/view/' in href or '/page/' in href:
                # This is a viewer page - need to extract images
                images = self._extract_images_from_viewer(href)
                for i, img_url in enumerate(images):
                    brochures.append({
                        'url': img_url,
                        'title': f"{title} - Page {i+1}",
                        'type': 'image',
                        'valid_from': valid_from,
                        'valid_to': valid_to
                    })
            else:
                # Try to find PDF link
                pdf_url = self._find_pdf_link(href)
                if pdf_url:
                    brochures.append({
                        'url': pdf_url,
                        'title': title,
                        'type': 'pdf',
                        'valid_from': valid_from,
                        'valid_to': valid_to
                    })

        if not brochures:
            self.logger.warning(
                "No brochures found. Lidl website may require JavaScript rendering. "
                "Consider using Selenium for dynamic content."
            )

        return brochures

    def _extract_images_from_viewer(self, viewer_url: str) -> List[str]:
        """
        Extract image URLs from brochure viewer page.

        Args:
            viewer_url: URL of the viewer page

        Returns:
            List of image URLs
        """
        images = []

        soup = self.fetch_page(viewer_url)
        if not soup:
            return images

        # Look for image tags in the viewer
        img_tags = soup.find_all('img', src=re.compile(r'\.(jpg|jpeg|png|webp)', re.IGNORECASE))

        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and 'prospekt' in src.lower():
                if not src.startswith('http'):
                    src = f"https://www.lidl.de{src}"
                images.append(src)

        return images

    def _find_pdf_link(self, page_url: str) -> str:
        """
        Find PDF download link on a brochure page.

        Args:
            page_url: URL of the brochure page

        Returns:
            PDF URL or None
        """
        soup = self.fetch_page(page_url)
        if not soup:
            return None

        # Look for PDF download link
        pdf_link = soup.find('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        if pdf_link:
            href = pdf_link.get('href')
            if not href.startswith('http'):
                href = f"https://www.lidl.de{href}"
            return href

        return None

    def _extract_dates_from_url(self, url: str) -> tuple:
        """
        Extract dates from URL pattern.

        Lidl URLs often contain date information:
        e.g., /prospekte/aktionsprospekt-01-11-2024-07-11-2024/

        Args:
            url: URL string

        Returns:
            Tuple of (valid_from, valid_to) as ISO date strings
        """
        # Pattern: DD-MM-YYYY-DD-MM-YYYY
        pattern = r'(\d{2})-(\d{2})-(\d{4})-(\d{2})-(\d{2})-(\d{4})'
        match = re.search(pattern, url)

        if match:
            try:
                day1, month1, year1 = match.group(1), match.group(2), match.group(3)
                day2, month2, year2 = match.group(4), match.group(5), match.group(6)

                valid_from = f"{year1}-{month1}-{day1}"
                valid_to = f"{year2}-{month2}-{day2}"

                return valid_from, valid_to
            except (ValueError, IndexError):
                pass

        return None, None

    def download_brochure(self, brochure_info: Dict[str, str]) -> bool:
        """
        Download a single Lidl brochure.

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
            # Determine image extension from URL
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
                'valid_from': brochure_info.get('valid_from'),
                'valid_to': brochure_info.get('valid_to'),
                'file_size_bytes': output_path.stat().st_size,
                'file_type': file_type
            }

            metadata_filename = f"{Path(filename).stem}.json"
            self.save_metadata(metadata, metadata_filename)

        return success

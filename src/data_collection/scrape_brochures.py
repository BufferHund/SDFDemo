"""
Command-line tool for scraping supermarket brochures.

Usage:
    python scrape_brochures.py --supermarket aldi_sued
    python scrape_brochures.py --supermarket aldi_nord
    python scrape_brochures.py --supermarket rewe --market-id 123456
    python scrape_brochures.py --all
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_collection.aldi_scraper import AldiSuedScraper, AldiNordScraper
from src.data_collection.rewe_scraper import ReweScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def scrape_aldi_sued(output_dir: str):
    """Scrape Aldi Süd brochures."""
    logger.info("Starting Aldi Süd scraper")
    with AldiSuedScraper(output_dir=output_dir) as scraper:
        summary = scraper.run()
        logger.info(f"Aldi Süd summary: {summary}")
        return summary


def scrape_aldi_nord(output_dir: str):
    """Scrape Aldi Nord brochures."""
    logger.info("Starting Aldi Nord scraper")
    with AldiNordScraper(output_dir=output_dir) as scraper:
        summary = scraper.run()
        logger.info(f"Aldi Nord summary: {summary}")
        return summary


def scrape_rewe(output_dir: str, market_id: str = None):
    """Scrape REWE brochures."""
    logger.info(f"Starting REWE scraper (market_id: {market_id})")
    with ReweScraper(market_id=market_id, output_dir=output_dir) as scraper:
        summary = scraper.run()
        logger.info(f"REWE summary: {summary}")
        return summary


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Scrape supermarket brochures from various retailers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape Aldi Süd brochures
  python scrape_brochures.py --supermarket aldi_sued

  # Scrape REWE brochures for a specific market
  python scrape_brochures.py --supermarket rewe --market-id 123456

  # Scrape all supermarkets
  python scrape_brochures.py --all

  # Custom output directory
  python scrape_brochures.py --supermarket aldi_sued --output-dir /path/to/data
        """
    )

    parser.add_argument(
        '--supermarket',
        type=str,
        choices=['aldi_sued', 'aldi_nord', 'rewe'],
        help='Supermarket to scrape'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Scrape all available supermarkets'
    )

    parser.add_argument(
        '--market-id',
        type=str,
        help='Market ID for REWE (optional, location-specific offers)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw',
        help='Output directory for downloaded brochures (default: data/raw)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if not args.all and not args.supermarket:
        parser.error("Either --supermarket or --all must be specified")

    # Run scrapers
    summaries = []

    if args.all or args.supermarket == 'aldi_sued':
        try:
            summary = scrape_aldi_sued(args.output_dir)
            summaries.append(summary)
        except Exception as e:
            logger.error(f"Failed to scrape Aldi Süd: {e}", exc_info=True)

    if args.all or args.supermarket == 'aldi_nord':
        try:
            summary = scrape_aldi_nord(args.output_dir)
            summaries.append(summary)
        except Exception as e:
            logger.error(f"Failed to scrape Aldi Nord: {e}", exc_info=True)

    if args.all or args.supermarket == 'rewe':
        try:
            summary = scrape_rewe(args.output_dir, args.market_id)
            summaries.append(summary)
        except Exception as e:
            logger.error(f"Failed to scrape REWE: {e}", exc_info=True)

    # Print final summary
    logger.info("=" * 80)
    logger.info("SCRAPING COMPLETE")
    logger.info("=" * 80)

    total_brochures = sum(s.get('total_brochures', 0) for s in summaries)
    total_successful = sum(s.get('successful_downloads', 0) for s in summaries)
    total_failed = sum(s.get('failed_downloads', 0) for s in summaries)

    logger.info(f"Total brochures found: {total_brochures}")
    logger.info(f"Successfully downloaded: {total_successful}")
    logger.info(f"Failed downloads: {total_failed}")

    return 0 if total_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

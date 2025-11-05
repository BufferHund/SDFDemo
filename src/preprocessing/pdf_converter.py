"""
PDF to Image Converter for Brochures
"""

import logging
from pathlib import Path
from typing import List, Optional, Union
from pdf2image import convert_from_path
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFConverter:
    """
    Convert PDF brochures to images for processing.

    This class handles conversion of multi-page PDFs into individual
    image files suitable for OCR and model training.
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = "data/processed/images",
        dpi: int = 300,
        fmt: str = "png"
    ):
        """
        Initialize PDF converter.

        Args:
            output_dir: Directory to save converted images
            dpi: Resolution in dots per inch (higher = better quality but larger files)
            fmt: Output format (png, jpg, jpeg)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        self.fmt = fmt.lower()

        if self.fmt not in ['png', 'jpg', 'jpeg']:
            raise ValueError(f"Unsupported format: {fmt}")

        logger.info(f"Initialized PDFConverter (dpi={dpi}, format={fmt})")

    def convert_pdf(
        self,
        pdf_path: Union[str, Path],
        output_prefix: Optional[str] = None
    ) -> List[Path]:
        """
        Convert a single PDF to images.

        Args:
            pdf_path: Path to the PDF file
            output_prefix: Optional prefix for output filenames.
                          If None, uses the PDF filename.

        Returns:
            List of paths to the created image files
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return []

        if output_prefix is None:
            output_prefix = pdf_path.stem

        logger.info(f"Converting {pdf_path} to images...")

        try:
            # Convert PDF to list of PIL Images
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                fmt=self.fmt
            )

            logger.info(f"Extracted {len(images)} page(s) from {pdf_path}")

            # Save each page as separate image
            output_paths = []

            for i, image in enumerate(images, 1):
                # Create filename: prefix_page001.png
                filename = f"{output_prefix}_page{i:03d}.{self.fmt}"
                output_path = self.output_dir / filename

                # Save image
                image.save(output_path, self.fmt.upper())
                logger.debug(f"Saved page {i} to {output_path}")

                output_paths.append(output_path)

            logger.info(f"Successfully converted {pdf_path} to {len(output_paths)} images")
            return output_paths

        except Exception as e:
            logger.error(f"Failed to convert {pdf_path}: {e}", exc_info=True)
            return []

    def convert_directory(
        self,
        input_dir: Union[str, Path],
        recursive: bool = False
    ) -> dict:
        """
        Convert all PDFs in a directory to images.

        Args:
            input_dir: Directory containing PDF files
            recursive: If True, search subdirectories recursively

        Returns:
            Dictionary with conversion summary:
                - total_pdfs: Number of PDFs found
                - successful: Number of successfully converted PDFs
                - failed: Number of failed conversions
                - total_images: Total number of images created
        """
        input_dir = Path(input_dir)

        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return {'total_pdfs': 0, 'successful': 0, 'failed': 0, 'total_images': 0}

        # Find all PDF files
        if recursive:
            pdf_files = list(input_dir.rglob("*.pdf"))
        else:
            pdf_files = list(input_dir.glob("*.pdf"))

        logger.info(f"Found {len(pdf_files)} PDF file(s) in {input_dir}")

        successful = 0
        failed = 0
        total_images = 0

        for pdf_path in pdf_files:
            logger.info(f"Processing {pdf_path.name}...")
            output_paths = self.convert_pdf(pdf_path)

            if output_paths:
                successful += 1
                total_images += len(output_paths)
            else:
                failed += 1

        summary = {
            'total_pdfs': len(pdf_files),
            'successful': successful,
            'failed': failed,
            'total_images': total_images
        }

        logger.info("Conversion complete:")
        logger.info(f"  Total PDFs: {summary['total_pdfs']}")
        logger.info(f"  Successful: {summary['successful']}")
        logger.info(f"  Failed: {summary['failed']}")
        logger.info(f"  Total images: {summary['total_images']}")

        return summary

    def convert_single_page(
        self,
        pdf_path: Union[str, Path],
        page_number: int,
        output_path: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Convert a single page from a PDF to an image.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to convert (1-indexed)
            output_path: Optional output path. If None, auto-generated.

        Returns:
            Path to the created image or None if failed
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None

        try:
            # Convert specific page
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                first_page=page_number,
                last_page=page_number
            )

            if not images:
                logger.error(f"Failed to extract page {page_number} from {pdf_path}")
                return None

            image = images[0]

            # Determine output path
            if output_path is None:
                filename = f"{pdf_path.stem}_page{page_number:03d}.{self.fmt}"
                output_path = self.output_dir / filename
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save image
            image.save(output_path, self.fmt.upper())
            logger.info(f"Saved page {page_number} to {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Failed to convert page {page_number} from {pdf_path}: {e}", exc_info=True)
            return None


def main():
    """Command-line interface for PDF conversion."""
    import argparse

    parser = argparse.ArgumentParser(description='Convert PDF brochures to images')
    parser.add_argument('input', help='Input PDF file or directory')
    parser.add_argument('--output-dir', default='data/processed/images',
                        help='Output directory for images')
    parser.add_argument('--dpi', type=int, default=300,
                        help='Resolution in DPI (default: 300)')
    parser.add_argument('--format', choices=['png', 'jpg', 'jpeg'], default='png',
                        help='Output image format')
    parser.add_argument('--recursive', action='store_true',
                        help='Process subdirectories recursively')
    parser.add_argument('--page', type=int,
                        help='Convert only specific page number')

    args = parser.parse_args()

    converter = PDFConverter(
        output_dir=args.output_dir,
        dpi=args.dpi,
        fmt=args.format
    )

    input_path = Path(args.input)

    if input_path.is_file():
        if args.page:
            converter.convert_single_page(input_path, args.page)
        else:
            converter.convert_pdf(input_path)
    elif input_path.is_dir():
        converter.convert_directory(input_path, recursive=args.recursive)
    else:
        logger.error(f"Invalid input: {input_path}")
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

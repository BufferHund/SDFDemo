"""
Image Processor for Brochure Standardization
"""

import logging
from pathlib import Path
from typing import Union, Tuple, Optional
from PIL import Image, ImageEnhance
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Process and standardize brochure images.

    This class handles image preprocessing tasks such as:
    - Resizing to standard dimensions
    - Normalization
    - Contrast/brightness enhancement
    - Noise reduction
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (1024, 1448),
        output_dir: Union[str, Path] = "data/processed/images"
    ):
        """
        Initialize image processor.

        Args:
            target_size: Target (width, height) for standardized images
            output_dir: Directory to save processed images
        """
        self.target_size = target_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized ImageProcessor (target_size={target_size})")

    def resize_image(
        self,
        image: Image.Image,
        maintain_aspect_ratio: bool = True
    ) -> Image.Image:
        """
        Resize image to target size.

        Args:
            image: PIL Image object
            maintain_aspect_ratio: If True, maintains aspect ratio and pads

        Returns:
            Resized PIL Image
        """
        if maintain_aspect_ratio:
            # Calculate aspect ratios
            img_aspect = image.width / image.height
            target_aspect = self.target_size[0] / self.target_size[1]

            if img_aspect > target_aspect:
                # Image is wider than target
                new_width = self.target_size[0]
                new_height = int(new_width / img_aspect)
            else:
                # Image is taller than target
                new_height = self.target_size[1]
                new_width = int(new_height * img_aspect)

            # Resize
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create padded image
            padded = Image.new('RGB', self.target_size, (255, 255, 255))
            paste_x = (self.target_size[0] - new_width) // 2
            paste_y = (self.target_size[1] - new_height) // 2
            padded.paste(resized, (paste_x, paste_y))

            return padded
        else:
            # Direct resize without maintaining aspect ratio
            return image.resize(self.target_size, Image.Resampling.LANCZOS)

    def enhance_contrast(
        self,
        image: Image.Image,
        factor: float = 1.5
    ) -> Image.Image:
        """
        Enhance image contrast.

        Args:
            image: PIL Image object
            factor: Enhancement factor (1.0 = no change, >1.0 = increase contrast)

        Returns:
            Enhanced PIL Image
        """
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    def enhance_sharpness(
        self,
        image: Image.Image,
        factor: float = 1.2
    ) -> Image.Image:
        """
        Enhance image sharpness.

        Args:
            image: PIL Image object
            factor: Enhancement factor (1.0 = no change, >1.0 = sharper)

        Returns:
            Enhanced PIL Image
        """
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)

    def normalize_brightness(
        self,
        image: Image.Image,
        target_brightness: float = 128.0
    ) -> Image.Image:
        """
        Normalize image brightness.

        Args:
            image: PIL Image object
            target_brightness: Target average brightness (0-255)

        Returns:
            Normalized PIL Image
        """
        # Convert to numpy array
        img_array = np.array(image)

        # Calculate current brightness
        current_brightness = img_array.mean()

        # Calculate adjustment factor
        factor = target_brightness / current_brightness

        # Apply adjustment
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    def process_image(
        self,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        enhance: bool = True,
        maintain_aspect_ratio: bool = True
    ) -> Optional[Path]:
        """
        Process a single image with all standardization steps.

        Args:
            image_path: Path to input image
            output_path: Optional output path. If None, auto-generated.
            enhance: Whether to apply contrast/sharpness enhancement
            maintain_aspect_ratio: Whether to maintain aspect ratio when resizing

        Returns:
            Path to processed image or None if failed
        """
        image_path = Path(image_path)

        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return None

        try:
            # Load image
            image = Image.open(image_path)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize
            image = self.resize_image(image, maintain_aspect_ratio)

            # Apply enhancements
            if enhance:
                image = self.enhance_contrast(image, factor=1.3)
                image = self.enhance_sharpness(image, factor=1.2)

            # Determine output path
            if output_path is None:
                filename = f"processed_{image_path.name}"
                output_path = self.output_dir / filename
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save processed image
            image.save(output_path, quality=95)
            logger.info(f"Processed {image_path.name} -> {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Failed to process {image_path}: {e}", exc_info=True)
            return None

    def process_directory(
        self,
        input_dir: Union[str, Path],
        recursive: bool = False,
        enhance: bool = True
    ) -> dict:
        """
        Process all images in a directory.

        Args:
            input_dir: Directory containing images
            recursive: If True, process subdirectories recursively
            enhance: Whether to apply enhancements

        Returns:
            Dictionary with processing summary
        """
        input_dir = Path(input_dir)

        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return {'total': 0, 'successful': 0, 'failed': 0}

        # Find all image files
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']
        image_files = []

        for ext in image_extensions:
            if recursive:
                image_files.extend(input_dir.rglob(ext))
            else:
                image_files.extend(input_dir.glob(ext))

        logger.info(f"Found {len(image_files)} image(s) in {input_dir}")

        successful = 0
        failed = 0

        for image_path in image_files:
            result = self.process_image(image_path, enhance=enhance)
            if result:
                successful += 1
            else:
                failed += 1

        summary = {
            'total': len(image_files),
            'successful': successful,
            'failed': failed
        }

        logger.info("Processing complete:")
        logger.info(f"  Total images: {summary['total']}")
        logger.info(f"  Successful: {summary['successful']}")
        logger.info(f"  Failed: {summary['failed']}")

        return summary

    def batch_process(
        self,
        image_paths: list,
        enhance: bool = True
    ) -> list:
        """
        Process a batch of images.

        Args:
            image_paths: List of image paths
            enhance: Whether to apply enhancements

        Returns:
            List of output paths for successfully processed images
        """
        output_paths = []

        for image_path in image_paths:
            result = self.process_image(image_path, enhance=enhance)
            if result:
                output_paths.append(result)

        return output_paths


def main():
    """Command-line interface for image processing."""
    import argparse

    parser = argparse.ArgumentParser(description='Process and standardize brochure images')
    parser.add_argument('input', help='Input image file or directory')
    parser.add_argument('--output-dir', default='data/processed/images',
                        help='Output directory for processed images')
    parser.add_argument('--width', type=int, default=1024,
                        help='Target width (default: 1024)')
    parser.add_argument('--height', type=int, default=1448,
                        help='Target height (default: 1448)')
    parser.add_argument('--no-enhance', action='store_true',
                        help='Disable contrast/sharpness enhancement')
    parser.add_argument('--no-aspect-ratio', action='store_true',
                        help='Do not maintain aspect ratio')
    parser.add_argument('--recursive', action='store_true',
                        help='Process subdirectories recursively')

    args = parser.parse_args()

    processor = ImageProcessor(
        target_size=(args.width, args.height),
        output_dir=args.output_dir
    )

    input_path = Path(args.input)

    if input_path.is_file():
        processor.process_image(
            input_path,
            enhance=not args.no_enhance,
            maintain_aspect_ratio=not args.no_aspect_ratio
        )
    elif input_path.is_dir():
        processor.process_directory(
            input_path,
            recursive=args.recursive,
            enhance=not args.no_enhance
        )
    else:
        logger.error(f"Invalid input: {input_path}")
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

"""
Core Pipeline for End-to-End Brochure Processing

Complete workflow:
1. Load/Download → 2. Preprocess → 3. OCR/VLM → 4. Extract Entities → 5. Save Results
"""

import logging
from dataclasses import dataclass, field
from typing import Union, List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import json
import time
from enum import Enum

from PIL import Image

# Import stages
from ..preprocessing.pdf_converter import PDFConverter
from ..preprocessing.image_processor import ImageProcessor
from ..models.ocr_engine import create_ocr_engine
from ..models.vlm_engine import create_vlm_engine
from ..models.entity_extractor import EntityExtractor, Deal
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ProcessingMethod(Enum):
    """Processing method options."""
    OCR = "ocr"
    VLM = "vlm"
    HYBRID = "hybrid"


@dataclass
class PipelineConfig:
    """Pipeline configuration."""

    # Processing method
    method: ProcessingMethod = ProcessingMethod.HYBRID

    # OCR settings
    ocr_engine: str = "paddleocr"
    ocr_languages: List[str] = field(default_factory=lambda: ["de", "en"])
    ocr_use_gpu: bool = False

    # VLM settings
    vlm_engine: str = "ollama"
    vlm_model: str = "llava:latest"
    vlm_api_key: Optional[str] = None

    # Preprocessing settings
    preprocess_images: bool = True
    target_size: tuple = (1024, 1448)
    enhance_images: bool = True

    # Output settings
    output_dir: str = "outputs/pipeline"
    save_intermediate: bool = False
    save_visualizations: bool = True

    # Performance
    batch_size: int = 1
    max_workers: int = 4

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        config = {
            'method': self.method.value,
            'ocr_engine': self.ocr_engine,
            'ocr_languages': self.ocr_languages,
            'ocr_use_gpu': self.ocr_use_gpu,
            'vlm_engine': self.vlm_engine,
            'vlm_model': self.vlm_model,
            'preprocess_images': self.preprocess_images,
            'target_size': self.target_size,
            'enhance_images': self.enhance_images,
            'output_dir': self.output_dir,
            'save_intermediate': self.save_intermediate,
            'save_visualizations': self.save_visualizations,
            'batch_size': self.batch_size,
            'max_workers': self.max_workers
        }
        return config


@dataclass
class PipelineResult:
    """Result of pipeline processing."""

    input_path: str
    success: bool
    processing_time: float

    # Intermediate results
    preprocessed_image: Optional[Path] = None
    ocr_results: Optional[List[Dict]] = None
    vlm_results: Optional[Dict] = None

    # Final results
    deals: List[Dict] = field(default_factory=list)

    # Metadata
    method: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'input_path': self.input_path,
            'success': self.success,
            'processing_time': self.processing_time,
            'preprocessed_image': str(self.preprocessed_image) if self.preprocessed_image else None,
            'num_ocr_regions': len(self.ocr_results) if self.ocr_results else 0,
            'deals': self.deals,
            'method': self.method,
            'timestamp': self.timestamp,
            'error': self.error
        }

    def save(self, output_path: Union[str, Path]):
        """Save result to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Result saved to {output_path}")


class BrochurePipeline:
    """
    End-to-end pipeline for brochure processing.

    Pipeline stages:
    1. Input validation and loading
    2. PDF to image conversion (if needed)
    3. Image preprocessing and enhancement
    4. Text extraction (OCR/VLM/Hybrid)
    5. Entity extraction and structuring
    6. Result saving and visualization

    Example:
        >>> config = PipelineConfig(method=ProcessingMethod.HYBRID)
        >>> pipeline = BrochurePipeline(config)
        >>> result = pipeline.process('brochure.pdf')
        >>> print(f"Found {len(result.deals)} deals")
    """

    def __init__(self, config: PipelineConfig = None):
        """
        Initialize pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()

        # Create output directory
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self._init_components()

        logger.info(f"Pipeline initialized with method: {self.config.method.value}")

    def _init_components(self):
        """Initialize processing components."""

        # Preprocessing
        if self.config.preprocess_images:
            self.pdf_converter = PDFConverter(output_dir=self.output_dir / "temp")
            self.image_processor = ImageProcessor(
                target_size=self.config.target_size,
                output_dir=self.output_dir / "temp"
            )

        # OCR
        if self.config.method in [ProcessingMethod.OCR, ProcessingMethod.HYBRID]:
            self.ocr = create_ocr_engine(
                engine_type=self.config.ocr_engine,
                languages=self.config.ocr_languages,
                use_gpu=self.config.ocr_use_gpu,
                gpu=self.config.ocr_use_gpu
            )

        # VLM
        if self.config.method in [ProcessingMethod.VLM, ProcessingMethod.HYBRID]:
            vlm_kwargs = {}
            if self.config.vlm_api_key:
                vlm_kwargs['api_key'] = self.config.vlm_api_key

            self.vlm = create_vlm_engine(
                engine_type=self.config.vlm_engine,
                model_name=self.config.vlm_model,
                **vlm_kwargs
            )

        # Entity extractor
        self.entity_extractor = EntityExtractor()

    def process(
        self,
        input_path: Union[str, Path],
        output_name: str = None
    ) -> PipelineResult:
        """
        Process a single brochure through the complete pipeline.

        Args:
            input_path: Path to brochure (PDF or image)
            output_name: Optional custom output name

        Returns:
            PipelineResult with extracted information
        """
        start_time = time.time()
        input_path = Path(input_path)

        logger.info(f"Processing: {input_path}")

        try:
            # Stage 1: Load and validate
            image = self._load_image(input_path)

            # Stage 2: Preprocess
            if self.config.preprocess_images:
                image = self._preprocess_image(image)

            # Stage 3: Extract information
            ocr_results = None
            vlm_results = None

            if self.config.method == ProcessingMethod.OCR:
                ocr_results = self._extract_ocr(image)
                deals = self._extract_entities_from_ocr(ocr_results)

            elif self.config.method == ProcessingMethod.VLM:
                vlm_results = self._extract_vlm(image)
                deals = vlm_results.get('deals', [])

            else:  # HYBRID
                ocr_results = self._extract_ocr(image)
                vlm_results = self._extract_vlm(image)
                deals = self._merge_results(ocr_results, vlm_results)

            # Stage 4: Save results
            result = PipelineResult(
                input_path=str(input_path),
                success=True,
                processing_time=time.time() - start_time,
                ocr_results=ocr_results,
                vlm_results=vlm_results,
                deals=deals,
                method=self.config.method.value
            )

            # Save outputs
            self._save_results(result, output_name or input_path.stem)

            logger.info(f"✓ Processed {input_path.name}: {len(deals)} deals in {result.processing_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"✗ Failed to process {input_path}: {e}", exc_info=True)

            return PipelineResult(
                input_path=str(input_path),
                success=False,
                processing_time=time.time() - start_time,
                method=self.config.method.value,
                error=str(e)
            )

    def _load_image(self, path: Path) -> Image.Image:
        """Load image from file (handles PDF conversion)."""

        if path.suffix.lower() == '.pdf':
            logger.info("Converting PDF to image...")
            image_paths = self.pdf_converter.convert_pdf(path)

            if not image_paths:
                raise ValueError("Failed to convert PDF")

            # Use first page
            return Image.open(image_paths[0])

        else:
            return Image.open(path).convert('RGB')

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess and enhance image."""

        logger.info("Preprocessing image...")

        # Resize
        image = self.image_processor.resize_image(image)

        # Enhance
        if self.config.enhance_images:
            image = self.image_processor.enhance_contrast(image)
            image = self.image_processor.enhance_sharpness(image)

        return image

    def _extract_ocr(self, image: Image.Image) -> List[Dict]:
        """Extract text using OCR."""

        logger.info(f"Running OCR ({self.config.ocr_engine})...")
        results = self.ocr.extract_text(image)
        logger.info(f"OCR extracted {len(results)} text regions")

        return results

    def _extract_vlm(self, image: Image.Image) -> Dict:
        """Extract information using VLM."""

        logger.info(f"Running VLM ({self.config.vlm_engine}/{self.config.vlm_model})...")
        results = self.vlm.analyze_image(image)
        logger.info(f"VLM extracted {len(results.get('deals', []))} deals")

        return results

    def _extract_entities_from_ocr(self, ocr_results: List[Dict]) -> List[Dict]:
        """Extract structured entities from OCR results."""

        logger.info("Extracting entities from OCR...")
        deals = self.entity_extractor.extract_from_ocr(ocr_results)

        return [deal.to_dict() for deal in deals]

    def _merge_results(
        self,
        ocr_results: List[Dict],
        vlm_results: Dict
    ) -> List[Dict]:
        """Merge OCR and VLM results for best accuracy."""

        logger.info("Merging OCR and VLM results...")

        # Get OCR deals
        ocr_deals = self._extract_entities_from_ocr(ocr_results)

        # Get VLM deals
        vlm_deals = vlm_results.get('deals', [])

        # Strategy: Use VLM for semantic understanding,
        # OCR for precise locations

        # For now, prefer VLM deals if available, otherwise use OCR
        if vlm_deals:
            logger.info(f"Using {len(vlm_deals)} VLM deals (primary)")
            return vlm_deals
        else:
            logger.info(f"Using {len(ocr_deals)} OCR deals (fallback)")
            return ocr_deals

    def _save_results(self, result: PipelineResult, output_name: str):
        """Save pipeline results."""

        # Create output directory for this run
        run_dir = self.output_dir / output_name
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON result
        result.save(run_dir / "result.json")

        # Save deals separately
        deals_path = run_dir / "deals.json"
        with open(deals_path, 'w', encoding='utf-8') as f:
            json.dump(result.deals, f, indent=2, ensure_ascii=False)

        # Save visualization if requested
        if self.config.save_visualizations and result.success:
            self._save_visualization(result, run_dir)

    def _save_visualization(self, result: PipelineResult, output_dir: Path):
        """Create and save visualization."""

        try:
            from PIL import ImageDraw, ImageFont

            # Load original image
            image = Image.open(result.input_path)

            # Draw deals
            draw = ImageDraw.Draw(image)

            # Try to load font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()

            # Draw each deal
            for i, deal in enumerate(result.deals, 1):
                # Simple text overlay
                text = f"{i}. {deal.get('product_name', 'Unknown')}: €{deal.get('discounted_price', '?')}"
                y_pos = 10 + (i-1) * 30

                # Background
                bbox = draw.textbbox((10, y_pos), text, font=font)
                draw.rectangle(bbox, fill='black')

                # Text
                draw.text((10, y_pos), text, fill='yellow', font=font)

            # Save
            viz_path = output_dir / "visualization.png"
            image.save(viz_path)
            logger.info(f"Visualization saved to {viz_path}")

        except Exception as e:
            logger.warning(f"Failed to create visualization: {e}")

    def process_batch(
        self,
        input_paths: List[Union[str, Path]],
        show_progress: bool = True
    ) -> List[PipelineResult]:
        """
        Process multiple brochures.

        Args:
            input_paths: List of input paths
            show_progress: Show progress bar

        Returns:
            List of PipelineResults
        """
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(input_paths, desc="Processing brochures")
            except ImportError:
                iterator = input_paths
        else:
            iterator = input_paths

        for path in iterator:
            result = self.process(path)
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch complete: {successful}/{len(results)} successful")

        return results


def create_pipeline(
    method: str = "hybrid",
    **kwargs
) -> BrochurePipeline:
    """
    Factory function to create pipeline.

    Args:
        method: Processing method ('ocr', 'vlm', 'hybrid')
        **kwargs: Additional config parameters

    Returns:
        Configured BrochurePipeline

    Example:
        >>> pipeline = create_pipeline('hybrid', ocr_engine='paddleocr')
        >>> result = pipeline.process('brochure.pdf')
    """
    method_enum = ProcessingMethod(method.lower())
    config = PipelineConfig(method=method_enum, **kwargs)
    return BrochurePipeline(config)

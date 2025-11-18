"""
Enhanced Pipeline with Advanced Features

New features:
- Integrated logging with enhanced_logger
- Performance monitoring
- Input/output validation
- Error recovery mechanisms
- Retry logic
- Caching
"""

import time
from pathlib import Path
from typing import Union, Optional
from datetime import datetime
import hashlib
import pickle

from .pipeline import BrochurePipeline, PipelineConfig, PipelineResult, ProcessingMethod
from .validator import InputValidator, OutputValidator
from .monitor import PipelineMonitor, BottleneckDetector
from ..utils.enhanced_logger import get_logger


class EnhancedPipeline(BrochurePipeline):
    """
    Enhanced pipeline with advanced features.

    Features:
    - Structured logging
    - Performance monitoring
    - Input validation
    - Output validation
    - Error recovery
    - Retry logic
    - Result caching
    """

    def __init__(
        self,
        config: PipelineConfig = None,
        enable_monitoring: bool = True,
        enable_validation: bool = True,
        enable_caching: bool = False,
        max_retries: int = 3,
        log_dir: str = "logs/pipeline"
    ):
        """
        Initialize enhanced pipeline.

        Args:
            config: Pipeline configuration
            enable_monitoring: Enable performance monitoring
            enable_validation: Enable input/output validation
            enable_caching: Enable result caching
            max_retries: Maximum retry attempts on failure
            log_dir: Directory for log files
        """
        super().__init__(config)

        # Enhanced logger
        self.logger = get_logger(
            name=f"pipeline.{config.method.value if config else 'default'}",
            log_dir=log_dir,
            enable_json=True,
            enable_color=True
        )

        # Features
        self.enable_monitoring = enable_monitoring
        self.enable_validation = enable_validation
        self.enable_caching = enable_caching
        self.max_retries = max_retries

        # Cache directory
        if self.enable_caching:
            self.cache_dir = Path(self.output_dir) / ".cache"
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            "Enhanced pipeline initialized",
            method=config.method.value if config else 'unknown',
            monitoring=enable_monitoring,
            validation=enable_validation,
            caching=enable_caching
        )

    def _get_cache_key(self, input_path: Path) -> str:
        """Generate cache key for input file."""
        # Use file path + modification time + config
        cache_data = f"{input_path}_{input_path.stat().st_mtime}_{self.config.to_dict()}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[PipelineResult]:
        """Load result from cache."""
        if not self.enable_caching:
            return None

        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    result = pickle.load(f)

                self.logger.info(f"Loaded result from cache: {cache_key}")
                return result

            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")

        return None

    def _save_to_cache(self, cache_key: str, result: PipelineResult):
        """Save result to cache."""
        if not self.enable_caching:
            return

        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            self.logger.debug(f"Saved result to cache: {cache_key}")

        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")

    def process(
        self,
        input_path: Union[str, Path],
        output_name: str = None
    ) -> PipelineResult:
        """
        Process with enhanced features.

        Args:
            input_path: Path to brochure
            output_name: Optional custom output name

        Returns:
            PipelineResult with processing results
        """
        input_path = Path(input_path)

        # Generate unique pipeline ID
        pipeline_id = f"{input_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Check cache
        if self.enable_caching:
            cache_key = self._get_cache_key(input_path)
            cached_result = self._load_from_cache(cache_key)

            if cached_result:
                self.logger.info(f"✓ Returning cached result for {input_path.name}")
                return cached_result

        # Initialize monitor
        monitor = None
        if self.enable_monitoring:
            monitor = PipelineMonitor(pipeline_id, self.config.method.value)
            monitor.start()

        # Start pipeline with logging
        with self.logger.timed_operation(f"pipeline_{input_path.name}"):
            # Input validation
            if self.enable_validation:
                with self.logger.step("Input validation"):
                    validation_result = self._validate_input(input_path)

                    if not validation_result.passed and validation_result.severity == 'error':
                        return self._create_error_result(
                            input_path,
                            f"Input validation failed: {validation_result.message}",
                            start_time=time.time()
                        )

            # Process with retry logic
            result = None
            last_error = None

            for attempt in range(self.max_retries):
                try:
                    if attempt > 0:
                        self.logger.info(f"Retry attempt {attempt + 1}/{self.max_retries}")

                    # Process
                    result = self._process_with_monitoring(
                        input_path,
                        output_name,
                        monitor
                    )

                    if result.success:
                        break
                    else:
                        last_error = result.error

                except Exception as e:
                    last_error = str(e)
                    self.logger.error(f"Processing attempt {attempt + 1} failed: {e}")

                    # Wait before retry (exponential backoff)
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)

            # If all attempts failed
            if not result or not result.success:
                result = self._create_error_result(
                    input_path,
                    f"All {self.max_retries} attempts failed. Last error: {last_error}",
                    start_time=time.time()
                )

            # Output validation
            if self.enable_validation and result.success:
                with self.logger.step("Output validation"):
                    validation_result = OutputValidator.validate_deals(result.deals)

                    if validation_result.details and 'issues' in validation_result.details:
                        self.logger.warning(
                            f"Output validation found {len(validation_result.details['issues'])} issues"
                        )

                        for issue in validation_result.details['issues'][:5]:  # Show first 5
                            self.logger.warning(f"  - {issue}")

            # Save to cache
            if self.enable_caching and result.success:
                cache_key = self._get_cache_key(input_path)
                self._save_to_cache(cache_key, result)

        # Stop monitoring
        if monitor:
            metrics = monitor.stop()

            # Save metrics
            metrics_path = Path(self.output_dir) / output_name or input_path.stem / "metrics.json"
            metrics.save(metrics_path)

            # Analyze bottlenecks
            if result.success:
                analysis = BottleneckDetector.analyze_metrics(metrics)

                if analysis['recommendations']:
                    self.logger.info("Performance recommendations:")
                    for rec in analysis['recommendations']:
                        self.logger.info(f"  💡 {rec}")

        # Log performance summary
        self.logger.log_performance_summary()

        return result

    def _validate_input(self, input_path: Path):
        """Validate input file."""
        ext = input_path.suffix.lower()

        if ext == '.pdf':
            return InputValidator.validate_pdf(str(input_path))
        elif ext in {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}:
            return InputValidator.validate_image(str(input_path))
        else:
            from .validator import ValidationResult
            return ValidationResult(
                passed=False,
                message=f"Unsupported file type: {ext}",
                severity='error'
            )

    def _process_with_monitoring(
        self,
        input_path: Path,
        output_name: Optional[str],
        monitor: Optional[PipelineMonitor]
    ) -> PipelineResult:
        """Process with monitoring integration."""
        start_time = time.time()

        self.logger.info(f"Processing: {input_path.name}")

        try:
            # Stage 1: Load
            with self.logger.step("Load image"):
                if monitor:
                    monitor.start_stage('load_image', input_size=input_path.stat().st_size)

                image = self._load_image(input_path)

                if monitor:
                    monitor.end_stage(success=True)

            # Stage 2: Preprocess
            if self.config.preprocess_images:
                with self.logger.step("Preprocess image"):
                    if monitor:
                        monitor.start_stage('preprocess')

                    image = self._preprocess_image(image)

                    if monitor:
                        monitor.end_stage(success=True)

            # Stage 3: Extract
            ocr_results = None
            vlm_results = None

            if self.config.method in [ProcessingMethod.OCR, ProcessingMethod.HYBRID]:
                with self.logger.step(f"OCR extraction ({self.config.ocr_engine})"):
                    if monitor:
                        monitor.start_stage('ocr_extraction')

                    ocr_results = self._extract_ocr(image)

                    if monitor:
                        monitor.end_stage(success=True, items_processed=len(ocr_results))

            if self.config.method in [ProcessingMethod.VLM, ProcessingMethod.HYBRID]:
                with self.logger.step(f"VLM extraction ({self.config.vlm_engine})"):
                    if monitor:
                        monitor.start_stage('vlm_extraction')

                    vlm_results = self._extract_vlm(image)

                    if monitor:
                        deals_count = len(vlm_results.get('deals', []))
                        monitor.end_stage(success=True, items_processed=deals_count)

            # Stage 4: Extract entities / merge
            with self.logger.step("Extract and structure entities"):
                if monitor:
                    monitor.start_stage('entity_extraction')

                if self.config.method == ProcessingMethod.OCR:
                    deals = self._extract_entities_from_ocr(ocr_results)
                elif self.config.method == ProcessingMethod.VLM:
                    deals = vlm_results.get('deals', [])
                else:  # HYBRID
                    deals = self._merge_results(ocr_results, vlm_results)

                if monitor:
                    monitor.end_stage(success=True, items_processed=len(deals))

            # Create result
            result = PipelineResult(
                input_path=str(input_path),
                success=True,
                processing_time=time.time() - start_time,
                ocr_results=ocr_results,
                vlm_results=vlm_results,
                deals=deals,
                method=self.config.method.value
            )

            # Stage 5: Save
            with self.logger.step("Save results"):
                if monitor:
                    monitor.start_stage('save_results')

                self._save_results(result, output_name or input_path.stem)

                if monitor:
                    monitor.end_stage(success=True)

            # Record in monitor
            if monitor:
                monitor.record_file_processed(success=True, deals_count=len(deals))

            self.logger.info(
                f"✓ Successfully processed {input_path.name}",
                deals_found=len(deals),
                processing_time=f"{result.processing_time:.2f}s"
            )

            return result

        except Exception as e:
            self.logger.error(f"Processing failed: {e}", exc_info=True)

            if monitor:
                monitor.end_stage(success=False, error=str(e))
                monitor.record_file_processed(success=False)

            return self._create_error_result(input_path, str(e), start_time)

    def _create_error_result(
        self,
        input_path: Path,
        error: str,
        start_time: float
    ) -> PipelineResult:
        """Create error result."""
        return PipelineResult(
            input_path=str(input_path),
            success=False,
            processing_time=time.time() - start_time,
            method=self.config.method.value,
            error=error
        )


def create_enhanced_pipeline(
    method: str = "hybrid",
    enable_monitoring: bool = True,
    enable_validation: bool = True,
    enable_caching: bool = False,
    max_retries: int = 3,
    **kwargs
) -> EnhancedPipeline:
    """
    Factory function to create enhanced pipeline.

    Args:
        method: Processing method ('ocr', 'vlm', 'hybrid')
        enable_monitoring: Enable performance monitoring
        enable_validation: Enable input/output validation
        enable_caching: Enable result caching
        max_retries: Maximum retry attempts
        **kwargs: Additional config parameters

    Returns:
        Configured EnhancedPipeline

    Example:
        >>> pipeline = create_enhanced_pipeline(
        ...     'hybrid',
        ...     enable_monitoring=True,
        ...     enable_caching=True,
        ...     max_retries=3
        ... )
        >>> result = pipeline.process('brochure.pdf')
    """
    method_enum = ProcessingMethod(method.lower())
    config = PipelineConfig(method=method_enum, **kwargs)

    return EnhancedPipeline(
        config=config,
        enable_monitoring=enable_monitoring,
        enable_validation=enable_validation,
        enable_caching=enable_caching,
        max_retries=max_retries
    )


if __name__ == '__main__':
    # Example usage
    pipeline = create_enhanced_pipeline(
        'hybrid',
        enable_monitoring=True,
        enable_validation=True,
        max_retries=2
    )

    print("Enhanced pipeline created successfully!")
    print(f"Method: {pipeline.config.method.value}")
    print(f"Monitoring: {pipeline.enable_monitoring}")
    print(f"Validation: {pipeline.enable_validation}")
    print(f"Max retries: {pipeline.max_retries}")

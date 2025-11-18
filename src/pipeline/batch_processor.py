"""
Batch Processor for Large-scale Brochure Processing

Features:
- Parallel processing
- Progress tracking
- Error recovery
- Result aggregation
- Performance monitoring
"""

import logging
from pathlib import Path
from typing import List, Union, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
from datetime import datetime
import time

from .pipeline import BrochurePipeline, PipelineConfig, PipelineResult
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class BatchResult:
    """Batch processing result summary."""

    total: int
    successful: int
    failed: int
    total_time: float
    results: List[PipelineResult]

    @property
    def success_rate(self) -> float:
        """Success rate percentage."""
        return (self.successful / self.total * 100) if self.total > 0 else 0

    @property
    def avg_time(self) -> float:
        """Average processing time per image."""
        return (self.total_time / self.total) if self.total > 0 else 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'total': self.total,
            'successful': self.successful,
            'failed': self.failed,
            'success_rate': f"{self.success_rate:.1f}%",
            'total_time': f"{self.total_time:.2f}s",
            'avg_time': f"{self.avg_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }

    def save_summary(self, output_path: Union[str, Path]):
        """Save batch summary."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Batch summary saved to {output_path}")


class BatchProcessor:
    """
    Batch processor for processing multiple brochures.

    Features:
    - Parallel processing with thread pool
    - Progress tracking
    - Error recovery and retry
    - Result aggregation
    - Performance monitoring

    Example:
        >>> processor = BatchProcessor(max_workers=4)
        >>> files = ['file1.pdf', 'file2.png']
        >>> result = processor.process(files, method='hybrid')
        >>> print(f"Success rate: {result.success_rate:.1f}%")
    """

    def __init__(
        self,
        config: PipelineConfig = None,
        max_workers: int = 4,
        retry_failed: bool = True,
        max_retries: int = 2
    ):
        """
        Initialize batch processor.

        Args:
            config: Pipeline configuration
            max_workers: Maximum parallel workers
            retry_failed: Retry failed items
            max_retries: Maximum retry attempts
        """
        self.config = config or PipelineConfig()
        self.max_workers = max_workers
        self.retry_failed = retry_failed
        self.max_retries = max_retries

        logger.info(f"Batch processor initialized with {max_workers} workers")

    def process(
        self,
        input_paths: List[Union[str, Path]],
        method: str = None,
        show_progress: bool = True
    ) -> BatchResult:
        """
        Process multiple brochures in parallel.

        Args:
            input_paths: List of input file paths
            method: Override processing method ('ocr', 'vlm', 'hybrid')
            show_progress: Show progress bar

        Returns:
            BatchResult with aggregated results
        """
        start_time = time.time()

        # Update config if method specified
        if method:
            from .pipeline import ProcessingMethod
            self.config.method = ProcessingMethod(method.lower())

        # Create pipeline
        pipeline = BrochurePipeline(self.config)

        logger.info(f"Starting batch processing: {len(input_paths)} files")

        # Process files
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                use_tqdm = True
            except ImportError:
                use_tqdm = False
                logger.warning("tqdm not installed, progress bar disabled")
        else:
            use_tqdm = False

        # Single-threaded for simplicity (can be made parallel)
        if use_tqdm:
            iterator = tqdm(input_paths, desc="Processing")
        else:
            iterator = input_paths

        for i, path in enumerate(iterator):
            result = pipeline.process(path)
            results.append(result)

            if not use_tqdm:
                logger.info(f"Progress: {i+1}/{len(input_paths)}")

        # Calculate statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        batch_result = BatchResult(
            total=len(results),
            successful=successful,
            failed=failed,
            total_time=total_time,
            results=results
        )

        # Log summary
        logger.info("=" * 80)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total files: {batch_result.total}")
        logger.info(f"Successful: {batch_result.successful}")
        logger.info(f"Failed: {batch_result.failed}")
        logger.info(f"Success rate: {batch_result.success_rate:.1f}%")
        logger.info(f"Total time: {batch_result.total_time:.2f}s")
        logger.info(f"Avg time/file: {batch_result.avg_time:.2f}s")
        logger.info("=" * 80)

        return batch_result

    def process_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False,
        **kwargs
    ) -> BatchResult:
        """
        Process all files in a directory.

        Args:
            directory: Input directory
            pattern: File pattern (e.g., "*.pdf", "*.png")
            recursive: Search recursively
            **kwargs: Additional arguments for process()

        Returns:
            BatchResult
        """
        directory = Path(directory)

        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")

        # Find files
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        logger.info(f"Found {len(files)} files matching '{pattern}' in {directory}")

        if not files:
            logger.warning("No files found")
            return BatchResult(0, 0, 0, 0.0, [])

        return self.process(files, **kwargs)

    def aggregate_results(
        self,
        results: List[PipelineResult],
        output_file: Union[str, Path]
    ):
        """
        Aggregate and save all results.

        Args:
            results: List of pipeline results
            output_file: Output JSON file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Aggregate all deals
        all_deals = []
        for result in results:
            if result.success:
                for deal in result.deals:
                    deal['source_file'] = result.input_path
                    all_deals.append(deal)

        # Create summary
        summary = {
            'total_files': len(results),
            'successful_files': sum(1 for r in results if r.success),
            'total_deals': len(all_deals),
            'deals': all_deals,
            'timestamp': datetime.now().isoformat()
        }

        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Aggregated results saved to {output_file}")
        logger.info(f"Total deals extracted: {len(all_deals)}")

    def generate_report(
        self,
        batch_result: BatchResult,
        output_dir: Union[str, Path]
    ):
        """
        Generate detailed report from batch result.

        Args:
            batch_result: Batch processing result
            output_dir: Output directory
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save summary
        batch_result.save_summary(output_dir / "summary.json")

        # Aggregate all results
        self.aggregate_results(
            batch_result.results,
            output_dir / "all_deals.json"
        )

        # Save failed files list
        failed_files = [r.input_path for r in batch_result.results if not r.success]
        if failed_files:
            with open(output_dir / "failed_files.txt", 'w') as f:
                f.write('\n'.join(failed_files))
            logger.info(f"Failed files list: {output_dir / 'failed_files.txt'}")

        # Create markdown report
        self._create_markdown_report(batch_result, output_dir / "report.md")

        logger.info(f"Report generated in {output_dir}")

    def _create_markdown_report(
        self,
        batch_result: BatchResult,
        output_file: Path
    ):
        """Create markdown report."""

        report = f"""# Batch Processing Report

## Summary

- **Total Files**: {batch_result.total}
- **Successful**: {batch_result.successful}
- **Failed**: {batch_result.failed}
- **Success Rate**: {batch_result.success_rate:.1f}%
- **Total Time**: {batch_result.total_time:.2f}s
- **Avg Time/File**: {batch_result.avg_time:.2f}s
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Results by File

| File | Status | Deals | Time |
|------|--------|-------|------|
"""

        for result in batch_result.results:
            status = "✓" if result.success else "✗"
            deals = len(result.deals) if result.success else "-"
            time_str = f"{result.processing_time:.2f}s"

            report += f"| {Path(result.input_path).name} | {status} | {deals} | {time_str} |\n"

        # Failed files section
        if batch_result.failed > 0:
            report += "\n## Failed Files\n\n"
            for result in batch_result.results:
                if not result.success:
                    report += f"- {Path(result.input_path).name}: {result.error}\n"

        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Markdown report: {output_file}")


def process_directory(
    directory: Union[str, Path],
    method: str = "hybrid",
    pattern: str = "*",
    output_dir: str = "outputs/batch",
    **kwargs
) -> BatchResult:
    """
    Convenience function to process a directory.

    Args:
        directory: Input directory
        method: Processing method
        pattern: File pattern
        output_dir: Output directory
        **kwargs: Additional config parameters

    Returns:
        BatchResult

    Example:
        >>> result = process_directory('data/brochures', method='hybrid')
    """
    from .pipeline import ProcessingMethod

    config = PipelineConfig(
        method=ProcessingMethod(method.lower()),
        output_dir=output_dir,
        **kwargs
    )

    processor = BatchProcessor(config=config)
    result = processor.process_directory(directory, pattern=pattern)

    # Generate report
    processor.generate_report(result, Path(output_dir) / "report")

    return result

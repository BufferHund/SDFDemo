#!/usr/bin/env python3
"""
Pipeline Examples - Complete End-to-End Workflows

This file demonstrates how to use the BrochurePipeline for end-to-end processing.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import (
    create_pipeline,
    BrochurePipeline,
    PipelineConfig,
    ProcessingMethod,
    BatchProcessor
)


def example_1_basic_ocr_pipeline():
    """Example 1: Simple OCR-only pipeline."""
    print("=" * 80)
    print("Example 1: Basic OCR Pipeline")
    print("=" * 80)

    # Create OCR pipeline
    pipeline = create_pipeline(
        method='ocr',
        ocr_engine='paddleocr',
        output_dir='outputs/example1'
    )

    # Process a brochure
    result = pipeline.process('data/samples/sample_brochure.png')

    # Print results
    print(f"\nProcessing time: {result.processing_time:.2f}s")
    print(f"Found {len(result.deals)} deals")

    for i, deal in enumerate(result.deals, 1):
        print(f"\n{i}. {deal.get('product_name', 'Unknown')}")
        if deal.get('discounted_price'):
            print(f"   Price: €{deal['discounted_price']}")


def example_2_vlm_pipeline():
    """Example 2: VLM-only pipeline with Ollama."""
    print("\n" + "=" * 80)
    print("Example 2: VLM Pipeline (Ollama)")
    print("=" * 80)

    # Create VLM pipeline
    pipeline = create_pipeline(
        method='vlm',
        vlm_engine='ollama',
        vlm_model='llava:latest',
        output_dir='outputs/example2'
    )

    # Process brochure
    result = pipeline.process('data/samples/sample_brochure.png')

    print(f"\nProcessing time: {result.processing_time:.2f}s")
    print(f"Found {len(result.deals)} deals")

    for deal in result.deals:
        print(f"- {deal.get('product_name')}: €{deal.get('discounted_price')}")


def example_3_hybrid_pipeline():
    """Example 3: Hybrid pipeline combining OCR and VLM."""
    print("\n" + "=" * 80)
    print("Example 3: Hybrid Pipeline (OCR + VLM)")
    print("=" * 80)

    # Create hybrid pipeline
    pipeline = create_pipeline(
        method='hybrid',
        ocr_engine='paddleocr',
        vlm_engine='ollama',
        vlm_model='llava:latest',
        output_dir='outputs/example3'
    )

    # Process brochure
    result = pipeline.process('data/samples/sample_brochure.png')

    print(f"\nProcessing time: {result.processing_time:.2f}s")
    print(f"Method: {result.method}")
    print(f"Found {len(result.deals)} deals")


def example_4_custom_config():
    """Example 4: Custom pipeline configuration."""
    print("\n" + "=" * 80)
    print("Example 4: Custom Pipeline Configuration")
    print("=" * 80)

    # Create custom config
    config = PipelineConfig(
        method=ProcessingMethod.HYBRID,
        ocr_engine='paddleocr',
        ocr_languages=['de', 'en', 'fr'],
        ocr_use_gpu=True,
        vlm_engine='ollama',
        vlm_model='bakllava',
        preprocess_images=True,
        enhance_images=True,
        target_size=(1024, 1448),
        output_dir='outputs/example4',
        save_intermediate=True,
        save_visualizations=True
    )

    # Create pipeline
    pipeline = BrochurePipeline(config)

    # Process
    result = pipeline.process('data/samples/sample_brochure.pdf')

    print(f"\nSuccess: {result.success}")
    print(f"Processing time: {result.processing_time:.2f}s")


def example_5_batch_processing():
    """Example 5: Batch processing multiple brochures."""
    print("\n" + "=" * 80)
    print("Example 5: Batch Processing")
    print("=" * 80)

    # Create batch processor
    config = PipelineConfig(
        method=ProcessingMethod.HYBRID,
        output_dir='outputs/example5'
    )

    processor = BatchProcessor(
        config=config,
        max_workers=4
    )

    # Process directory
    result = processor.process_directory(
        'data/samples',
        pattern='*.png',
        recursive=False
    )

    # Print summary
    print(f"\nBatch Results:")
    print(f"Total files: {result.total}")
    print(f"Successful: {result.successful}")
    print(f"Failed: {result.failed}")
    print(f"Success rate: {result.success_rate:.1f}%")
    print(f"Total time: {result.total_time:.2f}s")
    print(f"Avg time per file: {result.avg_time:.2f}s")


def example_6_batch_with_report():
    """Example 6: Batch processing with detailed report generation."""
    print("\n" + "=" * 80)
    print("Example 6: Batch Processing with Report")
    print("=" * 80)

    # Create processor
    config = PipelineConfig(
        method=ProcessingMethod.HYBRID,
        output_dir='outputs/example6'
    )

    processor = BatchProcessor(config=config)

    # Process files
    files = [
        'data/samples/brochure1.png',
        'data/samples/brochure2.png',
        'data/samples/brochure3.pdf'
    ]

    result = processor.process(files, show_progress=True)

    # Generate comprehensive report
    processor.generate_report(result, 'outputs/example6/report')

    print(f"\nReport generated:")
    print(f"- summary.json: Batch statistics")
    print(f"- all_deals.json: All extracted deals")
    print(f"- report.md: Markdown report")
    print(f"- failed_files.txt: List of failed files (if any)")


def example_7_error_handling():
    """Example 7: Robust pipeline with error handling."""
    print("\n" + "=" * 80)
    print("Example 7: Error Handling")
    print("=" * 80)

    pipeline = create_pipeline(method='hybrid')

    # Process with error handling
    files = [
        'data/samples/valid.png',
        'data/samples/invalid.png',
        'data/samples/missing.pdf'
    ]

    for file_path in files:
        result = pipeline.process(file_path)

        if result.success:
            print(f"✓ {file_path}: {len(result.deals)} deals")
        else:
            print(f"✗ {file_path}: {result.error}")


def example_8_gemini_vlm():
    """Example 8: Using Gemini API for VLM."""
    print("\n" + "=" * 80)
    print("Example 8: Gemini VLM Pipeline")
    print("=" * 80)

    import os

    # Check if API key is set
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠ GEMINI_API_KEY not set. Skipping this example.")
        return

    # Create Gemini VLM pipeline
    pipeline = create_pipeline(
        method='vlm',
        vlm_engine='gemini',
        vlm_model='gemini-1.5-flash',
        output_dir='outputs/example8'
    )

    result = pipeline.process('data/samples/sample_brochure.png')

    print(f"Found {len(result.deals)} deals using Gemini")


def example_9_pdf_processing():
    """Example 9: Processing PDF brochures."""
    print("\n" + "=" * 80)
    print("Example 9: PDF Processing")
    print("=" * 80)

    # Pipeline automatically handles PDF conversion
    pipeline = create_pipeline(
        method='hybrid',
        output_dir='outputs/example9'
    )

    # Process PDF (will be converted to image internally)
    result = pipeline.process('data/samples/brochure.pdf')

    print(f"PDF processed: {result.success}")
    print(f"Processing time: {result.processing_time:.2f}s")


def example_10_performance_comparison():
    """Example 10: Compare OCR vs VLM vs Hybrid performance."""
    print("\n" + "=" * 80)
    print("Example 10: Performance Comparison")
    print("=" * 80)

    import time

    test_file = 'data/samples/sample_brochure.png'

    # Test OCR
    ocr_pipeline = create_pipeline(method='ocr', output_dir='outputs/example10/ocr')
    start = time.time()
    ocr_result = ocr_pipeline.process(test_file)
    ocr_time = time.time() - start

    # Test VLM
    vlm_pipeline = create_pipeline(method='vlm', output_dir='outputs/example10/vlm')
    start = time.time()
    vlm_result = vlm_pipeline.process(test_file)
    vlm_time = time.time() - start

    # Test Hybrid
    hybrid_pipeline = create_pipeline(method='hybrid', output_dir='outputs/example10/hybrid')
    start = time.time()
    hybrid_result = hybrid_pipeline.process(test_file)
    hybrid_time = time.time() - start

    # Print comparison
    print("\nPerformance Comparison:")
    print(f"{'Method':<10} {'Time (s)':<12} {'Deals Found':<15} {'Success'}")
    print("-" * 50)
    print(f"{'OCR':<10} {ocr_time:<12.2f} {len(ocr_result.deals):<15} {ocr_result.success}")
    print(f"{'VLM':<10} {vlm_time:<12.2f} {len(vlm_result.deals):<15} {vlm_result.success}")
    print(f"{'Hybrid':<10} {hybrid_time:<12.2f} {len(hybrid_result.deals):<15} {hybrid_result.success}")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("SUPERMARKET BROCHURE AI - PIPELINE EXAMPLES")
    print("=" * 80)

    # Run examples
    try:
        example_1_basic_ocr_pipeline()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_3_hybrid_pipeline()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_custom_config()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        example_5_batch_processing()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    print("\n" + "=" * 80)
    print("Examples complete! Check outputs/ directory for results.")
    print("=" * 80)

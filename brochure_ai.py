#!/usr/bin/env python3
"""
Supermarket Brochure AI - Unified CLI Tool

Usage:
    python brochure_ai.py scrape --all
    python brochure_ai.py extract image.png
    python brochure_ai.py train --config configs/config.yaml
    python brochure_ai.py serve --api
    python brochure_ai.py serve --web
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def cmd_scrape(args):
    """Data collection command."""
    from src.data_collection.scrape_brochures import main as scrape_main

    sys.argv = ['scrape_brochures.py']
    if args.all:
        sys.argv.append('--all')
    elif args.supermarket:
        sys.argv.extend(['--supermarket', args.supermarket])

    if args.output:
        sys.argv.extend(['--output-dir', args.output])

    return scrape_main()


def cmd_extract(args):
    """OCR extraction command."""
    from src.models.ocr_engine import create_ocr_engine
    import json

    logger.info(f"Extracting text from {args.image}")

    ocr = create_ocr_engine(
        engine_type=args.engine,
        languages=args.languages,
        use_gpu=args.gpu
    )

    results = ocr.extract_text(args.image)

    logger.info(f"Extracted {len(results)} text regions")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {args.output}")
    else:
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['text']} (confidence: {result['confidence']:.2f})")

    return 0


def cmd_train(args):
    """Model training command."""
    from src.models.train import main as train_main

    sys.argv = ['train.py']

    if args.config:
        sys.argv.extend(['--config', args.config])
    if args.train_dir:
        sys.argv.extend(['--train-dir', args.train_dir])
    if args.val_dir:
        sys.argv.extend(['--val-dir', args.val_dir])
    if args.output_dir:
        sys.argv.extend(['--output-dir', args.output_dir])

    return train_main()


def cmd_serve(args):
    """Start services command."""
    if args.api:
        logger.info("Starting API server...")
        from src.webapp.api import main as api_main
        return api_main()

    elif args.web:
        import subprocess

        # Choose which interface to run
        if hasattr(args, 'enhanced') and args.enhanced == False:
            webapp_file = 'src/webapp/app.py'
            logger.info("Starting basic web interface...")
        else:
            webapp_file = 'src/webapp/app_enhanced.py'
            logger.info("Starting enhanced web interface...")

        # Build streamlit command
        cmd = ['streamlit', 'run', webapp_file]

        # Add port if specified
        if hasattr(args, 'port') and args.port:
            cmd.extend(['--server.port', str(args.port)])

        subprocess.run(cmd)
        return 0

    else:
        logger.error("Please specify --api or --web")
        return 1


def cmd_analyze(args):
    """VLM analysis command."""
    from src.models.vlm_engine import create_vlm_engine
    import json

    logger.info(f"Analyzing {args.image} with {args.vlm}")

    # Create VLM engine
    kwargs = {}
    if args.api_key:
        kwargs['api_key'] = args.api_key
    if args.model:
        kwargs['model_name'] = args.model

    vlm = create_vlm_engine(engine_type=args.vlm, **kwargs)

    # Analyze
    result = vlm.analyze_image(args.image, prompt=args.prompt)

    # Print results
    logger.info(f"Found {len(result.get('deals', []))} deals")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {args.output}")
    else:
        for i, deal in enumerate(result.get('deals', []), 1):
            print(f"{i}. {deal.get('product_name', 'Unknown')}")
            if deal.get('discounted_price'):
                print(f"   Price: €{deal['discounted_price']}")

    return 0


def cmd_preprocess(args):
    """Preprocessing command."""
    if args.pdf:
        from src.preprocessing.pdf_converter import main as pdf_main
        sys.argv = ['pdf_converter.py', args.input]
        if args.output:
            sys.argv.extend(['--output-dir', args.output])
        if args.dpi:
            sys.argv.extend(['--dpi', str(args.dpi)])
        return pdf_main()

    elif args.images:
        from src.preprocessing.image_processor import main as img_main
        sys.argv = ['image_processor.py', args.input]
        if args.output:
            sys.argv.extend(['--output-dir', args.output])
        return img_main()

    else:
        logger.error("Please specify --pdf or --images")
        return 1


def cmd_pipeline(args):
    """Pipeline processing command."""
    from src.pipeline import create_pipeline, BatchProcessor, PipelineConfig, ProcessingMethod
    import json

    logger.info(f"Running pipeline with method: {args.method}")

    if args.batch:
        # Batch processing
        config = PipelineConfig(
            method=ProcessingMethod(args.method),
            ocr_engine=args.ocr_engine,
            vlm_engine=args.vlm_engine,
            vlm_model=args.vlm_model or "llava:latest",
            ocr_use_gpu=args.gpu,
            output_dir=args.output or "outputs/pipeline",
            save_visualizations=not args.no_viz
        )

        processor = BatchProcessor(config=config, max_workers=args.workers)

        if Path(args.input).is_dir():
            result = processor.process_directory(
                args.input,
                pattern=args.pattern,
                recursive=args.recursive
            )
        else:
            # Single file in batch mode
            result = processor.process([args.input])

        # Generate report
        if args.report:
            report_dir = Path(args.output or "outputs/pipeline") / "report"
            processor.generate_report(result, report_dir)
            logger.info(f"Report generated in {report_dir}")

        logger.info(f"Batch processing complete: {result.success_rate:.1f}% success rate")

    else:
        # Single file processing
        pipeline = create_pipeline(
            method=args.method,
            ocr_engine=args.ocr_engine,
            vlm_engine=args.vlm_engine,
            vlm_model=args.vlm_model or "llava:latest",
            ocr_use_gpu=args.gpu,
            output_dir=args.output or "outputs/pipeline",
            save_visualizations=not args.no_viz
        )

        result = pipeline.process(args.input)

        if result.success:
            logger.info(f"✓ Success: Found {len(result.deals)} deals in {result.processing_time:.2f}s")

            # Print deals
            if not args.quiet:
                print("\nExtracted Deals:")
                print("=" * 80)
                for i, deal in enumerate(result.deals, 1):
                    print(f"\n{i}. {deal.get('product_name', 'Unknown')}")
                    if deal.get('discounted_price'):
                        print(f"   Price: €{deal['discounted_price']}")
                    if deal.get('discount_percentage'):
                        print(f"   Discount: {deal['discount_percentage']}%")
        else:
            logger.error(f"✗ Failed: {result.error}")
            return 1

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Supermarket Brochure AI - Unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape brochures from supermarkets')
    scrape_parser.add_argument('--all', action='store_true', help='Scrape all supermarkets')
    scrape_parser.add_argument('--supermarket', choices=['aldi_sued', 'aldi_nord', 'rewe', 'lidl', 'edeka'])
    scrape_parser.add_argument('--output', help='Output directory')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract text from image')
    extract_parser.add_argument('image', help='Image file path')
    extract_parser.add_argument('--engine', default='paddleocr', choices=['tesseract', 'paddleocr', 'easyocr'])
    extract_parser.add_argument('--languages', nargs='+', default=['de', 'en'])
    extract_parser.add_argument('--gpu', action='store_true', help='Use GPU')
    extract_parser.add_argument('--output', help='Output JSON file')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train model')
    train_parser.add_argument('--config', help='Config file')
    train_parser.add_argument('--train-dir', default='data/annotated/train')
    train_parser.add_argument('--val-dir', default='data/annotated/val')
    train_parser.add_argument('--output-dir', default='models/checkpoints')

    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start services')
    serve_parser.add_argument('--api', action='store_true', help='Start API server')
    serve_parser.add_argument('--web', action='store_true', help='Start web app')
    serve_parser.add_argument('--enhanced', action='store_true', default=True,
                             help='Use enhanced interface (default)')
    serve_parser.add_argument('--basic', action='store_false', dest='enhanced',
                             help='Use basic interface')
    serve_parser.add_argument('--port', type=int, help='Port number (default: 8501 for web, 8000 for API)')

    # Analyze command (VLM)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze image with VLM')
    analyze_parser.add_argument('image', help='Image file path')
    analyze_parser.add_argument('--vlm', default='ollama', choices=['ollama', 'gemini'], help='VLM engine')
    analyze_parser.add_argument('--model', help='Model name (e.g., llava:latest, gemini-1.5-flash)')
    analyze_parser.add_argument('--prompt', help='Custom prompt')
    analyze_parser.add_argument('--api-key', help='API key (for Gemini)')
    analyze_parser.add_argument('--output', help='Output JSON file')

    # Preprocess command
    preprocess_parser = subparsers.add_parser('preprocess', help='Preprocess data')
    preprocess_parser.add_argument('input', help='Input directory or file')
    preprocess_parser.add_argument('--output', help='Output directory')
    preprocess_parser.add_argument('--pdf', action='store_true', help='Convert PDFs to images')
    preprocess_parser.add_argument('--images', action='store_true', help='Process images')
    preprocess_parser.add_argument('--dpi', type=int, default=300, help='DPI for PDF conversion')

    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run complete pipeline')
    pipeline_parser.add_argument('input', help='Input file or directory')
    pipeline_parser.add_argument('--method', default='hybrid', choices=['ocr', 'vlm', 'hybrid'],
                                 help='Processing method')
    pipeline_parser.add_argument('--ocr-engine', default='paddleocr',
                                 choices=['tesseract', 'paddleocr', 'easyocr'],
                                 help='OCR engine')
    pipeline_parser.add_argument('--vlm-engine', default='ollama', choices=['ollama', 'gemini'],
                                 help='VLM engine')
    pipeline_parser.add_argument('--vlm-model', help='VLM model name')
    pipeline_parser.add_argument('--gpu', action='store_true', help='Use GPU for OCR')
    pipeline_parser.add_argument('--output', help='Output directory')
    pipeline_parser.add_argument('--batch', action='store_true', help='Batch processing mode')
    pipeline_parser.add_argument('--pattern', default='*', help='File pattern for batch mode')
    pipeline_parser.add_argument('--recursive', action='store_true', help='Recursive directory search')
    pipeline_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    pipeline_parser.add_argument('--report', action='store_true', help='Generate detailed report')
    pipeline_parser.add_argument('--no-viz', action='store_true', help='Disable visualizations')
    pipeline_parser.add_argument('--quiet', action='store_true', help='Suppress output')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to appropriate command
    commands = {
        'scrape': cmd_scrape,
        'extract': cmd_extract,
        'analyze': cmd_analyze,
        'train': cmd_train,
        'serve': cmd_serve,
        'preprocess': cmd_preprocess,
        'pipeline': cmd_pipeline
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

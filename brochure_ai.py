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
        logger.info("Starting Streamlit web app...")
        import subprocess
        subprocess.run(['streamlit', 'run', 'src/webapp/app.py'])
        return 0

    else:
        logger.error("Please specify --api or --web")
        return 1


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

    # Preprocess command
    preprocess_parser = subparsers.add_parser('preprocess', help='Preprocess data')
    preprocess_parser.add_argument('input', help='Input directory or file')
    preprocess_parser.add_argument('--output', help='Output directory')
    preprocess_parser.add_argument('--pdf', action='store_true', help='Convert PDFs to images')
    preprocess_parser.add_argument('--images', action='store_true', help='Process images')
    preprocess_parser.add_argument('--dpi', type=int, default=300, help='DPI for PDF conversion')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to appropriate command
    commands = {
        'scrape': cmd_scrape,
        'extract': cmd_extract,
        'train': cmd_train,
        'serve': cmd_serve,
        'preprocess': cmd_preprocess
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

# CLI Usage Guide

This guide covers all command-line tools and shortcuts available in the project.

## Quick Start

### Using Makefile (Recommended)

```bash
# Setup project
make setup

# Run tests
make test

# Start API server
make run-api

# Start web app
make run-webapp

# Scrape all supermarkets
make scrape-all

# Clean temporary files
make clean
```

### Using Unified CLI

The `brochure_ai.py` script provides a unified interface for all operations:

```bash
# Make executable
chmod +x brochure_ai.py

# Show help
./brochure_ai.py --help
```

## Commands

### 1. Data Collection (scrape)

```bash
# Scrape all supermarkets
./brochure_ai.py scrape --all

# Scrape specific supermarket
./brochure_ai.py scrape --supermarket aldi_sued

# Custom output directory
./brochure_ai.py scrape --all --output data/custom/
```

**Available supermarkets:**
- `aldi_sued` - Aldi Süd
- `aldi_nord` - Aldi Nord
- `rewe` - REWE
- `lidl` - Lidl
- `edeka` - Edeka

### 2. Text Extraction (extract)

```bash
# Extract text from image
./brochure_ai.py extract brochure.png

# Use specific OCR engine
./brochure_ai.py extract image.png --engine paddleocr

# Use GPU acceleration
./brochure_ai.py extract image.png --gpu

# Save to JSON file
./brochure_ai.py extract image.png --output results.json

# Specify languages
./brochure_ai.py extract image.png --languages de en fr
```

**OCR Engines:**
- `tesseract` - Traditional OCR
- `paddleocr` - Deep learning OCR (recommended)
- `easyocr` - PyTorch-based OCR

### 3. Preprocessing (preprocess)

```bash
# Convert PDFs to images
./brochure_ai.py preprocess data/raw/pdfs --pdf --output data/processed/images

# Process and standardize images
./brochure_ai.py preprocess data/raw/images --images --output data/processed/standardized

# Custom DPI for PDF conversion
./brochure_ai.py preprocess file.pdf --pdf --dpi 300
```

### 4. Model Training (train)

```bash
# Train with default settings
./brochure_ai.py train

# Train with config file
./brochure_ai.py train --config configs/config.yaml

# Custom data directories
./brochure_ai.py train --train-dir data/annotated/train --val-dir data/annotated/val

# Custom output directory
./brochure_ai.py train --output-dir models/custom/
```

### 5. Start Services (serve)

```bash
# Start API server (http://localhost:8000)
./brochure_ai.py serve --api

# Start web application (http://localhost:8501)
./brochure_ai.py serve --web
```

## Direct Module Usage

### Data Collection

```bash
# Using module directly
python src/data_collection/scrape_brochures.py --supermarket aldi_sued

# Multiple options
python src/data_collection/scrape_brochures.py --supermarket rewe --market-id 123456
python src/data_collection/scrape_brochures.py --supermarket edeka --market-url "https://..."
```

### PDF Conversion

```bash
# Convert single PDF
python src/preprocessing/pdf_converter.py brochure.pdf

# Convert directory
python src/preprocessing/pdf_converter.py data/raw/pdfs/ --output-dir data/processed/images

# Custom settings
python src/preprocessing/pdf_converter.py file.pdf --dpi 300 --format png
```

### Image Processing

```bash
# Process single image
python src/preprocessing/image_processor.py image.png

# Process directory
python src/preprocessing/image_processor.py data/images/ --output-dir data/processed/

# Custom dimensions
python src/preprocessing/image_processor.py image.png --width 1024 --height 1448

# Disable enhancements
python src/preprocessing/image_processor.py image.png --no-enhance
```

### OCR Extraction

```bash
# PaddleOCR (recommended)
python src/models/ocr_engine.py image.png --engine paddleocr --languages de en

# EasyOCR with GPU
python src/models/ocr_engine.py image.png --engine easyocr --gpu

# Tesseract
python src/models/ocr_engine.py image.png --engine tesseract

# Save to file
python src/models/ocr_engine.py image.png --output results.json
```

### Model Training

```bash
# Basic training
python src/models/train.py --train-dir data/annotated/train

# With validation
python src/models/train.py --train-dir data/annotated/train --val-dir data/annotated/val

# Use LoRA for efficient fine-tuning
python src/models/train.py --use-lora --lora-r 16 --lora-alpha 32

# Custom hyperparameters
python src/models/train.py --batch-size 8 --learning-rate 5e-5 --num-epochs 20

# Resume from checkpoint
python src/models/train.py --resume models/checkpoints/checkpoint-1000

# Enable W&B logging
python src/models/train.py --use-wandb
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_entity_extractor.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run tests verbosely
pytest tests/ -v

# Using Makefile
make test
```

## Utility Scripts

### Setup Script

```bash
# Initial setup (recommended for first-time setup)
bash scripts/setup.sh

# Or using Make
make setup
```

This script:
- Creates virtual environment
- Installs dependencies
- Creates necessary directories
- Checks system dependencies

### Test Runner

```bash
# Run tests with coverage
bash scripts/run_tests.sh

# Or using Make
make test
```

## Docker Commands

```bash
# Build images
docker-compose build
# Or: make docker-build

# Start services
docker-compose up -d
# Or: make docker-up

# View logs
docker-compose logs -f

# Stop services
docker-compose down
# Or: make docker-down

# Rebuild and restart
docker-compose up --build
```

## Development Workflow

### Complete Pipeline Example

```bash
# 1. Setup
make setup

# 2. Collect data
./brochure_ai.py scrape --all

# 3. Preprocess
./brochure_ai.py preprocess data/raw/pdfs --pdf --output data/processed/images

# 4. Extract and test OCR
./brochure_ai.py extract data/processed/images/sample.png --output test_results.json

# 5. Annotate data (manual step using annotation tool)
# ...

# 6. Train model
./brochure_ai.py train --train-dir data/annotated/train --val-dir data/annotated/val

# 7. Start application
./brochure_ai.py serve --web
```

## Tips & Shortcuts

### Aliases (add to ~/.bashrc or ~/.zshrc)

```bash
alias brochure='python /path/to/brochure_ai.py'
alias brochure-api='make run-api'
alias brochure-web='make run-webapp'
alias brochure-test='make test'
```

Then use:
```bash
brochure extract image.png
brochure-api
brochure-test
```

### Environment Variables

```bash
# Set default OCR engine
export BROCHURE_OCR_ENGINE=paddleocr

# Set default output directory
export BROCHURE_OUTPUT_DIR=/path/to/output

# Enable GPU by default
export BROCHURE_USE_GPU=1
```

### Batch Processing

```bash
# Process all PDFs in directory
for pdf in data/raw/pdfs/*.pdf; do
    ./brochure_ai.py preprocess "$pdf" --pdf --output data/processed/images/
done

# Extract text from all images
for img in data/processed/images/*.png; do
    ./brochure_ai.py extract "$img" --output "results/$(basename $img .png).json"
done
```

## Troubleshooting

### Command not found

```bash
# Make sure script is executable
chmod +x brochure_ai.py

# Or run with python
python brochure_ai.py --help
```

### Module import errors

```bash
# Ensure you're in project root
cd /path/to/SDFDemo

# Activate virtual environment
source venv/bin/activate
```

### Permission denied

```bash
# Make scripts executable
chmod +x scripts/*.sh brochure_ai.py
```

## See Also

- [Quick Start Guide](QUICKSTART.md)
- [API Usage Guide](API_GUIDE.md)
- [Project Plan](PROJECT_PLAN.md)
- [Contributing Guide](CONTRIBUTING.md)

# Supermarket Brochure AI - Information Extraction System

## Project Overview

An intelligent system that automatically detects and extracts structured deal information (product names, prices, and discounts) from supermarket brochures. The system processes visually complex brochures published as images or PDFs and provides structured access to promotional information.

## Problem Statement

Supermarket brochures contain valuable information about weekly discounts, product offers, and price changes. However, these brochures are usually published as unstructured images or PDFs, making it difficult for customers to extract and analyze deals.

## Goals

- Build an AI system that extracts structured deal information from brochures
- Detect and highlight promotional regions in brochure images
- Output structured data (JSON/tables) with product details
- Provide a user-friendly web interface for uploads and visualization

## Project Timeline (8 Weeks)

| Week | Phase | Main Tasks |
|------|-------|------------|
| Week 1 | Project setup & data collection planning | Define scope, collect samples, design data structure |
| Week 2 | Data collection & initial preprocessing | Download/clean data, standardize formats, run initial OCR |
| Week 3 | Data annotation & standardization | Manual annotation, define JSON schema, evaluate OCR accuracy |
| Week 4 | Model selection & environment setup | Research models, configure environment, design pipeline |
| Week 5 | Model fine-tuning | Apply PEFT, tune hyperparameters, data augmentation |
| Week 6 | Evaluation & refinement | Evaluate accuracy, error analysis, iterate improvements |
| Week 7 | Application prototyping | Develop web UI, visualize regions, display structured output |
| Week 8 | Integration, testing & presentation | Integrate components, test formats, prepare presentation |

## Technology Stack

### OCR & Text Extraction
- **Tesseract OCR**: Open-source OCR engine
- **PaddleOCR**: Deep learning-based multilingual OCR
- **EasyOCR**: Lightweight PyTorch-based OCR

### Layout Analysis & Document Understanding
- **LayoutLMv3**: Transformer combining text, layout, and image embeddings
- **Donut**: OCR-free vision transformer for end-to-end extraction
- **DocFormer**: Joint text and visual embedding model

### Fine-tuning & Training
- **PEFT (LoRA/Adapter)**: Parameter-efficient fine-tuning
- **Hugging Face Transformers**: Pre-trained model library

### Application Layer
- **Streamlit/Gradio**: Rapid web app prototyping
- **Flask/FastAPI**: Production backend API

## Data Sources

Target German supermarket chains:
- Aldi Süd / Aldi Nord
- Lidl Deutschland
- REWE
- Edeka
- Penny Markt
- Netto Marken-Discount
- Kaufland

## Project Structure

```
supermarket-brochure-ai/
├── data/
│   ├── raw/              # Raw PDFs and images
│   │   ├── pdfs/
│   │   └── images/
│   ├── processed/        # Cleaned and standardized data
│   │   ├── pdfs/
│   │   └── images/
│   ├── annotated/        # Manually annotated data
│   │   ├── pdfs/
│   │   └── images/
│   └── metadata/         # JSON metadata files
├── src/
│   ├── data_collection/  # Web scraping and download scripts
│   ├── preprocessing/    # Data cleaning and standardization
│   ├── models/          # Model training and inference
│   ├── evaluation/      # Evaluation metrics and scripts
│   └── webapp/          # Web application code
├── notebooks/           # Jupyter notebooks for experiments
├── configs/            # Configuration files
├── tests/              # Unit and integration tests
├── docs/               # Documentation and images
├── models/             # Saved model checkpoints
│   └── checkpoints/
├── logs/               # Training and application logs
└── outputs/            # Generated outputs and results
```

## Main Challenges

1. **Data Format Variation**: Flyers vary from PDF, images to scanned copies
2. **Layout Variability**: Each retailer designs flyers differently
3. **OCR Noise**: Distorted fonts and price symbols lead to recognition errors
4. **Entity Alignment**: Linking visual blocks with semantic fields
5. **Limited Labeled Data**: Only small subset can be manually annotated

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Data Collection
```bash
# Scrape specific supermarket
python src/data_collection/scrape_brochures.py --supermarket aldi_sued

# Scrape all supermarkets
python src/data_collection/scrape_brochures.py --all

# Scrape with specific options
python src/data_collection/scrape_brochures.py --supermarket rewe --market-id 123456
python src/data_collection/scrape_brochures.py --supermarket edeka --market-url "https://..."
```

### Preprocessing
```bash
# Convert PDFs to images
python src/preprocessing/pdf_converter.py data/raw/pdfs --output-dir data/processed/images

# Process and standardize images
python src/preprocessing/image_processor.py data/raw/images --output-dir data/processed/standardized
```

### OCR Extraction
```bash
# Using PaddleOCR (recommended)
python src/models/ocr_engine.py image.png --engine paddleocr --languages de en

# Using EasyOCR with GPU
python src/models/ocr_engine.py image.png --engine easyocr --gpu --output results.json
```

### Model Training
```bash
# Train LayoutLMv3 with LoRA
python src/models/train.py --train-dir data/annotated/train --val-dir data/annotated/val --use-lora

# Resume from checkpoint
python src/models/train.py --resume models/checkpoints/checkpoint-1000
```

### Web Application

**Option 1: Streamlit (User Interface)**
```bash
streamlit run src/webapp/app.py
```
Then open http://localhost:8501

**Option 2: FastAPI (REST API)**
```bash
cd src/webapp
python api.py
```
API docs: http://localhost:8000/docs

**Option 3: Docker**
```bash
docker-compose up
```
- API: http://localhost:8000
- Web UI: http://localhost:8501

## Expected Outputs

1. **Original image** with detected deal regions highlighted
2. **Structured table or JSON** listing extracted items:
   - Product name
   - Original price
   - Discounted price
   - Discount percentage
   - Valid dates
   - Store location (if available)
3. **Purchase recommendations** (optional, advanced feature)

## Evaluation Metrics

- **F1 Score**: Entity extraction accuracy
- **mAP (mean Average Precision)**: Detection accuracy
- **OCR Accuracy**: Character/word recognition rate
- **Entity Linking Accuracy**: Correct association of text blocks

## Contributors

- Liyang
- Zhaokun

## License

MIT License

## Acknowledgments

This project is part of a university seminar on Document AI and multimodal information extraction.

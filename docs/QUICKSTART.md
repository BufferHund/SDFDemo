# Quick Start Guide

This guide will help you get started with the Supermarket Brochure AI project.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) CUDA-capable GPU for faster processing
- (Optional) Tesseract OCR installed on your system

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd supermarket-brochure-ai
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

### 4. Install System Dependencies

**For PDF processing:**

```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows
# Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases
```

**For Tesseract OCR (optional):**

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-deu

# macOS
brew install tesseract tesseract-lang

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

## Usage

### 1. Data Collection

Scrape brochures from supermarket websites:

```bash
# Scrape Aldi Süd
python src/data_collection/scrape_brochures.py --supermarket aldi_sued

# Scrape REWE
python src/data_collection/scrape_brochures.py --supermarket rewe

# Scrape all
python src/data_collection/scrape_brochures.py --all
```

### 2. Preprocessing

Convert PDFs to images:

```bash
python src/preprocessing/pdf_converter.py data/raw/pdfs/aldi_sued --output-dir data/processed/images
```

Process and standardize images:

```bash
python src/preprocessing/image_processor.py data/processed/images --output-dir data/processed/standardized
```

### 3. OCR Extraction

Extract text from images:

```bash
# Using PaddleOCR (recommended)
python src/models/ocr_engine.py image.png --engine paddleocr --languages de en

# Using EasyOCR
python src/models/ocr_engine.py image.png --engine easyocr --languages de en --gpu

# Using Tesseract
python src/models/ocr_engine.py image.png --engine tesseract --languages de en

# Save results to JSON
python src/models/ocr_engine.py image.png --engine paddleocr --output results.json
```

### 4. Web Application

Launch the Streamlit web interface:

```bash
streamlit run src/webapp/app.py
```

Then open your browser to http://localhost:8501

## Project Workflow

### Week 1-2: Data Collection and Preprocessing

```bash
# Step 1: Scrape brochures
python src/data_collection/scrape_brochures.py --all

# Step 2: Convert PDFs to images
python src/preprocessing/pdf_converter.py data/raw/pdfs --output-dir data/processed/images --recursive

# Step 3: Standardize images
python src/preprocessing/image_processor.py data/processed/images --output-dir data/processed/standardized --recursive
```

### Week 3: Data Annotation

1. Select 10-15 representative brochure pages
2. Use annotation tools (e.g., LabelImg, LabelStudio) to annotate:
   - Product names
   - Prices (original and discounted)
   - Discount percentages
   - Valid dates
3. Save annotations in the defined JSON schema (see `configs/config.yaml`)

### Week 4-5: Model Training

(To be implemented)

```bash
# Fine-tune LayoutLMv3 on annotated data
python src/models/train.py --config configs/layoutlmv3_config.yaml

# Monitor training with TensorBoard
tensorboard --logdir logs
```

### Week 6: Evaluation

(To be implemented)

```bash
# Evaluate model on test set
python src/evaluation/evaluate.py --model models/checkpoints/best_model.pt --test-data data/annotated/test
```

### Week 7-8: Application Development

```bash
# Run web application
streamlit run src/webapp/app.py

# Or use Gradio
python src/webapp/gradio_app.py
```

## Configuration

Edit `configs/config.yaml` to customize:

- Data collection settings
- Preprocessing parameters
- OCR engine preferences
- Model hyperparameters
- Annotation schema

## Troubleshooting

### OCR Engine Issues

**PaddleOCR:**
- If you encounter GPU memory issues, set `use_gpu: false` in config
- For better accuracy, adjust `det_db_thresh` parameter

**Tesseract:**
- Ensure Tesseract is in your PATH
- Install language data: `sudo apt-get install tesseract-ocr-deu`

**EasyOCR:**
- First run downloads models (~100MB) - be patient
- Use `--gpu` flag for faster processing

### PDF Conversion Issues

If PDF conversion fails:
1. Check if poppler is installed: `pdftoppm -v`
2. On Windows, set poppler path: `pdf2image.convert_from_path(..., poppler_path=r'C:\path\to\poppler\bin')`

### Web Application Issues

If Streamlit doesn't start:
1. Check if port 8501 is available
2. Try different port: `streamlit run src/webapp/app.py --server.port 8502`
3. Clear cache: `streamlit cache clear`

## Next Steps

1. **Collect More Data**: Expand to more supermarket chains
2. **Improve Annotations**: Annotate more diverse brochure samples
3. **Fine-tune Models**: Train LayoutLMv3 or Donut on your annotated data
4. **Enhance Application**: Add product recommendation features
5. **Deploy**: Package and deploy the application

## Resources

- [PaddleOCR Documentation](https://github.com/PaddlePaddle/PaddleOCR)
- [LayoutLMv3 Paper](https://arxiv.org/abs/2204.08387)
- [Donut Paper](https://arxiv.org/abs/2111.15664)
- [Streamlit Documentation](https://docs.streamlit.io/)

## Support

For issues and questions:
- Check the [README.md](../README.md)
- Review project documentation in `docs/`
- Open an issue on GitHub

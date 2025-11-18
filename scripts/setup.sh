#!/bin/bash
# Setup script for Supermarket Brochure AI

set -e

echo "🚀 Setting up Supermarket Brochure AI..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for system dependencies
echo "🔍 Checking system dependencies..."

# Check for poppler (PDF processing)
if ! command -v pdftoppm &> /dev/null; then
    echo "⚠️  poppler-utils not found. Install it for PDF processing:"
    echo "   Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "   macOS: brew install poppler"
fi

# Check for tesseract (OCR)
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  tesseract-ocr not found. Install it for Tesseract OCR:"
    echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-deu"
    echo "   macOS: brew install tesseract tesseract-lang"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{raw,processed,annotated}/{pdfs,images}
mkdir -p data/metadata
mkdir -p models/checkpoints
mkdir -p logs
mkdir -p outputs

# Create .gitkeep files
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/annotated/.gitkeep
touch models/checkpoints/.gitkeep
touch logs/.gitkeep
touch outputs/.gitkeep

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run tests: pytest tests/"
echo "  3. Start web app: streamlit run src/webapp/app.py"
echo "  4. Start API: python src/webapp/api.py"
echo ""
echo "For more information, see docs/QUICKSTART.md"

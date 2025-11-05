"""
Setup script for Supermarket Brochure AI project
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="supermarket-brochure-ai",
    version="0.1.0",
    author="Liyang, Zhaokun",
    description="AI system for extracting structured information from supermarket brochures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/supermarket-brochure-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "transformers>=4.30.0",
        "datasets>=2.12.0",
        "pytesseract>=0.3.10",
        "paddleocr>=2.6.1",
        "easyocr>=1.7.0",
        "opencv-python>=4.8.0",
        "pdf2image>=1.16.3",
        "PyPDF2>=3.0.1",
        "pillow>=10.0.0",
        "pdfplumber>=0.9.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "selenium>=4.10.0",
        "pandas>=2.0.3",
        "numpy>=1.24.3",
        "scikit-learn>=1.3.0",
        "matplotlib>=3.7.2",
        "streamlit>=1.25.0",
        "gradio>=3.35.0",
        "tqdm>=4.65.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "jsonschema>=4.18.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.4.1",
            "jupyter>=1.0.0",
        ],
        "training": [
            "peft>=0.4.0",
            "bitsandbytes>=0.41.0",
            "accelerate>=0.20.0",
            "wandb>=0.15.5",
            "tensorboard>=2.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scrape-brochures=src.data_collection.scrape_brochures:main",
            "convert-pdf=src.preprocessing.pdf_converter:main",
            "process-images=src.preprocessing.image_processor:main",
            "extract-ocr=src.models.ocr_engine:main",
        ],
    },
)

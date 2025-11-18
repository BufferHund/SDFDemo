# Dockerfile for Supermarket Brochure AI

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-deu \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/annotated models/checkpoints logs outputs

# Expose port for API
EXPOSE 8000

# Expose port for Streamlit
EXPOSE 8501

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "src.webapp.api:app", "--host", "0.0.0.0", "--port", "8000"]

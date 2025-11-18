"""
FastAPI Backend Service for Brochure Information Extraction

Provides RESTful API endpoints for:
- Uploading brochure images/PDFs
- Running OCR extraction
- Model inference
- Retrieving results
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import uvicorn
import tempfile
import uuid
import json
from PIL import Image
import logging

# Import project modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.ocr_engine import create_ocr_engine
from src.preprocessing.pdf_converter import PDFConverter
from src.models.entity_extractor import EntityExtractor, Deal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Supermarket Brochure AI API",
    description="API for extracting structured information from supermarket brochures",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for results (in production, use a database)
results_store = {}


# Request/Response models
class OCRRequest(BaseModel):
    """OCR extraction request parameters."""
    engine: str = "paddleocr"
    languages: List[str] = ["de", "en"]
    use_gpu: bool = False


class OCRResult(BaseModel):
    """OCR extraction result."""
    text: str
    bbox: List[int]
    confidence: float


class ExtractionResponse(BaseModel):
    """Response for extraction endpoint."""
    task_id: str
    status: str
    message: str


class ResultResponse(BaseModel):
    """Response for result retrieval."""
    task_id: str
    status: str
    ocr_results: Optional[List[Dict]] = None
    entities: Optional[List[Dict]] = None
    deals: Optional[List[Dict]] = None
    error: Optional[str] = None


# Helper functions
def save_uploaded_file(upload_file: UploadFile) -> Path:
    """Save uploaded file to temporary location."""
    suffix = Path(upload_file.filename).suffix
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(upload_file.file.read())
    temp_file.close()
    return Path(temp_file.name)


def process_brochure(
    task_id: str,
    file_path: Path,
    ocr_engine: str,
    languages: List[str],
    use_gpu: bool
):
    """
    Background task to process brochure.

    Args:
        task_id: Unique task identifier
        file_path: Path to uploaded file
        ocr_engine: OCR engine to use
        languages: Languages to recognize
        use_gpu: Whether to use GPU
    """
    try:
        # Update status
        results_store[task_id] = {
            'status': 'processing',
            'ocr_results': None,
            'entities': None,
            'deals': None,
            'error': None
        }

        # Convert PDF to image if needed
        if file_path.suffix.lower() == '.pdf':
            logger.info(f"Converting PDF to images for task {task_id}")
            converter = PDFConverter()
            image_paths = converter.convert_pdf(file_path)

            if not image_paths:
                raise ValueError("Failed to convert PDF")

            # Process first page for now
            image_path = image_paths[0]
        else:
            image_path = file_path

        # Load image
        image = Image.open(image_path).convert('RGB')

        # Run OCR
        logger.info(f"Running OCR for task {task_id}")
        ocr = create_ocr_engine(
            engine_type=ocr_engine,
            languages=languages,
            use_gpu=use_gpu,
            gpu=use_gpu
        )

        ocr_results = ocr.extract_text(image)

        # Extract entities
        logger.info(f"Extracting entities for task {task_id}")
        extractor = EntityExtractor()
        deals = extractor.extract_from_ocr(ocr_results)

        # Convert to dicts
        deals_dict = [deal.to_dict() for deal in deals]

        # Store results
        results_store[task_id] = {
            'status': 'completed',
            'ocr_results': ocr_results,
            'entities': [],  # Would be populated if using model predictions
            'deals': deals_dict,
            'error': None
        }

        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
        results_store[task_id] = {
            'status': 'failed',
            'ocr_results': None,
            'entities': None,
            'deals': None,
            'error': str(e)
        }

    finally:
        # Clean up temporary file
        try:
            file_path.unlink()
        except:
            pass


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Supermarket Brochure AI API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/extract", response_model=ExtractionResponse)
async def extract_brochure(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    engine: str = "paddleocr",
    languages: str = "de,en",
    use_gpu: bool = False
):
    """
    Extract information from uploaded brochure.

    Args:
        file: Uploaded brochure file (image or PDF)
        engine: OCR engine to use (tesseract, paddleocr, easyocr)
        languages: Comma-separated language codes
        use_gpu: Whether to use GPU acceleration

    Returns:
        Task ID for retrieving results
    """
    # Validate file type
    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )

    # Generate task ID
    task_id = str(uuid.uuid4())

    # Save uploaded file
    file_path = save_uploaded_file(file)

    # Parse languages
    lang_list = [lang.strip() for lang in languages.split(',')]

    # Add background task
    background_tasks.add_task(
        process_brochure,
        task_id=task_id,
        file_path=file_path,
        ocr_engine=engine,
        languages=lang_list,
        use_gpu=use_gpu
    )

    return ExtractionResponse(
        task_id=task_id,
        status="pending",
        message="Processing started. Use task_id to retrieve results."
    )


@app.get("/api/results/{task_id}", response_model=ResultResponse)
async def get_results(task_id: str):
    """
    Retrieve extraction results for a task.

    Args:
        task_id: Task identifier from /api/extract

    Returns:
        Extraction results
    """
    if task_id not in results_store:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    result = results_store[task_id]

    return ResultResponse(
        task_id=task_id,
        status=result['status'],
        ocr_results=result.get('ocr_results'),
        entities=result.get('entities'),
        deals=result.get('deals'),
        error=result.get('error')
    )


@app.delete("/api/results/{task_id}")
async def delete_results(task_id: str):
    """
    Delete results for a task.

    Args:
        task_id: Task identifier

    Returns:
        Confirmation message
    """
    if task_id in results_store:
        del results_store[task_id]
        return {"message": "Results deleted successfully"}
    else:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )


@app.get("/api/engines")
async def list_engines():
    """List available OCR engines."""
    return {
        "engines": [
            {
                "name": "tesseract",
                "description": "Tesseract OCR (traditional)",
                "requires_gpu": False
            },
            {
                "name": "paddleocr",
                "description": "PaddleOCR (deep learning, recommended)",
                "requires_gpu": False
            },
            {
                "name": "easyocr",
                "description": "EasyOCR (PyTorch-based)",
                "requires_gpu": False
            }
        ]
    }


@app.get("/api/languages")
async def list_languages():
    """List supported languages."""
    return {
        "languages": [
            {"code": "de", "name": "German"},
            {"code": "en", "name": "English"},
            {"code": "fr", "name": "French"},
            {"code": "es", "name": "Spanish"}
        ]
    }


# Run server
def main():
    """Run the API server."""
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()

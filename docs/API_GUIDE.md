# API Usage Guide

This guide explains how to use the FastAPI backend service for brochure information extraction.

## Starting the API Server

```bash
# Option 1: Using Python directly
cd src/webapp
python api.py

# Option 2: Using uvicorn
uvicorn src.webapp.api:app --host 0.0.0.0 --port 8000 --reload

# Option 3: Using Docker (see Docker section)
docker-compose up
```

The API will be available at http://localhost:8000

Interactive API documentation: http://localhost:8000/docs

## API Endpoints

### 1. Health Check

Check if the API is running.

**Endpoint:** `GET /health`

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### 2. Extract Information from Brochure

Upload a brochure file and start extraction.

**Endpoint:** `POST /api/extract`

**Parameters:**
- `file` (required): Brochure file (PDF, PNG, JPG, JPEG)
- `engine` (optional): OCR engine ('tesseract', 'paddleocr', 'easyocr'), default: 'paddleocr'
- `languages` (optional): Comma-separated language codes, default: 'de,en'
- `use_gpu` (optional): Use GPU acceleration, default: false

**Example:**

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@brochure.pdf" \
  -F "engine=paddleocr" \
  -F "languages=de,en" \
  -F "use_gpu=false"
```

**Response:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Processing started. Use task_id to retrieve results."
}
```

### 3. Get Extraction Results

Retrieve results for a submitted task.

**Endpoint:** `GET /api/results/{task_id}`

**Example:**

```bash
curl http://localhost:8000/api/results/123e4567-e89b-12d3-a456-426614174000
```

**Response (Processing):**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "ocr_results": null,
  "entities": null,
  "deals": null,
  "error": null
}
```

**Response (Completed):**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "ocr_results": [
    {
      "text": "Milch",
      "bbox": [100, 200, 300, 250],
      "confidence": 0.95
    },
    {
      "text": "1.99€",
      "bbox": [350, 200, 450, 250],
      "confidence": 0.98
    }
  ],
  "entities": [],
  "deals": [
    {
      "product_name": "Milch",
      "original_price": null,
      "discounted_price": 1.99,
      "discount_percentage": null,
      "valid_from": null,
      "valid_to": null,
      "store": null,
      "location": null,
      "confidence": 0.95
    }
  ],
  "error": null
}
```

**Response (Failed):**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "failed",
  "ocr_results": null,
  "entities": null,
  "deals": null,
  "error": "Failed to convert PDF"
}
```

### 4. Delete Results

Remove results from storage.

**Endpoint:** `DELETE /api/results/{task_id}`

```bash
curl -X DELETE http://localhost:8000/api/results/123e4567-e89b-12d3-a456-426614174000
```

**Response:**
```json
{
  "message": "Results deleted successfully"
}
```

### 5. List Available OCR Engines

Get information about supported OCR engines.

**Endpoint:** `GET /api/engines`

```bash
curl http://localhost:8000/api/engines
```

**Response:**
```json
{
  "engines": [
    {
      "name": "tesseract",
      "description": "Tesseract OCR (traditional)",
      "requires_gpu": false
    },
    {
      "name": "paddleocr",
      "description": "PaddleOCR (deep learning, recommended)",
      "requires_gpu": false
    },
    {
      "name": "easyocr",
      "description": "EasyOCR (PyTorch-based)",
      "requires_gpu": false
    }
  ]
}
```

### 6. List Supported Languages

Get list of supported language codes.

**Endpoint:** `GET /api/languages`

```bash
curl http://localhost:8000/api/languages
```

**Response:**
```json
{
  "languages": [
    {"code": "de", "name": "German"},
    {"code": "en", "name": "English"},
    {"code": "fr", "name": "French"},
    {"code": "es", "name": "Spanish"}
  ]
}
```

## Python Client Example

```python
import requests
import time

# API base URL
BASE_URL = "http://localhost:8000"

# Upload file and start extraction
with open("brochure.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "engine": "paddleocr",
        "languages": "de,en",
        "use_gpu": False
    }

    response = requests.post(f"{BASE_URL}/api/extract", files=files, data=data)
    result = response.json()
    task_id = result["task_id"]

    print(f"Task started: {task_id}")

# Poll for results
while True:
    response = requests.get(f"{BASE_URL}/api/results/{task_id}")
    result = response.json()

    status = result["status"]
    print(f"Status: {status}")

    if status == "completed":
        print("Extraction completed!")
        print(f"Found {len(result['deals'])} deals:")

        for deal in result["deals"]:
            print(f"  - {deal['product_name']}: €{deal['discounted_price']}")

        break

    elif status == "failed":
        print(f"Extraction failed: {result['error']}")
        break

    # Wait before polling again
    time.sleep(2)

# Clean up
requests.delete(f"{BASE_URL}/api/results/{task_id}")
```

## JavaScript/TypeScript Client Example

```javascript
// Using fetch API
async function extractBrochure(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('engine', 'paddleocr');
  formData.append('languages', 'de,en');

  // Submit extraction task
  const response = await fetch('http://localhost:8000/api/extract', {
    method: 'POST',
    body: formData
  });

  const { task_id } = await response.json();
  console.log(`Task started: ${task_id}`);

  // Poll for results
  while (true) {
    const resultResponse = await fetch(`http://localhost:8000/api/results/${task_id}`);
    const result = await resultResponse.json();

    console.log(`Status: ${result.status}`);

    if (result.status === 'completed') {
      console.log('Extraction completed!');
      console.log('Deals:', result.deals);
      return result;
    } else if (result.status === 'failed') {
      throw new Error(`Extraction failed: ${result.error}`);
    }

    // Wait before polling again
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

// Usage
const fileInput = document.querySelector('input[type="file"]');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  try {
    const results = await extractBrochure(file);
    console.log('Results:', results);
  } catch (error) {
    console.error('Error:', error);
  }
});
```

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid parameters or file type)
- `404`: Resource not found (invalid task_id)
- `500`: Internal server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, there are no rate limits. In production, consider implementing rate limiting to prevent abuse.

## Production Deployment

For production deployment:

1. **Use a production ASGI server:**
   ```bash
   gunicorn src.webapp.api:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Set up a reverse proxy** (nginx, Caddy)

3. **Use a persistent database** instead of in-memory storage

4. **Implement authentication** (API keys, OAuth)

5. **Add HTTPS** with SSL certificates

6. **Configure CORS** properly for your frontend domain

7. **Set up monitoring** and logging

8. **Use Docker/Kubernetes** for containerization

## Troubleshooting

### "Failed to convert PDF"
- Ensure poppler-utils is installed on the system
- Check if the PDF file is valid and not corrupted

### "OCR extraction failed"
- Verify the OCR engine is properly installed
- Check if the image is readable and not too low quality
- Try a different OCR engine

### "Task not found"
- The task_id may have expired or been deleted
- Results are stored in-memory and lost on server restart

### Slow performance
- Enable GPU acceleration if available
- Use a more efficient OCR engine (PaddleOCR is recommended)
- Reduce image resolution during preprocessing

## Support

For issues and feature requests, please open an issue on GitHub.

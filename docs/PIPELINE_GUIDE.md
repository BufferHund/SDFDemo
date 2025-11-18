# Pipeline Guide

Complete guide to the end-to-end brochure processing pipeline.

## Overview

The pipeline provides a unified, configurable workflow for processing supermarket brochures from raw input (PDF/image) to structured deal extraction.

### Pipeline Stages

```
Input (PDF/Image)
    ↓
1. Load & Validate
    ↓
2. PDF Conversion (if needed)
    ↓
3. Image Preprocessing
    ↓
4. Text Extraction (OCR/VLM/Hybrid)
    ↓
5. Entity Extraction
    ↓
6. Result Saving & Visualization
    ↓
Output (JSON + Visualization)
```

## Processing Methods

### 1. OCR Method

Uses traditional OCR engines for text extraction.

**Pros:**
- Fast processing
- Works offline
- No API costs
- Precise bounding boxes

**Cons:**
- Requires post-processing
- May miss context
- Less accurate with complex layouts

**Best for:**
- Simple brochures
- Batch processing
- When speed is priority

### 2. VLM Method

Uses Vision Language Models for semantic understanding.

**Pros:**
- Understands context
- Direct structured output
- Handles complex layouts
- Better accuracy

**Cons:**
- Slower processing
- Requires Ollama server or API key
- Higher resource usage

**Best for:**
- Complex brochures
- When accuracy is critical
- Semantic understanding needed

### 3. Hybrid Method (Recommended)

Combines OCR and VLM for best results.

**Strategy:**
- OCR provides precise text locations
- VLM provides semantic understanding
- Merges results intelligently

**Best for:**
- Production use
- Maximum accuracy
- Balanced performance

## Quick Start

### Command Line

```bash
# Single file - Hybrid method
./brochure_ai.py pipeline brochure.pdf

# Single file - OCR only
./brochure_ai.py pipeline brochure.png --method ocr

# Single file - VLM only
./brochure_ai.py pipeline brochure.png --method vlm --vlm-engine ollama

# Batch processing
./brochure_ai.py pipeline data/brochures/ --batch --report

# Custom configuration
./brochure_ai.py pipeline brochure.pdf \
  --method hybrid \
  --ocr-engine paddleocr \
  --vlm-engine ollama \
  --vlm-model bakllava \
  --output outputs/custom \
  --gpu
```

### Python API

```python
from src.pipeline import create_pipeline

# Simple usage
pipeline = create_pipeline('hybrid')
result = pipeline.process('brochure.pdf')

print(f"Found {len(result.deals)} deals")
for deal in result.deals:
    print(f"- {deal['product_name']}: €{deal['discounted_price']}")
```

## Configuration

### PipelineConfig Options

```python
from src.pipeline import PipelineConfig, ProcessingMethod

config = PipelineConfig(
    # Processing method
    method=ProcessingMethod.HYBRID,  # 'ocr', 'vlm', or 'hybrid'

    # OCR settings
    ocr_engine='paddleocr',  # 'tesseract', 'paddleocr', 'easyocr'
    ocr_languages=['de', 'en'],
    ocr_use_gpu=False,

    # VLM settings
    vlm_engine='ollama',  # 'ollama' or 'gemini'
    vlm_model='llava:latest',
    vlm_api_key=None,  # For Gemini

    # Preprocessing
    preprocess_images=True,
    target_size=(1024, 1448),
    enhance_images=True,

    # Output
    output_dir='outputs/pipeline',
    save_intermediate=False,
    save_visualizations=True,

    # Performance
    batch_size=1,
    max_workers=4
)
```

## Usage Examples

### Example 1: Basic OCR Pipeline

```python
from src.pipeline import create_pipeline

# Create OCR pipeline
pipeline = create_pipeline(
    method='ocr',
    ocr_engine='paddleocr'
)

# Process brochure
result = pipeline.process('brochure.png')

# Check result
if result.success:
    print(f"Found {len(result.deals)} deals")
    print(f"Processing time: {result.processing_time:.2f}s")
else:
    print(f"Error: {result.error}")
```

### Example 2: VLM Pipeline with Ollama

```python
from src.pipeline import create_pipeline

# Create VLM pipeline
pipeline = create_pipeline(
    method='vlm',
    vlm_engine='ollama',
    vlm_model='llava:latest'
)

result = pipeline.process('brochure.png')

for deal in result.deals:
    print(f"{deal['product_name']}: €{deal['discounted_price']}")
```

### Example 3: Hybrid Pipeline

```python
from src.pipeline import create_pipeline

# Best of both worlds
pipeline = create_pipeline(
    method='hybrid',
    ocr_engine='paddleocr',
    vlm_engine='ollama',
    vlm_model='bakllava'
)

result = pipeline.process('brochure.pdf')
```

### Example 4: Custom Configuration

```python
from src.pipeline import BrochurePipeline, PipelineConfig, ProcessingMethod

config = PipelineConfig(
    method=ProcessingMethod.HYBRID,
    ocr_engine='paddleocr',
    ocr_languages=['de', 'en', 'fr'],
    ocr_use_gpu=True,
    vlm_engine='gemini',
    vlm_model='gemini-1.5-flash',
    vlm_api_key='your-api-key',
    enhance_images=True,
    save_visualizations=True,
    output_dir='outputs/custom'
)

pipeline = BrochurePipeline(config)
result = pipeline.process('brochure.pdf')
```

### Example 5: Batch Processing

```python
from src.pipeline import BatchProcessor, PipelineConfig

config = PipelineConfig(method='hybrid')
processor = BatchProcessor(config=config, max_workers=4)

# Process directory
result = processor.process_directory(
    'data/brochures',
    pattern='*.png',
    recursive=True
)

print(f"Success rate: {result.success_rate:.1f}%")
print(f"Total time: {result.total_time:.2f}s")
```

### Example 6: Generate Report

```python
from src.pipeline import BatchProcessor, PipelineConfig

config = PipelineConfig(method='hybrid')
processor = BatchProcessor(config=config)

# Process files
files = ['brochure1.pdf', 'brochure2.png', 'brochure3.pdf']
result = processor.process(files)

# Generate detailed report
processor.generate_report(result, 'outputs/report')

# Report includes:
# - summary.json: Statistics
# - all_deals.json: All deals from all files
# - report.md: Markdown report with tables
# - failed_files.txt: List of failures
```

## Output Structure

### Directory Layout

```
outputs/pipeline/
├── brochure1/
│   ├── result.json          # Complete result
│   ├── deals.json           # Extracted deals only
│   └── visualization.png    # Annotated image
├── brochure2/
│   └── ...
└── report/                  # Batch report
    ├── summary.json
    ├── all_deals.json
    ├── report.md
    └── failed_files.txt
```

### Result JSON Format

```json
{
  "input_path": "brochure.pdf",
  "success": true,
  "processing_time": 3.45,
  "method": "hybrid",
  "timestamp": "2024-11-18T10:30:00",
  "deals": [
    {
      "product_name": "Fresh Strawberries",
      "original_price": 4.99,
      "discounted_price": 2.99,
      "discount_percentage": 40,
      "valid_from": "2024-11-18",
      "valid_to": "2024-11-24"
    }
  ]
}
```

## Performance Tuning

### GPU Acceleration

```python
# Enable GPU for OCR
config = PipelineConfig(
    ocr_use_gpu=True,
    ocr_engine='paddleocr'  # Best GPU support
)
```

### Parallel Processing

```python
# Batch processing with multiple workers
processor = BatchProcessor(
    config=config,
    max_workers=8  # Adjust based on CPU cores
)
```

### Disable Visualizations

```python
# Skip visualization generation for speed
config = PipelineConfig(
    save_visualizations=False
)
```

### Skip Preprocessing

```python
# If images are already optimized
config = PipelineConfig(
    preprocess_images=False,
    enhance_images=False
)
```

## Troubleshooting

### Issue: PDF Conversion Fails

**Solution:**
```bash
# Install poppler
sudo apt-get install poppler-utils  # Ubuntu/Debian
brew install poppler  # macOS
```

### Issue: Ollama Connection Error

**Solution:**
```bash
# Start Ollama server
ollama serve

# Pull model
ollama pull llava

# Check status
curl http://localhost:11434/api/tags
```

### Issue: Gemini API Error

**Solution:**
```bash
# Set API key
export GEMINI_API_KEY="your-api-key"

# Or in code
config = PipelineConfig(
    vlm_engine='gemini',
    vlm_api_key='your-api-key'
)
```

### Issue: Out of Memory

**Solutions:**
1. Reduce max_workers
2. Process smaller batches
3. Disable preprocessing
4. Use smaller VLM model

```python
# Reduce memory usage
config = PipelineConfig(
    preprocess_images=False,
    save_intermediate=False,
    vlm_model='llava:7b'  # Instead of llava:13b
)

processor = BatchProcessor(
    config=config,
    max_workers=2  # Reduce workers
)
```

### Issue: Slow Processing

**Solutions:**
1. Use OCR-only method
2. Enable GPU
3. Increase workers
4. Use faster VLM model

```python
# Speed optimizations
config = PipelineConfig(
    method='ocr',  # Fastest
    ocr_use_gpu=True,
    vlm_model='gemini-1.5-flash'  # Fast cloud VLM
)

processor = BatchProcessor(
    config=config,
    max_workers=8
)
```

## Advanced Usage

### Custom Merge Strategy

```python
from src.pipeline import BrochurePipeline

class CustomPipeline(BrochurePipeline):
    def _merge_results(self, ocr_results, vlm_results):
        """Custom merge logic."""
        # Example: Spatial matching
        ocr_deals = self._extract_entities_from_ocr(ocr_results)
        vlm_deals = vlm_results.get('deals', [])

        # Your custom matching logic here
        merged = []
        # ...

        return merged
```

### Pipeline Hooks

```python
from src.pipeline import BrochurePipeline

class HookedPipeline(BrochurePipeline):
    def process(self, input_path, output_name=None):
        # Pre-processing hook
        self.on_before_process(input_path)

        # Run pipeline
        result = super().process(input_path, output_name)

        # Post-processing hook
        self.on_after_process(result)

        return result

    def on_before_process(self, path):
        print(f"Starting: {path}")

    def on_after_process(self, result):
        print(f"Finished: {result.success}")
```

## Best Practices

### 1. Choose the Right Method

- **Development/Testing**: OCR (fast iteration)
- **Production**: Hybrid (best accuracy)
- **Complex Brochures**: VLM (semantic understanding)
- **Simple Brochures**: OCR (speed)

### 2. Optimize Configuration

```python
# Development
dev_config = PipelineConfig(
    method='ocr',
    save_visualizations=True,
    save_intermediate=True
)

# Production
prod_config = PipelineConfig(
    method='hybrid',
    ocr_use_gpu=True,
    save_visualizations=False,
    max_workers=8
)
```

### 3. Error Handling

```python
def robust_processing(files):
    pipeline = create_pipeline('hybrid')

    results = []
    for file_path in files:
        try:
            result = pipeline.process(file_path)
            results.append(result)
        except Exception as e:
            print(f"Failed {file_path}: {e}")
            continue

    return results
```

### 4. Monitoring

```python
from src.pipeline import BatchProcessor

processor = BatchProcessor(config=config)
result = processor.process_directory('data/brochures')

# Monitor metrics
print(f"Success rate: {result.success_rate:.1f}%")
print(f"Avg time: {result.avg_time:.2f}s")
print(f"Failed: {result.failed}")

# Generate report for analysis
processor.generate_report(result, 'outputs/monitoring')
```

## Integration

### With Web API

```python
from fastapi import FastAPI, UploadFile
from src.pipeline import create_pipeline

app = FastAPI()
pipeline = create_pipeline('hybrid')

@app.post("/api/process")
async def process_brochure(file: UploadFile):
    # Save uploaded file
    file_path = f"temp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Process
    result = pipeline.process(file_path)

    return result.to_dict()
```

### With Streamlit

```python
import streamlit as st
from src.pipeline import create_pipeline

st.title("Brochure Analyzer")

uploaded = st.file_uploader("Upload brochure", type=['pdf', 'png', 'jpg'])
method = st.selectbox("Method", ['ocr', 'vlm', 'hybrid'])

if uploaded and st.button("Process"):
    pipeline = create_pipeline(method)
    result = pipeline.process(uploaded)

    st.json(result.to_dict())
```

## See Also

- [CLI Usage Guide](CLI_USAGE.md)
- [VLM Guide](VLM_GUIDE.md)
- [API Guide](API_GUIDE.md)
- [Examples](../examples/pipeline_examples.py)

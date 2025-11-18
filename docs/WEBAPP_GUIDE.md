# Web Application Guide

Complete guide to the interactive web interface for Supermarket Brochure AI.

## Overview

The project includes two web interfaces:

1. **Enhanced Interface** (Recommended) - Full-featured with pipeline integration
2. **Basic Interface** - Simple OCR-only interface

## Quick Start

### Method 1: Using Launch Script

```bash
# Enhanced interface (default)
./run_webapp.sh

# Or explicitly
./run_webapp.sh enhanced

# Basic interface
./run_webapp.sh basic
```

### Method 2: Direct Streamlit

```bash
# Enhanced interface
streamlit run src/webapp/app_enhanced.py

# Basic interface
streamlit run src/webapp/app.py
```

### Method 3: Using Unified CLI

```bash
# Enhanced interface
./brochure_ai.py serve --web

# With custom port
./brochure_ai.py serve --web --port 8502
```

The interface will open automatically at http://localhost:8501

## Enhanced Interface Features

### 1. Single File Processing Tab 📄

**Purpose**: Process individual brochures with full control over settings.

**Features**:
- Three processing methods (OCR/VLM/Hybrid)
- Real-time processing with progress bar
- Visual deal highlighting on images
- Interactive deal cards with pricing information
- Multiple export formats (JSON/CSV/TXT)
- Comprehensive statistics

**Usage**:
1. Select processing method:
   - **Hybrid**: Best accuracy (recommended)
   - **OCR**: Fastest processing
   - **VLM**: Best semantic understanding

2. Configure engines:
   - OCR Engine: paddleocr, tesseract, or easyocr
   - VLM Engine: ollama or gemini

3. Advanced settings (optional):
   - GPU acceleration
   - Image preprocessing
   - Visualization options
   - Custom VLM model

4. Upload brochure (PNG/JPG/PDF)

5. Click "Process Brochure"

6. View results:
   - Metrics (deals found, processing time, savings)
   - Highlighted image with deal overlays
   - Interactive deal cards
   - Export options

**Example Workflow**:
```
Upload brochure.pdf
  ↓
Select "Hybrid" method
  ↓
Click "Process Brochure"
  ↓
View 12 deals found in 3.5s
  ↓
Download results as JSON
```

### 2. Batch Processing Tab 📦

**Purpose**: Process multiple brochures efficiently with parallel execution.

**Features**:
- Upload multiple files at once
- Parallel processing with configurable workers
- Real-time progress tracking
- Success/failure statistics
- Comprehensive batch reports
- Aggregated results export

**Usage**:
1. Select processing method

2. Configure parallel workers (1-8)
   - More workers = faster processing
   - Recommended: 4 workers for most systems

3. Enable "Generate Report" for detailed analysis

4. Upload multiple brochures

5. Click "Process All Files"

6. Monitor progress:
   - Overall progress bar
   - Individual file status
   - Success/failure counts

7. Review results:
   - Batch statistics
   - Individual file results
   - Aggregated deals

8. Export:
   - Summary JSON
   - All deals CSV
   - Individual file results

**Example Workflow**:
```
Upload 50 brochures
  ↓
Set workers to 4
  ↓
Click "Process All Files"
  ↓
48/50 successful (96%)
  ↓
Download aggregated deals CSV
```

### 3. Method Comparison Tab ⚖️

**Purpose**: Compare OCR, VLM, and Hybrid methods side-by-side on the same brochure.

**Features**:
- Simultaneous processing with all three methods
- Side-by-side comparison
- Performance metrics (speed, accuracy)
- Detailed results for each method

**Usage**:
1. Upload a brochure

2. Click "Run Comparison"

3. Wait for all three methods to complete

4. Review comparison:
   - Number of deals found
   - Processing time
   - Success status
   - Detailed results

5. Expand each method to see extracted deals

**Use Cases**:
- Evaluate which method works best for your brochures
- Understand speed vs accuracy trade-offs
- Quality assurance and validation
- Choosing optimal settings

**Example Results**:
```
OCR:    15 deals in 1.2s
VLM:    18 deals in 5.3s
Hybrid: 19 deals in 6.1s
```

## Visual Features

### Deal Highlighting

Deals are highlighted on the original brochure image with:
- Dark semi-transparent background
- Product name in white
- Price in green (€XX.XX format)
- Discount percentage in red badge
- Numbered for easy reference

### Deal Cards

Interactive cards displaying:
- 🏷️ Product name
- 💰 Discounted price (large, red)
- ~~Original price~~ (strikethrough)
- Discount badge (e.g., "-40%")
- 📅 Validity dates (if available)
- Styled with color-coded backgrounds

### Metrics Display

Real-time metrics shown as cards:
- **Deals Found**: Total number of extracted deals
- **Processing Time**: Seconds elapsed
- **Total Savings**: Sum of all discounts
- **Success Rate**: For batch processing

## Configuration Options

### Processing Methods

**OCR Method**:
```
Pros:
- Fast (1-3 seconds per brochure)
- Works offline
- No API costs
- GPU acceleration available

Cons:
- Requires entity extraction
- May miss semantic context
- Lower accuracy on complex layouts

Best for:
- Simple brochures
- Batch processing
- Limited resources
```

**VLM Method**:
```
Pros:
- High accuracy
- Semantic understanding
- Direct structured output
- Handles complex layouts

Cons:
- Slower (3-10 seconds per brochure)
- Requires Ollama server or Gemini API
- Higher resource usage

Best for:
- Complex brochures
- Maximum accuracy needed
- Semantic analysis
```

**Hybrid Method** (Recommended):
```
Pros:
- Best overall accuracy
- Combines OCR precision with VLM intelligence
- Balanced performance

Cons:
- Longest processing time
- Requires both OCR and VLM

Best for:
- Production use
- Critical applications
- Comprehensive extraction
```

### OCR Engines

**PaddleOCR** (Recommended):
- Multi-language support (80+ languages)
- GPU acceleration
- High accuracy
- Good for German text

**Tesseract**:
- Open source
- Fast
- Good for English
- Lower accuracy on complex fonts

**EasyOCR**:
- PyTorch-based
- Good language support
- Medium speed and accuracy

### VLM Engines

**Ollama** (Recommended for local):
- Free
- Runs locally
- Privacy-friendly
- Models: llava, bakllava, llava:13b

**Gemini**:
- Cloud-based
- Fast processing
- Requires API key
- Models: gemini-1.5-flash, gemini-1.5-pro

## Advanced Settings

### GPU Acceleration

Enable GPU for OCR processing:
```
Benefits:
- 2-5x faster processing
- Better for batch operations
- Requires CUDA-compatible GPU

Requirements:
- NVIDIA GPU
- CUDA toolkit installed
- PaddlePaddle-GPU or EasyOCR
```

### Image Preprocessing

Enable/disable image preprocessing:
```
When enabled:
- Resize to optimal dimensions
- Enhance contrast
- Sharpen text
- Normalize brightness

When to disable:
- Images already optimized
- Need original quality
- Faster processing required
```

### Custom VLM Models

Specify custom Ollama models:
```
Available models:
- llava:latest (7B, default)
- llava:13b (better accuracy, slower)
- llava:34b (best accuracy, much slower)
- bakllava (specialized for documents)

Usage:
Enter model name in "VLM Model" field
Example: bakllava
```

## Export Formats

### JSON Export

Full detailed results:
```json
{
  "input_path": "brochure.pdf",
  "success": true,
  "processing_time": 3.45,
  "method": "hybrid",
  "deals": [
    {
      "product_name": "Fresh Strawberries",
      "discounted_price": 2.99,
      "original_price": 4.99,
      "discount_percentage": 40,
      "valid_from": "2024-11-18",
      "valid_to": "2024-11-24"
    }
  ]
}
```

### CSV Export

Tabular format for Excel/spreadsheets:
```csv
product_name,discounted_price,original_price,discount_percentage,valid_from,valid_to
Fresh Strawberries,2.99,4.99,40,2024-11-18,2024-11-24
```

### TXT Report

Human-readable summary:
```
Brochure Analysis Report
Generated: 2024-11-18 10:30:00
Method: hybrid
Processing Time: 3.45s
Deals Found: 12

Deals:
1. Fresh Strawberries
   Price: €2.99 (-40%)
```

## Performance Tips

### For Fast Processing
```python
Method: OCR
Engine: PaddleOCR
GPU: Enabled
Workers: 8 (batch mode)
Preprocessing: Disabled
```

### For Maximum Accuracy
```python
Method: Hybrid
OCR Engine: PaddleOCR
VLM Engine: Ollama (llava:13b)
Preprocessing: Enabled
```

### For Resource-Constrained Systems
```python
Method: OCR
Engine: Tesseract
GPU: Disabled
Workers: 2
Preprocessing: Disabled
```

## Troubleshooting

### Issue: Webapp won't start

**Solution**:
```bash
# Check if streamlit is installed
pip install streamlit

# Check if port is in use
lsof -i :8501

# Use different port
streamlit run src/webapp/app_enhanced.py --server.port 8502
```

### Issue: Ollama connection error

**Solution**:
```bash
# Start Ollama server
ollama serve

# Check if running
curl http://localhost:11434/api/tags

# Pull model if needed
ollama pull llava
```

### Issue: No deals found

**Possible causes**:
1. Brochure quality too low
   - Solution: Use higher resolution images
   - Enable preprocessing

2. Wrong language settings
   - Solution: Add correct language in settings
   - German brochures: ensure 'de' is selected

3. OCR engine not suitable
   - Solution: Try different OCR engine
   - Use VLM method instead

### Issue: Processing too slow

**Solutions**:
1. Enable GPU acceleration
2. Use OCR-only method
3. Disable preprocessing
4. Reduce image size
5. Use faster VLM model (gemini-1.5-flash)

### Issue: Out of memory (batch processing)

**Solutions**:
1. Reduce number of workers
2. Process in smaller batches
3. Disable preprocessing
4. Use lighter VLM model

## Keyboard Shortcuts

While in the webapp:

- `R` - Rerun the app
- `Ctrl + C` (in terminal) - Stop server
- `Ctrl + Shift + R` - Clear cache and rerun

## Browser Compatibility

Tested and supported:
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ⚠️ IE 11 (Limited support)

## Mobile Support

The interface is responsive and works on mobile devices:
- Simplified layout on small screens
- Touch-friendly buttons
- Vertical scrolling for results

## API Alternative

For programmatic access, use the FastAPI backend:

```bash
# Start API server
./brochure_ai.py serve --api

# Or directly
cd src/webapp && python api.py
```

API docs: http://localhost:8000/docs

## Best Practices

### 1. Start Simple
- Begin with single file processing
- Try all three methods
- Understand the differences

### 2. Optimize Settings
- Test different engines
- Enable GPU if available
- Adjust workers for batch processing

### 3. Quality Control
- Use comparison tab to validate
- Review extracted deals manually
- Adjust confidence thresholds

### 4. Production Use
- Use Hybrid method
- Enable batch processing
- Generate reports for auditing

## Examples

### Example 1: Quick Analysis

```
1. Upload: weekly_brochure.pdf
2. Method: Hybrid (default)
3. Click: "Process Brochure"
4. Wait: 3-5 seconds
5. Review: 15 deals found
6. Download: deals.json
```

### Example 2: Weekly Batch Processing

```
1. Collect: All weekly brochures (5 stores)
2. Method: Hybrid
3. Workers: 4
4. Upload: All 5 files
5. Process: ~30 seconds total
6. Download: all_deals.csv
7. Import: Into Excel/database
```

### Example 3: Method Evaluation

```
1. Upload: test_brochure.png
2. Tab: "Compare Methods"
3. Click: "Run Comparison"
4. Review: OCR=12, VLM=14, Hybrid=15 deals
5. Decision: Use Hybrid for production
```

## See Also

- [Pipeline Guide](PIPELINE_GUIDE.md) - Programmatic usage
- [CLI Usage](CLI_USAGE.md) - Command-line interface
- [API Guide](API_GUIDE.md) - REST API documentation
- [VLM Guide](VLM_GUIDE.md) - Vision Language Models

## Support

For issues or questions:
1. Check this guide
2. Review troubleshooting section
3. Check project documentation
4. Open GitHub issue

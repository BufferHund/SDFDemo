# Vision Language Model (VLM) Integration Guide

This guide covers the use of Vision Language Models for intelligent brochure analysis.

## Supported VLM Engines

### 1. Ollama (Local, Free)
- **Models**: LLaVA, Bakllava, LLaVA 13B/34B
- **Cost**: Free, runs locally
- **Privacy**: Complete data privacy
- **Speed**: Fast (depends on hardware)

### 2. Gemini API (Cloud, Paid)
- **Models**: Gemini 1.5 Flash, Gemini 1.5 Pro
- **Cost**: Pay per API call
- **Privacy**: Data sent to Google
- **Speed**: Very fast, no local GPU needed

## Installation

### PaddleOCR
```bash
pip install paddleocr paddlepaddle
```

### Ollama Setup

1. **Install Ollama**:
```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Or download from: https://ollama.ai/download
```

2. **Pull a vision model**:
```bash
# LLaVA (7B - recommended for most users)
ollama pull llava

# Bakllava (specialized for OCR tasks)
ollama pull bakllava

# LLaVA 13B (better quality, needs more RAM)
ollama pull llava:13b

# LLaVA 34B (best quality, needs 32GB+ RAM)
ollama pull llava:34b
```

3. **Start Ollama server**:
```bash
ollama serve
```

The server will run at `http://localhost:11434`

### Gemini API Setup

1. **Get API Key**:
   - Visit: https://makersuite.google.com/app/apikey
   - Create a new API key

2. **Set environment variable**:
```bash
export GEMINI_API_KEY="your-api-key-here"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export GEMINI_API_KEY="your-api-key"' >> ~/.bashrc
```

3. **Install Python package**:
```bash
pip install google-generativeai
```

## Usage

### Command Line

#### Using Ollama
```bash
# Basic usage (default: llava:latest)
python src/models/vlm_engine.py brochure.png --engine ollama

# Specify model
python src/models/vlm_engine.py brochure.png --engine ollama --model bakllava

# Save results
python src/models/vlm_engine.py brochure.png --engine ollama --output results.json

# Custom prompt
python src/models/vlm_engine.py brochure.png --engine ollama \
  --prompt "List all products with prices from this image"
```

#### Using Gemini
```bash
# With API key
python src/models/vlm_engine.py brochure.png --engine gemini --api-key YOUR_KEY

# Using environment variable
python src/models/vlm_engine.py brochure.png --engine gemini

# Different model
python src/models/vlm_engine.py brochure.png --engine gemini --model gemini-1.5-pro
```

#### Using Unified CLI
```bash
# Ollama
./brochure_ai.py analyze brochure.png --vlm ollama

# Gemini
./brochure_ai.py analyze brochure.png --vlm gemini
```

### Python API

#### Ollama Example
```python
from src.models.vlm_engine import create_vlm_engine

# Create Ollama VLM
vlm = create_vlm_engine('ollama', model_name='llava:latest')

# Analyze image
result = vlm.analyze_image('brochure.png')

# Print deals
for deal in result['deals']:
    print(f"{deal['product_name']}: €{deal['discounted_price']}")
```

#### Gemini Example
```python
from src.models.vlm_engine import create_vlm_engine
import os

# Set API key
os.environ['GEMINI_API_KEY'] = 'your-key'

# Create Gemini VLM
vlm = create_vlm_engine('gemini', model_name='gemini-1.5-flash')

# Analyze with custom prompt
result = vlm.analyze_image(
    'brochure.png',
    prompt="Extract all product prices from this brochure",
    temperature=0.1
)

print(result)
```

#### Custom Prompts
```python
# Detailed extraction
custom_prompt = """
Analyze this supermarket brochure carefully.

Extract:
1. All product names
2. Prices (original and sale)
3. Discount percentages
4. Valid dates
5. Any special conditions (e.g., "while supplies last")

Format as JSON with this structure:
{
  "deals": [
    {
      "product_name": "...",
      "original_price": 0.00,
      "discounted_price": 0.00,
      "discount_percentage": 0,
      "valid_from": "YYYY-MM-DD",
      "valid_to": "YYYY-MM-DD",
      "conditions": "..."
    }
  ]
}
"""

result = vlm.analyze_image('brochure.png', prompt=custom_prompt)
```

### Configuration File

Edit `configs/config.yaml`:

```yaml
vlm:
  engine: "ollama"  # or "gemini"
  temperature: 0.1

  ollama:
    base_url: "http://localhost:11434"
    model: "llava:latest"
    timeout: 60

  gemini:
    model: "gemini-1.5-flash"
    max_output_tokens: 2048
```

## Model Comparison

### Ollama Models

| Model | Size | RAM Needed | Speed | Quality | Best For |
|-------|------|------------|-------|---------|----------|
| llava | 7B | 8GB | Fast | Good | General use |
| bakllava | 7B | 8GB | Fast | Better OCR | Text-heavy images |
| llava:13b | 13B | 16GB | Medium | Very Good | Better accuracy |
| llava:34b | 34B | 32GB | Slow | Excellent | Best quality |

### Gemini Models

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| gemini-1.5-flash | Very Fast | $0.00015/image | Good | High volume |
| gemini-1.5-pro | Fast | $0.0025/image | Excellent | Best quality |

## Comparison: OCR vs VLM

### Traditional OCR (PaddleOCR, Tesseract)
**Pros:**
- Fast
- Free
- Works offline
- Simple text extraction

**Cons:**
- Requires post-processing
- May miss context
- Struggles with complex layouts
- Needs entity linking

**Best for:**
- Simple brochures
- When you need bounding boxes
- Batch processing

### Vision Language Models (VLM)
**Pros:**
- Understands context
- Direct structured output
- Handles complex layouts
- No entity linking needed
- Better with handwriting

**Cons:**
- Slower (especially large models)
- May require GPU (Ollama) or API costs (Gemini)
- Less precise bounding boxes

**Best for:**
- Complex brochures
- When you need semantic understanding
- When accuracy is more important than speed

## Hybrid Approach (Recommended)

Use both for best results:

```python
from src.models.ocr_engine import create_ocr_engine
from src.models.vlm_engine import create_vlm_engine

# 1. Use OCR for text detection
ocr = create_ocr_engine('paddleocr')
ocr_results = ocr.extract_text('brochure.png')

# 2. Use VLM for semantic understanding
vlm = create_vlm_engine('ollama')
vlm_results = vlm.analyze_image('brochure.png')

# 3. Combine results
# OCR provides precise locations
# VLM provides semantic understanding
```

## Tips & Best Practices

### For Ollama

1. **Choose the right model**:
   - Start with `llava` for testing
   - Use `bakllava` for text-heavy brochures
   - Upgrade to `llava:13b` if you have RAM

2. **Optimize performance**:
   ```bash
   # Use GPU if available
   OLLAMA_GPU_LAYERS=35 ollama serve

   # Increase context
   OLLAMA_NUM_CTX=4096 ollama serve
   ```

3. **Monitor resources**:
   ```bash
   # Check GPU usage
   nvidia-smi

   # Check RAM
   htop
   ```

### For Gemini

1. **Cost optimization**:
   - Use `gemini-1.5-flash` for testing
   - Batch process images
   - Cache results

2. **Rate limiting**:
   - Free tier: 60 requests/minute
   - Paid tier: Higher limits

3. **Error handling**:
   ```python
   try:
       result = vlm.analyze_image('image.png')
   except Exception as e:
       print(f"API error: {e}")
       # Fallback to OCR
   ```

## Troubleshooting

### Ollama Issues

**Server not running:**
```bash
# Start server
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

**Model not found:**
```bash
# List installed models
ollama list

# Pull model
ollama pull llava
```

**Out of memory:**
- Try smaller model: `llava` instead of `llava:13b`
- Reduce concurrent requests
- Close other applications

### Gemini Issues

**API key not set:**
```bash
echo $GEMINI_API_KEY
# Should show your key

# Set it
export GEMINI_API_KEY="your-key"
```

**Rate limit exceeded:**
- Wait a minute
- Upgrade to paid tier
- Implement exponential backoff

**Invalid API key:**
- Regenerate key at https://makersuite.google.com/app/apikey
- Check for typos

## Examples

### Example 1: Compare All Methods

```python
from src.models.ocr_engine import create_ocr_engine
from src.models.vlm_engine import create_vlm_engine

image = 'brochure.png'

# Method 1: PaddleOCR
print("=== PaddleOCR ===")
ocr = create_ocr_engine('paddleocr')
ocr_result = ocr.extract_text(image)
print(f"Found {len(ocr_result)} text regions")

# Method 2: Ollama
print("\n=== Ollama (LLaVA) ===")
ollama = create_vlm_engine('ollama')
ollama_result = ollama.analyze_image(image)
print(f"Found {len(ollama_result['deals'])} deals")

# Method 3: Gemini
print("\n=== Gemini ===")
gemini = create_vlm_engine('gemini')
gemini_result = gemini.analyze_image(image)
print(f"Found {len(gemini_result['deals'])} deals")
```

### Example 2: Production Pipeline

```python
def analyze_brochure_robust(image_path):
    """Robust brochure analysis with fallback."""

    try:
        # Try Ollama first (free, local)
        vlm = create_vlm_engine('ollama')
        result = vlm.analyze_image(image_path)

        if result['deals']:
            return result
    except Exception as e:
        print(f"Ollama failed: {e}")

    try:
        # Fallback to Gemini
        vlm = create_vlm_engine('gemini')
        result = vlm.analyze_image(image_path)

        if result['deals']:
            return result
    except Exception as e:
        print(f"Gemini failed: {e}")

    # Final fallback: OCR + rule-based extraction
    ocr = create_ocr_engine('paddleocr')
    ocr_result = ocr.extract_text(image_path)

    from src.models.entity_extractor import EntityExtractor
    extractor = EntityExtractor()
    deals = extractor.extract_from_ocr(ocr_result)

    return {'deals': [d.to_dict() for d in deals]}
```

## See Also

- [OCR Engine Documentation](../src/models/ocr_engine.py)
- [Entity Extractor Documentation](../src/models/entity_extractor.py)
- [API Usage Guide](API_GUIDE.md)
- [Ollama Documentation](https://ollama.ai/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)

## Pipeline Optimization and Testing Guide

Complete guide to the optimized pipeline system with validation, monitoring, and testing.

## New Features

### 1. Enhanced Logging System

**Location**: `src/utils/enhanced_logger.py`

**Features**:
- Colored console output
- JSON structured logging
- Performance tracking
- Context managers for operations
- Automatic log rotation

**Usage**:
```python
from src.utils.enhanced_logger import get_logger

# Create logger
logger = get_logger('my_module', log_dir='logs')

# Basic logging
logger.info("Processing started")
logger.error("Something went wrong", error_code=500)

# Timed operations
with logger.timed_operation('pdf_conversion'):
    convert_pdf(file)  # Automatically logs duration

# Pipeline steps
with logger.step('OCR extraction'):
    results = ocr.extract(image)  # Logs start and completion

# Log dictionaries
logger.log_dict("Configuration", {'engine': 'paddle', 'gpu': True})

# Performance summary
logger.log_performance_summary()
```

**Output Example**:
```
2024-11-18 10:30:15 | INFO     | pipeline.hybrid | Starting: pdf_conversion
2024-11-18 10:30:18 | INFO     | pipeline.hybrid | Completed: pdf_conversion in 3.125s
```

### 2. Pipeline Validation

**Location**: `src/pipeline/validator.py`

#### System Validation

Check system requirements and dependencies:

```python
from src.pipeline import SystemValidator, run_full_validation

# Quick validation
success = run_full_validation()

# Custom validation
validator = SystemValidator()
results = validator.run_all_checks()
validator.print_summary()
```

**Checks**:
- ✓ Python version (≥ 3.8)
- ✓ Required dependencies (PaddleOCR, PIL, etc.)
- ✓ Optional dependencies (EasyOCR, Tesseract, etc.)
- ✓ GPU availability
- ✓ Disk space (≥ 1 GB)
- ✓ Available memory (≥ 2 GB)
- ✓ Ollama server status
- ✓ Gemini API availability

#### Input Validation

Validate files before processing:

```python
from src.pipeline import InputValidator

# Validate image
result = InputValidator.validate_image('brochure.png')
if result.passed:
    print(f"✓ {result.message}")
    print(f"  Size: {result.details['width']}x{result.details['height']}")
else:
    print(f"✗ {result.message}")

# Validate PDF
result = InputValidator.validate_pdf('brochure.pdf')

# Validate batch
file_paths = ['file1.png', 'file2.pdf', 'file3.jpg']
results = InputValidator.validate_batch_inputs(file_paths)

for r in results:
    status = "✓" if r.passed else "✗"
    print(f"{status} {r.message}")
```

**Validation Criteria**:
- File exists and is readable
- Correct file format
- Image dimensions (min: 100x100, warns if > 10000x10000)
- PDF file size (warns if > 50 MB)

#### Output Validation

Validate extracted deals:

```python
from src.pipeline import OutputValidator

deals = result.deals
validation = OutputValidator.validate_deals(deals)

if validation.details and 'issues' in validation.details:
    for issue in validation.details['issues']:
        print(f"⚠ {issue}")
```

**Validation Checks**:
- Required fields present (product_name)
- Price values are valid numbers
- Prices are non-negative
- Discount percentages are 0-100

#### Health Checks

Check component availability:

```python
from src.pipeline import PipelineHealthCheck

health = PipelineHealthCheck()
results = health.run_health_check()

for result in results:
    print(f"{'✓' if result.passed else '✗'} {result.message}")

# Check if pipeline is healthy
if health.is_healthy():
    print("Pipeline ready!")
```

### 3. Performance Monitoring

**Location**: `src/pipeline/monitor.py`

Track performance metrics in real-time:

```python
from src.pipeline import PipelineMonitor, BottleneckDetector

# Create monitor
monitor = PipelineMonitor('run-001', 'hybrid')
monitor.start()

# Track stages
monitor.start_stage('ocr_extraction', input_size=1024*1024)
# ... do OCR ...
monitor.end_stage(success=True, items_processed=150)

# Record files
monitor.record_file_processed(success=True, deals_count=12)

# Stop and get metrics
metrics = monitor.stop()

# Save metrics
metrics.save(Path('outputs/metrics.json'))

# Analyze bottlenecks
analysis = BottleneckDetector.analyze_metrics(metrics)
BottleneckDetector.print_analysis(analysis)
```

**Metrics Collected**:
- **Stage metrics**: Duration, CPU%, memory usage
- **Resource metrics**: Peak memory, average CPU
- **Processing metrics**: Files processed, success rate, deals extracted
- **Timing metrics**: Total duration, per-stage breakdown

**Bottleneck Detection**:
- Identifies slow stages (> 30% of total time)
- Detects resource issues (high memory, low CPU)
- Generates optimization recommendations

**Sample Output**:
```
==================== PERFORMANCE ANALYSIS ====================
Total Duration: 15.34s

Slowest Stages:
  • vlm_extraction: 8.45s (55.1%)
  • ocr_extraction: 4.23s (27.6%)
  • preprocess: 1.89s (12.3%)

⚠ Bottlenecks Detected:
  • vlm_extraction: 8.45s (55.1% of total)

💡 Recommendations:
  1. VLM stage is slow. Consider using a faster model or cloud API.
  2. Low CPU utilization. Consider enabling parallel processing.
==============================================================
```

### 4. Enhanced Pipeline

**Location**: `src/pipeline/enhanced_pipeline.py`

Pipeline with all advanced features:

```python
from src.pipeline import create_enhanced_pipeline

# Create enhanced pipeline
pipeline = create_enhanced_pipeline(
    method='hybrid',
    enable_monitoring=True,    # Performance tracking
    enable_validation=True,    # Input/output validation
    enable_caching=True,       # Result caching
    max_retries=3              # Automatic retry on failure
)

# Process
result = pipeline.process('brochure.pdf')
```

**Features**:

**Automatic Validation**:
```
→ Input validation...
✓ Valid image: 1024x768, mode=RGB
✓ Input validation completed in 0.015s

→ Output validation...
⚠ Output validation found 2 issues
  - Deal 3: Invalid discount percentage
✓ Output validation completed in 0.003s
```

**Error Recovery**:
```
✗ Processing attempt 1 failed: Connection timeout
Waiting 2s before retry...
→ Retry attempt 2/3
✓ Successfully processed brochure.pdf
```

**Performance Monitoring**:
```
Performance recommendations:
  💡 VLM stage is slow. Consider using a faster model.
  💡 Enable GPU acceleration for faster OCR.
```

**Result Caching**:
```
✓ Returning cached result for weekly_brochure.pdf
```

### 5. Comprehensive Testing

**Location**: `tests/test_pipeline.py`

Run tests:

```bash
# Run all pipeline tests
pytest tests/test_pipeline.py -v

# Run specific test class
pytest tests/test_pipeline.py::TestPipelineConfiguration -v

# Run with coverage
pytest tests/test_pipeline.py --cov=src/pipeline --cov-report=html

# Run only unit tests
pytest tests/test_pipeline.py -m unit

# Run integration tests
pytest tests/test_pipeline.py -m integration
```

**Test Categories**:
- `TestPipelineConfiguration` - Configuration tests
- `TestInputValidation` - Input validation tests
- `TestOutputValidation` - Output validation tests
- `TestSystemValidation` - System requirement tests
- `TestPipelineMonitor` - Performance monitoring tests
- `TestBottleneckDetection` - Bottleneck detection tests
- `TestPipelineFactory` - Pipeline creation tests
- `TestPipelineIntegration` - Integration tests
- `TestErrorHandling` - Error handling tests

## Complete Workflow Example

### Example 1: Production Pipeline with Full Monitoring

```python
from src.pipeline import create_enhanced_pipeline
from src.utils.enhanced_logger import get_logger

# Setup
logger = get_logger('production', log_dir='logs/production')

# Create pipeline
pipeline = create_enhanced_pipeline(
    method='hybrid',
    ocr_engine='paddleocr',
    vlm_engine='ollama',
    ocr_use_gpu=True,
    enable_monitoring=True,
    enable_validation=True,
    enable_caching=True,
    max_retries=3,
    output_dir='outputs/production'
)

# Process files
files = ['brochure1.pdf', 'brochure2.png', 'brochure3.pdf']

for file_path in files:
    logger.info(f"Processing {file_path}")

    result = pipeline.process(file_path)

    if result.success:
        logger.info(
            f"✓ {file_path}: {len(result.deals)} deals",
            time=f"{result.processing_time:.2f}s"
        )
    else:
        logger.error(f"✗ {file_path}: {result.error}")

# Performance summary
logger.log_performance_summary()
```

### Example 2: Validation Before Processing

```python
from src.pipeline import run_full_validation, create_enhanced_pipeline

# Run system validation
print("Checking system...")
if not run_full_validation():
    print("System validation failed!")
    exit(1)

print("\n✓ System ready, creating pipeline...")

# Create pipeline
pipeline = create_enhanced_pipeline('hybrid')

# Process
result = pipeline.process('brochure.pdf')
```

### Example 3: Performance Analysis

```python
from src.pipeline import create_enhanced_pipeline, BottleneckDetector
from pathlib import Path
import json

# Process with monitoring
pipeline = create_enhanced_pipeline(
    'hybrid',
    enable_monitoring=True,
    output_dir='outputs/analysis'
)

result = pipeline.process('brochure.pdf')

# Load metrics
metrics_file = Path('outputs/analysis/brochure/metrics.json')
with open(metrics_file) as f:
    metrics_data = json.load(f)

# Analyze
from src.pipeline.monitor import PipelineMetrics
# ... analyze bottlenecks ...
```

### Example 4: Batch Processing with Validation

```python
from src.pipeline import (
    create_enhanced_pipeline,
    InputValidator,
    BatchProcessor,
    PipelineConfig
)
from pathlib import Path

# Collect and validate files
files = list(Path('data/brochures').glob('*.pdf'))

print(f"Validating {len(files)} files...")
validation_results = InputValidator.validate_batch_inputs(
    [str(f) for f in files]
)

# Filter valid files
valid_files = [
    files[i] for i, r in enumerate(validation_results)
    if r.passed
]

print(f"✓ {len(valid_files)} valid files")

# Process with batch processor
config = PipelineConfig(
    method='hybrid',
    output_dir='outputs/batch'
)

processor = BatchProcessor(config=config, max_workers=4)
batch_result = processor.process([str(f) for f in valid_files])

print(f"\nBatch Results:")
print(f"  Success rate: {batch_result.success_rate:.1f}%")
print(f"  Total deals: {sum(len(r.deals) for r in batch_result.results if r.success)}")
```

## Performance Optimization Tips

### 1. Enable GPU Acceleration

```python
pipeline = create_enhanced_pipeline(
    'hybrid',
    ocr_use_gpu=True  # 2-5x faster OCR
)
```

### 2. Use Caching for Repeated Processing

```python
pipeline = create_enhanced_pipeline(
    'hybrid',
    enable_caching=True  # Skip re-processing unchanged files
)
```

### 3. Optimize for Speed

```python
# OCR-only for maximum speed
pipeline = create_enhanced_pipeline(
    'ocr',
    ocr_engine='tesseract',  # Fastest OCR
    preprocess_images=False,  # Skip preprocessing
    save_visualizations=False  # Skip visualization
)
```

### 4. Optimize for Accuracy

```python
# Hybrid with best models
pipeline = create_enhanced_pipeline(
    'hybrid',
    ocr_engine='paddleocr',
    vlm_model='llava:13b',  # Better but slower
    preprocess_images=True,
    enhance_images=True
)
```

### 5. Parallel Batch Processing

```python
# Process 50 files with 8 workers
processor = BatchProcessor(
    config=config,
    max_workers=8  # Adjust based on CPU cores
)

result = processor.process_directory(
    'data/brochures',
    pattern='*.pdf',
    recursive=True
)
```

## Monitoring and Debugging

### Enable Debug Logging

```python
from src.utils.enhanced_logger import get_logger
import logging

logger = get_logger('pipeline', level=logging.DEBUG)
```

### Monitor Resource Usage

```python
from src.pipeline.monitor import ResourceMonitor

monitor = ResourceMonitor(interval=0.1)
monitor.start()

# ... run pipeline ...

stats = monitor.stop()
print(f"Peak memory: {stats['max_memory_mb']:.1f} MB")
print(f"Avg CPU: {stats['avg_cpu_percent']:.1f}%")
```

### Save Detailed Metrics

```python
pipeline = create_enhanced_pipeline(
    'hybrid',
    enable_monitoring=True,
    output_dir='outputs/detailed'
)

result = pipeline.process('brochure.pdf')

# Metrics automatically saved to:
# outputs/detailed/brochure/metrics.json
```

### Analyze Bottlenecks

```python
from src.pipeline import PipelineMonitor, BottleneckDetector
from pathlib import Path
import json

# Load metrics
with open('outputs/detailed/brochure/metrics.json') as f:
    metrics_dict = json.load(f)

# Analyze
from src.pipeline.monitor import PipelineMetrics
# Convert dict to PipelineMetrics object
# ... analyze ...
```

## Error Handling

### Automatic Retry

```python
pipeline = create_enhanced_pipeline(
    'hybrid',
    max_retries=3  # Retry up to 3 times
)

# Automatically retries on:
# - Network errors (VLM API)
# - Temporary OCR failures
# - Resource limitations
```

### Custom Error Handling

```python
results = []
errors = []

for file_path in files:
    try:
        result = pipeline.process(file_path)

        if result.success:
            results.append(result)
        else:
            errors.append((file_path, result.error))

    except Exception as e:
        errors.append((file_path, str(e)))

# Report errors
if errors:
    print(f"\n{len(errors)} files failed:")
    for path, error in errors:
        print(f"  ✗ {path}: {error}")
```

## Best Practices

### 1. Always Validate First

```python
# Before processing
success = run_full_validation()
if not success:
    print("Fix system issues before processing")
    exit(1)
```

### 2. Use Enhanced Pipeline in Production

```python
# Standard pipeline for development
from src.pipeline import create_pipeline
dev_pipeline = create_pipeline('ocr')

# Enhanced pipeline for production
from src.pipeline import create_enhanced_pipeline
prod_pipeline = create_enhanced_pipeline(
    'hybrid',
    enable_monitoring=True,
    enable_validation=True,
    max_retries=3
)
```

### 3. Monitor Performance

```python
# Always enable monitoring for production
pipeline = create_enhanced_pipeline(
    method='hybrid',
    enable_monitoring=True
)

# Review metrics regularly
# Check outputs/*/metrics.json
```

### 4. Validate Outputs

```python
result = pipeline.process('brochure.pdf')

if result.success:
    # Validate deals
    from src.pipeline import OutputValidator
    validation = OutputValidator.validate_deals(result.deals)

    if validation.details and 'issues' in validation.details:
        print("⚠ Quality issues detected")
        # Review manually or retry with different method
```

### 5. Cache Results When Appropriate

```python
# Enable caching for:
# - Development/testing
# - Repeated processing
# - Expensive operations

pipeline = create_enhanced_pipeline(
    method='hybrid',
    enable_caching=True
)
```

## Troubleshooting

### Issue: Tests Failing

```bash
# Run validation first
python -m src.pipeline.validator

# Install missing dependencies
pip install -r requirements.txt

# Check specific test
pytest tests/test_pipeline.py::TestInputValidation::test_validate_valid_image -v
```

### Issue: Low Performance

```python
# Run with monitoring
pipeline = create_enhanced_pipeline('hybrid', enable_monitoring=True)
result = pipeline.process('brochure.pdf')

# Check bottlenecks in:
# outputs/*/metrics.json

# Follow recommendations in terminal output
```

### Issue: High Memory Usage

```python
# Use OCR-only method
pipeline = create_enhanced_pipeline(
    'ocr',
    preprocess_images=False
)

# Or process in smaller batches
processor = BatchProcessor(
    config=config,
    max_workers=2  # Reduce workers
)
```

## See Also

- [Pipeline Guide](PIPELINE_GUIDE.md) - Basic usage
- [Web Application Guide](WEBAPP_GUIDE.md) - Web interface
- [VLM Guide](VLM_GUIDE.md) - Vision Language Models
- [CLI Usage](CLI_USAGE.md) - Command-line tools

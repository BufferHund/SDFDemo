"""
Comprehensive Tests for Pipeline System

Test coverage:
- Pipeline configuration
- Input validation
- Processing methods (OCR/VLM/Hybrid)
- Batch processing
- Error handling
- Performance monitoring
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image
import json
import time

# Import pipeline components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import (
    BrochurePipeline,
    PipelineConfig,
    ProcessingMethod,
    create_pipeline,
    BatchProcessor
)
from src.pipeline.validator import (
    SystemValidator,
    InputValidator,
    OutputValidator,
    ValidationResult
)
from src.pipeline.monitor import PipelineMonitor, BottleneckDetector


class TestPipelineConfiguration:
    """Test pipeline configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = PipelineConfig()

        assert config.method == ProcessingMethod.HYBRID
        assert config.ocr_engine == "paddleocr"
        assert config.vlm_engine == "ollama"
        assert config.preprocess_images == True

    def test_custom_config(self):
        """Test custom configuration."""
        config = PipelineConfig(
            method=ProcessingMethod.OCR,
            ocr_engine="tesseract",
            preprocess_images=False
        )

        assert config.method == ProcessingMethod.OCR
        assert config.ocr_engine == "tesseract"
        assert config.preprocess_images == False

    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = PipelineConfig(method=ProcessingMethod.VLM)
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict['method'] == 'vlm'
        assert 'ocr_engine' in config_dict


class TestInputValidation:
    """Test input validation."""

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file."""
        result = InputValidator.validate_file_path('/nonexistent/file.png')

        assert not result.passed
        assert result.severity == 'error'
        assert 'not found' in result.message.lower()

    def test_validate_valid_image(self, tmp_path):
        """Test validation of valid image."""
        # Create test image
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (800, 600), color='white')
        img.save(img_path)

        result = InputValidator.validate_image(str(img_path))

        assert result.passed
        assert result.details['width'] == 800
        assert result.details['height'] == 600

    def test_validate_small_image(self, tmp_path):
        """Test validation of too-small image."""
        img_path = tmp_path / "small.png"
        img = Image.new('RGB', (50, 50), color='white')
        img.save(img_path)

        result = InputValidator.validate_image(str(img_path))

        assert not result.passed
        assert result.severity == 'warning'
        assert 'too small' in result.message.lower()

    def test_validate_large_image(self, tmp_path):
        """Test validation of large image."""
        img_path = tmp_path / "large.png"
        img = Image.new('RGB', (12000, 8000), color='white')
        img.save(img_path)

        result = InputValidator.validate_image(str(img_path))

        assert result.passed
        assert result.severity == 'warning'
        assert 'large' in result.message.lower()

    def test_validate_unsupported_format(self, tmp_path):
        """Test validation of unsupported file format."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("not an image")

        result = InputValidator.validate_image(str(file_path))

        assert not result.passed


class TestOutputValidation:
    """Test output validation."""

    def test_validate_empty_deals(self):
        """Test validation of empty deals list."""
        result = OutputValidator.validate_deals([])

        assert result.passed
        assert result.severity == 'warning'

    def test_validate_valid_deals(self):
        """Test validation of valid deals."""
        deals = [
            {
                'product_name': 'Test Product',
                'discounted_price': 2.99,
                'original_price': 4.99,
                'discount_percentage': 40
            }
        ]

        result = OutputValidator.validate_deals(deals)

        assert result.passed
        assert '1 deals' in result.message

    def test_validate_missing_product_name(self):
        """Test validation with missing product name."""
        deals = [
            {
                'discounted_price': 2.99
            }
        ]

        result = OutputValidator.validate_deals(deals)

        assert result.passed
        assert result.severity == 'warning'
        assert result.details and 'issues' in result.details

    def test_validate_negative_price(self):
        """Test validation with negative price."""
        deals = [
            {
                'product_name': 'Test',
                'discounted_price': -5.00
            }
        ]

        result = OutputValidator.validate_deals(deals)

        assert result.passed
        assert result.severity == 'warning'

    def test_validate_invalid_discount(self):
        """Test validation with invalid discount percentage."""
        deals = [
            {
                'product_name': 'Test',
                'discount_percentage': 150  # Invalid: > 100
            }
        ]

        result = OutputValidator.validate_deals(deals)

        assert result.passed
        assert result.severity == 'warning'


class TestSystemValidation:
    """Test system validation."""

    def test_python_version_check(self):
        """Test Python version check."""
        validator = SystemValidator()
        result = validator.check_python_version(min_version=(3, 6))

        assert result.passed

    def test_dependency_check(self):
        """Test dependency checking."""
        validator = SystemValidator()

        # Test existing module
        result = validator.check_dependency('sys')
        assert result.passed

        # Test non-existing module
        result = validator.check_dependency('nonexistent_module_xyz')
        assert not result.passed

    def test_disk_space_check(self):
        """Test disk space check."""
        validator = SystemValidator()
        result = validator.check_disk_space(min_space_gb=0.1)

        # Should pass unless disk is critically full
        assert isinstance(result, ValidationResult)

    def test_memory_check(self):
        """Test memory check."""
        validator = SystemValidator()
        result = validator.check_memory(min_memory_gb=0.1)

        assert isinstance(result, ValidationResult)


class TestPipelineMonitor:
    """Test performance monitoring."""

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = PipelineMonitor('test-001', 'hybrid')

        assert monitor.metrics.pipeline_id == 'test-001'
        assert monitor.metrics.method == 'hybrid'

    def test_stage_tracking(self):
        """Test stage tracking."""
        monitor = PipelineMonitor('test-002', 'ocr')
        monitor.start()

        # Start and end a stage
        monitor.start_stage('test_stage')
        time.sleep(0.1)
        monitor.end_stage(success=True, items_processed=10)

        metrics = monitor.stop()

        assert 'test_stage' in metrics.stages
        assert metrics.stages['test_stage'].success
        assert metrics.stages['test_stage'].duration > 0

    def test_file_processing_tracking(self):
        """Test file processing tracking."""
        monitor = PipelineMonitor('test-003', 'vlm')

        monitor.record_file_processed(success=True, deals_count=15)
        monitor.record_file_processed(success=True, deals_count=20)
        monitor.record_file_processed(success=False, deals_count=0)

        assert monitor.metrics.input_files == 3
        assert monitor.metrics.successful_files == 2
        assert monitor.metrics.failed_files == 1
        assert monitor.metrics.total_deals_extracted == 35

    def test_metrics_serialization(self):
        """Test metrics can be serialized."""
        monitor = PipelineMonitor('test-004', 'hybrid')
        monitor.start()

        monitor.start_stage('stage1')
        monitor.end_stage(success=True)

        metrics = monitor.stop()
        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert 'pipeline_id' in metrics_dict
        assert 'stages' in metrics_dict


class TestBottleneckDetection:
    """Test bottleneck detection."""

    def test_bottleneck_analysis(self):
        """Test bottleneck analysis."""
        monitor = PipelineMonitor('test-005', 'hybrid')
        monitor.start()

        # Create a slow stage (bottleneck)
        monitor.start_stage('slow_stage')
        time.sleep(0.5)
        monitor.end_stage(success=True)

        # Create a fast stage
        monitor.start_stage('fast_stage')
        time.sleep(0.1)
        monitor.end_stage(success=True)

        metrics = monitor.stop()
        analysis = BottleneckDetector.analyze_metrics(metrics)

        assert 'slowest_stages' in analysis
        assert 'bottlenecks' in analysis
        assert 'recommendations' in analysis
        assert len(analysis['slowest_stages']) > 0

    def test_recommendations_generation(self):
        """Test that recommendations are generated."""
        monitor = PipelineMonitor('test-006', 'hybrid')
        monitor.start()

        # Simulate low CPU usage scenario
        monitor.metrics.avg_cpu_percent = 15

        metrics = monitor.stop()
        analysis = BottleneckDetector.analyze_metrics(metrics)

        # Should have some recommendations
        assert isinstance(analysis['recommendations'], list)


class TestPipelineFactory:
    """Test pipeline factory function."""

    def test_create_ocr_pipeline(self):
        """Test creating OCR pipeline."""
        pipeline = create_pipeline('ocr', ocr_engine='tesseract')

        assert isinstance(pipeline, BrochurePipeline)
        assert pipeline.config.method == ProcessingMethod.OCR

    def test_create_vlm_pipeline(self):
        """Test creating VLM pipeline."""
        pipeline = create_pipeline('vlm', vlm_engine='ollama')

        assert isinstance(pipeline, BrochurePipeline)
        assert pipeline.config.method == ProcessingMethod.VLM

    def test_create_hybrid_pipeline(self):
        """Test creating hybrid pipeline."""
        pipeline = create_pipeline('hybrid')

        assert isinstance(pipeline, BrochurePipeline)
        assert pipeline.config.method == ProcessingMethod.HYBRID


class TestPipelineIntegration:
    """Integration tests for pipeline."""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a sample image for testing."""
        img_path = tmp_path / "sample.png"
        img = Image.new('RGB', (800, 600), color='white')

        # Draw some simple shapes (simulating a brochure)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 200], fill='red')
        draw.rectangle([400, 100, 600, 200], fill='blue')

        img.save(img_path)
        return img_path

    def test_pipeline_with_mock_data(self, sample_image, tmp_path):
        """Test pipeline with mock data (without actual OCR/VLM)."""
        # Note: This test validates pipeline structure, not actual processing
        # Full integration tests with real OCR/VLM would require those services

        output_dir = tmp_path / "output"

        config = PipelineConfig(
            method=ProcessingMethod.OCR,
            output_dir=str(output_dir),
            save_visualizations=True
        )

        pipeline = BrochurePipeline(config)

        # Verify pipeline was initialized
        assert pipeline.config.method == ProcessingMethod.OCR
        assert pipeline.output_dir == output_dir

    def test_batch_processor_initialization(self, tmp_path):
        """Test batch processor initialization."""
        config = PipelineConfig(
            output_dir=str(tmp_path / "batch_output")
        )

        processor = BatchProcessor(config=config, max_workers=2)

        assert processor.config == config
        assert processor.max_workers == 2


class TestErrorHandling:
    """Test error handling in pipeline."""

    def test_invalid_file_handling(self, tmp_path):
        """Test handling of invalid files."""
        # Create invalid file
        invalid_file = tmp_path / "invalid.png"
        invalid_file.write_text("This is not an image")

        # Validate - should fail gracefully
        result = InputValidator.validate_image(str(invalid_file))

        assert not result.passed
        assert result.severity == 'error'

    def test_missing_file_handling(self):
        """Test handling of missing files."""
        result = InputValidator.validate_file_path('/path/to/nonexistent/file.png')

        assert not result.passed
        assert 'not found' in result.message.lower()


# Markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])

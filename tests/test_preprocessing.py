"""Tests for preprocessing modules."""

import pytest
import tempfile
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.image_processor import ImageProcessor


class TestImageProcessor:
    """Test image processing."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        img = Image.new('RGB', (800, 600), color='white')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        img.save(temp_file.name)
        temp_file.close()
        yield Path(temp_file.name)
        Path(temp_file.name).unlink()

    def test_resize_image_maintain_aspect(self):
        processor = ImageProcessor(target_size=(1024, 1448))
        img = Image.new('RGB', (800, 600))

        result = processor.resize_image(img, maintain_aspect_ratio=True)

        assert result.size == (1024, 1448)
        assert result.mode == 'RGB'

    def test_resize_image_no_aspect(self):
        processor = ImageProcessor(target_size=(512, 512))
        img = Image.new('RGB', (800, 600))

        result = processor.resize_image(img, maintain_aspect_ratio=False)

        assert result.size == (512, 512)

    def test_enhance_contrast(self):
        processor = ImageProcessor()
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))

        result = processor.enhance_contrast(img, factor=1.5)

        assert result is not None
        assert result.size == img.size

    def test_process_image(self, sample_image):
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = ImageProcessor(output_dir=tmpdir)

            output = processor.process_image(sample_image)

            assert output is not None
            assert output.exists()

    def test_process_nonexistent_image(self):
        processor = ImageProcessor()
        result = processor.process_image("nonexistent.png")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Pipeline Validation and Health Check System

Features:
- Configuration validation
- System requirements checking
- Input validation
- Output validation
- Health checks for components
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import importlib
from PIL import Image
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    details: Optional[Dict[str, Any]] = None


class SystemValidator:
    """Validate system requirements and dependencies."""

    def __init__(self):
        self.results: List[ValidationResult] = []

    def check_python_version(self, min_version: Tuple[int, int] = (3, 8)) -> ValidationResult:
        """Check Python version."""
        current = sys.version_info[:2]
        passed = current >= min_version

        if passed:
            return ValidationResult(
                passed=True,
                message=f"Python version {current[0]}.{current[1]} is compatible",
                severity="info"
            )
        else:
            return ValidationResult(
                passed=False,
                message=f"Python {current[0]}.{current[1]} is below minimum {min_version[0]}.{min_version[1]}",
                severity="error"
            )

    def check_dependency(self, module_name: str, package_name: str = None) -> ValidationResult:
        """Check if a Python package is installed."""
        if package_name is None:
            package_name = module_name

        try:
            importlib.import_module(module_name)
            return ValidationResult(
                passed=True,
                message=f"Package '{package_name}' is installed",
                severity="info"
            )
        except ImportError:
            return ValidationResult(
                passed=False,
                message=f"Package '{package_name}' is not installed. Install with: pip install {package_name}",
                severity="error"
            )

    def check_required_dependencies(self) -> List[ValidationResult]:
        """Check all required dependencies."""
        dependencies = [
            ('PIL', 'Pillow'),
            ('paddleocr', 'paddleocr'),
            ('cv2', 'opencv-python'),
            ('numpy', 'numpy'),
            ('pandas', 'pandas'),
            ('streamlit', 'streamlit'),
            ('fastapi', 'fastapi'),
        ]

        results = []
        for module, package in dependencies:
            results.append(self.check_dependency(module, package))

        return results

    def check_optional_dependencies(self) -> List[ValidationResult]:
        """Check optional dependencies."""
        dependencies = [
            ('easyocr', 'easyocr'),
            ('pytesseract', 'pytesseract'),
            ('google.generativeai', 'google-generativeai'),
        ]

        results = []
        for module, package in dependencies:
            result = self.check_dependency(module, package)
            # Change severity to warning for optional deps
            result.severity = "warning" if not result.passed else "info"
            results.append(result)

        return results

    def check_gpu_availability(self) -> ValidationResult:
        """Check if GPU is available."""
        try:
            import torch
            gpu_available = torch.cuda.is_available()

            if gpu_available:
                gpu_name = torch.cuda.get_device_name(0)
                return ValidationResult(
                    passed=True,
                    message=f"GPU available: {gpu_name}",
                    severity="info",
                    details={'gpu_count': torch.cuda.device_count()}
                )
            else:
                return ValidationResult(
                    passed=True,
                    message="No GPU detected, will use CPU",
                    severity="warning"
                )
        except ImportError:
            return ValidationResult(
                passed=True,
                message="PyTorch not installed, GPU check skipped",
                severity="info"
            )

    def check_disk_space(self, min_space_gb: float = 1.0) -> ValidationResult:
        """Check available disk space."""
        try:
            import shutil
            stat = shutil.disk_usage(".")
            free_gb = stat.free / (1024**3)

            if free_gb >= min_space_gb:
                return ValidationResult(
                    passed=True,
                    message=f"Sufficient disk space: {free_gb:.2f} GB available",
                    severity="info"
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"Low disk space: {free_gb:.2f} GB available (minimum: {min_space_gb} GB)",
                    severity="warning"
                )
        except Exception as e:
            return ValidationResult(
                passed=True,
                message=f"Could not check disk space: {str(e)}",
                severity="info"
            )

    def check_memory(self, min_memory_gb: float = 2.0) -> ValidationResult:
        """Check available memory."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)

            if available_gb >= min_memory_gb:
                return ValidationResult(
                    passed=True,
                    message=f"Sufficient memory: {available_gb:.2f} GB available",
                    severity="info"
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"Low memory: {available_gb:.2f} GB available (minimum: {min_memory_gb} GB)",
                    severity="warning"
                )
        except ImportError:
            return ValidationResult(
                passed=True,
                message="psutil not installed, memory check skipped",
                severity="info"
            )

    def check_ollama_server(self) -> ValidationResult:
        """Check if Ollama server is running."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)

            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]

                return ValidationResult(
                    passed=True,
                    message=f"Ollama server running with {len(models)} models",
                    severity="info",
                    details={'models': model_names}
                )
            else:
                return ValidationResult(
                    passed=False,
                    message="Ollama server not responding correctly",
                    severity="warning"
                )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Ollama server not reachable: {str(e)}",
                severity="warning"
            )

    def run_all_checks(self) -> List[ValidationResult]:
        """Run all system validation checks."""
        results = []

        # Python version
        results.append(self.check_python_version())

        # Required dependencies
        results.extend(self.check_required_dependencies())

        # Optional dependencies
        results.extend(self.check_optional_dependencies())

        # System resources
        results.append(self.check_gpu_availability())
        results.append(self.check_disk_space())
        results.append(self.check_memory())

        # External services
        results.append(self.check_ollama_server())

        self.results = results
        return results

    def print_summary(self):
        """Print validation summary."""
        if not self.results:
            print("No validation results available")
            return

        errors = [r for r in self.results if not r.passed and r.severity == "error"]
        warnings = [r for r in self.results if not r.passed and r.severity == "warning"]
        passed = [r for r in self.results if r.passed]

        print("\n" + "=" * 80)
        print("SYSTEM VALIDATION SUMMARY")
        print("=" * 80)

        print(f"\n✓ Passed: {len(passed)}")
        print(f"⚠ Warnings: {len(warnings)}")
        print(f"✗ Errors: {len(errors)}")

        if errors:
            print("\n--- ERRORS ---")
            for r in errors:
                print(f"✗ {r.message}")

        if warnings:
            print("\n--- WARNINGS ---")
            for r in warnings:
                print(f"⚠ {r.message}")

        print("\n" + "=" * 80)


class InputValidator:
    """Validate pipeline inputs."""

    @staticmethod
    def validate_file_path(file_path: str) -> ValidationResult:
        """Validate file path exists and is readable."""
        path = Path(file_path)

        if not path.exists():
            return ValidationResult(
                passed=False,
                message=f"File not found: {file_path}",
                severity="error"
            )

        if not path.is_file():
            return ValidationResult(
                passed=False,
                message=f"Path is not a file: {file_path}",
                severity="error"
            )

        if not os.access(path, os.R_OK):
            return ValidationResult(
                passed=False,
                message=f"File is not readable: {file_path}",
                severity="error"
            )

        return ValidationResult(
            passed=True,
            message=f"File is valid: {file_path}",
            severity="info"
        )

    @staticmethod
    def validate_image(file_path: str) -> ValidationResult:
        """Validate image file."""
        # First check file path
        path_result = InputValidator.validate_file_path(file_path)
        if not path_result.passed:
            return path_result

        # Check file extension
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
        ext = Path(file_path).suffix.lower()

        if ext not in valid_extensions:
            return ValidationResult(
                passed=False,
                message=f"Unsupported image format: {ext}. Supported: {', '.join(valid_extensions)}",
                severity="error"
            )

        # Try to open image
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode

                # Check dimensions
                if width < 100 or height < 100:
                    return ValidationResult(
                        passed=False,
                        message=f"Image too small: {width}x{height} (minimum: 100x100)",
                        severity="warning"
                    )

                # Check if image is too large
                if width > 10000 or height > 10000:
                    return ValidationResult(
                        passed=True,
                        message=f"Large image: {width}x{height} (may be slow to process)",
                        severity="warning",
                        details={'width': width, 'height': height, 'mode': mode}
                    )

                return ValidationResult(
                    passed=True,
                    message=f"Valid image: {width}x{height}, mode={mode}",
                    severity="info",
                    details={'width': width, 'height': height, 'mode': mode}
                )

        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Cannot open image: {str(e)}",
                severity="error"
            )

    @staticmethod
    def validate_pdf(file_path: str) -> ValidationResult:
        """Validate PDF file."""
        # First check file path
        path_result = InputValidator.validate_file_path(file_path)
        if not path_result.passed:
            return path_result

        # Check extension
        if Path(file_path).suffix.lower() != '.pdf':
            return ValidationResult(
                passed=False,
                message=f"Not a PDF file: {file_path}",
                severity="error"
            )

        # Check file size
        size_mb = Path(file_path).stat().st_size / (1024 * 1024)

        if size_mb > 50:
            return ValidationResult(
                passed=True,
                message=f"Large PDF file: {size_mb:.1f} MB (may be slow to process)",
                severity="warning",
                details={'size_mb': size_mb}
            )

        return ValidationResult(
            passed=True,
            message=f"Valid PDF: {size_mb:.1f} MB",
            severity="info",
            details={'size_mb': size_mb}
        )

    @staticmethod
    def validate_batch_inputs(file_paths: List[str]) -> List[ValidationResult]:
        """Validate batch of input files."""
        results = []

        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()

            if ext == '.pdf':
                results.append(InputValidator.validate_pdf(file_path))
            elif ext in {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}:
                results.append(InputValidator.validate_image(file_path))
            else:
                results.append(ValidationResult(
                    passed=False,
                    message=f"Unsupported file type: {file_path}",
                    severity="error"
                ))

        return results


class OutputValidator:
    """Validate pipeline outputs."""

    @staticmethod
    def validate_deals(deals: List[Dict]) -> ValidationResult:
        """Validate extracted deals."""
        if not deals:
            return ValidationResult(
                passed=True,
                message="No deals extracted",
                severity="warning"
            )

        # Check deal structure
        required_fields = ['product_name']
        optional_fields = ['discounted_price', 'original_price', 'discount_percentage']

        issues = []

        for i, deal in enumerate(deals):
            # Check required fields
            for field in required_fields:
                if field not in deal or not deal[field]:
                    issues.append(f"Deal {i+1}: Missing {field}")

            # Validate price fields
            if 'discounted_price' in deal:
                try:
                    price = float(deal['discounted_price'])
                    if price < 0:
                        issues.append(f"Deal {i+1}: Negative price")
                except (ValueError, TypeError):
                    issues.append(f"Deal {i+1}: Invalid price format")

            # Validate discount percentage
            if 'discount_percentage' in deal:
                try:
                    discount = float(deal['discount_percentage'])
                    if discount < 0 or discount > 100:
                        issues.append(f"Deal {i+1}: Invalid discount percentage")
                except (ValueError, TypeError):
                    issues.append(f"Deal {i+1}: Invalid discount format")

        if issues:
            return ValidationResult(
                passed=True,
                message=f"Found {len(deals)} deals with {len(issues)} validation issues",
                severity="warning",
                details={'issues': issues}
            )

        return ValidationResult(
            passed=True,
            message=f"Validated {len(deals)} deals successfully",
            severity="info"
        )


class PipelineHealthCheck:
    """Health check for pipeline components."""

    def __init__(self):
        self.checks = []

    def check_ocr_engines(self) -> ValidationResult:
        """Check if OCR engines are available."""
        engines = []
        issues = []

        # PaddleOCR
        try:
            from paddleocr import PaddleOCR
            engines.append('paddleocr')
        except Exception as e:
            issues.append(f"PaddleOCR: {str(e)}")

        # Tesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            engines.append('tesseract')
        except Exception as e:
            issues.append(f"Tesseract: {str(e)}")

        # EasyOCR
        try:
            import easyocr
            engines.append('easyocr')
        except Exception as e:
            issues.append(f"EasyOCR: {str(e)}")

        if not engines:
            return ValidationResult(
                passed=False,
                message="No OCR engines available",
                severity="error",
                details={'issues': issues}
            )

        return ValidationResult(
            passed=True,
            message=f"OCR engines available: {', '.join(engines)}",
            severity="info",
            details={'engines': engines, 'issues': issues}
        )

    def check_vlm_engines(self) -> ValidationResult:
        """Check if VLM engines are available."""
        engines = []
        issues = []

        # Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                engines.append('ollama')
        except Exception as e:
            issues.append(f"Ollama: {str(e)}")

        # Gemini
        try:
            import google.generativeai as genai
            if os.getenv('GEMINI_API_KEY'):
                engines.append('gemini')
            else:
                issues.append("Gemini: GEMINI_API_KEY not set")
        except Exception as e:
            issues.append(f"Gemini: {str(e)}")

        if not engines:
            return ValidationResult(
                passed=True,
                message="No VLM engines available (optional)",
                severity="warning",
                details={'issues': issues}
            )

        return ValidationResult(
            passed=True,
            message=f"VLM engines available: {', '.join(engines)}",
            severity="info",
            details={'engines': engines, 'issues': issues}
        )

    def run_health_check(self) -> List[ValidationResult]:
        """Run complete health check."""
        results = []

        results.append(self.check_ocr_engines())
        results.append(self.check_vlm_engines())

        self.checks = results
        return results

    def is_healthy(self) -> bool:
        """Check if pipeline is healthy."""
        if not self.checks:
            self.run_health_check()

        # At least one OCR engine must be available
        ocr_check = next((c for c in self.checks if 'OCR' in c.message), None)

        return ocr_check and ocr_check.passed


def run_full_validation() -> bool:
    """
    Run complete validation suite.

    Returns:
        True if all critical checks pass
    """
    print("\n" + "=" * 80)
    print("RUNNING FULL PIPELINE VALIDATION")
    print("=" * 80)

    # System validation
    print("\n[1/3] Checking system requirements...")
    sys_validator = SystemValidator()
    sys_validator.run_all_checks()
    sys_validator.print_summary()

    # Health check
    print("\n[2/3] Checking component health...")
    health_check = PipelineHealthCheck()
    health_results = health_check.run_health_check()

    print("\n--- COMPONENT HEALTH ---")
    for result in health_results:
        status = "✓" if result.passed else "✗"
        print(f"{status} {result.message}")

    # Example input validation
    print("\n[3/3] Input validation ready")
    print("Use InputValidator.validate_image() or validate_pdf() to check inputs")

    # Overall result
    errors = [r for r in sys_validator.results if not r.passed and r.severity == "error"]
    critical_health_issues = [r for r in health_results if not r.passed and r.severity == "error"]

    success = len(errors) == 0 and len(critical_health_issues) == 0

    print("\n" + "=" * 80)
    if success:
        print("✓ VALIDATION PASSED - System ready for pipeline execution")
    else:
        print("✗ VALIDATION FAILED - Please address critical issues above")
    print("=" * 80 + "\n")

    return success


if __name__ == '__main__':
    # Run full validation
    success = run_full_validation()
    sys.exit(0 if success else 1)

"""Pipeline Module for End-to-End Brochure Processing"""

from .pipeline import (
    BrochurePipeline,
    PipelineConfig,
    PipelineResult,
    ProcessingMethod,
    create_pipeline
)
from .batch_processor import BatchProcessor, BatchResult, process_directory
from .enhanced_pipeline import EnhancedPipeline, create_enhanced_pipeline
from .validator import (
    SystemValidator,
    InputValidator,
    OutputValidator,
    PipelineHealthCheck,
    run_full_validation
)
from .monitor import (
    PipelineMonitor,
    PerformanceMetrics,
    BottleneckDetector
)

__all__ = [
    # Core pipeline
    'BrochurePipeline',
    'PipelineConfig',
    'PipelineResult',
    'ProcessingMethod',
    'create_pipeline',

    # Enhanced pipeline
    'EnhancedPipeline',
    'create_enhanced_pipeline',

    # Batch processing
    'BatchProcessor',
    'BatchResult',
    'process_directory',

    # Validation
    'SystemValidator',
    'InputValidator',
    'OutputValidator',
    'PipelineHealthCheck',
    'run_full_validation',

    # Monitoring
    'PipelineMonitor',
    'PerformanceMetrics',
    'BottleneckDetector'
]

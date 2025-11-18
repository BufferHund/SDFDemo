"""
Pipeline Performance Monitoring and Metrics

Features:
- Real-time performance tracking
- Resource usage monitoring
- Bottleneck detection
- Metrics export
"""

import time
import psutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from pathlib import Path
import threading


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""

    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None

    # Resource metrics
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    memory_percent: Optional[float] = None

    # Operation-specific metrics
    input_size: Optional[int] = None  # bytes
    output_size: Optional[int] = None
    items_processed: Optional[int] = None

    # Status
    success: bool = True
    error: Optional[str] = None

    def finalize(self):
        """Calculate final metrics."""
        if self.end_time:
            self.duration = self.end_time - self.start_time

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PipelineMetrics:
    """Metrics for entire pipeline run."""

    pipeline_id: str
    method: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration: Optional[float] = None

    # Stage metrics
    stages: Dict[str, PerformanceMetrics] = field(default_factory=dict)

    # Overall metrics
    input_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_deals_extracted: int = 0

    # Resource usage
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0

    def add_stage(self, stage_name: str, metrics: PerformanceMetrics):
        """Add stage metrics."""
        self.stages[stage_name] = metrics

        # Update peak memory
        if metrics.memory_mb:
            self.peak_memory_mb = max(self.peak_memory_mb, metrics.memory_mb)

    def finalize(self):
        """Calculate final metrics."""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time

        # Calculate average CPU
        cpu_values = [m.cpu_percent for m in self.stages.values() if m.cpu_percent]
        if cpu_values:
            self.avg_cpu_percent = sum(cpu_values) / len(cpu_values)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = {
            'pipeline_id': self.pipeline_id,
            'method': self.method,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            'total_duration': self.total_duration,
            'input_files': self.input_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'success_rate': (self.successful_files / self.input_files * 100) if self.input_files > 0 else 0,
            'total_deals_extracted': self.total_deals_extracted,
            'peak_memory_mb': self.peak_memory_mb,
            'avg_cpu_percent': self.avg_cpu_percent,
            'stages': {name: metrics.to_dict() for name, metrics in self.stages.items()}
        }
        return data

    def save(self, output_path: Path):
        """Save metrics to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class ResourceMonitor:
    """Monitor system resource usage."""

    def __init__(self, interval: float = 0.1):
        """
        Initialize resource monitor.

        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self.monitoring = False
        self.thread: Optional[threading.Thread] = None

        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []

        self.process = psutil.Process()

    def start(self):
        """Start monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self.cpu_samples = []
        self.memory_samples = []

        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self) -> Dict[str, float]:
        """
        Stop monitoring and return statistics.

        Returns:
            Dictionary with avg/max CPU and memory
        """
        self.monitoring = False

        if self.thread:
            self.thread.join(timeout=1.0)

        stats = {
            'avg_cpu_percent': sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
            'max_cpu_percent': max(self.cpu_samples) if self.cpu_samples else 0,
            'avg_memory_mb': sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0,
            'max_memory_mb': max(self.memory_samples) if self.memory_samples else 0,
        }

        return stats

    def _monitor_loop(self):
        """Monitoring loop (runs in separate thread)."""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = self.process.cpu_percent(interval=None)
                self.cpu_samples.append(cpu_percent)

                # Memory usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                self.memory_samples.append(memory_mb)

            except Exception:
                pass

            time.sleep(self.interval)

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current resource metrics."""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = self.process.memory_percent()

            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'memory_percent': memory_percent
            }
        except Exception:
            return {
                'cpu_percent': 0.0,
                'memory_mb': 0.0,
                'memory_percent': 0.0
            }


class PipelineMonitor:
    """Monitor pipeline execution."""

    def __init__(self, pipeline_id: str, method: str):
        """
        Initialize pipeline monitor.

        Args:
            pipeline_id: Unique identifier for this pipeline run
            method: Processing method (ocr/vlm/hybrid)
        """
        self.metrics = PipelineMetrics(pipeline_id=pipeline_id, method=method)
        self.resource_monitor = ResourceMonitor()
        self.current_stage: Optional[str] = None
        self.stage_start_time: Optional[float] = None

    def start(self):
        """Start monitoring."""
        self.resource_monitor.start()

    def start_stage(self, stage_name: str, input_size: Optional[int] = None):
        """
        Start monitoring a stage.

        Args:
            stage_name: Name of the stage
            input_size: Size of input data in bytes
        """
        self.current_stage = stage_name
        self.stage_start_time = time.time()

        # Get current resource metrics
        resources = self.resource_monitor.get_current_metrics()

        # Create stage metrics
        stage_metrics = PerformanceMetrics(
            operation=stage_name,
            start_time=self.stage_start_time,
            input_size=input_size,
            cpu_percent=resources['cpu_percent'],
            memory_mb=resources['memory_mb'],
            memory_percent=resources['memory_percent']
        )

        self.metrics.stages[stage_name] = stage_metrics

    def end_stage(
        self,
        success: bool = True,
        error: Optional[str] = None,
        output_size: Optional[int] = None,
        items_processed: Optional[int] = None
    ):
        """
        End monitoring current stage.

        Args:
            success: Whether stage succeeded
            error: Error message if failed
            output_size: Size of output data in bytes
            items_processed: Number of items processed
        """
        if not self.current_stage or self.current_stage not in self.metrics.stages:
            return

        stage_metrics = self.metrics.stages[self.current_stage]
        stage_metrics.end_time = time.time()
        stage_metrics.success = success
        stage_metrics.error = error
        stage_metrics.output_size = output_size
        stage_metrics.items_processed = items_processed
        stage_metrics.finalize()

        self.current_stage = None
        self.stage_start_time = None

    def record_file_processed(self, success: bool, deals_count: int = 0):
        """
        Record a file being processed.

        Args:
            success: Whether processing succeeded
            deals_count: Number of deals extracted
        """
        self.metrics.input_files += 1

        if success:
            self.metrics.successful_files += 1
            self.metrics.total_deals_extracted += deals_count
        else:
            self.metrics.failed_files += 1

    def stop(self) -> PipelineMetrics:
        """
        Stop monitoring and return metrics.

        Returns:
            Complete pipeline metrics
        """
        # Stop resource monitoring
        resource_stats = self.resource_monitor.stop()

        # Update metrics
        self.metrics.peak_memory_mb = resource_stats['max_memory_mb']
        self.metrics.avg_cpu_percent = resource_stats['avg_cpu_percent']

        # Finalize
        self.metrics.finalize()

        return self.metrics

    def get_current_metrics(self) -> PipelineMetrics:
        """Get current metrics (without stopping)."""
        return self.metrics


class BottleneckDetector:
    """Detect performance bottlenecks in pipeline."""

    @staticmethod
    def analyze_metrics(metrics: PipelineMetrics) -> Dict[str, Any]:
        """
        Analyze metrics to detect bottlenecks.

        Returns:
            Dictionary with bottleneck analysis
        """
        analysis = {
            'total_duration': metrics.total_duration,
            'slowest_stages': [],
            'bottlenecks': [],
            'recommendations': []
        }

        if not metrics.stages:
            return analysis

        # Find slowest stages
        sorted_stages = sorted(
            metrics.stages.items(),
            key=lambda x: x[1].duration or 0,
            reverse=True
        )

        analysis['slowest_stages'] = [
            {
                'name': name,
                'duration': stage.duration,
                'percentage': (stage.duration / metrics.total_duration * 100) if metrics.total_duration else 0
            }
            for name, stage in sorted_stages[:3]
        ]

        # Detect bottlenecks (stages taking > 30% of total time)
        for name, stage in metrics.stages.items():
            if stage.duration and metrics.total_duration:
                percentage = stage.duration / metrics.total_duration * 100

                if percentage > 30:
                    analysis['bottlenecks'].append({
                        'stage': name,
                        'duration': stage.duration,
                        'percentage': percentage
                    })

        # Generate recommendations
        if metrics.peak_memory_mb > 2000:
            analysis['recommendations'].append(
                "High memory usage detected. Consider processing in smaller batches."
            )

        if metrics.avg_cpu_percent < 20:
            analysis['recommendations'].append(
                "Low CPU utilization. Consider enabling parallel processing or GPU acceleration."
            )

        # Check for failed files
        if metrics.failed_files > 0:
            failure_rate = metrics.failed_files / metrics.input_files * 100
            if failure_rate > 10:
                analysis['recommendations'].append(
                    f"High failure rate ({failure_rate:.1f}%). Check input validation and error handling."
                )

        # Stage-specific recommendations
        for name, stage in metrics.stages.items():
            if not stage.success:
                continue

            if 'ocr' in name.lower() and stage.duration and stage.duration > 5:
                analysis['recommendations'].append(
                    "OCR stage is slow. Consider enabling GPU or using a faster OCR engine."
                )

            if 'vlm' in name.lower() and stage.duration and stage.duration > 10:
                analysis['recommendations'].append(
                    "VLM stage is slow. Consider using a faster model or cloud API."
                )

        return analysis

    @staticmethod
    def print_analysis(analysis: Dict[str, Any]):
        """Print bottleneck analysis."""
        print("\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS")
        print("=" * 80)

        print(f"\nTotal Duration: {analysis['total_duration']:.2f}s")

        if analysis['slowest_stages']:
            print("\nSlowest Stages:")
            for stage in analysis['slowest_stages']:
                print(f"  • {stage['name']}: {stage['duration']:.2f}s ({stage['percentage']:.1f}%)")

        if analysis['bottlenecks']:
            print("\n⚠ Bottlenecks Detected:")
            for bottleneck in analysis['bottlenecks']:
                print(f"  • {bottleneck['stage']}: {bottleneck['duration']:.2f}s ({bottleneck['percentage']:.1f}% of total)")

        if analysis['recommendations']:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"  {i}. {rec}")

        print("\n" + "=" * 80)


# Example usage
if __name__ == '__main__':
    import random

    # Create monitor
    monitor = PipelineMonitor('test-run-001', 'hybrid')
    monitor.start()

    # Simulate stages
    stages = [
        ('load_image', 0.5),
        ('preprocess', 1.0),
        ('ocr_extraction', 3.0),
        ('vlm_extraction', 5.0),
        ('merge_results', 0.5),
        ('save_output', 0.3)
    ]

    for stage_name, duration in stages:
        monitor.start_stage(stage_name, input_size=1024*1024)
        time.sleep(duration)
        monitor.end_stage(
            success=True,
            items_processed=random.randint(10, 50)
        )

    # Record processed files
    for i in range(10):
        monitor.record_file_processed(success=True, deals_count=random.randint(5, 20))

    # Stop and get metrics
    metrics = monitor.stop()

    # Print metrics
    print(json.dumps(metrics.to_dict(), indent=2))

    # Analyze bottlenecks
    analysis = BottleneckDetector.analyze_metrics(metrics)
    BottleneckDetector.print_analysis(analysis)

"""
Enhanced Logging System with Structured Logging

Features:
- Colored console output
- JSON structured logging
- Performance tracking
- Context managers
- Multiple handlers
"""

import logging
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager
import traceback


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BRIGHT_RED + Colors.BOLD,
    }

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.RESET}"

        # Format the message
        result = super().format(record)

        # Reset levelname for other handlers
        record.levelname = levelname

        return result


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class PerformanceLogger:
    """Logger for tracking performance metrics."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = {}

    def track_time(self, operation: str, duration: float):
        """Track operation duration."""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0
            }

        metric = self.metrics[operation]
        metric['count'] += 1
        metric['total_time'] += duration
        metric['min_time'] = min(metric['min_time'], duration)
        metric['max_time'] = max(metric['max_time'], duration)

        avg_time = metric['total_time'] / metric['count']

        self.logger.debug(
            f"Performance: {operation} took {duration:.3f}s "
            f"(avg: {avg_time:.3f}s, min: {metric['min_time']:.3f}s, max: {metric['max_time']:.3f}s)"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        for operation, metric in self.metrics.items():
            stats[operation] = {
                'count': metric['count'],
                'total_time': metric['total_time'],
                'avg_time': metric['total_time'] / metric['count'],
                'min_time': metric['min_time'],
                'max_time': metric['max_time']
            }
        return stats

    def log_summary(self):
        """Log performance summary."""
        self.logger.info("=== Performance Summary ===")
        for operation, stats in self.get_stats().items():
            self.logger.info(
                f"{operation}: {stats['count']} calls, "
                f"avg={stats['avg_time']:.3f}s, "
                f"total={stats['total_time']:.3f}s"
            )


class EnhancedLogger:
    """Enhanced logger with multiple features."""

    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: int = logging.INFO,
        enable_json: bool = False,
        enable_color: bool = True
    ):
        """
        Initialize enhanced logger.

        Args:
            name: Logger name
            log_file: Path to log file (optional)
            level: Logging level
            enable_json: Enable JSON logging to file
            enable_color: Enable colored console output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        # Performance tracking
        self.perf_logger = PerformanceLogger(self.logger)

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        if enable_color:
            console_formatter = ColoredFormatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)

            if enable_json:
                file_formatter = JsonFormatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )

            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, msg, **kwargs)

    def _log(self, level: int, msg: str, **kwargs):
        """Internal logging method with extra data."""
        extra_dict = {'extra_data': kwargs} if kwargs else {}
        self.logger.log(level, msg, extra=extra_dict)

    @contextmanager
    def timed_operation(self, operation: str, log_start: bool = True, log_end: bool = True):
        """
        Context manager for timing operations.

        Usage:
            with logger.timed_operation('pdf_conversion'):
                convert_pdf()
        """
        if log_start:
            self.info(f"Starting: {operation}")

        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.perf_logger.track_time(operation, duration)

            if log_end:
                self.info(f"Completed: {operation} in {duration:.3f}s")

    @contextmanager
    def step(self, description: str, log_start: bool = True, log_end: bool = True):
        """
        Context manager for pipeline steps.

        Usage:
            with logger.step('OCR extraction'):
                results = ocr.extract(image)
        """
        if log_start:
            self.info(f"→ {description}...")

        start_time = time.time()
        success = False

        try:
            yield
            success = True
        except Exception as e:
            self.error(f"✗ {description} failed: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time

            if log_end and success:
                self.info(f"✓ {description} completed in {duration:.3f}s")

    def log_dict(self, title: str, data: Dict[str, Any], level: int = logging.INFO):
        """Log a dictionary in a readable format."""
        self._log(level, f"{title}:")
        for key, value in data.items():
            self._log(level, f"  {key}: {value}")

    def log_list(self, title: str, items: list, level: int = logging.INFO):
        """Log a list in a readable format."""
        self._log(level, f"{title}:")
        for i, item in enumerate(items, 1):
            self._log(level, f"  {i}. {item}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self.perf_logger.get_stats()

    def log_performance_summary(self):
        """Log performance summary."""
        self.perf_logger.log_summary()


def get_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.INFO,
    enable_json: bool = False,
    enable_color: bool = True
) -> EnhancedLogger:
    """
    Get or create an enhanced logger.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level
        enable_json: Enable JSON logging
        enable_color: Enable colored output

    Returns:
        EnhancedLogger instance
    """
    log_file = Path(log_dir) / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    return EnhancedLogger(
        name=name,
        log_file=str(log_file),
        level=level,
        enable_json=enable_json,
        enable_color=enable_color
    )


# Example usage
if __name__ == '__main__':
    # Create logger
    logger = get_logger('test', log_dir='logs/test')

    # Basic logging
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Timed operation
    with logger.timed_operation('test_operation'):
        time.sleep(1)

    # Step logging
    with logger.step('Processing data'):
        time.sleep(0.5)

    # Log dict
    logger.log_dict("Configuration", {
        'model': 'llava',
        'batch_size': 4,
        'gpu': True
    })

    # Performance summary
    logger.log_performance_summary()

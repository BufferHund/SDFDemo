"""Configuration management utilities."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

_config_cache: Optional[Dict[str, Any]] = None


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    global _config_cache

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, 'r') as f:
        _config_cache = yaml.safe_load(f)

    return _config_cache


def get_config() -> Dict[str, Any]:
    """
    Get cached configuration.

    Returns:
        Configuration dictionary

    Raises:
        RuntimeError: If configuration not loaded
    """
    if _config_cache is None:
        load_config()

    return _config_cache


def get_value(key_path: str, default: Any = None) -> Any:
    """
    Get configuration value by dot-separated path.

    Args:
        key_path: Dot-separated path (e.g., "training.batch_size")
        default: Default value if not found

    Returns:
        Configuration value

    Example:
        >>> get_value("training.hyperparameters.batch_size", 4)
        4
    """
    config = get_config()
    keys = key_path.split('.')

    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value

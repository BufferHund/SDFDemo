"""
Training script for brochure information extraction.

Usage:
    python src/models/train.py --config configs/layoutlmv3_config.yaml
    python src/models/train.py --train-dir data/annotated/train --val-dir data/annotated/val
"""

import argparse
import yaml
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.layoutlmv3_model import BrochureLayoutLMv3
from src.models.trainer import BrochureDataset, BrochureTrainer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    parser = argparse.ArgumentParser(description='Train brochure information extraction model')

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration YAML file'
    )

    parser.add_argument(
        '--train-dir',
        type=str,
        default='data/annotated/train',
        help='Directory with training annotations'
    )

    parser.add_argument(
        '--val-dir',
        type=str,
        default='data/annotated/val',
        help='Directory with validation annotations'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='models/checkpoints',
        help='Output directory for checkpoints'
    )

    parser.add_argument(
        '--model-name',
        type=str,
        default='microsoft/layoutlmv3-base',
        help='Pretrained model name'
    )

    parser.add_argument(
        '--num-labels',
        type=int,
        default=5,
        help='Number of entity labels'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Batch size'
    )

    parser.add_argument(
        '--learning-rate',
        type=float,
        default=5e-5,
        help='Learning rate'
    )

    parser.add_argument(
        '--num-epochs',
        type=int,
        default=10,
        help='Number of epochs'
    )

    parser.add_argument(
        '--use-lora',
        action='store_true',
        default=True,
        help='Use LoRA for PEFT'
    )

    parser.add_argument(
        '--lora-r',
        type=int,
        default=16,
        help='LoRA rank'
    )

    parser.add_argument(
        '--lora-alpha',
        type=int,
        default=32,
        help='LoRA alpha'
    )

    parser.add_argument(
        '--use-wandb',
        action='store_true',
        help='Use Weights & Biases for logging'
    )

    parser.add_argument(
        '--resume',
        type=str,
        help='Resume from checkpoint'
    )

    args = parser.parse_args()

    # Load config if provided
    if args.config:
        config = load_config(args.config)
        # Override with config values
        training_config = config.get('training', {})
        args.model_name = training_config.get('layoutlmv3', {}).get('pretrained', args.model_name)
        args.num_labels = training_config.get('layoutlmv3', {}).get('num_labels', args.num_labels)
        args.batch_size = training_config.get('hyperparameters', {}).get('batch_size', args.batch_size)
        args.learning_rate = training_config.get('hyperparameters', {}).get('learning_rate', args.learning_rate)
        args.num_epochs = training_config.get('hyperparameters', {}).get('num_epochs', args.num_epochs)

    # Initialize model
    logger.info("Initializing model...")
    model = BrochureLayoutLMv3(
        model_name=args.model_name,
        num_labels=args.num_labels,
        use_lora=args.use_lora,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha
    )

    # Load datasets
    logger.info("Loading datasets...")
    train_dataset = BrochureDataset(
        data_dir=args.train_dir,
        processor=model.processor
    )

    val_dataset = None
    if Path(args.val_dir).exists():
        val_dataset = BrochureDataset(
            data_dir=args.val_dir,
            processor=model.processor
        )

    # Initialize trainer
    logger.info("Initializing trainer...")
    trainer = BrochureTrainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_epochs=args.num_epochs,
        use_wandb=args.use_wandb
    )

    # Resume from checkpoint if specified
    if args.resume:
        logger.info(f"Resuming from checkpoint: {args.resume}")
        trainer.load_checkpoint(args.resume)

    # Start training
    trainer.train()

    logger.info("Training complete!")


if __name__ == '__main__':
    main()

"""
Training module for brochure information extraction models.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrochureDataset(Dataset):
    """
    Dataset for brochure annotation data.

    Expected data format:
    {
        "image_path": "path/to/image.png",
        "words": ["word1", "word2", ...],
        "boxes": [[x0, y0, x1, y1], ...],
        "labels": [0, 1, 2, ...]  # Entity label IDs
    }
    """

    def __init__(
        self,
        data_dir: str,
        processor,
        max_samples: Optional[int] = None
    ):
        """
        Initialize dataset.

        Args:
            data_dir: Directory containing annotation JSON files
            processor: LayoutLMv3 processor
            max_samples: Maximum number of samples to load
        """
        self.data_dir = Path(data_dir)
        self.processor = processor

        # Load all annotation files
        self.samples = []
        json_files = list(self.data_dir.glob("*.json"))

        if max_samples:
            json_files = json_files[:max_samples]

        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.samples.append(data)

        logger.info(f"Loaded {len(self.samples)} samples from {data_dir}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        """Get a single sample."""
        sample = self.samples[idx]

        # Load image
        from PIL import Image
        image = Image.open(sample['image_path']).convert('RGB')

        # Prepare encoding
        encoding = self.processor(
            image,
            sample['words'],
            boxes=sample['boxes'],
            word_labels=sample['labels'],
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        # Remove batch dimension
        encoding = {k: v.squeeze(0) for k, v in encoding.items()}

        return encoding


class BrochureTrainer:
    """
    Trainer for brochure information extraction models.
    """

    def __init__(
        self,
        model,
        train_dataset: Dataset,
        val_dataset: Optional[Dataset] = None,
        output_dir: str = "models/checkpoints",
        batch_size: int = 4,
        learning_rate: float = 5e-5,
        num_epochs: int = 10,
        warmup_steps: int = 500,
        weight_decay: float = 0.01,
        max_grad_norm: float = 1.0,
        save_steps: int = 500,
        eval_steps: int = 500,
        logging_steps: int = 100,
        use_wandb: bool = False
    ):
        """
        Initialize trainer.

        Args:
            model: BrochureLayoutLMv3 model
            train_dataset: Training dataset
            val_dataset: Validation dataset
            output_dir: Directory to save checkpoints
            batch_size: Batch size
            learning_rate: Learning rate
            num_epochs: Number of training epochs
            warmup_steps: Warmup steps for learning rate scheduler
            weight_decay: Weight decay
            max_grad_norm: Maximum gradient norm for clipping
            save_steps: Save checkpoint every N steps
            eval_steps: Evaluate every N steps
            logging_steps: Log every N steps
            use_wandb: Whether to use Weights & Biases for logging
        """
        self.model = model
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.save_steps = save_steps
        self.eval_steps = eval_steps
        self.logging_steps = logging_steps
        self.max_grad_norm = max_grad_norm

        # Create data loaders
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0  # Set to 0 to avoid multiprocessing issues
        )

        if val_dataset:
            self.val_loader = DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=0
            )
        else:
            self.val_loader = None

        # Set up optimizer
        self.optimizer = AdamW(
            model.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        # Set up learning rate scheduler
        total_steps = len(self.train_loader) * num_epochs
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )

        # Initialize tracking
        self.global_step = 0
        self.best_val_loss = float('inf')

        # Weights & Biases
        self.use_wandb = use_wandb
        if use_wandb:
            try:
                import wandb
                self.wandb = wandb
                wandb.init(project="supermarket-brochure-ai")
            except ImportError:
                logger.warning("wandb not installed. Logging disabled.")
                self.use_wandb = False

        logger.info(f"Trainer initialized. Total steps: {total_steps}")

    def train(self):
        """Run training loop."""
        logger.info("Starting training...")

        for epoch in range(self.num_epochs):
            logger.info(f"Epoch {epoch + 1}/{self.num_epochs}")

            # Training phase
            self.model.model.train()
            train_loss = 0.0

            progress_bar = tqdm(self.train_loader, desc=f"Training Epoch {epoch + 1}")

            for step, batch in enumerate(progress_bar):
                # Forward pass
                outputs = self.model.forward(
                    pixel_values=batch['pixel_values'],
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    bbox=batch['bbox'],
                    labels=batch['labels']
                )

                loss = outputs.loss
                train_loss += loss.item()

                # Backward pass
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(
                    self.model.model.parameters(),
                    self.max_grad_norm
                )

                # Optimizer step
                self.optimizer.step()
                self.scheduler.step()
                self.optimizer.zero_grad()

                self.global_step += 1

                # Update progress bar
                progress_bar.set_postfix({
                    'loss': loss.item(),
                    'lr': self.scheduler.get_last_lr()[0]
                })

                # Logging
                if self.global_step % self.logging_steps == 0:
                    avg_loss = train_loss / (step + 1)
                    logger.info(f"Step {self.global_step}: loss={avg_loss:.4f}")

                    if self.use_wandb:
                        self.wandb.log({
                            'train/loss': loss.item(),
                            'train/learning_rate': self.scheduler.get_last_lr()[0],
                            'train/epoch': epoch
                        }, step=self.global_step)

                # Evaluation
                if self.val_loader and self.global_step % self.eval_steps == 0:
                    val_loss = self.evaluate()
                    logger.info(f"Validation loss: {val_loss:.4f}")

                    if self.use_wandb:
                        self.wandb.log({
                            'val/loss': val_loss
                        }, step=self.global_step)

                    # Save best model
                    if val_loss < self.best_val_loss:
                        self.best_val_loss = val_loss
                        self.save_checkpoint("best_model")
                        logger.info(f"New best model saved! Val loss: {val_loss:.4f}")

                    # Return to training mode
                    self.model.model.train()

                # Save checkpoint
                if self.global_step % self.save_steps == 0:
                    self.save_checkpoint(f"checkpoint-{self.global_step}")

            # End of epoch
            avg_train_loss = train_loss / len(self.train_loader)
            logger.info(f"Epoch {epoch + 1} average loss: {avg_train_loss:.4f}")

        logger.info("Training complete!")

        # Save final model
        self.save_checkpoint("final_model")

    def evaluate(self) -> float:
        """
        Evaluate on validation set.

        Returns:
            Average validation loss
        """
        self.model.model.eval()
        total_loss = 0.0

        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Evaluating"):
                outputs = self.model.forward(
                    pixel_values=batch['pixel_values'],
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    bbox=batch['bbox'],
                    labels=batch['labels']
                )

                total_loss += outputs.loss.item()

        avg_loss = total_loss / len(self.val_loader)
        return avg_loss

    def save_checkpoint(self, name: str):
        """Save model checkpoint."""
        checkpoint_dir = self.output_dir / name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.model.save_model(str(checkpoint_dir))

        # Save training state
        state = {
            'global_step': self.global_step,
            'best_val_loss': self.best_val_loss,
            'optimizer_state': self.optimizer.state_dict(),
            'scheduler_state': self.scheduler.state_dict()
        }

        torch.save(state, checkpoint_dir / "training_state.pt")
        logger.info(f"Checkpoint saved to {checkpoint_dir}")

    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint."""
        checkpoint_path = Path(checkpoint_path)

        # Load model
        self.model.load_model(str(checkpoint_path))

        # Load training state
        state_path = checkpoint_path / "training_state.pt"
        if state_path.exists():
            state = torch.load(state_path)
            self.global_step = state['global_step']
            self.best_val_loss = state['best_val_loss']
            self.optimizer.load_state_dict(state['optimizer_state'])
            self.scheduler.load_state_dict(state['scheduler_state'])

            logger.info(f"Checkpoint loaded from {checkpoint_path}")
        else:
            logger.warning("Training state not found. Only model weights loaded.")

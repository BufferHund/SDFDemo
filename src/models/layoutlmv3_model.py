"""
LayoutLMv3 Model for Brochure Information Extraction

This module implements fine-tuning of LayoutLMv3 for extracting
structured information from supermarket brochures.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from transformers import (
    LayoutLMv3ForTokenClassification,
    LayoutLMv3Processor,
    LayoutLMv3Config
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftModel
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrochureLayoutLMv3:
    """
    LayoutLMv3 model wrapper for brochure information extraction.

    Supports:
    - Token classification for entity recognition
    - PEFT/LoRA for parameter-efficient fine-tuning
    - Custom entity types (product_name, price, discount, etc.)
    """

    def __init__(
        self,
        model_name: str = "microsoft/layoutlmv3-base",
        num_labels: int = 5,
        use_lora: bool = True,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.1,
        device: str = None
    ):
        """
        Initialize LayoutLMv3 model.

        Args:
            model_name: Pretrained model name or path
            num_labels: Number of entity labels
            use_lora: Whether to use LoRA for PEFT
            lora_r: LoRA rank
            lora_alpha: LoRA alpha parameter
            lora_dropout: LoRA dropout rate
            device: Device to use (cuda/cpu)
        """
        self.model_name = model_name
        self.num_labels = num_labels
        self.use_lora = use_lora

        # Set device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Using device: {self.device}")

        # Load processor
        self.processor = LayoutLMv3Processor.from_pretrained(
            model_name,
            apply_ocr=False  # We use our own OCR
        )

        # Load model
        self.model = LayoutLMv3ForTokenClassification.from_pretrained(
            model_name,
            num_labels=num_labels
        )

        # Apply LoRA if requested
        if use_lora:
            logger.info("Applying LoRA for parameter-efficient fine-tuning")
            lora_config = LoraConfig(
                task_type=TaskType.TOKEN_CLS,
                r=lora_r,
                lora_alpha=lora_alpha,
                lora_dropout=lora_dropout,
                target_modules=["query", "value"],
                bias="none"
            )
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()

        self.model.to(self.device)
        logger.info(f"Model initialized: {model_name}")

    def prepare_inputs(
        self,
        image,
        words: List[str],
        boxes: List[List[int]],
        word_labels: Optional[List[int]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Prepare inputs for the model.

        Args:
            image: PIL Image
            words: List of words from OCR
            boxes: List of bounding boxes [x0, y0, x1, y1]
            word_labels: Optional list of labels for training

        Returns:
            Dictionary of model inputs
        """
        # Prepare encoding
        encoding = self.processor(
            image,
            words,
            boxes=boxes,
            word_labels=word_labels,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        # Move to device
        encoding = {k: v.to(self.device) for k, v in encoding.items()}

        return encoding

    def forward(
        self,
        pixel_values: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        bbox: torch.Tensor,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the model.

        Args:
            pixel_values: Image tensor
            input_ids: Token IDs
            attention_mask: Attention mask
            bbox: Bounding boxes
            labels: Optional labels for training

        Returns:
            Model outputs (loss, logits)
        """
        outputs = self.model(
            pixel_values=pixel_values,
            input_ids=input_ids,
            attention_mask=attention_mask,
            bbox=bbox,
            labels=labels
        )

        return outputs

    def predict(
        self,
        image,
        words: List[str],
        boxes: List[List[int]]
    ) -> Tuple[List[int], List[float]]:
        """
        Predict entity labels for words.

        Args:
            image: PIL Image
            words: List of words
            boxes: List of bounding boxes

        Returns:
            Tuple of (predicted_labels, confidence_scores)
        """
        self.model.eval()

        with torch.no_grad():
            # Prepare inputs
            encoding = self.prepare_inputs(image, words, boxes)

            # Forward pass
            outputs = self.forward(
                pixel_values=encoding['pixel_values'],
                input_ids=encoding['input_ids'],
                attention_mask=encoding['attention_mask'],
                bbox=encoding['bbox']
            )

            # Get predictions
            logits = outputs.logits
            predictions = torch.argmax(logits, dim=-1)
            probabilities = torch.softmax(logits, dim=-1)

            # Get confidence scores
            confidence = torch.max(probabilities, dim=-1).values

            # Convert to lists (skip special tokens)
            attention_mask = encoding['attention_mask'][0].cpu().numpy()
            predictions = predictions[0].cpu().numpy()
            confidence = confidence[0].cpu().numpy()

            # Filter out special tokens
            word_predictions = []
            word_confidence = []

            for i, mask in enumerate(attention_mask):
                if mask and i < len(words):  # Valid token
                    word_predictions.append(int(predictions[i]))
                    word_confidence.append(float(confidence[i]))

            return word_predictions, word_confidence

    def save_model(self, output_dir: str):
        """Save model to directory."""
        logger.info(f"Saving model to {output_dir}")
        self.model.save_pretrained(output_dir)
        self.processor.save_pretrained(output_dir)

    def load_model(self, model_path: str):
        """Load model from directory."""
        logger.info(f"Loading model from {model_path}")

        if self.use_lora:
            # Load PEFT model
            self.model = PeftModel.from_pretrained(
                self.model,
                model_path
            )
        else:
            # Load full model
            self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                model_path,
                num_labels=self.num_labels
            )

        self.model.to(self.device)
        self.processor = LayoutLMv3Processor.from_pretrained(model_path)


# Entity label mapping
ENTITY_LABELS = {
    0: "O",  # Outside
    1: "B-PRODUCT",  # Product name
    2: "B-PRICE",  # Original price
    3: "B-DISCOUNT_PRICE",  # Discounted price
    4: "B-DISCOUNT_PERCENT",  # Discount percentage
}

LABEL_TO_ID = {v: k for k, v in ENTITY_LABELS.items()}


def decode_predictions(
    words: List[str],
    predictions: List[int],
    boxes: List[List[int]],
    confidence: List[float] = None
) -> List[Dict]:
    """
    Decode predictions into structured entities.

    Args:
        words: List of words
        predictions: List of predicted label IDs
        boxes: List of bounding boxes
        confidence: Optional confidence scores

    Returns:
        List of extracted entities
    """
    entities = []
    current_entity = None

    for i, (word, pred, box) in enumerate(zip(words, predictions, boxes)):
        label = ENTITY_LABELS.get(pred, "O")
        conf = confidence[i] if confidence else 1.0

        if label.startswith("B-"):
            # Save previous entity
            if current_entity:
                entities.append(current_entity)

            # Start new entity
            entity_type = label[2:]  # Remove "B-"
            current_entity = {
                "type": entity_type,
                "text": word,
                "bbox": box,
                "confidence": conf
            }
        elif label == "O":
            # Save previous entity
            if current_entity:
                entities.append(current_entity)
                current_entity = None
        else:
            # Continue current entity (I- tags)
            if current_entity:
                current_entity["text"] += " " + word

    # Save last entity
    if current_entity:
        entities.append(current_entity)

    return entities

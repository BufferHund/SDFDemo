"""
Evaluation Metrics for Brochure Information Extraction

Implements:
- Token-level metrics (F1, Precision, Recall)
- Entity-level metrics (Exact match, Partial match)
- Detection metrics (mAP, IoU)
"""

import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_iou(box1: List[int], box2: List[int]) -> float:
    """
    Compute Intersection over Union (IoU) between two boxes.

    Args:
        box1: [x1, y1, x2, y2]
        box2: [x1, y1, x2, y2]

    Returns:
        IoU score (0-1)
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union = box1_area + box2_area - intersection

    if union == 0:
        return 0.0

    return intersection / union


def compute_token_metrics(
    true_labels: List[int],
    pred_labels: List[int],
    label_names: Dict[int, str] = None
) -> Dict[str, float]:
    """
    Compute token-level classification metrics.

    Args:
        true_labels: Ground truth labels
        pred_labels: Predicted labels
        label_names: Optional mapping of label IDs to names

    Returns:
        Dictionary with precision, recall, F1 for each label
    """
    from sklearn.metrics import precision_recall_fscore_support, accuracy_score

    # Compute overall metrics
    accuracy = accuracy_score(true_labels, pred_labels)

    # Compute per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        true_labels,
        pred_labels,
        average=None,
        zero_division=0
    )

    # Compute macro average
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        true_labels,
        pred_labels,
        average='macro',
        zero_division=0
    )

    metrics = {
        'accuracy': accuracy,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1
    }

    # Per-class metrics
    unique_labels = set(true_labels) | set(pred_labels)
    for label_id in unique_labels:
        label_name = label_names.get(label_id, f"label_{label_id}") if label_names else f"label_{label_id}"

        if label_id < len(precision):
            metrics[f'{label_name}_precision'] = precision[label_id]
            metrics[f'{label_name}_recall'] = recall[label_id]
            metrics[f'{label_name}_f1'] = f1[label_id]
            metrics[f'{label_name}_support'] = int(support[label_id])

    return metrics


def compute_entity_metrics(
    true_entities: List[Dict],
    pred_entities: List[Dict],
    iou_threshold: float = 0.5
) -> Dict[str, float]:
    """
    Compute entity-level metrics with spatial matching.

    Args:
        true_entities: Ground truth entities
            [{"type": "PRODUCT", "text": "Milk", "bbox": [x1, y1, x2, y2]}, ...]
        pred_entities: Predicted entities
        iou_threshold: Minimum IoU for matching

    Returns:
        Dictionary with precision, recall, F1
    """
    if not true_entities and not pred_entities:
        return {
            'entity_precision': 1.0,
            'entity_recall': 1.0,
            'entity_f1': 1.0,
            'exact_match': 1.0
        }

    if not pred_entities:
        return {
            'entity_precision': 0.0,
            'entity_recall': 0.0,
            'entity_f1': 0.0,
            'exact_match': 0.0
        }

    if not true_entities:
        return {
            'entity_precision': 0.0,
            'entity_recall': 1.0,
            'entity_f1': 0.0,
            'exact_match': 0.0
        }

    # Match entities by type and spatial overlap
    true_matched = set()
    pred_matched = set()
    exact_matches = 0

    for i, pred_ent in enumerate(pred_entities):
        best_match = None
        best_iou = iou_threshold

        for j, true_ent in enumerate(true_entities):
            if j in true_matched:
                continue

            # Check if types match
            if pred_ent['type'] != true_ent['type']:
                continue

            # Compute IoU
            iou = compute_iou(pred_ent['bbox'], true_ent['bbox'])

            if iou > best_iou:
                best_iou = iou
                best_match = j

        if best_match is not None:
            pred_matched.add(i)
            true_matched.add(best_match)

            # Check for exact match (text + bbox)
            if pred_ent['text'].strip().lower() == true_entities[best_match]['text'].strip().lower():
                exact_matches += 1

    # Compute metrics
    true_positive = len(pred_matched)
    false_positive = len(pred_entities) - true_positive
    false_negative = len(true_entities) - len(true_matched)

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    exact_match_rate = exact_matches / len(true_entities) if true_entities else 0

    return {
        'entity_precision': precision,
        'entity_recall': recall,
        'entity_f1': f1,
        'exact_match': exact_match_rate,
        'true_positives': true_positive,
        'false_positives': false_positive,
        'false_negatives': false_negative
    }


def compute_per_type_metrics(
    true_entities: List[Dict],
    pred_entities: List[Dict],
    iou_threshold: float = 0.5
) -> Dict[str, Dict[str, float]]:
    """
    Compute metrics per entity type.

    Args:
        true_entities: Ground truth entities
        pred_entities: Predicted entities
        iou_threshold: Minimum IoU for matching

    Returns:
        Dictionary mapping entity types to their metrics
    """
    # Group entities by type
    true_by_type = defaultdict(list)
    pred_by_type = defaultdict(list)

    for ent in true_entities:
        true_by_type[ent['type']].append(ent)

    for ent in pred_entities:
        pred_by_type[ent['type']].append(ent)

    # Get all entity types
    all_types = set(true_by_type.keys()) | set(pred_by_type.keys())

    # Compute metrics for each type
    results = {}
    for entity_type in all_types:
        results[entity_type] = compute_entity_metrics(
            true_by_type[entity_type],
            pred_by_type[entity_type],
            iou_threshold
        )

    return results


def compute_detection_ap(
    true_boxes: List[List[int]],
    pred_boxes: List[List[int]],
    pred_scores: List[float],
    iou_threshold: float = 0.5
) -> float:
    """
    Compute Average Precision (AP) for detection.

    Args:
        true_boxes: Ground truth bounding boxes
        pred_boxes: Predicted bounding boxes
        pred_scores: Confidence scores for predictions
        iou_threshold: IoU threshold for positive match

    Returns:
        Average Precision score
    """
    if not pred_boxes:
        return 0.0

    if not true_boxes:
        return 0.0

    # Sort predictions by confidence (descending)
    sorted_indices = np.argsort(pred_scores)[::-1]
    pred_boxes = [pred_boxes[i] for i in sorted_indices]
    pred_scores = [pred_scores[i] for i in sorted_indices]

    # Track which ground truth boxes have been matched
    matched_gt = set()

    tp = []  # True positives
    fp = []  # False positives

    for pred_box in pred_boxes:
        best_iou = 0
        best_gt_idx = -1

        for gt_idx, gt_box in enumerate(true_boxes):
            if gt_idx in matched_gt:
                continue

            iou = compute_iou(pred_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx

        if best_iou >= iou_threshold:
            tp.append(1)
            fp.append(0)
            matched_gt.add(best_gt_idx)
        else:
            tp.append(0)
            fp.append(1)

    # Compute precision and recall at each threshold
    tp_cumsum = np.cumsum(tp)
    fp_cumsum = np.cumsum(fp)

    recalls = tp_cumsum / len(true_boxes)
    precisions = tp_cumsum / (tp_cumsum + fp_cumsum)

    # Compute AP using 11-point interpolation
    ap = 0
    for t in np.linspace(0, 1, 11):
        if np.sum(recalls >= t) == 0:
            p = 0
        else:
            p = np.max(precisions[recalls >= t])
        ap += p / 11

    return ap


def compute_metrics(
    true_labels: List[int],
    pred_labels: List[int],
    true_entities: List[Dict] = None,
    pred_entities: List[Dict] = None,
    label_names: Dict[int, str] = None
) -> Dict[str, float]:
    """
    Compute all evaluation metrics.

    Args:
        true_labels: Ground truth token labels
        pred_labels: Predicted token labels
        true_entities: Optional ground truth entities
        pred_entities: Optional predicted entities
        label_names: Optional label ID to name mapping

    Returns:
        Dictionary with all metrics
    """
    metrics = {}

    # Token-level metrics
    token_metrics = compute_token_metrics(true_labels, pred_labels, label_names)
    metrics.update(token_metrics)

    # Entity-level metrics
    if true_entities is not None and pred_entities is not None:
        entity_metrics = compute_entity_metrics(true_entities, pred_entities)
        metrics.update(entity_metrics)

        # Per-type metrics
        per_type_metrics = compute_per_type_metrics(true_entities, pred_entities)
        for entity_type, type_metrics in per_type_metrics.items():
            for metric_name, value in type_metrics.items():
                metrics[f'{entity_type}_{metric_name}'] = value

    return metrics


def evaluate_model(
    model,
    test_dataset,
    label_names: Dict[int, str] = None
) -> Dict[str, float]:
    """
    Evaluate model on test dataset.

    Args:
        model: BrochureLayoutLMv3 model
        test_dataset: Test dataset
        label_names: Label ID to name mapping

    Returns:
        Dictionary with evaluation metrics
    """
    from PIL import Image
    import json

    all_true_labels = []
    all_pred_labels = []
    all_true_entities = []
    all_pred_entities = []

    logger.info(f"Evaluating on {len(test_dataset)} samples...")

    for i in range(len(test_dataset)):
        sample = test_dataset.samples[i]

        # Load image
        image = Image.open(sample['image_path']).convert('RGB')

        # Predict
        pred_labels, confidence = model.predict(
            image,
            sample['words'],
            sample['boxes']
        )

        # Collect token-level labels
        all_true_labels.extend(sample['labels'])
        all_pred_labels.extend(pred_labels)

        # TODO: Extract entities from labels
        # This would require implementing entity extraction from BIO tags
        # For now, we focus on token-level metrics

    # Compute metrics
    metrics = compute_metrics(
        all_true_labels,
        all_pred_labels,
        label_names=label_names
    )

    # Log results
    logger.info("Evaluation Results:")
    for key, value in metrics.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")

    return metrics

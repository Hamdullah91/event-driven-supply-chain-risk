from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

import numpy as np
import torch
from datasets import load_from_disk
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

import matplotlib.pyplot as plt

from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "event_classifier"
    / "distilbert_supply_chain"
)

TEST_DIR = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "processed"
    / "test"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "evaluation"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    LOGGER.info("Loading test dataset: %s", TEST_DIR)
    test_dataset = load_from_disk(str(TEST_DIR))

    LOGGER.info("Loading model: %s", MODEL_DIR)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_DIR
    )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    model.to(device)
    model.eval()

    LOGGER.info("Device: %s", device)
    LOGGER.info("Test samples: %d", len(test_dataset))

    y_true: list[int] = []
    y_pred: list[int] = []
    confidences: list[float] = []

    batch_size = 16

    for start in range(0, len(test_dataset), batch_size):
        batch = test_dataset[
            start : start + batch_size
        ]

        encoded = tokenizer.pad(
            {
                "input_ids": batch["input_ids"],
                "attention_mask": batch["attention_mask"],
            },
            padding=True,
            return_tensors="pt",
        )

        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)

        labels = batch["label"]

        with torch.no_grad():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )

        confidence, predictions = torch.max(
            probabilities,
            dim=-1,
        )

        y_true.extend(labels)
        y_pred.extend(
            predictions.cpu().tolist()
        )
        confidences.extend(
            confidence.cpu().tolist()
        )

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    macro_precision, macro_recall, macro_f1, _ = (
        precision_recall_fscore_support(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        )
    )

    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0,
        )
    )

    label_ids = sorted(
        set(y_true) | set(y_pred)
    )

    label_names = [
        model.config.id2label.get(
            label_id,
            f"LABEL_{label_id}",
        )
        for label_id in label_ids
    ]

    label_ids = sorted(
        set(y_true) | set(y_pred)
    )

    label_names = [
        model.config.id2label.get(
            label_id,
            f"LABEL_{label_id}",
        )
        for label_id in label_ids
    ]

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=label_ids,
    )

    # Generate confusion matrix image
    fig, ax = plt.subplots(figsize=(11, 8))

    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=label_names,
    )

    display.plot(
        ax=ax,
        xticks_rotation=45,
        values_format="d",
    )

    ax.set_title(
        "DistilBERT Supply Chain Event Classifier\n"
        "Confusion Matrix"
    )

    fig.tight_layout()

    confusion_matrix_path = (
        OUTPUT_DIR / "confusion_matrix.png"
    )

    fig.savefig(
        confusion_matrix_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    report_dict = classification_report(
        y_true,
        y_pred,
        labels=label_ids,
        target_names=label_names,
        zero_division=0,
        output_dict=True,
    )

    report_text = classification_report(
        y_true,
        y_pred,
        labels=label_ids,
        target_names=label_names,
        zero_division=0,
    )

    metrics = {
        "test_samples": len(y_true),
        "accuracy": accuracy,
        "precision_macro": macro_precision,
        "recall_macro": macro_recall,
        "f1_macro": macro_f1,
        "precision_weighted": weighted_precision,
        "recall_weighted": weighted_recall,
        "f1_weighted": weighted_f1,
        "labels": label_names,
        "confusion_matrix": matrix.tolist(),
    }

    with (
        OUTPUT_DIR / "test_metrics.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=2,
        )

    with (
        OUTPUT_DIR / "classification_report.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report_dict,
            file,
            indent=2,
        )

    with (
        OUTPUT_DIR / "classification_report.txt"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(report_text)

    with (
        OUTPUT_DIR / "test_predictions.csv"
    ).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "true_label_id",
                "true_label",
                "predicted_label_id",
                "predicted_label",
                "confidence",
                "correct",
            ]
        )

        for true_id, pred_id, confidence in zip(
            y_true,
            y_pred,
            confidences,
            strict=True,
        ):
            writer.writerow(
                [
                    true_id,
                    model.config.id2label.get(
                        true_id,
                        f"LABEL_{true_id}",
                    ),
                    pred_id,
                    model.config.id2label.get(
                        pred_id,
                        f"LABEL_{pred_id}",
                    ),
                    round(confidence, 6),
                    true_id == pred_id,
                ]
            )

    print("\n========== DAY 30 TEST EVALUATION ==========\n")

    print(f"Test Samples       : {len(y_true)}")
    print(f"Accuracy           : {accuracy:.4f}")

    print(
        f"Macro Precision    : "
        f"{macro_precision:.4f}"
    )

    print(
        f"Macro Recall       : "
        f"{macro_recall:.4f}"
    )

    print(
        f"Macro F1           : "
        f"{macro_f1:.4f}"
    )

    print(
        f"Weighted Precision : "
        f"{weighted_precision:.4f}"
    )

    print(
        f"Weighted Recall    : "
        f"{weighted_recall:.4f}"
    )

    print(
        f"Weighted F1        : "
        f"{weighted_f1:.4f}"
    )

    print("\nClassification Report:\n")
    print(report_text)

    print("Confusion Matrix:")
    print(matrix)

    print(
        f"\nEvaluation files saved to:\n"
        f"{OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
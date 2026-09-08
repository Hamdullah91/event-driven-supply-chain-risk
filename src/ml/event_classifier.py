from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassificationResult:
    event_type: str
    confidence: float
    requires_review: bool
    second_event_type: str
    second_confidence: float
    confidence_margin: float


class EventClassifier:
    """
    Reusable inference wrapper for the fine-tuned
    DistilBERT supply-chain event classifier.
    """

    def __init__(
        self,
        model_path: str | Path,
        max_length: int = 256,
        confidence_threshold: float = 0.70,
    ) -> None:
        self.model_path = Path(model_path)
        self.max_length = max_length

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model directory does not exist: {self.model_path}"
            )

        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "confidence_threshold must be between 0 and 1."
            )

        self.confidence_threshold = confidence_threshold

        self.device = (
            torch.device("cuda")
            if torch.cuda.is_available()
            else torch.device("cpu")
        )

        logger.info(
            "Loading event classifier from %s on %s",
            self.model_path,
            self.device,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path
        )

        self.model = (
            AutoModelForSequenceClassification.from_pretrained(
                self.model_path
            )
        )

        self.model.to(self.device)
        self.model.eval()

        self._validate_label_mapping()

    def _validate_label_mapping(self) -> None:
        id2label = self.model.config.id2label

        if not id2label:
            raise ValueError(
                "Model configuration has no id2label mapping."
            )

        if len(id2label) != self.model.config.num_labels:
            raise ValueError(
                "id2label mapping does not match num_labels."
            )

    @staticmethod
    def _validate_text(article: str) -> str:
        if not isinstance(article, str):
            raise TypeError("Article must be a string.")

        article = article.strip()

        if not article:
            raise ValueError("Article cannot be empty.")

        return article

    def classify(
        self,
        article: str,
    ) -> ClassificationResult:

        article = self._validate_text(article)

        encoded = self.tokenizer(
            article,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        encoded = {
            key: value.to(self.device)
            for key, value in encoded.items()
        }

        with torch.inference_mode():
            outputs = self.model(**encoded)

        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )[0]

        top_values, top_indices = torch.topk(
            probabilities,
            k=2,
        )

        predicted_id = int(top_indices[0].item())
        second_id = int(top_indices[1].item())

        confidence = float(top_values[0].item())
        second_confidence = float(top_values[1].item())

        event_type = str(
            self.model.config.id2label[predicted_id]
        )

        second_event_type = str(
            self.model.config.id2label[second_id]
        )

        confidence_margin = confidence - second_confidence

        return ClassificationResult(
            event_type=event_type,
            confidence=confidence,
            requires_review=(
                confidence < self.confidence_threshold
            ),
            second_event_type=second_event_type,
            second_confidence=second_confidence,
            confidence_margin=confidence_margin,
        )
    def predict_proba(
        self,
        article: str,
    ) -> dict[str, float]:
        article = self._validate_text(article)

        encoded = self.tokenizer(
            article,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        encoded = {
            key: value.to(self.device)
            for key, value in encoded.items()
        }

        with torch.inference_mode():
            outputs = self.model(**encoded)

        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )[0]

        return {
            str(self.model.config.id2label[class_id]): float(probability)
            for class_id, probability in enumerate(probabilities.tolist())
        }
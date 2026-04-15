"""
SilentWitness - Evidence Classifier Module
ML pipeline for classifying abuse evidence from text transcripts
"""

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


class AbuseType(Enum):
    PHYSICAL = "physical"
    EMOTIONAL = "emotional"
    FINANCIAL = "financial"
    SEXUAL = "sexual"
    NEGLECT = "neglect"
    UNKNOWN = "unknown"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceStrength(Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class LegalRelevance(Enum):
    CIVIL = "civil"
    CRIMINAL = "criminal"
    BOTH = "both"
    NONE = "none"


@dataclass
class EvidenceClassification:
    abuse_type: AbuseType
    severity: Severity
    evidence_strength: EvidenceStrength
    legal_relevance: LegalRelevance
    confidence_score: float
    keywords_detected: List[str]
    recommended_actions: List[str]


class EvidenceClassifier(nn.Module):
    """
    Multi-task classification model for abuse evidence.
    Uses transformer encoder with task-specific heads.
    """

    def __init__(
        self,
        model_name: str = "google/gemma-2b",  # Base model for embeddings
        hidden_size: int = 256,
        num_abuse_types: int = 6,
        num_severities: int = 4,
        num_strengths: int = 3,
        num_legal: int = 4
    ):
        super().__init__()

        # Encoder (using Gemma or lightweight model for local inference)
        self.encoder = AutoModel.from_pretrained(model_name)
        encoder_size = self.encoder.config.hidden_size

        # Shared representation layer
        self.shared_layer = nn.Sequential(
            nn.Linear(encoder_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )

        # Task-specific classification heads
        self.abuse_type_head = nn.Linear(hidden_size, num_abuse_types)
        self.severity_head = nn.Linear(hidden_size, num_severities)
        self.evidence_strength_head = nn.Linear(hidden_size, num_strengths)
        self.legal_relevance_head = nn.Linear(hidden_size, num_legal)

        # Confidence estimation head
        self.confidence_head = nn.Linear(hidden_size, 1)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass returning all classification outputs.
        """
        # Get encoder outputs
        encoder_outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = encoder_outputs.last_hidden_state[:, 0]  # Use first token (CLS)

        # Shared representation
        shared_repr = self.shared_layer(pooled_output)

        # Multi-task outputs
        return {
            "abuse_type": self.abuse_type_head(shared_repr),
            "severity": self.severity_head(shared_repr),
            "evidence_strength": self.evidence_strength_head(shared_repr),
            "legal_relevance": self.legal_relevance_head(shared_repr),
            "confidence": self.confidence_head(shared_repr)
        }

    def classify(self, text: str, tokenizer: AutoTokenizer) -> EvidenceClassification:
        """
        Classify a text transcript and return structured evidence classification.
        """
        # Tokenize
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )

        # Forward pass
        with torch.no_grad():
            outputs = self.forward(inputs["input_ids"], inputs["attention_mask"])

        # Convert to predictions
        abuse_type_idx = torch.argmax(outputs["abuse_type"], dim=-1).item()
        severity_idx = torch.argmax(outputs["severity"], dim=-1).item()
        strength_idx = torch.argmax(outputs["evidence_strength"], dim=-1).item()
        legal_idx = torch.argmax(outputs["legal_relevance"], dim=-1).item()
        confidence = torch.sigmoid(outputs["confidence"]).item()

        # Map to enums
        abuse_types = list(AbuseType)
        severities = list(Severity)
        strengths = list(EvidenceStrength)
        legal_rels = list(LegalRelevance)

        # Extract keywords (simple implementation)
        keywords = self._extract_keywords(text)

        # Generate recommended actions
        actions = self._generate_recommendations(
            abuse_types[abuse_type_idx],
            severities[severity_idx]
        )

        return EvidenceClassification(
            abuse_type=abuse_types[abuse_type_idx],
            severity=severities[severity_idx],
            evidence_strength=strengths[strength_idx],
            legal_relevance=legal_rels[legal_idx],
            confidence_score=confidence,
            keywords_detected=keywords,
            recommended_actions=actions
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from evidence text.
        """
        # Abuse-related keywords to detect
        keyword_categories = {
            "physical": ["hit", "push", "slap", "kick", "punch", "grab", "throw", "burn", "cut", "bruise"],
            "emotional": ["threaten", "insult", "humiliate", "control", "isolate", "gaslight", "manipulate", "blame"],
            "financial": ["money", "steal", "control finances", "debt", "credit", "bank", "force work", "no access"],
            "sexual": ["force", "touch", "assault", "rape", "harass", "inappropriate"],
            "neglect": ["ignore", "abandon", "no food", "no medical", "no care", "left alone"]
        }

        detected = []
        text_lower = text.lower()
        for category, keywords in keyword_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(keyword)

        return detected[:10]  # Limit to top 10

    def _generate_recommendations(
        self,
        abuse_type: AbuseType,
        severity: Severity
    ) -> List[str]:
        """
        Generate recommended actions based on classification.
        """
        recommendations = []

        if severity == Severity.CRITICAL:
            recommendations.append("Seek immediate safety - call emergency services")
            recommendations.append("Document this incident immediately")

        if severity in [Severity.HIGH, Severity.CRITICAL]:
            recommendations.append("Contact local abuse support hotline")
            recommendations.append("Consider safe housing options")

        if abuse_type == AbuseType.PHYSICAL:
            recommendations.append("Seek medical attention if injured")
            recommendations.append("Photograph any visible injuries")

        if abuse_type == AbuseType.FINANCIAL:
            recommendations.append("Secure important documents")
            recommendations.append("Review financial accounts for unauthorized access")

        recommendations.append("Continue documenting all incidents")
        recommendations.append("Save this evidence securely")

        return recommendations

    def export_onnx(self, tokenizer: AutoTokenizer, output_path: str):
        """
        Export model to ONNX format for mobile deployment.
        """
        dummy_input = tokenizer(
            "Sample evidence text",
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        torch.onnx.export(
            self,
            (dummy_input["input_ids"], dummy_input["attention_mask"]),
            output_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["abuse_type", "severity", "evidence_strength", "legal_relevance", "confidence"],
            dynamic_axes={
                "input_ids": {0: "batch_size", 1: "sequence_length"},
                "attention_mask": {0: "batch_size", 1: "sequence_length"}
            }
        )


def create_classifier(model_path: Optional[str] = None) -> EvidenceClassifier:
    """
    Factory function to create or load evidence classifier.
    """
    model_name = "google/gemma-2b-it"  # Use instruction-tuned variant

    classifier = EvidenceClassifier(model_name=model_name)

    if model_path and torch.cuda.is_available():
        classifier.load_state_dict(torch.load(model_path))
    elif model_path:
        classifier.load_state_dict(torch.load(model_path, map_location="cpu"))

    return classifier


def classification_to_json(classification: EvidenceClassification) -> str:
    """
    Convert classification to JSON for storage/export.
    """
    return json.dumps({
        "abuse_type": classification.abuse_type.value,
        "severity": classification.severity.value,
        "evidence_strength": classification.evidence_strength.value,
        "legal_relevance": classification.legal_relevance.value,
        "confidence_score": classification.confidence_score,
        "keywords_detected": classification.keywords_detected,
        "recommended_actions": classification.recommended_actions,
        "timestamp": classification.timestamp if hasattr(classification, "timestamp") else None
    })


if __name__ == "__main__":
    # Test the classifier
    print("Testing Evidence Classifier...")

    # Note: This requires Gemma model to be available
    # For initial testing, use a mock implementation
    test_text = "He pushed me against the wall yesterday and threatened to hurt me if I told anyone."

    print(f"Input: {test_text}")
    print("Classifier ready for integration with Gemma 4")
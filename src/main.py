"""
SilentWitness - Main Entry Point
Orchestrates evidence documentation pipeline
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.evidence_classifier import (
    EvidenceClassifier,
    EvidenceClassification,
    AbuseType,
    Severity,
    create_classifier
)
from storage.encrypted_storage import (
    EncryptedStorage,
    EvidenceRecord,
    create_storage
)
from voice.voice_processor import (
    VoiceProcessor,
    TranscriptionResult,
    create_voice_processor
)


class SilentWitness:
    """
    Main application class orchestrating the evidence documentation pipeline.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        password: Optional[str] = None,
        gemma_model: str = "gemma3:1b",
        offline_mode: bool = True
    ):
        """
        Initialize SilentWitness application.

        Args:
            storage_path: Path for encrypted storage
            password: Password for encryption
            gemma_model: Ollama model name
            offline_mode: Force offline operation
        """
        self.storage = create_storage(db_path=storage_path, password=password)
        self.voice_processor = create_voice_processor(backend="ollama")
        self.classifier = None  # Initialized when model available
        self.gemma_model = gemma_model
        self.offline_mode = offline_mode

        print("SilentWitness initialized")
        print(f"Storage: {self.storage.db_path}")
        print(f"Offline mode: {offline_mode}")

    def document_incident(
        self,
        transcript: str,
        source: str = "voice"
    ) -> Dict:
        """
        Document an abuse incident from transcript.

        Args:
            transcript: Text transcript of incident
            source: Source type ("voice", "text", "image")

        Returns:
            Documentation result with evidence ID
        """
        print(f"\nDocumenting incident from {source}...")

        # Generate evidence ID
        evidence_id = self.storage._generate_id()

        # Process with Gemma for extraction
        gemma_result = self.voice_processor.process_with_gemma(
            transcript,
            self.gemma_model
        )

        # Classify evidence
        if gemma_result.get("success"):
            # Use Gemma classification
            classification = gemma_result.get("classification", {})
            print(f"Gemma classification: {classification.get('abuse_type', 'unknown')}")
        else:
            # Fallback: basic keyword classification
            classification = self._basic_classify(transcript)
            print(f"Warning: {gemma_result.get('error', 'Unknown error')}")
            print("Using fallback classification")

        # Create evidence record
        record = EvidenceRecord(
            id=evidence_id,
            timestamp=datetime.now().isoformat(),
            transcript=transcript,
            abuse_type=classification.get("abuse_type", "unknown"),
            severity=classification.get("severity", "medium"),
            evidence_strength=classification.get("evidence_strength", "moderate"),
            legal_relevance=classification.get("legal_relevance", "civil"),
            confidence_score=classification.get("confidence", 0.7),
            keywords=classification.get("keywords", []),
            recommendations=classification.get("recommendations", [
                "Document all incidents",
                "Seek support if needed"
            ])
        )

        # Store encrypted
        stored_id = self.storage.store_evidence(record)

        print(f"Evidence stored: {stored_id}")

        return {
            "evidence_id": stored_id,
            "classification": classification,
            "timestamp": record.timestamp,
            "success": True
        }

    def retrieve_evidence(self, evidence_id: str) -> Optional[Dict]:
        """
        Retrieve stored evidence.

        Args:
            evidence_id: Evidence ID

        Returns:
            Evidence data dict or None
        """
        record = self.storage.retrieve_evidence(evidence_id)
        if record:
            return {
                "id": record.id,
                "timestamp": record.timestamp,
                "transcript": record.transcript,
                "abuse_type": record.abuse_type,
                "severity": record.severity,
                "evidence_strength": record.evidence_strength,
                "legal_relevance": record.legal_relevance,
                "confidence_score": record.confidence_score,
                "keywords": record.keywords,
                "recommendations": record.recommendations
            }
        return None

    def export_legal_document(self, evidence_id: str) -> str:
        """
        Export evidence in legal format.

        Args:
            evidence_id: Evidence ID

        Returns:
            Legal document string
        """
        return self.storage.export_legal_format(evidence_id)

    def list_all_evidence(self) -> list:
        """
        List all stored evidence IDs.

        Returns:
            List of (id, timestamp) tuples
        """
        return self.storage.list_evidence()

    def emergency_delete_all(self) -> Dict:
        """
        Emergency deletion of all evidence.

        Returns:
            Result with count deleted
        """
        count = self.storage.emergency_delete_all()
        return {
            "deleted_count": count,
            "timestamp": datetime.now().isoformat()
        }

    def _parse_gemma_classification(self, gemma_response: str, transcript: str) -> Dict:
        """
        Parse Gemma response into classification dict.
        """
        try:
            # Try to parse as JSON
            parsed = json.loads(gemma_response)
            return {
                "abuse_type": parsed.get("abuse_type", "unknown"),
                "severity": parsed.get("severity", "medium"),
                "evidence_strength": parsed.get("evidence_strength", "moderate"),
                "legal_relevance": parsed.get("legal_relevance", "civil"),
                "confidence": parsed.get("confidence", 0.8),
                "keywords": parsed.get("keywords", []),
                "recommendations": parsed.get("recommendations", [])
            }
        except json.JSONDecodeError:
            # Fallback to basic classification
            return self._basic_classify(transcript)

    def _basic_classify(self, transcript: str) -> Dict:
        """
        Basic keyword-based classification fallback.
        """
        text_lower = transcript.lower()

        # Detect abuse type
        abuse_type = "unknown"
        if any(w in text_lower for w in ["hit", "push", "slap", "kick", "punch", "bruise", "hurt", "physical"]):
            abuse_type = "physical"
        elif any(w in text_lower for w in ["threaten", "insult", "humiliate", "control", "isolate", "manipulate"]):
            abuse_type = "emotional"
        elif any(w in text_lower for w in ["money", "steal", "debt", "financial", "account"]):
            abuse_type = "financial"
        elif any(w in text_lower for w in ["force", "touch", "assault", "harass"]):
            abuse_type = "sexual"

        # Detect severity
        severity = "medium"
        if any(w in text_lower for w in ["emergency", "danger", "afraid", "threatened", "weapon"]):
            severity = "critical"
        elif any(w in text_lower for w in ["hurt", "injured", "multiple", "repeated"]):
            severity = "high"

        # Keywords detected
        keywords = []
        keyword_lists = {
            "physical": ["hit", "push", "slap", "kick", "punch", "grab", "bruise"],
            "emotional": ["threaten", "insult", "humiliate", "control", "isolate"],
            "financial": ["money", "steal", "debt", "account", "control finances"],
            "sexual": ["force", "touch", "assault", "harass"]
        }
        for category, words in keyword_lists.items():
            for word in words:
                if word in text_lower:
                    keywords.append(word)

        # Recommendations
        recommendations = ["Document this incident", "Save evidence securely"]
        if severity in ["high", "critical"]:
            recommendations.append("Seek immediate safety")
            recommendations.append("Contact support hotline")
        if abuse_type == "physical":
            recommendations.append("Seek medical attention if injured")

        return {
            "abuse_type": abuse_type,
            "severity": severity,
            "evidence_strength": "moderate",
            "legal_relevance": "criminal" if severity in ["high", "critical"] else "civil",
            "confidence": 0.75,
            "keywords": keywords[:10],
            "recommendations": recommendations
        }

    def verify_offline(self) -> Dict:
        """
        Verify application works offline.

        Returns:
            Offline verification result
        """
        print("\nVerifying offline capability...")

        # Test storage (always offline)
        test_record = EvidenceRecord(
            id="offline_test",
            timestamp=datetime.now().isoformat(),
            transcript="Offline test transcript",
            abuse_type="emotional",
            severity="low",
            evidence_strength="moderate",
            legal_relevance="civil",
            confidence_score=0.8,
            keywords=["test"],
            recommendations=["Test recommendation"]
        )

        # Store and retrieve
        test_id = self.storage.store_evidence(test_record)
        retrieved = self.storage.retrieve_evidence(test_id)

        # Cleanup
        self.storage.delete_evidence(test_id)

        offline_works = retrieved is not None and retrieved.transcript == test_record.transcript

        return {
            "storage_offline": True,
            "retrieval_works": offline_works,
            "encryption_active": retrieved.encrypted if retrieved else False,
            "verified": offline_works
        }


def main():
    """
    Main entry point for SilentWitness.
    """
    print("=" * 60)
    print("SilentWitness - Abuse Evidence Documentation System")
    print("=" * 60)

    # Initialize
    app = SilentWitness(offline_mode=True)

    # Verify offline
    offline_result = app.verify_offline()
    print(f"\nOffline verification: {offline_result['verified']}")

    # Demo: Document test incident
    print("\n--- Demo: Documenting Test Incident ---")
    test_transcript = """
    Yesterday, March 15th, my partner pushed me against the wall in our apartment.
    He threatened to hurt me if I told anyone. I was scared and couldn't leave.
    This has happened multiple times this month.
    """

    result = app.document_incident(test_transcript, source="text")
    print(f"Evidence ID: {result['evidence_id']}")
    print(f"Classification: {result['classification']['abuse_type']}")
    print(f"Severity: {result['classification']['severity']}")

    # Export legal format
    print("\n--- Legal Export ---")
    legal_doc = app.export_legal_document(result['evidence_id'])
    print(legal_doc[:300])

    # List all evidence
    print("\n--- Stored Evidence ---")
    all_evidence = app.list_all_evidence()
    for eid, ts in all_evidence:
        print(f"ID: {eid} | Timestamp: {ts}")

    print("\n" + "=" * 60)
    print("SilentWitness ready for Gemma 4 integration")
    print("Run 'ollama serve' to enable full AI processing")
    print("=" * 60)


if __name__ == "__main__":
    main()
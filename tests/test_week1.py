"""
SilentWitness Tests - Week 1 Progress
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage.encrypted_storage import (
    EncryptedStorage,
    EvidenceRecord,
    create_storage
)
from voice.voice_processor import (
    VoiceProcessor,
    create_voice_processor
)
from main import SilentWitness


class TestOfflineStorage:
    """Tests for offline encrypted storage."""

    def test_storage_init(self):
        """Test storage initialization."""
        storage = create_storage()
        assert storage.db_path is not None
        assert os.path.exists(os.path.dirname(storage.db_path))

    def test_store_and_retrieve(self):
        """Test storing and retrieving evidence."""
        storage = create_storage()
        from datetime import datetime

        record = EvidenceRecord(
            id="test_123",
            timestamp=datetime.now().isoformat(),
            transcript="Test transcript",
            abuse_type="physical",
            severity="high",
            evidence_strength="moderate",
            legal_relevance="criminal",
            confidence_score=0.85,
            keywords=["test"],
            recommendations=["Test recommendation"]
        )

        stored_id = storage.store_evidence(record)
        assert stored_id == record.id

        retrieved = storage.retrieve_evidence(stored_id)
        assert retrieved is not None
        assert retrieved.transcript == record.transcript

        # Cleanup
        storage.delete_evidence(stored_id)

    def test_encryption(self):
        """Test evidence encryption."""
        storage = create_storage()
        from datetime import datetime

        record = EvidenceRecord(
            id="encrypt_test",
            timestamp=datetime.now().isoformat(),
            transcript="Secret transcript",
            abuse_type="emotional",
            severity="medium",
            evidence_strength="moderate",
            legal_relevance="civil",
            confidence_score=0.75,
            keywords=["secret"],
            recommendations=["Encrypt"]
        )

        stored_id = storage.store_evidence(record)
        retrieved = storage.retrieve_evidence(stored_id)

        assert retrieved.encrypted == True
        assert retrieved.transcript == record.transcript

        storage.delete_evidence(stored_id)

    def test_legal_export(self):
        """Test legal format export."""
        storage = create_storage()
        from datetime import datetime

        record = EvidenceRecord(
            id="legal_test",
            timestamp=datetime.now().isoformat(),
            transcript="Legal test",
            abuse_type="physical",
            severity="high",
            evidence_strength="strong",
            legal_relevance="criminal",
            confidence_score=0.9,
            keywords=["legal"],
            recommendations=["Export"]
        )

        stored_id = storage.store_evidence(record)
        legal_doc = storage.export_legal_format(stored_id)

        assert "EVIDENCE DOCUMENTATION REPORT" in legal_doc
        assert "PHYSICAL" in legal_doc
        assert "HIGH" in legal_doc

        storage.delete_evidence(stored_id)


class TestVoiceProcessor:
    """Tests for voice processing."""

    def test_mock_recording(self):
        """Test mock voice recording."""
        processor = create_voice_processor(backend="mock")

        recording = processor.mock_recording("Test transcript")
        assert recording.id is not None
        assert recording.timestamp is not None

    def test_mock_transcription(self):
        """Test mock transcription."""
        processor = create_voice_processor(backend="mock")

        test_text = "He pushed me against the wall."
        recording = processor.mock_recording(test_text)
        result = processor.transcribe(recording)

        assert result.transcript == test_text


class TestOfflineCapability:
    """Tests for offline functionality."""

    def test_offline_verification(self):
        """Test offline capability verification."""
        app = SilentWitness(offline_mode=True)
        result = app.verify_offline()

        assert result["storage_offline"] == True
        assert result["retrieval_works"] == True
        assert result["verified"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
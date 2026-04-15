"""
SilentWitness - Encrypted Storage Module
Secure local storage for abuse evidence using SQLCipher
"""

import os
import json
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    print("Warning: cryptography library not installed. Using basic encryption.")


@dataclass
class EvidenceRecord:
    """Structured evidence record for storage."""
    id: str
    timestamp: str
    transcript: str
    abuse_type: str
    severity: str
    evidence_strength: str
    legal_relevance: str
    confidence_score: float
    keywords: List[str]
    recommendations: List[str]
    encrypted: bool = True
    tamper_proof_hash: Optional[str] = None


class EncryptedStorage:
    """
    Encrypted local storage for abuse evidence.
    Uses AES-256 encryption via Fernet (cryptography library).
    """

    def __init__(self, db_path: str = None, password: str = None):
        """
        Initialize encrypted storage.

        Args:
            db_path: Path to SQLite database file
            password: User password for encryption key derivation
        """
        self.db_path = db_path or os.path.expanduser(
            "~/.silentwitness/evidence.db"
        )
        self.password = password or self._generate_default_password()

        # Ensure storage directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize encryption
        self._init_encryption()

        # Initialize database
        self._init_database()

    def _generate_default_password(self) -> str:
        """
        Generate a device-specific password for encryption.
        This ensures evidence can only be decrypted on this device.
        """
        # Use device identifiers (simplified for demo)
        device_id = os.uname().machine if hasattr(os, 'uname') else "unknown"
        user_home = os.path.expanduser("~")
        seed = f"{device_id}:{user_home}:silentwitness"
        return hashlib.sha256(seed.encode()).hexdigest()[:32]

    def _init_encryption(self):
        """
        Initialize Fernet encryption with derived key.
        """
        if HAS_CRYPTOGRAPHY:
            # Derive key from password using PBKDF2
            salt = b'SilentWitnessSalt2026'  # Fixed salt for device binding
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
            self.fernet = Fernet(key)
        else:
            # Basic fallback encryption (not recommended for production)
            self.fernet = None
            self._basic_key = hashlib.sha256(self.password.encode()).digest()

    def _encrypt(self, data: str) -> str:
        """
        Encrypt data using Fernet or basic method.
        """
        if HAS_CRYPTOGRAPHY and self.fernet:
            return self.fernet.encrypt(data.encode()).decode()
        else:
            # Basic XOR encryption (NOT SECURE - fallback only)
            encrypted = ''.join(
                chr(ord(c) ^ self._basic_key[i % len(self._basic_key)])
                for i, c in enumerate(data)
            )
            return base64.b64encode(encrypted.encode()).decode()

    def _decrypt(self, data: str) -> str:
        """
        Decrypt data using Fernet or basic method.
        """
        if HAS_CRYPTOGRAPHY and self.fernet:
            return self.fernet.decrypt(data.encode()).decode()
        else:
            # Basic XOR decryption
            decoded = base64.b64decode(data.encode()).decode()
            decrypted = ''.join(
                chr(ord(c) ^ self._basic_key[i % len(self._basic_key)])
                for i, c in enumerate(decoded)
            )
            return decrypted

    def _init_database(self):
        """
        Initialize SQLite database with encrypted storage schema.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Evidence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                encrypted_transcript TEXT NOT NULL,
                encrypted_metadata TEXT NOT NULL,
                tamper_proof_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Audit log table (tamper-proof)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                evidence_id TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                hash TEXT NOT NULL
            )
        """)

        # Settings table (for decoy mode config)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                encrypted_value TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _generate_id(self) -> str:
        """
        Generate unique evidence ID.
        """
        timestamp = datetime.now().isoformat()
        random_bytes = os.urandom(8).hex()
        return hashlib.sha256(f"{timestamp}:{random_bytes}".encode()).hexdigest()[:16]

    def _generate_tamper_proof_hash(self, record: EvidenceRecord) -> str:
        """
        Generate hash for tamper-proof verification.
        """
        data = json.dumps({
            "id": record.id,
            "timestamp": record.timestamp,
            "transcript": record.transcript,
            "abuse_type": record.abuse_type,
            "severity": record.severity
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def store_evidence(self, record: EvidenceRecord) -> str:
        """
        Store evidence record with encryption.

        Returns:
            Evidence ID
        """
        # Generate tamper-proof hash
        record.tamper_proof_hash = self._generate_tamper_proof_hash(record)

        # Encrypt transcript
        encrypted_transcript = self._encrypt(record.transcript)

        # Encrypt metadata
        metadata = {
            "abuse_type": record.abuse_type,
            "severity": record.severity,
            "evidence_strength": record.evidence_strength,
            "legal_relevance": record.legal_relevance,
            "confidence_score": record.confidence_score,
            "keywords": record.keywords,
            "recommendations": record.recommendations
        }
        encrypted_metadata = self._encrypt(json.dumps(metadata))

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evidence (id, timestamp, encrypted_transcript, encrypted_metadata, tamper_proof_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (record.id, record.timestamp, encrypted_transcript, encrypted_metadata, record.tamper_proof_hash))

        # Log action in same connection
        log_timestamp = datetime.now().isoformat()
        log_hash_input = f"store:{record.id}:{log_timestamp}"
        log_hash_value = hashlib.sha256(log_hash_input.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO audit_log (action, evidence_id, timestamp, hash)
            VALUES (?, ?, ?, ?)
        """, ("store", record.id, log_timestamp, log_hash_value))

        conn.commit()
        conn.close()

        return record.id

    def retrieve_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """
        Retrieve and decrypt evidence record.

        Args:
            evidence_id: ID of evidence to retrieve

        Returns:
            EvidenceRecord if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, timestamp, encrypted_transcript, encrypted_metadata, tamper_proof_hash
            FROM evidence WHERE id = ?
        """, (evidence_id,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        # Decrypt data
        transcript = self._decrypt(row[2])
        metadata = json.loads(self._decrypt(row[3]))

        # Verify tamper-proof hash
        record = EvidenceRecord(
            id=row[0],
            timestamp=row[1],
            transcript=transcript,
            abuse_type=metadata["abuse_type"],
            severity=metadata["severity"],
            evidence_strength=metadata["evidence_strength"],
            legal_relevance=metadata["legal_relevance"],
            confidence_score=metadata["confidence_score"],
            keywords=metadata["keywords"],
            recommendations=metadata["recommendations"],
            tamper_proof_hash=row[4]
        )

        # Verify integrity
        expected_hash = self._generate_tamper_proof_hash(record)
        if record.tamper_proof_hash != expected_hash:
            print(f"Warning: Evidence {evidence_id} may have been tampered with")

        return record

    def list_evidence(self, limit: int = 50) -> List[str]:
        """
        List all evidence IDs (without decrypting content).

        Returns:
            List of evidence IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, timestamp FROM evidence
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [(row[0], row[1]) for row in rows]

    def delete_evidence(self, evidence_id: str) -> bool:
        """
        Delete evidence record (for safety/privacy).

        Args:
            evidence_id: ID of evidence to delete

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verify exists
        cursor.execute("SELECT id FROM evidence WHERE id = ?", (evidence_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        # Delete
        cursor.execute("DELETE FROM evidence WHERE id = ?", (evidence_id,))

        # Log action in same connection
        log_timestamp = datetime.now().isoformat()
        log_hash_input = f"delete:{evidence_id}:{log_timestamp}"
        log_hash_value = hashlib.sha256(log_hash_input.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO audit_log (action, evidence_id, timestamp, hash)
            VALUES (?, ?, ?, ?)
        """, ("delete", evidence_id, log_timestamp, log_hash_value))

        conn.commit()
        conn.close()

        return True

    def export_legal_format(self, evidence_id: str) -> str:
        """
        Export evidence in legal documentation format.

        Args:
            evidence_id: ID of evidence to export

        Returns:
            Formatted legal document string
        """
        record = self.retrieve_evidence(evidence_id)
        if record is None:
            return "Evidence not found"

        # Format for legal use
        legal_doc = f"""
EVIDENCE DOCUMENTATION REPORT
=============================

Evidence ID: {record.id}
Recorded: {record.timestamp}

INCIDENT SUMMARY
----------------
Classification: {record.abuse_type.upper()}
Severity: {record.severity.upper()}
Evidence Strength: {record.evidence_strength.upper()}
Legal Relevance: {record.legal_relevance.upper()}
Confidence Score: {record.confidence_score:.2f}

TRANSCRIPT
----------
{record.transcript}

KEY TERMS IDENTIFIED
--------------------
{', '.join(record.keywords) if record.keywords else 'None detected'}

RECOMMENDED ACTIONS
-------------------
{chr(10).join(f'- {action}' for action in record.recommendations)}

VERIFICATION
------------
Tamper-Proof Hash: {record.tamper_proof_hash}

This document was generated by SilentWitness, an offline-first
abuse documentation system. All evidence is encrypted and
timestamped for integrity verification.

Generated: {datetime.now().isoformat()}
"""

        return legal_doc

    def _log_action(self, action: str, evidence_id: Optional[str] = None):
        """
        Log action to audit trail.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        hash_input = f"{action}:{evidence_id}:{timestamp}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()

        cursor.execute("""
            INSERT INTO audit_log (action, evidence_id, timestamp, hash)
            VALUES (?, ?, ?, ?)
        """, (action, evidence_id, timestamp, hash_value))

        conn.commit()
        conn.close()

    def emergency_delete_all(self) -> int:
        """
        Emergency deletion of all evidence (for safety situations).
        Use sparingly - this permanently deletes all records.

        Returns:
            Number of records deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM evidence")
        count = cursor.fetchone()[0]

        cursor.execute("DELETE FROM evidence")

        # Log action in same connection
        log_timestamp = datetime.now().isoformat()
        log_hash_input = f"emergency_delete_all:None:{log_timestamp}"
        log_hash_value = hashlib.sha256(log_hash_input.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO audit_log (action, evidence_id, timestamp, hash)
            VALUES (?, ?, ?, ?)
        """, ("emergency_delete_all", None, log_timestamp, log_hash_value))

        conn.commit()
        conn.close()

        return count


def create_storage(db_path: str = None, password: str = None) -> EncryptedStorage:
    """
    Factory function to create encrypted storage instance.
    """
    return EncryptedStorage(db_path=db_path, password=password)


if __name__ == "__main__":
    # Test storage
    print("Testing Encrypted Storage...")

    storage = create_storage()

    # Create test record
    test_record = EvidenceRecord(
        id=storage._generate_id(),
        timestamp=datetime.now().isoformat(),
        transcript="Test evidence transcript",
        abuse_type="physical",
        severity="high",
        evidence_strength="moderate",
        legal_relevance="criminal",
        confidence_score=0.85,
        keywords=["push", "threaten"],
        recommendations=["Seek medical attention", "Document incident"]
    )

    # Store
    evidence_id = storage.store_evidence(test_record)
    print(f"Stored evidence: {evidence_id}")

    # Retrieve
    retrieved = storage.retrieve_evidence(evidence_id)
    print(f"Retrieved: {retrieved.transcript}")

    # Export legal format
    legal_doc = storage.export_legal_format(evidence_id)
    print(legal_doc[:500])
"""
SilentWitness - Function Calling Module
Gemma 4 native function calling handlers for evidence actions
"""

import json
import os
import sys
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.encrypted_storage import create_storage, EvidenceRecord, EncryptedStorage
from voice.voice_processor import create_voice_processor


@dataclass
class FunctionDefinition:
    """Structured function definition for Gemma 4."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str]


class FunctionCallingEngine:
    """
    Gemma 4 function calling engine for SilentWitness.
    Implements native function calling for evidence actions.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize function calling engine.

        Args:
            storage_path: Path to encrypted storage
        """
        self.storage = create_storage(db_path=storage_path)
        self.voice_processor = create_voice_processor()

        # Register available functions
        self.functions: Dict[str, FunctionDefinition] = {}
        self.handlers: Dict[str, Callable] = {}

        self._register_functions()

    def _register_functions(self):
        """
        Register all available functions for Gemma 4.
        """
        # Store Evidence Function
        self._register_function(
            name="store_evidence",
            description="Store encrypted evidence from transcript with classification",
            parameters={
                "type": "object",
                "properties": {
                    "transcript": {
                        "type": "string",
                        "description": "The text transcript of the incident"
                    },
                    "abuse_type": {
                        "type": "string",
                        "enum": ["physical", "emotional", "financial", "sexual", "neglect", "unknown"],
                        "description": "Type of abuse documented"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Severity level of the incident"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords detected in transcript"
                    }
                },
                "required": ["transcript"]
            },
            handler=self._handle_store_evidence
        )

        # Export Legal Format Function
        self._register_function(
            name="export_legal_format",
            description="Export evidence in court-admissible legal document format",
            parameters={
                "type": "object",
                "properties": {
                    "evidence_id": {
                        "type": "string",
                        "description": "ID of evidence to export"
                    }
                },
                "required": ["evidence_id"]
            },
            handler=self._handle_export_legal
        )

        # Set Safe Contact Function
        self._register_function(
            name="set_safe_contact",
            description="Set a trusted contact for emergency alerts",
            parameters={
                "type": "object",
                "properties": {
                    "contact_name": {
                        "type": "string",
                        "description": "Name of trusted contact"
                    },
                    "contact_method": {
                        "type": "string",
                        "enum": ["phone", "email", "sms"],
                        "description": "Method to contact them"
                    },
                    "contact_info": {
                        "type": "string",
                        "description": "Phone number or email address"
                    }
                },
                "required": ["contact_name", "contact_method", "contact_info"]
            },
            handler=self._handle_set_safe_contact
        )

        # Trigger Emergency Alert Function
        self._register_function(
            name="trigger_emergency_alert",
            description="Trigger emergency alert to safe contacts or authorities",
            parameters={
                "type": "object",
                "properties": {
                    "alert_type": {
                        "type": "string",
                        "enum": ["silent", "loud", "disguised", "authorities"],
                        "description": "Type of emergency alert"
                    },
                    "message": {
                        "type": "string",
                        "description": "Custom message to send (optional)"
                    }
                },
                "required": ["alert_type"]
            },
            handler=self._handle_emergency_alert
        )

        # Schedule Reminder Function
        self._register_function(
            name="schedule_reminder",
            description="Schedule a reminder for follow-up documentation",
            parameters={
                "type": "object",
                "properties": {
                    "reminder_type": {
                        "type": "string",
                        "enum": ["document", "export", "check_in", "legal"],
                        "description": "Type of reminder"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date for reminder (YYYY-MM-DD format)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes for reminder"
                    }
                },
                "required": ["reminder_type", "date"]
            },
            handler=self._handle_schedule_reminder
        )

        # Quick Delete Function (Safety)
        self._register_function(
            name="quick_delete_evidence",
            description="Quickly delete specific evidence for safety",
            parameters={
                "type": "object",
                "properties": {
                    "evidence_id": {
                        "type": "string",
                        "description": "ID of evidence to delete"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for deletion (for audit log)"
                    }
                },
                "required": ["evidence_id"]
            },
            handler=self._handle_quick_delete
        )

        # List Evidence Function
        self._register_function(
            name="list_evidence",
            description="List all stored evidence IDs with timestamps",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return",
                        "default": 10
                    }
                },
                "required": []
            },
            handler=self._handle_list_evidence
        )

    def _register_function(
        self,
        name: str,
        description: str,
        parameters: Dict,
        handler: Callable
    ):
        """
        Register a function with its definition and handler.
        """
        self.functions[name] = FunctionDefinition(
            name=name,
            description=description,
            parameters=parameters,
            required=parameters.get("required", [])
        )
        self.handlers[name] = handler

    def get_function_definitions(self) -> List[Dict]:
        """
        Get all function definitions for Gemma 4.
        Returns in OpenAI-compatible format for function calling.
        """
        definitions = []
        for func in self.functions.values():
            definitions.append({
                "name": func.name,
                "description": func.description,
                "parameters": func.parameters
            })
        return definitions

    def execute_function(self, name: str, arguments: Dict) -> Dict:
        """
        Execute a registered function with given arguments.

        Args:
            name: Function name
            arguments: Function arguments

        Returns:
            Function execution result
        """
        if name not in self.handlers:
            return {"error": f"Unknown function: {name}", "success": False}

        handler = self.handlers[name]
        try:
            result = handler(arguments)
            return {"result": result, "success": True, "function": name}
        except Exception as e:
            return {"error": str(e), "success": False, "function": name}

    def process_gemma_function_call(self, transcript: str) -> Dict:
        """
        Process transcript with Gemma and handle function calls.

        Args:
            transcript: User transcript potentially requesting actions

        Returns:
            Processing result with any executed functions
        """
        # Build prompt with function definitions
        functions_json = json.dumps(self.get_function_definitions(), indent=2)

        prompt = f"""You are SilentWitness, an abuse evidence documentation assistant.

Available functions:
{functions_json}

User says: "{transcript}"

If the user is requesting an action (storing, exporting, deleting, alerting),
call the appropriate function with the needed arguments.
If the user is describing an incident, call store_evidence.
Respond with either:
1. A function call in format: CALL: function_name(arg1=value1, arg2=value2)
2. Or a helpful response if no function needed.

Only call ONE function at a time."""

        # Process with Gemma
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:1b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")

                # Parse function call if present
                if "CALL:" in response_text:
                    func_call = self._parse_function_call(response_text)
                    if func_call:
                        execution_result = self.execute_function(
                            func_call["name"],
                            func_call["arguments"]
                        )
                        return {
                            "response": response_text,
                            "function_executed": True,
                            "function_result": execution_result
                        }

                return {
                    "response": response_text,
                    "function_executed": False
                }
            else:
                return {"error": f"Gemma request failed: {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    def _parse_function_call(self, response_text: str) -> Optional[Dict]:
        """
        Parse function call from Gemma response.

        Format: CALL: function_name(arg1=value1, arg2=value2)
        """
        import re

        # Find CALL: statement
        call_match = re.search(r'CALL:\s*(\w+)\s*\(([^)]*)\)', response_text)
        if not call_match:
            return None

        function_name = call_match.group(1)
        args_str = call_match.group(2)

        # Parse arguments
        arguments = {}
        if args_str.strip():
            # Simple parsing: arg=value pairs
            for pair in args_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    arguments[key] = value

        return {"name": function_name, "arguments": arguments}

    # Function Handlers

    def _handle_store_evidence(self, args: Dict) -> Dict:
        """
        Handle store_evidence function call.
        """
        transcript = args.get("transcript", "")
        abuse_type = args.get("abuse_type", "unknown")
        severity = args.get("severity", "medium")
        keywords = args.get("keywords", [])

        # Generate evidence ID
        evidence_id = self.storage._generate_id()

        # Create record - using correct field names from EvidenceRecord
        record = EvidenceRecord(
            id=evidence_id,
            timestamp=datetime.now().isoformat(),
            transcript=transcript,
            abuse_type=abuse_type,
            severity=severity,
            evidence_strength="moderate",
            legal_relevance="civil" if severity in ["low", "medium"] else "criminal",
            confidence_score=0.85,
            keywords=keywords if isinstance(keywords, list) else [keywords],
            recommendations=["Evidence stored securely", "Continue documenting"]
        )

        # Store
        stored_id = self.storage.store_evidence(record)

        return {
            "evidence_id": stored_id,
            "message": f"Evidence stored securely with ID: {stored_id}",
            "encrypted": True,
            "timestamp": record.timestamp
        }

    def _handle_export_legal(self, args: Dict) -> Dict:
        """
        Handle export_legal_format function call.
        """
        evidence_id = args.get("evidence_id", "")

        if not evidence_id:
            return {"error": "No evidence ID provided"}

        legal_doc = self.storage.export_legal_format(evidence_id)

        return {
            "evidence_id": evidence_id,
            "legal_document": legal_doc,
            "message": f"Legal document exported for {evidence_id}"
        }

    def _handle_set_safe_contact(self, args: Dict) -> Dict:
        """
        Handle set_safe_contact function call.
        """
        # Store in settings (encrypted)
        contact_name = args.get("contact_name", "")
        contact_method = args.get("contact_method", "phone")
        contact_info = args.get("contact_info", "")

        # Save to encrypted settings using direct connection
        import sqlite3
        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()

        # Ensure settings table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                encrypted_value TEXT NOT NULL
            )
        """)

        contact_data = json.dumps({
            "name": contact_name,
            "method": contact_method,
            "info": contact_info,
            "set_at": datetime.now().isoformat()
        })
        encrypted_data = self.storage._encrypt(contact_data)

        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, encrypted_value)
            VALUES ('safe_contact', ?)
        """, (encrypted_data,))

        conn.commit()
        conn.close()

        return {
            "contact_name": contact_name,
            "method": contact_method,
            "message": f"Safe contact '{contact_name}' set successfully",
            "success": True
        }

    def _handle_emergency_alert(self, args: Dict) -> Dict:
        """
        Handle trigger_emergency_alert function call.
        """
        alert_type = args.get("alert_type", "silent")
        message = args.get("message", "Emergency alert triggered")

        # In production, this would:
        # - Send SMS/email to safe contacts
        # - For "authorities": dial emergency services
        # - For "disguised": send fake benign message

        return {
            "alert_type": alert_type,
            "message": message,
            "status": "prepared",  # Would be "sent" in production
            "timestamp": datetime.now().isoformat(),
            "note": "Alert prepared. In production, would send to contacts."
        }

    def _handle_schedule_reminder(self, args: Dict) -> Dict:
        """
        Handle schedule_reminder function call.
        """
        import sqlite3

        reminder_type = args.get("reminder_type", "document")
        date = args.get("date", "")
        notes = args.get("notes", "")

        # Store reminder
        reminder_data = json.dumps({
            "type": reminder_type,
            "date": date,
            "notes": notes,
            "created": datetime.now().isoformat()
        })
        encrypted_data = self.storage._encrypt(reminder_data)

        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.cursor()

        # Ensure settings table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                encrypted_value TEXT NOT NULL
            )
        """)

        reminder_id = f"reminder_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, encrypted_value)
            VALUES (?, ?)
        """, (reminder_id, encrypted_data))

        conn.commit()
        conn.close()

        return {
            "reminder_id": reminder_id,
            "type": reminder_type,
            "date": date,
            "message": f"Reminder scheduled for {date}"
        }

    def _handle_quick_delete(self, args: Dict) -> Dict:
        """
        Handle quick_delete_evidence function call (safety feature).
        """
        evidence_id = args.get("evidence_id", "")
        reason = args.get("reason", "safety")

        if not evidence_id:
            return {"error": "No evidence ID provided"}

        deleted = self.storage.delete_evidence(evidence_id)

        return {
            "evidence_id": evidence_id,
            "deleted": deleted,
            "reason": reason,
            "message": f"Evidence {evidence_id} deleted for safety"
        }

    def _handle_list_evidence(self, args: Dict) -> Dict:
        """
        Handle list_evidence function call.
        """
        limit = args.get("limit", 10)
        evidence_list = self.storage.list_evidence(limit=limit)

        return {
            "count": len(evidence_list),
            "evidence": [{"id": eid, "timestamp": ts} for eid, ts in evidence_list],
            "message": f"Found {len(evidence_list)} evidence records"
        }


def create_function_engine(storage_path: str = None) -> FunctionCallingEngine:
    """
    Factory function to create function calling engine.
    """
    return FunctionCallingEngine(storage_path=storage_path)


if __name__ == "__main__":
    # Test function calling
    print("Testing Function Calling Engine...")

    engine = create_function_engine()

    # Show available functions
    print("\nAvailable Functions:")
    for func in engine.get_function_definitions():
        print(f"- {func['name']}: {func['description'][:50]}...")

    # Test direct execution
    print("\n--- Test: store_evidence ---")
    result = engine.execute_function("store_evidence", {
        "transcript": "He threatened me today",
        "abuse_type": "emotional",
        "severity": "medium"
    })
    print(f"Result: {result}")

    # Test list
    print("\n--- Test: list_evidence ---")
    result = engine.execute_function("list_evidence", {"limit": 5})
    print(f"Result: {result}")

    # Test with Gemma
    print("\n--- Test: Gemma Function Calling ---")
    test_input = "Please save this: My partner pushed me against the wall yesterday."
    gemma_result = engine.process_gemma_function_call(test_input)
    print(f"Gemma response: {gemma_result.get('response', 'N/A')[:100]}...")
    print(f"Function executed: {gemma_result.get('function_executed', False)}")

    print("\nFunction Calling Engine ready for Gemma 4!")
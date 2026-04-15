"""
SilentWitness - Voice Processing Module
Voice-to-text processing for evidence documentation
"""

import os
import wave
import json
import base64
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import tempfile

# Voice recording (using standard library + optional whisper)
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

# Alternative: Use Ollama for transcription
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class VoiceRecording:
    """Voice recording metadata and data."""
    id: str
    timestamp: str
    audio_data: bytes
    duration_seconds: float
    format: str = "wav"
    sample_rate: int = 16000


@dataclass
class TranscriptionResult:
    """Result of voice transcription."""
    transcript: str
    confidence: float
    language: str
    duration_seconds: float
    timestamp: str
    segments: list  # Word-level timestamps if available


class VoiceProcessor:
    """
    Voice processing for evidence documentation.
    Supports multiple backends: Whisper, Ollama, or basic recording.
    """

    def __init__(self, backend: str = "ollama", model: str = "gemma3:1b"):
        """
        Initialize voice processor.

        Args:
            backend: Transcription backend ("whisper", "ollama", "mock")
            model: Model name for backend
        """
        self.backend = backend
        self.model = model

        # Initialize backend
        if backend == "whisper" and HAS_WHISPER:
            self.whisper_model = whisper.load_model("base")
        else:
            self.whisper_model = None

        # Ollama endpoint
        self.ollama_url = "http://localhost:11434"

    def record_voice(
        self,
        duration: float = 30.0,
        sample_rate: int = 16000,
        output_path: Optional[str] = None
    ) -> VoiceRecording:
        """
        Record voice audio from microphone.

        Note: This requires microphone access.
        For testing without hardware, use mock_recording().

        Args:
            duration: Recording duration in seconds
            sample_rate: Audio sample rate
            output_path: Optional path to save audio file

        Returns:
            VoiceRecording object
        """
        # Generate recording ID
        recording_id = self._generate_id()

        # For actual recording, would use pyaudio or similar
        # This is a placeholder implementation
        print(f"Recording voice for {duration} seconds...")
        print("Note: Actual recording requires microphone hardware")

        # Mock recording data
        audio_data = self._mock_audio_data(duration, sample_rate)

        recording = VoiceRecording(
            id=recording_id,
            timestamp=datetime.now().isoformat(),
            audio_data=audio_data,
            duration_seconds=duration,
            format="wav",
            sample_rate=sample_rate
        )

        # Save to file if path provided
        if output_path:
            self._save_audio_file(recording, output_path)

        return recording

    def mock_recording(self, transcript_text: str) -> VoiceRecording:
        """
        Create mock recording for testing without microphone.

        Args:
            transcript_text: Simulated transcript content

        Returns:
            VoiceRecording with embedded metadata
        """
        recording_id = self._generate_id()

        # Encode transcript as "audio data" for testing
        audio_data = base64.b64encode(transcript_text.encode())

        return VoiceRecording(
            id=recording_id,
            timestamp=datetime.now().isoformat(),
            audio_data=audio_data,
            duration_seconds=len(transcript_text) / 10,  # Approximate
            format="mock",
            sample_rate=0
        )

    def transcribe(self, recording: VoiceRecording) -> TranscriptionResult:
        """
        Transcribe voice recording to text.

        Args:
            recording: VoiceRecording object

        Returns:
            TranscriptionResult
        """
        if self.backend == "whisper" and self.whisper_model:
            return self._transcribe_whisper(recording)
        elif self.backend == "ollama":
            return self._transcribe_ollama(recording)
        else:
            return self._transcribe_mock(recording)

    def _transcribe_whisper(self, recording: VoiceRecording) -> TranscriptionResult:
        """
        Transcribe using Whisper model.
        """
        # Save to temp file for Whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(recording.audio_data)
            tmp_path = tmp.name

        # Transcribe
        result = self.whisper_model.transcribe(tmp_path)

        # Cleanup
        os.unlink(tmp_path)

        return TranscriptionResult(
            transcript=result["text"],
            confidence=result.get("confidence", 0.9),
            language=result.get("language", "en"),
            duration_seconds=recording.duration_seconds,
            timestamp=datetime.now().isoformat(),
            segments=result.get("segments", [])
        )

    def _transcribe_ollama(self, recording: VoiceRecording) -> TranscriptionResult:
        """
        Transcribe using Ollama/Gemma.
        Note: Gemma doesn't directly transcribe audio, but can process text.
        This is for integration with Gemma 4's capabilities.
        """
        # For actual audio transcription, would need separate STT model
        # Gemma processes the text output

        # Mock transcription for now
        if recording.format == "mock":
            transcript = base64.b64decode(recording.audio_data).decode()
        else:
            transcript = "Audio transcription requires Whisper integration"

        return TranscriptionResult(
            transcript=transcript,
            confidence=0.85,
            language="en",
            duration_seconds=recording.duration_seconds,
            timestamp=datetime.now().isoformat(),
            segments=[]
        )

    def _transcribe_mock(self, recording: VoiceRecording) -> TranscriptionResult:
        """
        Mock transcription for testing.
        """
        if recording.format == "mock":
            transcript = base64.b64decode(recording.audio_data).decode()
        else:
            transcript = "Mock transcription result"

        return TranscriptionResult(
            transcript=transcript,
            confidence=0.9,
            language="en",
            duration_seconds=recording.duration_seconds,
            timestamp=datetime.now().isoformat(),
            segments=[]
        )

    def process_with_gemma(
        self,
        transcript: str,
        ollama_model: str = "gemma3:1b"
    ) -> Dict:
        """
        Process transcript with Gemma 4 for evidence extraction.

        Args:
            transcript: Text transcript
            ollama_model: Ollama model name

        Returns:
            Structured evidence data
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}

        # Evidence extraction prompt - requesting structured analysis
        prompt = f"""Analyze this abuse incident transcript and provide a brief classification.

Transcript: "{transcript}"

Answer these questions briefly:
1. Type: physical, emotional, financial, sexual, or unknown
2. Severity: low, medium, high, or critical
3. Keywords found (list 2-5)

Format your answer as:
Type: [type]
Severity: [severity]
Keywords: [keywords]"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")

                # Parse response for classification
                classification = self._parse_gemma_response(response_text)

                return {
                    "response": response_text,
                    "classification": classification,
                    "model": ollama_model,
                    "total_duration": result.get("total_duration", 0),
                    "success": True
                }
            else:
                return {"error": f"Ollama request failed: {response.status_code}", "success": False}

        except requests.exceptions.ConnectionError:
            return {"error": "Ollama not running. Start with: ollama serve", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _parse_gemma_response(self, response_text: str) -> Dict:
        """
        Parse Gemma's text response into classification dict.
        """
        text_lower = response_text.lower()

        # Extract type
        abuse_type = "unknown"
        for type_name in ["physical", "emotional", "financial", "sexual"]:
            if type_name in text_lower:
                abuse_type = type_name
                break

        # Extract severity
        severity = "medium"
        for sev_name in ["critical", "high", "medium", "low"]:
            if sev_name in text_lower:
                severity = sev_name
                break

        # Simple keyword extraction from response
        keywords = []
        keyword_pool = ["push", "threaten", "hit", "control", "isolate", "insult", "hurt", "force", "grab", "slap"]
        for kw in keyword_pool:
            if kw in text_lower:
                keywords.append(kw)

        return {
            "abuse_type": abuse_type,
            "severity": severity,
            "keywords": keywords[:5],
            "confidence": 0.85 if abuse_type != "unknown" else 0.5
        }

    def _generate_id(self) -> str:
        """
        Generate unique recording ID.
        """
        timestamp = datetime.now().isoformat()
        random_bytes = os.urandom(4).hex()
        import hashlib
        return hashlib.md5(f"{timestamp}:{random_bytes}".encode()).hexdigest()[:12]

    def _mock_audio_data(self, duration: float, sample_rate: int) -> bytes:
        """
        Generate mock audio data for testing.
        """
        # Simple WAV header + silence
        num_samples = int(duration * sample_rate)
        return b'\x00' * num_samples * 2  # 16-bit samples

    def _save_audio_file(self, recording: VoiceRecording, path: str):
        """
        Save audio recording to file.
        """
        with wave.open(path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(recording.sample_rate)
            wav_file.writeframes(recording.audio_data)


def create_voice_processor(backend: str = "ollama") -> VoiceProcessor:
    """
    Factory function to create voice processor.
    """
    return VoiceProcessor(backend=backend)


if __name__ == "__main__":
    # Test voice processor
    print("Testing Voice Processor...")

    processor = create_voice_processor(backend="mock")

    # Create mock recording
    test_text = "He pushed me against the wall yesterday and threatened to hurt me."
    recording = processor.mock_recording(test_text)

    print(f"Recording ID: {recording.id}")
    print(f"Timestamp: {recording.timestamp}")

    # Transcribe
    result = processor.transcribe(recording)
    print(f"Transcript: {result.transcript}")

    # Process with Gemma (requires Ollama running)
    if HAS_REQUESTS:
        print("\nProcessing with Gemma...")
        evidence = processor.process_with_gemma(result.transcript)
        print(json.dumps(evidence, indent=2))
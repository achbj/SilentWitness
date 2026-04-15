"""
SilentWitness - Severity Analyzer Module
ML-based severity detection for abuse evidence
"""

import re
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SeverityAnalysis:
    """Severity analysis result."""
    severity: str  # low, medium, high, critical
    confidence: float
    indicators: List[str]
    emotional_intensity: str  # calm, distressed, panicked, traumatized
    urgency: str  # none, low, medium, high, critical
    recommended_response: str


class SeverityAnalyzer:
    """
    ML-based severity analyzer for abuse evidence.
    Uses linguistic markers, emotional indicators, and context cues.
    """

    def __init__(self):
        """
        Initialize severity analyzer with indicator patterns.
        """
        # Severity indicators - organized by level
        self.indicators = {
            "critical": {
                "physical": [
                    "weapon", "gun", "knife", "strangled", "choked",
                    "unconscious", "bleeding", "hospital", "emergency",
                    "life-threatening", "almost died", "could have died"
                ],
                "emotional": [
                    "will kill", "going to kill", "threatened to kill",
                    "kill you", "kill myself", "suicide",
                    "no escape", "trapped", "can't leave", "held captive"
                ],
                "contextual": [
                    "multiple times", "years", "daily", "every day",
                    " escalating", "getting worse", "more violent"
                ]
            },
            "high": {
                "physical": [
                    "pushed", "slapped", "hit", "kicked", "punched",
                    "grabbed", "thrown", "against wall", "bruise",
                    "injured", "hurt", "pain", "blood"
                ],
                "emotional": [
                    "threatened", "scared", "afraid", "terrified",
                    "forced", "coerced", "manipulated", "controlled",
                    "isolated", "no money", "no access"
                ],
                "contextual": [
                    "children present", "in front of kids", "public",
                    "at work", "repeatedly", "often", "pattern"
                ]
            },
            "medium": {
                "physical": [
                    "grabbed arm", "held tight", "blocked", "cornered",
                    "followed", "watched", "stood over"
                ],
                "emotional": [
                    "insulted", "humiliated", "called names", "yelled",
                    "screamed", "criticized", "blamed", "gaslighting"
                ],
                "contextual": [
                    "argument", "disagreement", "tension",
                    "stressful", "difficult"
                ]
            },
            "low": {
                "physical": [
                    "stood close", "raised voice", "angry look",
                    "threatening gesture"
                ],
                "emotional": [
                    "dismissive", "ignored", "冷漠", "冷落",
                    "rolled eyes", "sighed", "annoyed"
                ],
                "contextual": [
                    "rarely", "once", "first time", "minor"
                ]
            }
        }

        # Emotional intensity markers
        self.emotional_markers = {
            "traumatized": ["can't sleep", "flashbacks", "nightmares", "panic", "ptsd"],
            "panicked": ["terrified", "frozen", "can't move", "heart racing", "shaking"],
            "distressed": ["scared", "anxious", "worried", "nervous", "upset"],
            "calm": ["documenting", "recording", "matter of fact", "objective"]
        }

        # Urgency markers
        self.urgency_markers = {
            "critical": ["right now", "happening now", "currently", "immediate danger"],
            "high": ["today", "yesterday", "this week", "recently", "just happened"],
            "medium": ["last week", "last month", "few weeks ago"],
            "low": ["months ago", "last year", "in the past", "historical"]
        }

    def analyze(self, transcript: str, context: Dict = None) -> SeverityAnalysis:
        """
        Analyze transcript for severity indicators.

        Args:
            transcript: Text transcript of incident
            context: Optional context (previous incidents, user state)

        Returns:
            SeverityAnalysis result
        """
        text_lower = transcript.lower()

        # Detect severity level
        severity, indicators_found = self._detect_severity(text_lower)

        # Detect emotional intensity
        emotional_intensity = self._detect_emotional_intensity(text_lower)

        # Detect urgency
        urgency = self._detect_urgency(text_lower)

        # Calculate confidence
        confidence = self._calculate_confidence(
            severity, indicators_found, emotional_intensity, urgency
        )

        # Generate recommended response
        recommended_response = self._generate_response(
            severity, urgency, emotional_intensity
        )

        return SeverityAnalysis(
            severity=severity,
            confidence=confidence,
            indicators=indicators_found,
            emotional_intensity=emotional_intensity,
            urgency=urgency,
            recommended_response=recommended_response
        )

    def _detect_severity(self, text: str) -> Tuple[str, List[str]]:
        """
        Detect severity level from text.
        Returns severity level and indicators found.
        """
        all_indicators = []

        # Check each severity level (descending order)
        for level in ["critical", "high", "medium", "low"]:
            level_indicators = []
            for category, keywords in self.indicators[level].items():
                for keyword in keywords:
                    if keyword in text:
                        level_indicators.append(keyword)

            if level_indicators:
                all_indicators.extend(level_indicators)
                # Return highest severity found
                return level, all_indicators

        # Default to medium if no clear indicators
        return "medium", ["unspecified indicators"]

    def _detect_emotional_intensity(self, text: str) -> str:
        """
        Detect emotional intensity from text.
        """
        for intensity, markers in self.emotional_markers.items():
            for marker in markers:
                if marker in text:
                    return intensity

        return "distressed"  # Default for abuse documentation

    def _detect_urgency(self, text: str) -> str:
        """
        Detect urgency from time markers.
        """
        for urgency_level, markers in self.urgency_markers.items():
            for marker in markers:
                if marker in text:
                    return urgency_level

        return "medium"  # Default - documenting past event

    def _calculate_confidence(
        self,
        severity: str,
        indicators: List[str],
        emotional_intensity: str,
        urgency: str
    ) -> float:
        """
        Calculate confidence score for severity classification.
        """
        base_confidence = 0.6

        # More indicators = higher confidence
        indicator_boost = min(len(indicators) * 0.05, 0.2)

        # Intensity alignment
        intensity_boost = {
            "traumatized": 0.15,
            "panicked": 0.12,
            "distressed": 0.08,
            "calm": 0.0
        }.get(emotional_intensity, 0.05)

        # Urgency alignment
        urgency_boost = {
            "critical": 0.15,
            "high": 0.10,
            "medium": 0.05,
            "low": 0.0
        }.get(urgency, 0.05)

        # Severity-weighted confidence
        severity_weight = {
            "critical": 0.1,
            "high": 0.08,
            "medium": 0.05,
            "low": 0.02
        }.get(severity, 0.05)

        total_confidence = min(
            base_confidence + indicator_boost + intensity_boost + urgency_boost + severity_weight,
            0.95
        )

        return round(total_confidence, 2)

    def _generate_response(
        self,
        severity: str,
        urgency: str,
        emotional_intensity: str
    ) -> str:
        """
        Generate recommended response based on analysis.
        """
        if severity == "critical" or urgency == "critical":
            return "Immediate safety required. Contact emergency services or support hotline immediately."

        if severity == "high":
            return "Serious incident documented. Consider seeking professional support and safe housing options."

        if severity == "medium" and emotional_intensity in ["panicked", "traumatized"]:
            return "Evidence recorded. Emotional support recommended. Continue documenting pattern."

        if severity == "medium":
            return "Incident documented. This evidence may be important for future action."

        return "Evidence recorded. Continue monitoring and documenting."

    def analyze_with_gemma(self, transcript: str) -> Dict:
        """
        Enhanced analysis using Gemma for deeper understanding.
        """
        # First do local analysis
        local_analysis = self.analyze(transcript)

        # Then enhance with Gemma
        try:
            import requests

            prompt = f"""Analyze this abuse incident transcript for severity assessment:

Transcript: "{transcript}"

Provide:
1. Severity level (critical/high/medium/low)
2. Key risk indicators detected
3. Emotional state assessment
4. Recommended immediate action

Keep response brief and actionable."""

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:1b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                gemma_response = response.json().get("response", "")
                return {
                    "local_analysis": {
                        "severity": local_analysis.severity,
                        "confidence": local_analysis.confidence,
                        "indicators": local_analysis.indicators,
                        "emotional_intensity": local_analysis.emotional_intensity,
                        "urgency": local_analysis.urgency
                    },
                    "gemma_enhanced": gemma_response,
                    "recommended_response": local_analysis.recommended_response
                }
            else:
                return {
                    "local_analysis": local_analysis.__dict__,
                    "gemma_enhanced": "Gemma unavailable",
                    "error": f"Status: {response.status_code}"
                }

        except Exception as e:
            return {
                "local_analysis": local_analysis.__dict__,
                "gemma_enhanced": "Gemma unavailable",
                "error": str(e)
            }

    def get_analysis_summary(self, analysis: SeverityAnalysis) -> str:
        """
        Generate human-readable summary of analysis.
        """
        summary = f"""
Severity Analysis Summary
========================
Level: {analysis.severity.upper()}
Confidence: {analysis.confidence:.0%}

Indicators Detected:
{chr(10).join(f'- {ind}' for ind in analysis.indicators)}

Emotional State: {analysis.emotional_intensity}
Urgency: {analysis.urgency}

Recommended Response:
{analysis.recommended_response}
"""
        return summary


def create_severity_analyzer() -> SeverityAnalyzer:
    """
    Factory function to create severity analyzer.
    """
    return SeverityAnalyzer()


if __name__ == "__main__":
    # Test severity analyzer
    print("Testing Severity Analyzer...")

    analyzer = create_severity_analyzer()

    # Test cases
    test_cases = [
        "He pushed me against the wall yesterday and threatened to hurt me if I told anyone.",
        "He held a knife to my throat and said he would kill me.",
        "She yelled at me and called me names during an argument last week.",
        "My partner controls all the money and I can't leave the house.",
    ]

    for test in test_cases:
        print(f"\n--- Test Case ---")
        print(f"Transcript: {test[:50]}...")
        result = analyzer.analyze(test)
        print(f"Severity: {result.severity}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"Indicators: {result.indicators[:3]}")
        print(f"Response: {result.recommended_response[:50]}...")

    print("\nSeverity Analyzer ready!")
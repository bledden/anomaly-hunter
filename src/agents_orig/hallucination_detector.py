"""
Hallucination Detector Module
Detects common hallucination patterns in LLM outputs using lightweight pattern matching
"""

import re
from typing import Dict, List


class HallucinationDetector:
    """
    Detects hallucinations in LLM outputs using regex-based pattern matching.
    Fast and lightweight, designed for real-time evaluation during benchmarks.
    """

    # Pattern categories
    UNFOUNDED_CLAIMS = [
        r"I have access to",
        r"I can browse",
        r"I searched",
        r"I can search",
        r"I can see",
        r"I can view",
        r"I have browsed",
        r"I have searched",
        r"I just searched",
        r"I found online",
        r"according to my search",
        r"based on my search",
    ]

    SELF_CONTRADICTIONS = [
        r"both true and false",
        r"simultaneously opposite",
        r"is and is not",
        r"can and cannot",
        r"will and will not",
        r"always never",
        r"never always",
    ]

    FABRICATED_APIS = [
        r"import imaginary",
        r"from fake_",
        r"import nonexistent",
        r"from fictional",
        r"import madeup",
        r"\.fakmethod\(",
        r"\.nonexistentmethod\(",
        r"\.imaginaryfunction\(",
    ]

    MADE_UP_VERSIONS = [
        r"version 99\.",
        r"v99\.",
        r"version 100\.",
        r"v100\.",
        r"@version\s+\d{5,}",  # Suspiciously high version numbers
    ]

    FICTIONAL_PACKAGES = [
        r"pip install fake",
        r"npm install nonexistent",
        r"import doesnotexist",
        r"require\(['\"]imaginary",
        r"from makebelieve import",
    ]

    FUTURE_CLAIMS = [
        r"in \d{4,}",  # Years far in future (context dependent)
        r"will be released in 20\d{2}",  # Past release claims for future
        r"coming in 20\d{2}",
        r"scheduled for 20\d{2}",
    ]

    IMPOSSIBLE_CLAIMS = [
        r"O\(0\)",  # Impossible time complexity
        r"O\(-1\)",
        r"100% accuracy guaranteed",
        r"never fails",
        r"always correct",
        r"guaranteed perfect",
        r"infinite speed",
        r"zero memory usage",
        r"instantaneous",
        r"perfect accuracy",
    ]

    INVALID_SYNTAX = [
        r"def async lambda",
        r"class static final",
        r"async sync def",
        r"public private",
        r"const let var",
    ]

    def __init__(self):
        """Initialize the hallucination detector with compiled regex patterns."""
        self.pattern_categories = {
            "unfounded_claims": [re.compile(p, re.IGNORECASE) for p in self.UNFOUNDED_CLAIMS],
            "self_contradictions": [re.compile(p, re.IGNORECASE) for p in self.SELF_CONTRADICTIONS],
            "fabricated_apis": [re.compile(p, re.IGNORECASE) for p in self.FABRICATED_APIS],
            "made_up_versions": [re.compile(p, re.IGNORECASE) for p in self.MADE_UP_VERSIONS],
            "fictional_packages": [re.compile(p, re.IGNORECASE) for p in self.FICTIONAL_PACKAGES],
            "future_claims": [re.compile(p, re.IGNORECASE) for p in self.FUTURE_CLAIMS],
            "impossible_claims": [re.compile(p, re.IGNORECASE) for p in self.IMPOSSIBLE_CLAIMS],
            "invalid_syntax": [re.compile(p, re.IGNORECASE) for p in self.INVALID_SYNTAX],
        }

    def detect(self, output: str) -> Dict:
        """
        Detect hallucinations in the given output.

        Args:
            output: The LLM output text to analyze

        Returns:
            Dict containing:
                - hallucination_detected: bool indicating if hallucinations were found
                - confidence: float between 0 and 1 indicating confidence level
                - indicators: List of specific indicators found
        """
        if not output or not isinstance(output, str):
            return {
                "hallucination_detected": False,
                "confidence": 0.0,
                "indicators": []
            }

        indicators = []
        category_scores = {}

        # Check each pattern category
        for category, patterns in self.pattern_categories.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(output)
                if found:
                    matches.extend(found)

            if matches:
                category_scores[category] = len(matches)
                indicators.extend([f"{category}: {match}" for match in matches[:3]])  # Limit to 3 per category

        # Calculate confidence score
        # Weight different categories differently
        weights = {
            "unfounded_claims": 0.3,
            "self_contradictions": 0.5,
            "fabricated_apis": 0.4,
            "made_up_versions": 0.2,
            "fictional_packages": 0.4,
            "future_claims": 0.15,  # Lower weight as some future references may be valid
            "impossible_claims": 0.5,
            "invalid_syntax": 0.4,
        }

        total_score = 0.0
        for category, count in category_scores.items():
            weight = weights.get(category, 0.3)
            # Logarithmic scaling to prevent single category from dominating
            category_contribution = weight * min(1.0, count * 0.3)
            total_score += category_contribution

        # Normalize confidence to 0-1 range
        confidence = min(1.0, total_score)

        # Detection threshold
        hallucination_detected = confidence > 0.2

        return {
            "hallucination_detected": hallucination_detected,
            "confidence": round(confidence, 3),
            "indicators": indicators[:10]  # Return top 10 indicators
        }

    def check_code_quality(self, output: str) -> Dict:
        """
        Additional method to check for basic code quality issues that might indicate hallucination.

        Args:
            output: The LLM output text to analyze

        Returns:
            Dict with quality indicators
        """
        has_code = any(marker in output for marker in ["```", "def ", "class ", "function ", "const ", "let "])
        has_logic = any(keyword in output.lower() for keyword in ["if ", "for ", "while ", "return ", "elif "])
        reasonable_length = 50 < len(output) < 50000

        # Check for excessive repetition (copy-paste errors)
        lines = output.split('\n')
        unique_lines = set(lines)
        repetition_ratio = len(lines) / len(unique_lines) if unique_lines else 1.0

        return {
            "has_code": has_code,
            "has_logic": has_logic,
            "reasonable_length": reasonable_length,
            "repetition_ratio": round(repetition_ratio, 2),
            "quality_issues": repetition_ratio > 2.0  # Flag if too repetitive
        }

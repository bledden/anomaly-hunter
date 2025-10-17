"""
Semantic Relevance Checker - Detects Hallucinations in Code Generation

This module adds LLM-as-judge evaluation to detect when generated code
doesn't match the task requirements (hallucinations).
"""

import re
from typing import Dict, Tuple
from agents.llm_client import MultiAgentLLMOrchestrator


class SemanticRelevanceChecker:
    """
    Checks if generated code actually addresses the task requirements.

    This prevents hallucinations where code is syntactically correct
    but solves a completely different problem.
    """

    def __init__(self, use_llm_judge: bool = False):
        """
        Initialize semantic relevance checker.

        Args:
            use_llm_judge: If True, use LLM for deeper analysis (slower but more accurate).
                          If False, use only keyword matching (fast, good enough for most cases).
        """
        self.use_llm_judge = use_llm_judge
        self.llm = None

        if use_llm_judge:
            try:
                import yaml
                with open("config/agents.yaml", 'r') as f:
                    config = yaml.safe_load(f)
                self.llm = MultiAgentLLMOrchestrator(config)
            except Exception as e:
                print(f"[WARN] Could not initialize LLM judge: {e}")
                print("[WARN] Falling back to keyword-only matching")
                self.use_llm_judge = False

    def check_relevance(self, code: str, task: str, language: str = "python") -> Tuple[float, Dict]:
        """
        Check if code is semantically relevant to the task.

        Args:
            code: Generated code to evaluate
            task: Original task description
            language: Programming language

        Returns:
            Tuple of (relevance_score, details_dict)
            - relevance_score: 0.0-1.0 indicating how well code matches task
            - details_dict: Explanation of scoring
        """

        # Extract key requirements from task
        keywords = self._extract_task_keywords(task)

        # Basic keyword matching (fast, heuristic check)
        keyword_score = self._keyword_matching_score(code, keywords)

        # If keyword score is very low, likely hallucination
        if keyword_score < 0.3:
            return keyword_score, {
                "method": "keyword_matching",
                "score": keyword_score,
                "matched_keywords": keywords["matched"],
                "missing_keywords": keywords["missing"],
                "likely_hallucination": True
            }

        # For medium scores, use LLM-as-judge for deeper analysis (if enabled)
        if keyword_score < 0.7 and self.use_llm_judge and self.llm:
            llm_score, llm_details = self._llm_judge_relevance(code, task, language)
            # Weighted combination: 40% keywords, 60% LLM
            final_score = 0.4 * keyword_score + 0.6 * llm_score
            return final_score, {
                "method": "hybrid",
                "keyword_score": keyword_score,
                "llm_score": llm_score,
                "final_score": final_score,
                "llm_reasoning": llm_details,
                "likely_hallucination": final_score < 0.5
            }
        elif keyword_score < 0.7:
            # LLM not available, use keyword + requirement check
            return keyword_score, {
                "method": "keyword_matching",
                "score": keyword_score,
                "matched_keywords": keywords["matched"],
                "missing_keywords": keywords["missing"],
                "likely_hallucination": keyword_score < 0.5,
                "note": "LLM judge not available - using keyword matching only"
            }

        # High keyword match - trust it
        return keyword_score, {
            "method": "keyword_matching",
            "score": keyword_score,
            "matched_keywords": keywords["matched"],
            "likely_hallucination": False
        }

    def _extract_task_keywords(self, task: str) -> Dict:
        """Extract key technical terms from task description"""
        task_lower = task.lower()

        # Common technical keyword patterns
        tech_patterns = [
            r'\b(?:bcrypt|jwt|oauth2?|csrf|xss|sql|redis|aes|hmac|2fa|totp)\b',
            r'\b(?:password|hash|token|encrypt|decrypt|sign|verify|sanitize)\b',
            r'\b(?:authentication|authorization|validation|security|permission)\b',
            r'\b(?:rate\s*limit|query\s*builder|session|cookie|middleware)\b',
        ]

        keywords = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, task_lower)
            keywords.update(matches)

        return {
            "keywords": list(keywords),
            "matched": [],
            "missing": []
        }

    def _keyword_matching_score(self, code: str, keywords: Dict) -> float:
        """
        Check what percentage of task keywords appear in code.
        Returns 0.0-1.0 score.
        """
        if not keywords["keywords"]:
            return 0.5  # No keywords extracted, can't judge

        code_lower = code.lower()
        matched = []
        missing = []

        for keyword in keywords["keywords"]:
            if keyword in code_lower:
                matched.append(keyword)
            else:
                missing.append(keyword)

        keywords["matched"] = matched
        keywords["missing"] = missing

        match_ratio = len(matched) / len(keywords["keywords"])
        return match_ratio

    def _llm_judge_relevance(self, code: str, task: str, language: str) -> Tuple[float, str]:
        """
        Use LLM to judge semantic relevance of code to task.
        """

        prompt = f"""You are evaluating if generated code matches task requirements.

Task Description:
{task}

Generated Code ({language}):
```{language}
{code}
```

Evaluate if the code addresses the task requirements. Consider:
1. Does it implement the requested functionality?
2. Are the key concepts from the task present?
3. Is this solving the right problem, or a different one?

Respond with JSON:
{{
  "relevance_score": <0.0-1.0>,
  "reasoning": "<brief explanation>",
  "hallucination_detected": <true/false>,
  "missing_requirements": ["<req1>", "<req2>"]
}}

Be strict - partial implementations should score lower."""

        try:
            response = self.llm.execute_single_agent(
                "reviewer",
                prompt,
                max_tokens=500
            )

            # Parse JSON response
            import json
            # Extract JSON from markdown if present
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)

            result = json.loads(response)
            score = float(result.get("relevance_score", 0.5))
            reasoning = result.get("reasoning", "No reasoning provided")

            return score, reasoning

        except Exception as e:
            # Fallback if LLM fails
            return 0.5, f"LLM evaluation failed: {str(e)}"

    def check_task_specific_requirements(self, code: str, task: str) -> Tuple[float, Dict]:
        """
        Check for specific security/quality requirements mentioned in task.

        Examples:
        - "with bcrypt" -> code must import/use bcrypt
        - "parameterized queries" -> code must use parameterization
        - "HTTP-only cookies" -> code must set httponly flag
        """
        requirements_met = []
        requirements_missing = []

        task_lower = task.lower()
        code_lower = code.lower()

        # Security requirement patterns
        security_checks = [
            ("bcrypt", ["bcrypt", "hashpw"]),
            ("jwt", ["jwt", "jsonwebtoken"]),
            ("parameterized", ["parameterized", "prepare", "bind", "placeholder", "?"]),
            ("xss", ["escape", "sanitize", "dompurify", "bleach"]),
            ("csrf", ["csrf", "token", "verify"]),
            ("rate limit", ["rate", "limit", "throttle"]),
            ("aes", ["aes", "cipher", "encrypt"]),
            ("hmac", ["hmac", "sign"]),
            ("2fa", ["totp", "otp", "authenticator"]),
            ("http-only", ["httponly", "http_only"]),
        ]

        for requirement, indicators in security_checks:
            if requirement in task_lower:
                found = any(indicator in code_lower for indicator in indicators)
                if found:
                    requirements_met.append(requirement)
                else:
                    requirements_missing.append(requirement)

        # Calculate score
        total_requirements = len(requirements_met) + len(requirements_missing)
        if total_requirements == 0:
            return 1.0, {"requirements_met": [], "requirements_missing": []}

        score = len(requirements_met) / total_requirements

        return score, {
            "requirements_met": requirements_met,
            "requirements_missing": requirements_missing,
            "total_requirements": total_requirements
        }


def add_semantic_check_to_evaluator():
    """
    Helper function showing how to integrate semantic checking
    into the existing quality_evaluator.py
    """
    return """
# Add to quality_evaluator.py:

# 1. Import at top:
from semantic_relevance_checker import SemanticRelevanceChecker

# 2. Add to QualityDimension enum:
class QualityDimension(Enum):
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    SEMANTIC_RELEVANCE = "semantic_relevance"  # NEW

# 3. Add to __init__:
def __init__(self, pass_threshold: float = 0.7):
    self.pass_threshold = pass_threshold
    self.semantic_checker = SemanticRelevanceChecker()  # NEW

# 4. Add to _evaluate_python (and other language methods):
# 7. Semantic Relevance (does it solve the right problem?)
relevance, rel_details = self.semantic_checker.check_relevance(code, task, "python")
dimensions[QualityDimension.SEMANTIC_RELEVANCE.value] = relevance
details["semantic_relevance"] = rel_details

# 5. Update DIMENSION_WEIGHTS dict:
DIMENSION_WEIGHTS = {
    QualityDimension.CORRECTNESS.value: 0.25,        # 25% (was 30%)
    QualityDimension.COMPLETENESS.value: 0.20,       # 20% (was 25%)
    QualityDimension.CODE_QUALITY.value: 0.15,       # 15% (was 20%)
    QualityDimension.DOCUMENTATION.value: 0.10,      # 10% (same)
    QualityDimension.ERROR_HANDLING.value: 0.10,     # 10% (same)
    QualityDimension.TESTING.value: 0.05,            # 5% (same)
    QualityDimension.SEMANTIC_RELEVANCE.value: 0.15  # 15% NEW (most important!)
}
"""


if __name__ == "__main__":
    # Example usage
    checker = SemanticRelevanceChecker()

    # Test case 1: Correct implementation
    task1 = "Implement password hashing with bcrypt, salt, and pepper"
    code1 = """
import bcrypt
import os

def hash_password(password: str, pepper: str) -> str:
    salt = bcrypt.gensalt()
    peppered = password + pepper
    hashed = bcrypt.hashpw(peppered.encode(), salt)
    return hashed.decode()
"""
    score1, details1 = checker.check_relevance(code1, task1, "python")
    print(f"Test 1 - Correct Implementation:")
    print(f"  Score: {score1:.2f}")
    print(f"  Details: {details1}")
    print()

    # Test case 2: Hallucination (wrong implementation)
    task2 = "Implement password hashing with bcrypt, salt, and pepper"
    code2 = """
import jwt
import datetime

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, 'secret', algorithm='HS256')
"""
    score2, details2 = checker.check_relevance(code2, task2, "python")
    print(f"Test 2 - Hallucination (JWT instead of bcrypt):")
    print(f"  Score: {score2:.2f}")
    print(f"  Details: {details2}")
    print()

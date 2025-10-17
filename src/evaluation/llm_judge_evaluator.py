"""
LLM-as-Judge Evaluator - Semantic code quality assessment using LLM

Uses an LLM to evaluate code across dimensions that are hard to capture
with static analysis:
- Semantic correctness
- Best practices adherence
- Code clarity and readability
- Appropriate patterns and idioms
- Edge case handling
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class JudgementCategory(Enum):
    """Categories for LLM judge evaluation"""
    CORRECTNESS = "correctness"
    BEST_PRACTICES = "best_practices"
    READABILITY = "readability"
    EDGE_CASES = "edge_cases"
    DESIGN_PATTERNS = "design_patterns"


@dataclass
class JudgementScore:
    """Individual category judgement"""
    category: JudgementCategory
    score: float  # 0.0 - 1.0
    reasoning: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class LLMJudgeScore:
    """Complete LLM judge evaluation results"""
    overall: float  # 0.0 - 1.0 weighted average
    correctness_score: float = 0.0
    best_practices_score: float = 0.0
    readability_score: float = 0.0
    edge_cases_score: float = 0.0
    design_patterns_score: float = 0.0

    judgements: List[JudgementScore] = field(default_factory=list)
    overall_strengths: List[str] = field(default_factory=list)
    overall_weaknesses: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

    passed: bool = True  # True if overall >= 0.7
    confidence: str = "medium"  # low, medium, high


class LLMJudgeEvaluator:
    """
    LLM-as-judge evaluator for semantic code quality.

    Scoring weights:
    - Correctness: 40% (most important)
    - Best Practices: 25%
    - Readability: 15%
    - Edge Cases: 15%
    - Design Patterns: 5%

    Final score = weighted average of category scores
    """

    def __init__(
        self,
        openrouter_api_key: Optional[str] = None,
        judge_model: str = "anthropic/claude-sonnet-4.5",
        temperature: float = 0.3,  # Low temp for consistent judgement
        timeout: int = 60
    ):
        """
        Initialize LLM judge evaluator.

        Args:
            openrouter_api_key: OpenRouter API key (or uses OPENROUTER_API_KEY env var)
            judge_model: Model to use for judging
            temperature: Sampling temperature for judge
            timeout: Max seconds for LLM call
        """
        self.api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.judge_model = judge_model
        self.temperature = temperature
        self.timeout = timeout

        # Category weights
        self.weights = {
            JudgementCategory.CORRECTNESS: 0.40,
            JudgementCategory.BEST_PRACTICES: 0.25,
            JudgementCategory.READABILITY: 0.15,
            JudgementCategory.EDGE_CASES: 0.15,
            JudgementCategory.DESIGN_PATTERNS: 0.05
        }

    def evaluate(
        self,
        code: str,
        task_description: str,
        language: str = "python"
    ) -> LLMJudgeScore:
        """
        Evaluate code using LLM judge.

        Args:
            code: Source code to evaluate
            task_description: What the code is supposed to do
            language: Programming language

        Returns:
            LLMJudgeScore with detailed assessment
        """
        if not self.api_key:
            logger.warning("No OpenRouter API key found, skipping LLM judge evaluation")
            return self._create_default_score()

        try:
            # Get LLM judgement
            judgements = self._get_llm_judgement(code, task_description, language)

            # Calculate scores
            return self._combine_judgements(judgements)

        except Exception as e:
            logger.error(f"LLM judge evaluation failed: {e}", exc_info=True)
            return self._create_default_score()

    def _get_llm_judgement(
        self,
        code: str,
        task_description: str,
        language: str
    ) -> List[JudgementScore]:
        """Get LLM judgement for all categories"""
        prompt = self._build_judge_prompt(code, task_description, language)

        try:
            # Call OpenRouter API
            import requests

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/bledden/corch",
                },
                json={
                    "model": self.judge_model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": self.temperature,
                    "max_tokens": 2000
                },
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} {response.text}")
                return []

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            return self._parse_llm_response(content)

        except requests.Timeout:
            logger.warning("LLM judge timed out")
            return []
        except Exception as e:
            logger.error(f"LLM judge API call failed: {e}")
            return []

    def _build_judge_prompt(
        self,
        code: str,
        task_description: str,
        language: str
    ) -> str:
        """Build prompt for LLM judge"""
        return f"""You are an expert code reviewer evaluating {language} code.

TASK DESCRIPTION:
{task_description}

CODE TO EVALUATE:
```{language}
{code}
```

Evaluate this code across these 5 dimensions and provide scores from 0.0 to 1.0:

1. **CORRECTNESS** (40% weight): Does the code correctly implement the task?
   - Does it solve the stated problem?
   - Are there logical errors or bugs?
   - Does it handle inputs correctly?

2. **BEST PRACTICES** (25% weight): Does it follow language best practices?
   - Proper error handling
   - Appropriate use of language features
   - Security considerations
   - Performance considerations

3. **READABILITY** (15% weight): Is the code clear and understandable?
   - Variable naming
   - Code structure
   - Comments and documentation
   - Complexity management

4. **EDGE CASES** (15% weight): Does it handle edge cases?
   - Boundary conditions
   - Null/empty inputs
   - Error conditions
   - Invalid inputs

5. **DESIGN PATTERNS** (5% weight): Are appropriate patterns used?
   - Proper abstractions
   - SOLID principles
   - Idiomatic {language} code

Return ONLY valid JSON with this exact structure:
{{
  "judgements": [
    {{
      "category": "correctness",
      "score": 0.9,
      "reasoning": "The code correctly implements...",
      "strengths": ["Handles main case well", "Logic is sound"],
      "weaknesses": ["Missing input validation"],
      "suggestions": ["Add type checking for inputs"]
    }},
    {{
      "category": "best_practices",
      "score": 0.8,
      "reasoning": "...",
      "strengths": [...],
      "weaknesses": [...],
      "suggestions": [...]
    }},
    {{
      "category": "readability",
      "score": 0.85,
      "reasoning": "...",
      "strengths": [...],
      "weaknesses": [...],
      "suggestions": [...]
    }},
    {{
      "category": "edge_cases",
      "score": 0.7,
      "reasoning": "...",
      "strengths": [...],
      "weaknesses": [...],
      "suggestions": [...]
    }},
    {{
      "category": "design_patterns",
      "score": 0.8,
      "reasoning": "...",
      "strengths": [...],
      "weaknesses": [...],
      "suggestions": [...]
    }}
  ],
  "overall_strengths": ["List", "of", "overall", "strengths"],
  "overall_weaknesses": ["List", "of", "overall", "weaknesses"],
  "improvement_suggestions": ["Priority", "improvements"],
  "confidence": "high"
}}

Be honest and constructive. Focus on what matters for production code quality."""

    def _parse_llm_response(self, content: str) -> List[JudgementScore]:
        """Parse LLM JSON response into JudgementScore objects"""
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            judgements = []

            for j in data.get("judgements", []):
                try:
                    category = JudgementCategory(j["category"])
                    judgements.append(JudgementScore(
                        category=category,
                        score=float(j["score"]),
                        reasoning=j.get("reasoning", ""),
                        strengths=j.get("strengths", []),
                        weaknesses=j.get("weaknesses", []),
                        suggestions=j.get("suggestions", [])
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse judgement: {e}")
                    continue

            return judgements

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response content: {content[:500]}")
            return []

    def _combine_judgements(self, judgements: List[JudgementScore]) -> LLMJudgeScore:
        """Combine individual judgements into overall score"""
        if not judgements:
            return self._create_default_score()

        # Extract scores by category
        scores = {j.category: j.score for j in judgements}

        correctness = scores.get(JudgementCategory.CORRECTNESS, 0.5)
        best_practices = scores.get(JudgementCategory.BEST_PRACTICES, 0.5)
        readability = scores.get(JudgementCategory.READABILITY, 0.5)
        edge_cases = scores.get(JudgementCategory.EDGE_CASES, 0.5)
        design_patterns = scores.get(JudgementCategory.DESIGN_PATTERNS, 0.5)

        # Calculate weighted overall
        overall = (
            correctness * self.weights[JudgementCategory.CORRECTNESS] +
            best_practices * self.weights[JudgementCategory.BEST_PRACTICES] +
            readability * self.weights[JudgementCategory.READABILITY] +
            edge_cases * self.weights[JudgementCategory.EDGE_CASES] +
            design_patterns * self.weights[JudgementCategory.DESIGN_PATTERNS]
        )

        # Aggregate strengths, weaknesses, suggestions
        all_strengths = []
        all_weaknesses = []
        all_suggestions = []

        for j in judgements:
            all_strengths.extend(j.strengths)
            all_weaknesses.extend(j.weaknesses)
            all_suggestions.extend(j.suggestions)

        return LLMJudgeScore(
            overall=round(overall, 3),
            correctness_score=round(correctness, 3),
            best_practices_score=round(best_practices, 3),
            readability_score=round(readability, 3),
            edge_cases_score=round(edge_cases, 3),
            design_patterns_score=round(design_patterns, 3),
            judgements=judgements,
            overall_strengths=list(set(all_strengths))[:5],  # Top 5 unique
            overall_weaknesses=list(set(all_weaknesses))[:5],
            improvement_suggestions=list(set(all_suggestions))[:5],
            passed=overall >= 0.7,
            confidence="high" if len(judgements) == 5 else "medium"
        )

    def _create_default_score(self) -> LLMJudgeScore:
        """Create neutral score when evaluation fails"""
        return LLMJudgeScore(
            overall=0.5,
            correctness_score=0.5,
            best_practices_score=0.5,
            readability_score=0.5,
            edge_cases_score=0.5,
            design_patterns_score=0.5,
            passed=False,
            confidence="low"
        )

"""
Evaluation middleware - Runs all code quality evaluators on generated code
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from .base_middleware import BaseMiddleware, MiddlewareHook, MiddlewareContext
from src.evaluation import (
    SecurityEvaluator,
    StaticAnalysisEvaluator,
    ComplexityEvaluator,
    LLMJudgeEvaluator
)

logger = logging.getLogger(__name__)


@dataclass
class AggregatedEvaluationResult:
    """Combined results from all evaluators"""
    overall_score: float  # 0.0 - 1.0 weighted average
    passed: bool  # True if all evaluators pass

    # Individual evaluator scores
    security_score: float = 0.0
    static_analysis_score: float = 0.0
    complexity_score: float = 0.0
    llm_judge_score: float = 0.0

    # Detailed results
    security_details: Optional[Any] = None
    static_analysis_details: Optional[Any] = None
    complexity_details: Optional[Any] = None
    llm_judge_details: Optional[Any] = None

    # Summary
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Metadata
    evaluators_run: int = 0
    evaluators_failed: int = 0


class EvaluationMiddleware(BaseMiddleware):
    """
    Middleware that runs all code quality evaluators on generated code.

    Executes at POST_REFINER and POST_DOCUMENTER hooks.

    Scoring weights:
    - Security: 30% (most critical)
    - Static Analysis: 30% (code quality)
    - Complexity: 20% (maintainability)
    - LLM Judge: 20% (semantic quality)

    Pass threshold: overall >= 0.7 AND all individual >= 0.6
    """

    def __init__(
        self,
        enabled: bool = True,
        enable_security: bool = True,
        enable_static_analysis: bool = True,
        enable_complexity: bool = True,
        enable_llm_judge: bool = True,
        pass_threshold: float = 0.7,
        gate_on_failure: bool = False  # If True, block progression on failure
    ):
        """
        Initialize evaluation middleware.

        Args:
            enabled: Whether middleware is active
            enable_security: Run security evaluator
            enable_static_analysis: Run static analysis evaluator
            enable_complexity: Run complexity evaluator
            enable_llm_judge: Run LLM judge evaluator
            pass_threshold: Minimum overall score for passing
            gate_on_failure: If True, block workflow on evaluation failure
        """
        super().__init__(enabled)

        # Evaluator enable flags
        self.enable_security = enable_security
        self.enable_static_analysis = enable_static_analysis
        self.enable_complexity = enable_complexity
        self.enable_llm_judge = enable_llm_judge

        # Configuration
        self.pass_threshold = pass_threshold
        self.gate_on_failure = gate_on_failure

        # Initialize evaluators
        self.security_eval = SecurityEvaluator() if enable_security else None
        self.static_eval = StaticAnalysisEvaluator() if enable_static_analysis else None
        self.complexity_eval = ComplexityEvaluator() if enable_complexity else None
        self.llm_judge_eval = LLMJudgeEvaluator() if enable_llm_judge else None

        # Scoring weights
        self.weights = {
            'security': 0.30,
            'static_analysis': 0.30,
            'complexity': 0.20,
            'llm_judge': 0.20
        }

    def get_hooks(self) -> list[MiddlewareHook]:
        """Subscribe to POST_REFINER and POST_DOCUMENTER hooks"""
        return [MiddlewareHook.POST_REFINER, MiddlewareHook.POST_DOCUMENTER]

    def execute(self, context: MiddlewareContext) -> Dict[str, Any]:
        """
        Run all enabled evaluators on generated code.

        Args:
            context: Middleware context with stage data

        Returns:
            Dict with evaluation results and pass/fail status
        """
        logger.info(f"Running evaluation middleware at {context.hook.value}")

        # Extract code and task description from context
        code = self._extract_code(context)
        task_description = self._extract_task_description(context)
        language = self._extract_language(context)

        if not code:
            logger.warning("No code found in context, skipping evaluation")
            return {'passed': True, 'evaluation': None}

        # Run all evaluators
        result = self._run_evaluations(code, task_description, language)

        # Log results
        logger.info(f"Evaluation complete: overall={result.overall_score:.3f}, passed={result.passed}")

        # Determine if workflow should proceed
        should_pass = result.passed or not self.gate_on_failure

        return {
            'passed': should_pass,
            'evaluation': result,
            'metadata': {
                'overall_score': result.overall_score,
                'individual_scores': {
                    'security': result.security_score,
                    'static_analysis': result.static_analysis_score,
                    'complexity': result.complexity_score,
                    'llm_judge': result.llm_judge_score
                },
                'evaluators_run': result.evaluators_run,
                'evaluators_failed': result.evaluators_failed
            }
        }

    def _run_evaluations(
        self,
        code: str,
        task_description: str,
        language: str
    ) -> AggregatedEvaluationResult:
        """Run all enabled evaluators and aggregate results"""
        evaluators_run = 0
        evaluators_failed = 0

        # Security evaluation
        security_score = 0.0
        security_details = None
        if self.security_eval:
            try:
                sec_result = self.security_eval.evaluate(code, language)
                security_score = sec_result.overall
                security_details = sec_result
                evaluators_run += 1
            except Exception as e:
                logger.error(f"Security evaluator failed: {e}")
                evaluators_failed += 1
                security_score = 0.5  # Neutral score on failure

        # Static analysis evaluation
        static_score = 0.0
        static_details = None
        if self.static_eval:
            try:
                static_result = self.static_eval.evaluate(code, language)
                static_score = static_result.overall
                static_details = static_result
                evaluators_run += 1
            except Exception as e:
                logger.error(f"Static analysis evaluator failed: {e}")
                evaluators_failed += 1
                static_score = 0.5

        # Complexity evaluation
        complexity_score = 0.0
        complexity_details = None
        if self.complexity_eval:
            try:
                complexity_result = self.complexity_eval.evaluate(code, language)
                complexity_score = complexity_result.overall
                complexity_details = complexity_result
                evaluators_run += 1
            except Exception as e:
                logger.error(f"Complexity evaluator failed: {e}")
                evaluators_failed += 1
                complexity_score = 0.5

        # LLM judge evaluation
        llm_score = 0.0
        llm_details = None
        if self.llm_judge_eval:
            try:
                llm_result = self.llm_judge_eval.evaluate(code, task_description, language)
                llm_score = llm_result.overall
                llm_details = llm_result
                evaluators_run += 1
            except Exception as e:
                logger.error(f"LLM judge evaluator failed: {e}")
                evaluators_failed += 1
                llm_score = 0.5

        # Calculate weighted overall score
        overall = (
            security_score * self.weights['security'] +
            static_score * self.weights['static_analysis'] +
            complexity_score * self.weights['complexity'] +
            llm_score * self.weights['llm_judge']
        )

        # Determine pass/fail
        passed = (
            overall >= self.pass_threshold and
            security_score >= 0.6 and
            static_score >= 0.6 and
            complexity_score >= 0.6 and
            llm_score >= 0.6
        )

        # Aggregate strengths/weaknesses
        strengths, weaknesses, recommendations = self._aggregate_feedback(
            security_details, static_details, complexity_details, llm_details
        )

        return AggregatedEvaluationResult(
            overall_score=round(overall, 3),
            passed=passed,
            security_score=round(security_score, 3),
            static_analysis_score=round(static_score, 3),
            complexity_score=round(complexity_score, 3),
            llm_judge_score=round(llm_score, 3),
            security_details=security_details,
            static_analysis_details=static_details,
            complexity_details=complexity_details,
            llm_judge_details=llm_details,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            evaluators_run=evaluators_run,
            evaluators_failed=evaluators_failed
        )

    def _extract_code(self, context: MiddlewareContext) -> Optional[str]:
        """Extract code from middleware context"""
        # Try output_data first (POST hooks)
        if context.output_data:
            code = context.output_data.get('code') or context.output_data.get('final_implementation')
            if code:
                return code

        # Try input_data
        if context.input_data:
            code = context.input_data.get('code') or context.input_data.get('final_implementation')
            if code:
                return code

        return None

    def _extract_task_description(self, context: MiddlewareContext) -> str:
        """Extract task description from context"""
        if context.input_data:
            return context.input_data.get('original_request', 'Code implementation')
        return 'Code implementation'

    def _extract_language(self, context: MiddlewareContext) -> str:
        """Extract programming language from context"""
        if context.input_data:
            return context.input_data.get('language', 'python')
        return 'python'

    def _aggregate_feedback(
        self,
        security_details,
        static_details,
        complexity_details,
        llm_details
    ) -> tuple[list[str], list[str], list[str]]:
        """Aggregate strengths, weaknesses, and recommendations from all evaluators"""
        strengths = []
        weaknesses = []
        recommendations = []

        # Security feedback
        if security_details:
            if security_details.safe:
                strengths.append("No security vulnerabilities detected")
            if security_details.total_issues > 0:
                weaknesses.append(f"Found {security_details.total_issues} security issues")
                if security_details.critical_issues:
                    recommendations.append(f"Fix {len(security_details.critical_issues)} critical security issues")

        # Static analysis feedback
        if static_details:
            if static_details.pylint_score >= 8.0:
                strengths.append(f"High code quality (pylint {static_details.pylint_score}/10)")
            total_violations = static_details.flake8_violations + static_details.mypy_errors
            if total_violations > 20:
                weaknesses.append(f"Many code quality violations ({total_violations})")
                recommendations.append("Review and fix code quality issues")

        # Complexity feedback
        if complexity_details:
            if complexity_details.maintainability_index >= 70:
                strengths.append(f"Highly maintainable (MI {complexity_details.maintainability_index})")
            if complexity_details.high_complexity_functions:
                weaknesses.append(f"{len(complexity_details.high_complexity_functions)} functions are too complex")
                recommendations.append("Refactor complex functions to reduce cyclomatic complexity")

        # LLM judge feedback
        if llm_details and hasattr(llm_details, 'overall_strengths'):
            strengths.extend(llm_details.overall_strengths[:2])  # Top 2
            weaknesses.extend(llm_details.overall_weaknesses[:2])
            recommendations.extend(llm_details.improvement_suggestions[:2])

        return strengths[:5], weaknesses[:5], recommendations[:5]

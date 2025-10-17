"""
Quality Evaluation System for Code Generation
Uses multiple objective metrics to score generated code
"""

import ast
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json


class QualityDimension(Enum):
    """Dimensions of code quality to evaluate"""
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"


@dataclass
class QualityScore:
    """Quality evaluation result"""
    overall: float  # 0.0 - 1.0
    dimensions: Dict[str, float]  # Per-dimension scores
    details: Dict[str, Any]  # Detailed findings
    passed: bool  # Pass/fail based on threshold


class CodeQualityEvaluator:
    """
    Evaluates generated code quality using objective metrics

    This is a lightweight evaluator that doesn't require test execution.
    For production, consider adding:
    - Unit test execution
    - Static analysis tools (pylint, mypy, etc.)
    - LLM-as-judge for semantic correctness
    """

    def __init__(self, pass_threshold: float = 0.7):
        self.pass_threshold = pass_threshold

    def evaluate(self, code: str, task: str, language: str = "python") -> QualityScore:
        """
        Evaluate code quality

        Args:
            code: Generated code
            task: Original task description
            language: Programming language

        Returns:
            QualityScore with overall score and dimension breakdown
        """
        if language == "python":
            return self._evaluate_python(code, task)
        elif language in ["javascript", "typescript"]:
            return self._evaluate_javascript(code, task)
        elif language == "java":
            return self._evaluate_java(code, task)
        else:
            # Fallback to basic text analysis
            return self._evaluate_generic(code, task)

    def _evaluate_python(self, code: str, task: str) -> QualityScore:
        """Evaluate Python code"""
        dimensions = {}
        details = {}

        # 1. Correctness (can it parse?)
        correctness, parse_details = self._check_python_syntax(code)
        dimensions[QualityDimension.CORRECTNESS.value] = correctness
        details["syntax"] = parse_details

        # 2. Completeness (has key components?)
        completeness, comp_details = self._check_completeness(code, task)
        dimensions[QualityDimension.COMPLETENESS.value] = completeness
        details["completeness"] = comp_details

        # 3. Code Quality (structure, naming)
        quality, qual_details = self._check_python_quality(code)
        dimensions[QualityDimension.CODE_QUALITY.value] = quality
        details["code_quality"] = qual_details

        # 4. Documentation (docstrings, comments)
        docs, docs_details = self._check_documentation(code)
        dimensions[QualityDimension.DOCUMENTATION.value] = docs
        details["documentation"] = docs_details

        # 5. Error Handling (try/except, validation)
        error_handling, err_details = self._check_error_handling(code)
        dimensions[QualityDimension.ERROR_HANDLING.value] = error_handling
        details["error_handling"] = err_details

        # 6. Testing (test functions present)
        testing, test_details = self._check_testing(code)
        dimensions[QualityDimension.TESTING.value] = testing
        details["testing"] = test_details

        # Calculate overall score (weighted average)
        weights = {
            QualityDimension.CORRECTNESS.value: 0.30,  # Most important
            QualityDimension.COMPLETENESS.value: 0.25,
            QualityDimension.CODE_QUALITY.value: 0.20,
            QualityDimension.DOCUMENTATION.value: 0.10,
            QualityDimension.ERROR_HANDLING.value: 0.10,
            QualityDimension.TESTING.value: 0.05,
        }

        overall = sum(dimensions[dim.value] * weights[dim.value]
                     for dim in QualityDimension)

        return QualityScore(
            overall=overall,
            dimensions=dimensions,
            details=details,
            passed=overall >= self.pass_threshold
        )

    def _check_python_syntax(self, code: str) -> tuple[float, Dict]:
        """Check if Python code is syntactically valid"""
        try:
            ast.parse(code)
            return 1.0, {"valid": True, "error": None}
        except SyntaxError as e:
            return 0.0, {"valid": False, "error": str(e)}
        except Exception as e:
            return 0.0, {"valid": False, "error": f"Parse error: {str(e)}"}

    def _check_completeness(self, code: str, task: str) -> tuple[float, Dict]:
        """Check if code addresses the task requirements"""
        details = {}
        score = 0.0

        # Extract key requirements from task
        task_lower = task.lower()

        # Check for function/class definition
        has_function = bool(re.search(r'\bdef\s+\w+', code))
        has_class = bool(re.search(r'\bclass\s+\w+', code))
        details["has_function"] = has_function
        details["has_class"] = has_class

        if has_function or has_class:
            score += 0.5

        # Check for return statements (if applicable)
        if "return" in task_lower or "calculate" in task_lower or "compute" in task_lower:
            has_return = "return " in code
            details["has_return"] = has_return
            if has_return:
                score += 0.2

        # Check for main logic (if/for/while)
        has_logic = any(keyword in code for keyword in [" if ", " for ", " while "])
        details["has_logic"] = has_logic
        if has_logic:
            score += 0.2

        # Check for imports (if needed)
        if any(lib in task_lower for lib in ["request", "http", "api", "json", "database"]):
            has_imports = bool(re.search(r'^import |^from \w+ import', code, re.MULTILINE))
            details["has_imports"] = has_imports
            if has_imports:
                score += 0.1

        return min(score, 1.0), details

    def _check_python_quality(self, code: str) -> tuple[float, Dict]:
        """Check Python code quality"""
        details = {}
        score = 1.0  # Start high, deduct for issues

        lines = code.split('\n')

        # Check line length
        long_lines = [i for i, line in enumerate(lines) if len(line) > 100]
        if long_lines:
            score -= 0.1
            details["long_lines"] = len(long_lines)

        # Check for meaningful names (not x, y, z, etc.)
        poor_names = re.findall(r'\b[a-z]\s*=', code)
        if len(poor_names) > 3:
            score -= 0.1
            details["poor_variable_names"] = len(poor_names)

        # Check for proper spacing
        spacing_issues = len(re.findall(r'[a-zA-Z]\(|[a-zA-Z]\{|\)if|\)for', code))
        if spacing_issues > 2:
            score -= 0.1
            details["spacing_issues"] = spacing_issues

        # Check for type hints (bonus)
        has_type_hints = bool(re.search(r':\s*(?:int|str|float|bool|List|Dict)', code))
        if has_type_hints:
            score += 0.1
            details["has_type_hints"] = True

        return max(0.0, min(score, 1.0)), details

    def _check_documentation(self, code: str) -> tuple[float, Dict]:
        """Check for documentation"""
        details = {}
        score = 0.0

        # Check for docstrings
        docstrings = re.findall(r'""".*?"""', code, re.DOTALL)
        docstrings += re.findall(r"'''.*?'''", code, re.DOTALL)

        details["docstring_count"] = len(docstrings)
        if docstrings:
            score += 0.6

        # Check for comments
        comments = re.findall(r'#.*$', code, re.MULTILINE)
        details["comment_count"] = len(comments)
        if comments:
            score += 0.2

        # Check for module-level docstring
        if code.strip().startswith('"""') or code.strip().startswith("'''"):
            score += 0.2
            details["has_module_docstring"] = True

        return min(score, 1.0), details

    def _check_error_handling(self, code: str) -> tuple[float, Dict]:
        """Check for error handling"""
        details = {}
        score = 0.0

        # Check for try/except blocks
        try_blocks = len(re.findall(r'\btry:', code))
        except_blocks = len(re.findall(r'\bexcept\b', code))

        details["try_blocks"] = try_blocks
        details["except_blocks"] = except_blocks

        if try_blocks > 0 and except_blocks > 0:
            score += 0.5

        # Check for input validation
        validations = len(re.findall(r'\bif\s+not\s+|raise\s+ValueError|raise\s+TypeError', code))
        details["validations"] = validations
        if validations > 0:
            score += 0.3

        # Check for finally blocks (bonus)
        finally_blocks = len(re.findall(r'\bfinally:', code))
        if finally_blocks > 0:
            score += 0.2
            details["finally_blocks"] = finally_blocks

        return min(score, 1.0), details

    def _check_testing(self, code: str) -> tuple[float, Dict]:
        """Check for test code"""
        details = {}
        score = 0.0

        # Check for test functions
        test_functions = re.findall(r'def\s+test_\w+', code)
        details["test_functions"] = len(test_functions)

        if test_functions:
            score += 0.5

        # Check for assertions
        assertions = len(re.findall(r'\bassert\b', code))
        details["assertions"] = assertions
        if assertions > 0:
            score += 0.3

        # Check for test frameworks
        has_unittest = "import unittest" in code
        has_pytest = "import pytest" in code
        details["has_test_framework"] = has_unittest or has_pytest
        if has_unittest or has_pytest:
            score += 0.2

        return min(score, 1.0), details

    def _evaluate_javascript(self, code: str, task: str) -> QualityScore:
        """Evaluate JavaScript/TypeScript code (simplified)"""
        # Similar to Python but with JS-specific checks
        return self._evaluate_generic(code, task, is_typed=("interface" in code or "type " in code))

    def _evaluate_java(self, code: str, task: str) -> QualityScore:
        """Evaluate Java code (simplified)"""
        return self._evaluate_generic(code, task, is_typed=True)

    def _evaluate_generic(self, code: str, task: str, is_typed: bool = False) -> QualityScore:
        """Generic evaluation for any language"""
        dimensions = {}
        details = {}

        # Basic checks that work for any language
        has_code = len(code.strip()) > 50
        has_function = bool(re.search(r'(def|function|public|private)\s+\w+', code))
        has_logic = any(kw in code for kw in [" if ", " for ", " while ", " switch "])
        reasonable_length = 100 < len(code) < 10000

        # Correctness: Has basic structure
        dimensions[QualityDimension.CORRECTNESS.value] = 1.0 if has_code else 0.0

        # Completeness: Has expected components
        completeness = 0.0
        if has_function:
            completeness += 0.5
        if has_logic:
            completeness += 0.3
        if reasonable_length:
            completeness += 0.2
        dimensions[QualityDimension.COMPLETENESS.value] = min(completeness, 1.0)

        # Code quality: Basic heuristics
        lines = code.split('\n')
        long_lines = sum(1 for line in lines if len(line) > 100)
        quality = 1.0 - (min(long_lines, 5) * 0.1)
        dimensions[QualityDimension.CODE_QUALITY.value] = quality

        # Documentation: Comments present
        comment_count = len(re.findall(r'//.*$|/\*.*?\*/|#.*$', code, re.MULTILINE))
        dimensions[QualityDimension.DOCUMENTATION.value] = min(comment_count / 5, 1.0)

        # Error handling: Basic checks
        has_try = bool(re.search(r'\btry\s*\{', code))
        has_throw = bool(re.search(r'\bthrow\b', code))
        dimensions[QualityDimension.ERROR_HANDLING.value] = 0.5 if (has_try or has_throw) else 0.2

        # Testing: Minimal
        dimensions[QualityDimension.TESTING.value] = 0.3 if "test" in code.lower() else 0.0

        # Overall
        weights = {
            QualityDimension.CORRECTNESS.value: 0.30,
            QualityDimension.COMPLETENESS.value: 0.30,
            QualityDimension.CODE_QUALITY.value: 0.20,
            QualityDimension.DOCUMENTATION.value: 0.10,
            QualityDimension.ERROR_HANDLING.value: 0.05,
            QualityDimension.TESTING.value: 0.05,
        }

        overall = sum(dimensions[dim.value] * weights[dim.value]
                     for dim in QualityDimension)

        details["generic_evaluation"] = True
        details["is_typed"] = is_typed

        return QualityScore(
            overall=overall,
            dimensions=dimensions,
            details=details,
            passed=overall >= self.pass_threshold
        )


def detect_language(code: str) -> str:
    """Detect programming language from code"""
    if "def " in code and ("import " in code or "from " in code):
        return "python"
    elif "function " in code or "const " in code or "let " in code:
        return "javascript"
    elif "interface " in code and ": " in code:
        return "typescript"
    elif "public class " in code or "private class " in code:
        return "java"
    elif "#include" in code:
        return "cpp"
    elif "fn " in code and "let " in code:
        return "rust"
    else:
        return "unknown"


# Demo
if __name__ == "__main__":
    evaluator = CodeQualityEvaluator()

    # Test code examples
    good_code = '''
def factorial(n: int) -> int:
    """
    Calculate factorial of n using recursion

    Args:
        n: Non-negative integer

    Returns:
        Factorial of n

    Raises:
        ValueError: If n is negative
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")

    if n < 0:
        raise ValueError("Input must be non-negative")

    if n == 0 or n == 1:
        return 1

    return n * factorial(n - 1)


# Tests
assert factorial(0) == 1
assert factorial(5) == 120
'''

    bad_code = '''
def f(x):
    if x==0:return 1
    return x*f(x-1)
'''

    print("Evaluating GOOD code:")
    score = evaluator.evaluate(good_code, "Implement factorial using recursion")
    print(f"  Overall: {score.overall:.2f}")
    print(f"  Passed: {score.passed}")
    print(f"  Dimensions:")
    for dim, val in score.dimensions.items():
        print(f"    {dim}: {val:.2f}")

    print("\nEvaluating BAD code:")
    score = evaluator.evaluate(bad_code, "Implement factorial using recursion")
    print(f"  Overall: {score.overall:.2f}")
    print(f"  Passed: {score.passed}")
    print(f"  Dimensions:")
    for dim, val in score.dimensions.items():
        print(f"    {dim}: {val:.2f}")

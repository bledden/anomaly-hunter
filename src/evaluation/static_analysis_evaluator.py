"""
Static Analysis Evaluator - Comprehensive Python code quality analysis

Integrates multiple static analysis tools:
- pylint: Code quality, style, potential bugs (score 0-10)
- flake8: PEP 8 compliance, style violations
- mypy: Static type checking

Provides unified quality scoring and detailed issue reporting.
"""

import json
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels across all analyzers"""
    ERROR = "ERROR"      # Critical issues that must be fixed
    WARNING = "WARNING"  # Important issues that should be fixed
    INFO = "INFO"        # Style/convention suggestions
    HINT = "HINT"        # Minor improvements


@dataclass
class AnalysisIssue:
    """Individual code quality issue"""
    tool: str  # pylint, flake8, mypy
    severity: IssueSeverity
    category: str  # convention, refactor, warning, error, type-hint, etc.
    code: str  # E501, C0103, error, etc.
    message: str
    line_number: int
    column: Optional[int] = None
    symbol: Optional[str] = None  # pylint symbol name


@dataclass
class StaticAnalysisScore:
    """Comprehensive static analysis results"""
    overall: float  # 0.0 - 1.0
    pylint_score: float  # 0.0 - 10.0
    flake8_violations: int
    mypy_errors: int

    errors: List[AnalysisIssue] = field(default_factory=list)
    warnings: List[AnalysisIssue] = field(default_factory=list)
    info: List[AnalysisIssue] = field(default_factory=list)
    hints: List[AnalysisIssue] = field(default_factory=list)

    total_issues: int = 0
    passed: bool = True  # True if overall >= 0.7

    # Detailed breakdown
    pylint_details: Dict[str, Any] = field(default_factory=dict)
    flake8_details: Dict[str, List[str]] = field(default_factory=dict)
    mypy_details: Dict[str, List[str]] = field(default_factory=dict)


class StaticAnalysisEvaluator:
    """
    Static analysis evaluator using pylint, flake8, and mypy.

    Scoring algorithm:
    1. Pylint score (0-10) → normalized to 0.0-1.0 (weight: 50%)
    2. Flake8 violations → penalty-based scoring (weight: 25%)
    3. Mypy errors → penalty-based scoring (weight: 25%)

    Final score = (pylint_norm * 0.5) + (flake8_score * 0.25) + (mypy_score * 0.25)
    """

    def __init__(
        self,
        pylint_threshold: float = 7.0,  # Min score for passing (0-10 scale)
        flake8_max_violations: int = 20,  # Max violations before 0 score
        mypy_max_errors: int = 10,  # Max errors before 0 score
        timeout: int = 30
    ):
        """
        Initialize evaluator with thresholds.

        Args:
            pylint_threshold: Minimum pylint score for passing (0-10)
            flake8_max_violations: Max flake8 violations before score = 0
            mypy_max_errors: Max mypy errors before score = 0
            timeout: Max seconds per tool execution
        """
        self.pylint_threshold = pylint_threshold
        self.flake8_max_violations = flake8_max_violations
        self.mypy_max_errors = mypy_max_errors
        self.timeout = timeout

    def evaluate(self, code: str, language: str = "python") -> StaticAnalysisScore:
        """
        Run static analysis on code.

        Args:
            code: Source code to analyze
            language: Programming language (only 'python' supported)

        Returns:
            StaticAnalysisScore with comprehensive results
        """
        if language.lower() != "python":
            logger.warning(f"Static analysis only supports Python, got: {language}")
            return self._create_default_score()

        try:
            # Run all analyzers
            pylint_result = self._run_pylint(code)
            flake8_result = self._run_flake8(code)
            mypy_result = self._run_mypy(code)

            # Combine results
            return self._combine_results(pylint_result, flake8_result, mypy_result)

        except Exception as e:
            logger.error(f"Static analysis evaluation failed: {e}", exc_info=True)
            return self._create_default_score()

    def _run_pylint(self, code: str) -> Dict[str, Any]:
        """Run pylint and return parsed results"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run pylint with JSON output
            result = subprocess.run(
                ['python3', '-m', 'pylint', '--output-format=json', '--score=yes', tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse JSON output
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                except json.JSONDecodeError:
                    issues = []
            else:
                issues = []

            # Extract score from stderr (pylint outputs score to stderr)
            score = self._extract_pylint_score(result.stderr)

            return {
                'score': score,
                'issues': issues,
                'raw_output': result.stderr
            }

        except subprocess.TimeoutExpired:
            logger.warning("Pylint timed out")
            return {'score': 5.0, 'issues': [], 'raw_output': ''}
        except Exception as e:
            logger.error(f"Pylint execution failed: {e}")
            return {'score': 5.0, 'issues': [], 'raw_output': ''}
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _run_flake8(self, code: str) -> Dict[str, Any]:
        """Run flake8 and return parsed results"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run flake8 with default configuration
            result = subprocess.run(
                ['python3', '-m', 'flake8', '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s', tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse output
            violations = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        violations.append(line)

            return {
                'violations': violations,
                'count': len(violations)
            }

        except subprocess.TimeoutExpired:
            logger.warning("Flake8 timed out")
            return {'violations': [], 'count': 0}
        except Exception as e:
            logger.error(f"Flake8 execution failed: {e}")
            return {'violations': [], 'count': 0}
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _run_mypy(self, code: str) -> Dict[str, Any]:
        """Run mypy and return parsed results"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run mypy with strict checking
            result = subprocess.run(
                ['python3', '-m', 'mypy', '--strict', '--no-error-summary', tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse output
            errors = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line and 'error:' in line:
                        errors.append(line)

            return {
                'errors': errors,
                'count': len(errors)
            }

        except subprocess.TimeoutExpired:
            logger.warning("Mypy timed out")
            return {'errors': [], 'count': 0}
        except Exception as e:
            logger.error(f"Mypy execution failed: {e}")
            return {'errors': [], 'count': 0}
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _extract_pylint_score(self, stderr_output: str) -> float:
        """Extract numerical score from pylint stderr output"""
        # Look for "Your code has been rated at X.XX/10"
        match = re.search(r'rated at ([\d.]+)/10', stderr_output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 5.0  # Default neutral score

    def _parse_pylint_issues(self, issues: List[Dict]) -> List[AnalysisIssue]:
        """Convert pylint JSON issues to AnalysisIssue objects"""
        parsed = []
        for issue in issues:
            severity_map = {
                'error': IssueSeverity.ERROR,
                'warning': IssueSeverity.WARNING,
                'refactor': IssueSeverity.INFO,
                'convention': IssueSeverity.HINT
            }

            severity = severity_map.get(issue.get('type', 'info').lower(), IssueSeverity.INFO)

            parsed.append(AnalysisIssue(
                tool='pylint',
                severity=severity,
                category=issue.get('type', 'unknown'),
                code=issue.get('message-id', ''),
                message=issue.get('message', ''),
                line_number=issue.get('line', 0),
                column=issue.get('column', 0),
                symbol=issue.get('symbol', '')
            ))

        return parsed

    def _parse_flake8_violations(self, violations: List[str]) -> List[AnalysisIssue]:
        """Convert flake8 violations to AnalysisIssue objects"""
        parsed = []
        for violation in violations:
            # Format: path:line:col: CODE message
            match = re.match(r'.*?:(\d+):(\d+): ([A-Z]\d+) (.+)', violation)
            if match:
                line_num = int(match.group(1))
                col_num = int(match.group(2))
                code = match.group(3)
                message = match.group(4)

                # Determine severity based on code prefix
                if code.startswith('E'):
                    severity = IssueSeverity.ERROR
                elif code.startswith('W'):
                    severity = IssueSeverity.WARNING
                else:
                    severity = IssueSeverity.INFO

                parsed.append(AnalysisIssue(
                    tool='flake8',
                    severity=severity,
                    category='style',
                    code=code,
                    message=message,
                    line_number=line_num,
                    column=col_num
                ))

        return parsed

    def _parse_mypy_errors(self, errors: List[str]) -> List[AnalysisIssue]:
        """Convert mypy errors to AnalysisIssue objects"""
        parsed = []
        for error in errors:
            # Format: path:line: error: message
            match = re.match(r'.*?:(\d+): error: (.+)', error)
            if match:
                line_num = int(match.group(1))
                message = match.group(2)

                parsed.append(AnalysisIssue(
                    tool='mypy',
                    severity=IssueSeverity.ERROR,
                    category='type-check',
                    code='error',
                    message=message,
                    line_number=line_num
                ))

        return parsed

    def _combine_results(
        self,
        pylint_result: Dict,
        flake8_result: Dict,
        mypy_result: Dict
    ) -> StaticAnalysisScore:
        """Combine results from all analyzers into unified score"""
        # Parse issues
        pylint_issues = self._parse_pylint_issues(pylint_result.get('issues', []))
        flake8_issues = self._parse_flake8_violations(flake8_result.get('violations', []))
        mypy_issues = self._parse_mypy_errors(mypy_result.get('errors', []))

        all_issues = pylint_issues + flake8_issues + mypy_issues

        # Categorize by severity
        errors = [i for i in all_issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in all_issues if i.severity == IssueSeverity.WARNING]
        info = [i for i in all_issues if i.severity == IssueSeverity.INFO]
        hints = [i for i in all_issues if i.severity == IssueSeverity.HINT]

        # Calculate component scores
        pylint_score = pylint_result.get('score', 5.0)  # 0-10 scale
        pylint_normalized = pylint_score / 10.0  # Normalize to 0-1

        flake8_violations = flake8_result.get('count', 0)
        flake8_score = max(0.0, 1.0 - (flake8_violations / self.flake8_max_violations))

        mypy_errors_count = mypy_result.get('count', 0)
        mypy_score = max(0.0, 1.0 - (mypy_errors_count / self.mypy_max_errors))

        # Weighted overall score
        overall = (
            pylint_normalized * 0.5 +
            flake8_score * 0.25 +
            mypy_score * 0.25
        )

        return StaticAnalysisScore(
            overall=round(overall, 3),
            pylint_score=round(pylint_score, 2),
            flake8_violations=flake8_violations,
            mypy_errors=mypy_errors_count,
            errors=errors,
            warnings=warnings,
            info=info,
            hints=hints,
            total_issues=len(all_issues),
            passed=overall >= 0.7,
            pylint_details=pylint_result,
            flake8_details={'violations': flake8_result.get('violations', [])},
            mypy_details={'errors': mypy_result.get('errors', [])}
        )

    def _create_default_score(self) -> StaticAnalysisScore:
        """Create neutral score when evaluation fails"""
        return StaticAnalysisScore(
            overall=0.5,
            pylint_score=5.0,
            flake8_violations=0,
            mypy_errors=0,
            passed=False
        )

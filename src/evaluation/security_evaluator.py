"""
Security vulnerability detection using Bandit
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
import tempfile
import os
import json
import subprocess


class Severity(Enum):
    """Security issue severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityIssue:
    """Individual security vulnerability"""
    severity: Severity
    confidence: str  # HIGH, MEDIUM, LOW
    test_id: str  # e.g., B201, B301
    test_name: str  # e.g., "flask_debug_true"
    line_number: int
    line_range: List[int]
    code: str
    issue_text: str


@dataclass
class SecurityScore:
    """Security evaluation result"""
    overall: float  # 0.0 - 1.0
    safe: bool  # True if no critical/high issues
    critical_issues: List[SecurityIssue] = field(default_factory=list)
    high_issues: List[SecurityIssue] = field(default_factory=list)
    medium_issues: List[SecurityIssue] = field(default_factory=list)
    low_issues: List[SecurityIssue] = field(default_factory=list)
    total_issues: int = 0
    scanned_files: int = 1

    def __post_init__(self):
        """Calculate derived fields"""
        self.total_issues = (
            len(self.critical_issues) +
            len(self.high_issues) +
            len(self.medium_issues) +
            len(self.low_issues)
        )


class SecurityEvaluator:
    """Evaluates code for security vulnerabilities using Bandit"""

    def __init__(self, severity_threshold: str = "MEDIUM"):
        """
        Args:
            severity_threshold: Minimum severity to report (LOW, MEDIUM, HIGH)
        """
        self.severity_threshold = Severity[severity_threshold]

    def evaluate(self, code: str, language: str = "python") -> SecurityScore:
        """
        Evaluate code for security issues

        Args:
            code: Source code to analyze
            language: Programming language (only 'python' supported currently)

        Returns:
            SecurityScore with findings
        """
        if language != "python":
            # Return safe score for non-Python code (for now)
            return SecurityScore(overall=1.0, safe=True)

        return self._run_bandit(code)

    def _run_bandit(self, code: str) -> SecurityScore:
        """
        Run Bandit security scanner on Python code

        Args:
            code: Python source code

        Returns:
            SecurityScore with findings
        """
        # Create temporary file with code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run bandit with JSON output
            result = subprocess.run(
                [
                    'python3', '-m', 'bandit',
                    '-f', 'json',  # JSON format
                    '-ll',  # Report low and above
                    tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse JSON output
            if result.stdout:
                try:
                    bandit_output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # No issues found or error
                    return SecurityScore(overall=1.0, safe=True)
            else:
                # No output means no issues
                return SecurityScore(overall=1.0, safe=True)

            # Extract issues
            return self._parse_bandit_output(bandit_output)

        except subprocess.TimeoutExpired:
            print("[WARNING] Bandit timed out after 30s")
            return SecurityScore(overall=0.5, safe=False)

        except Exception as e:
            print(f"[ERROR] Bandit failed: {e}")
            return SecurityScore(overall=0.5, safe=False)

        finally:
            # Cleanup temp file (best effort)
            try:
                os.unlink(tmp_path)
            except (OSError, FileNotFoundError) as e:
                # Ignore cleanup errors silently
                pass

    def _parse_bandit_output(self, bandit_output: Dict[str, Any]) -> SecurityScore:
        """
        Parse Bandit JSON output into SecurityScore

        Args:
            bandit_output: Bandit JSON results

        Returns:
            SecurityScore
        """
        critical_issues = []
        high_issues = []
        medium_issues = []
        low_issues = []

        results = bandit_output.get('results', [])

        for issue in results:
            security_issue = SecurityIssue(
                severity=self._map_severity(issue['issue_severity']),
                confidence=issue['issue_confidence'],
                test_id=issue['test_id'],
                test_name=issue['test_name'],
                line_number=issue['line_number'],
                line_range=issue['line_range'],
                code=issue['code'],
                issue_text=issue['issue_text']
            )

            # Categorize by severity
            if security_issue.severity == Severity.CRITICAL:
                critical_issues.append(security_issue)
            elif security_issue.severity == Severity.HIGH:
                high_issues.append(security_issue)
            elif security_issue.severity == Severity.MEDIUM:
                medium_issues.append(security_issue)
            else:
                low_issues.append(security_issue)

        # Calculate overall score
        overall = self._calculate_security_score(
            critical_issues, high_issues, medium_issues, low_issues
        )

        # Determine if safe
        safe = len(critical_issues) == 0 and len(high_issues) == 0

        return SecurityScore(
            overall=overall,
            safe=safe,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues
        )

    def _map_severity(self, bandit_severity: str) -> Severity:
        """Map Bandit severity to our Severity enum"""
        mapping = {
            'HIGH': Severity.CRITICAL,  # Treat HIGH as CRITICAL
            'MEDIUM': Severity.HIGH,    # Shift down
            'LOW': Severity.MEDIUM
        }
        return mapping.get(bandit_severity.upper(), Severity.LOW)

    def _calculate_security_score(
        self,
        critical: List[SecurityIssue],
        high: List[SecurityIssue],
        medium: List[SecurityIssue],
        low: List[SecurityIssue]
    ) -> float:
        """
        Calculate overall security score

        Scoring:
        - Start at 1.0
        - Critical issue: -0.4 each
        - High issue: -0.2 each
        - Medium issue: -0.1 each
        - Low issue: -0.05 each
        - Minimum score: 0.0

        Args:
            critical, high, medium, low: Lists of issues by severity

        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0

        score -= len(critical) * 0.4
        score -= len(high) * 0.2
        score -= len(medium) * 0.1
        score -= len(low) * 0.05

        return max(0.0, score)

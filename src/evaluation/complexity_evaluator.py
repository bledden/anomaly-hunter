"""
Complexity Evaluator - Code complexity and maintainability analysis

Uses radon to measure:
- Cyclomatic Complexity (CC): Number of independent code paths
- Maintainability Index (MI): 0-100 score for code maintainability
- Halstead metrics: Volume, difficulty, effort

Provides actionable scoring for production code quality.
"""

import json
import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ComplexityRank(Enum):
    """Radon cyclomatic complexity ranks"""
    A = "A"  # CC 1-5: Simple, low risk
    B = "B"  # CC 6-10: Well structured, low risk
    C = "C"  # CC 11-20: Moderate complexity, medium risk
    D = "D"  # CC 21-30: High complexity, high risk
    E = "E"  # CC 31-40: Very high complexity, very high risk
    F = "F"  # CC 41+: Extremely high complexity, unmaintainable


class MaintainabilityRank(Enum):
    """Maintainability Index ranks"""
    A = "A"  # MI 20-100: Highly maintainable
    B = "B"  # MI 10-19: Moderately maintainable
    C = "C"  # MI 0-9: Difficult to maintain


@dataclass
class FunctionComplexity:
    """Complexity metrics for a single function"""
    name: str
    lineno: int
    complexity: int  # Cyclomatic complexity
    rank: ComplexityRank
    closures: int = 0  # Number of nested functions
    classname: Optional[str] = None


@dataclass
class MaintainabilityScore:
    """Maintainability index for a file or block"""
    score: float  # 0-100 scale
    rank: MaintainabilityRank


@dataclass
class ComplexityScore:
    """Comprehensive complexity analysis results"""
    overall: float  # 0.0 - 1.0 normalized score
    average_complexity: float  # Average CC across all functions
    max_complexity: int  # Highest CC found
    maintainability_index: float  # 0-100 MI score

    total_functions: int = 0
    high_complexity_functions: List[FunctionComplexity] = field(default_factory=list)
    all_functions: List[FunctionComplexity] = field(default_factory=list)

    # Rank distribution
    rank_a_count: int = 0  # Simple (CC 1-5)
    rank_b_count: int = 0  # Well-structured (CC 6-10)
    rank_c_count: int = 0  # Moderate (CC 11-20)
    rank_d_count: int = 0  # High (CC 21-30)
    rank_e_count: int = 0  # Very high (CC 31-40)
    rank_f_count: int = 0  # Unmaintainable (CC 41+)

    maintainability_rank: MaintainabilityRank = MaintainabilityRank.A
    passed: bool = True  # True if overall >= 0.7


class ComplexityEvaluator:
    """
    Complexity evaluator using radon for cyclomatic complexity and maintainability.

    Scoring algorithm:
    1. Maintainability Index (0-100) → normalized to 0-1 (weight: 60%)
    2. Average Complexity penalty → (weight: 25%)
       - CC 1-5: 1.0
       - CC 6-10: 0.9
       - CC 11-20: 0.7
       - CC 21-30: 0.4
       - CC 31+: 0.0
    3. Max Complexity penalty → (weight: 15%)
       - Max CC < 10: 1.0
       - Max CC < 20: 0.7
       - Max CC < 30: 0.4
       - Max CC >= 30: 0.0

    Final score = (MI_norm * 0.6) + (avg_score * 0.25) + (max_score * 0.15)
    """

    def __init__(
        self,
        max_acceptable_complexity: int = 10,
        min_maintainability: float = 20.0,
        timeout: int = 30
    ):
        """
        Initialize evaluator with thresholds.

        Args:
            max_acceptable_complexity: Max cyclomatic complexity before penalty
            min_maintainability: Min maintainability index (0-100)
            timeout: Max seconds for radon execution
        """
        self.max_acceptable_complexity = max_acceptable_complexity
        self.min_maintainability = min_maintainability
        self.timeout = timeout

    def evaluate(self, code: str, language: str = "python") -> ComplexityScore:
        """
        Run complexity analysis on code.

        Args:
            code: Source code to analyze
            language: Programming language (only 'python' supported)

        Returns:
            ComplexityScore with comprehensive metrics
        """
        if language.lower() != "python":
            logger.warning(f"Complexity analysis only supports Python, got: {language}")
            return self._create_default_score()

        try:
            # Run radon for complexity and maintainability
            cc_result = self._run_cyclomatic_complexity(code)
            mi_result = self._run_maintainability_index(code)

            # Combine results
            return self._combine_results(cc_result, mi_result)

        except Exception as e:
            logger.error(f"Complexity evaluation failed: {e}", exc_info=True)
            return self._create_default_score()

    def _run_cyclomatic_complexity(self, code: str) -> Dict[str, Any]:
        """Run radon cc (cyclomatic complexity) and return parsed results"""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run radon cc with JSON output
            result = subprocess.run(
                ['python3', '-m', 'radon', 'cc', '-j', tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse JSON output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # radon returns {filepath: [function_data, ...]}
                    functions = data.get(tmp_path, [])
                    return {'functions': functions}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse radon cc JSON output")
                    return {'functions': []}
            else:
                return {'functions': []}

        except subprocess.TimeoutExpired:
            logger.warning("Radon CC timed out")
            return {'functions': []}
        except Exception as e:
            logger.error(f"Radon CC execution failed: {e}")
            return {'functions': []}
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _run_maintainability_index(self, code: str) -> Dict[str, Any]:
        """Run radon mi (maintainability index) and return parsed results"""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run radon mi with JSON output
            result = subprocess.run(
                ['python3', '-m', 'radon', 'mi', '-j', tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse JSON output
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # radon returns {filepath: {...}}
                    mi_data = data.get(tmp_path, {})
                    mi_score = mi_data.get('mi', 100.0)
                    rank = mi_data.get('rank', 'A')
                    return {'score': mi_score, 'rank': rank}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse radon mi JSON output")
                    return {'score': 100.0, 'rank': 'A'}
            else:
                return {'score': 100.0, 'rank': 'A'}

        except subprocess.TimeoutExpired:
            logger.warning("Radon MI timed out")
            return {'score': 100.0, 'rank': 'A'}
        except Exception as e:
            logger.error(f"Radon MI execution failed: {e}")
            return {'score': 100.0, 'rank': 'A'}
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _parse_complexity_functions(self, functions: List[Dict]) -> List[FunctionComplexity]:
        """Convert radon function data to FunctionComplexity objects"""
        parsed = []
        for func in functions:
            # Radon function structure:
            # {
            #   "type": "function" | "method",
            #   "name": "function_name",
            #   "lineno": 10,
            #   "col_offset": 0,
            #   "endline": 20,
            #   "complexity": 5,
            #   "rank": "A",
            #   "closures": [],
            #   "classname": "ClassName" (optional)
            # }
            try:
                rank_str = func.get('rank', 'A')
                rank = ComplexityRank[rank_str] if rank_str in ComplexityRank.__members__ else ComplexityRank.A

                parsed.append(FunctionComplexity(
                    name=func.get('name', 'unknown'),
                    lineno=func.get('lineno', 0),
                    complexity=func.get('complexity', 1),
                    rank=rank,
                    closures=len(func.get('closures', [])),
                    classname=func.get('classname')
                ))
            except Exception as e:
                logger.warning(f"Failed to parse function complexity: {e}")
                continue

        return parsed

    def _calculate_rank_distribution(self, functions: List[FunctionComplexity]) -> Dict[str, int]:
        """Count functions by complexity rank"""
        distribution = {
            'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0
        }
        for func in functions:
            distribution[func.rank.value] += 1
        return distribution

    def _calculate_average_complexity_score(self, avg_cc: float) -> float:
        """Convert average CC to 0-1 score"""
        if avg_cc <= 5:
            return 1.0
        elif avg_cc <= 10:
            return 0.9
        elif avg_cc <= 20:
            return 0.7
        elif avg_cc <= 30:
            return 0.4
        else:
            return 0.0

    def _calculate_max_complexity_score(self, max_cc: int) -> float:
        """Convert max CC to 0-1 score"""
        if max_cc < 10:
            return 1.0
        elif max_cc < 20:
            return 0.7
        elif max_cc < 30:
            return 0.4
        else:
            return 0.0

    def _combine_results(
        self,
        cc_result: Dict,
        mi_result: Dict
    ) -> ComplexityScore:
        """Combine complexity and maintainability results into unified score"""
        # Parse functions
        functions = self._parse_complexity_functions(cc_result.get('functions', []))

        # Calculate metrics
        if functions:
            complexities = [f.complexity for f in functions]
            avg_complexity = sum(complexities) / len(complexities)
            max_complexity = max(complexities)
        else:
            avg_complexity = 1.0
            max_complexity = 1

        # Get maintainability
        mi_score = mi_result.get('score', 100.0)
        mi_rank_str = mi_result.get('rank', 'A')
        mi_rank = MaintainabilityRank[mi_rank_str] if mi_rank_str in MaintainabilityRank.__members__ else MaintainabilityRank.A

        # Calculate component scores
        mi_normalized = min(100.0, max(0.0, mi_score)) / 100.0  # Normalize to 0-1
        avg_score = self._calculate_average_complexity_score(avg_complexity)
        max_score = self._calculate_max_complexity_score(max_complexity)

        # Weighted overall score
        overall = (
            mi_normalized * 0.6 +
            avg_score * 0.25 +
            max_score * 0.15
        )

        # Identify high complexity functions (CC > max_acceptable)
        high_complexity = [f for f in functions if f.complexity > self.max_acceptable_complexity]

        # Rank distribution
        distribution = self._calculate_rank_distribution(functions)

        return ComplexityScore(
            overall=round(overall, 3),
            average_complexity=round(avg_complexity, 2),
            max_complexity=max_complexity,
            maintainability_index=round(mi_score, 2),
            total_functions=len(functions),
            high_complexity_functions=high_complexity,
            all_functions=functions,
            rank_a_count=distribution['A'],
            rank_b_count=distribution['B'],
            rank_c_count=distribution['C'],
            rank_d_count=distribution['D'],
            rank_e_count=distribution['E'],
            rank_f_count=distribution['F'],
            maintainability_rank=mi_rank,
            passed=overall >= 0.7 and mi_score >= self.min_maintainability
        )

    def _create_default_score(self) -> ComplexityScore:
        """Create neutral score when evaluation fails"""
        return ComplexityScore(
            overall=0.5,
            average_complexity=10.0,
            max_complexity=10,
            maintainability_index=50.0,
            maintainability_rank=MaintainabilityRank.B,
            passed=False
        )

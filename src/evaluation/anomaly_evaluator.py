"""
Anomaly Detection Evaluator
Validates detection accuracy using ground truth labels
"""

import json
import csv
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np


class DetectionMetric(Enum):
    """Metrics for anomaly detection quality"""
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    FALSE_POSITIVE_RATE = "false_positive_rate"
    SEVERITY_ACCURACY = "severity_accuracy"
    EXPLANATION_QUALITY = "explanation_quality"


@dataclass
class AnomalyEvaluationScore:
    """Evaluation result for anomaly detection"""
    overall: float  # 0.0 - 1.0
    precision: float  # True positives / (True positives + False positives)
    recall: float  # True positives / (True positives + False negatives)
    f1_score: float  # Harmonic mean of precision and recall
    false_positive_rate: float  # False positives / Total negatives
    severity_accuracy: float  # How close predicted severity to expected
    explanation_quality: float  # LLM judge score for explanation

    metrics: Dict[str, float]
    details: Dict[str, Any]
    passed: bool  # Pass if F1 >= 0.7
    confidence: str = "high"


class AnomalyDetectionEvaluator:
    """
    Evaluates anomaly detection quality using ground truth

    Ground truth format (CSV):
    - timestamp, value, metric, source, is_anomaly, expected_severity

    Or define expected anomaly windows:
    - scenario_name: {"anomaly_ranges": [(start, end), ...], "expected_severity": 8}
    """

    def __init__(self, pass_threshold: float = 0.7):
        self.pass_threshold = pass_threshold

        # Known ground truth for demo scenarios
        self.ground_truth = {
            "data_database_spike.csv": {
                "anomaly_ranges": [(100, 115)],  # Hours 100-115
                "expected_severity": 8,
                "scenario_type": "spike"
            },
            "data_api_latency_drift.csv": {
                "anomaly_ranges": [(150, 300)],  # Points 150-300 (drift + spikes)
                "expected_severity": 6,
                "scenario_type": "drift"
            },
            "data_cache_miss.csv": {
                "anomaly_ranges": [(80, 110), (170, 200)],  # Two spike events
                "expected_severity": 6,
                "scenario_type": "spike"
            },
            "data_disk_saturation.csv": {
                "anomaly_ranges": [(120, 140)],  # Hours 120-140
                "expected_severity": 8,
                "scenario_type": "sustained"
            },
            "data_network_loss.csv": {
                "anomaly_ranges": [(100, 115), (200, 210), (320, 350)],  # 3 bursts
                "expected_severity": 9,
                "scenario_type": "burst"
            },
            "data_error_spike.csv": {
                "anomaly_ranges": [(150, 190)],  # Points 150-190
                "expected_severity": 7,
                "scenario_type": "spike"
            },
            "data_memory_leak.csv": {
                "anomaly_ranges": [(200, 480)],  # Points 200-480 (leak until crash)
                "expected_severity": 9,
                "scenario_type": "drift"
            }
        }

    def evaluate(
        self,
        detected_indices: List[int],
        detected_severity: int,
        explanation: str,
        scenario_name: str,
        total_points: int
    ) -> AnomalyEvaluationScore:
        """
        Evaluate detection against ground truth

        Args:
            detected_indices: Indices flagged as anomalies
            detected_severity: Predicted severity (1-10)
            explanation: Agent explanation text
            scenario_name: Name of scenario (e.g., "data_network_loss.csv")
            total_points: Total data points in dataset

        Returns:
            AnomalyEvaluationScore with metrics
        """
        if scenario_name not in self.ground_truth:
            # Unknown scenario, return neutral score
            return self._create_default_score()

        gt = self.ground_truth[scenario_name]

        # Build ground truth set of anomaly indices
        true_anomalies = set()
        for start, end in gt["anomaly_ranges"]:
            true_anomalies.update(range(start, end + 1))

        # Build predicted set
        predicted_anomalies = set(detected_indices)

        # Calculate detection metrics
        precision, recall, f1, fpr = self._calculate_detection_metrics(
            predicted_anomalies,
            true_anomalies,
            total_points
        )

        # Calculate severity accuracy
        severity_accuracy = self._calculate_severity_accuracy(
            detected_severity,
            gt["expected_severity"]
        )

        # Score explanation quality (simple heuristic for now)
        explanation_quality = self._score_explanation(
            explanation,
            gt["scenario_type"]
        )

        # Overall score (weighted average)
        weights = {
            "precision": 0.25,
            "recall": 0.25,
            "f1_score": 0.30,
            "severity_accuracy": 0.10,
            "explanation_quality": 0.10
        }

        overall = (
            precision * weights["precision"] +
            recall * weights["recall"] +
            f1 * weights["f1_score"] +
            severity_accuracy * weights["severity_accuracy"] +
            explanation_quality * weights["explanation_quality"]
        )

        return AnomalyEvaluationScore(
            overall=round(overall, 3),
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1_score=round(f1, 3),
            false_positive_rate=round(fpr, 3),
            severity_accuracy=round(severity_accuracy, 3),
            explanation_quality=round(explanation_quality, 3),
            metrics={
                "true_positives": len(predicted_anomalies & true_anomalies),
                "false_positives": len(predicted_anomalies - true_anomalies),
                "false_negatives": len(true_anomalies - predicted_anomalies),
                "true_negatives": total_points - len(predicted_anomalies | true_anomalies)
            },
            details={
                "scenario": scenario_name,
                "expected_severity": gt["expected_severity"],
                "detected_severity": detected_severity,
                "scenario_type": gt["scenario_type"],
                "ground_truth_ranges": gt["anomaly_ranges"]
            },
            passed=f1 >= self.pass_threshold,
            confidence="high"
        )

    def _calculate_detection_metrics(
        self,
        predicted: set,
        actual: set,
        total_points: int
    ) -> Tuple[float, float, float, float]:
        """Calculate precision, recall, F1, FPR"""

        tp = len(predicted & actual)  # True positives
        fp = len(predicted - actual)  # False positives
        fn = len(actual - predicted)  # False negatives
        tn = total_points - len(predicted | actual)  # True negatives

        # Precision: TP / (TP + FP)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        # Recall: TP / (TP + FN)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # F1 Score: 2 * (precision * recall) / (precision + recall)
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # False Positive Rate: FP / (FP + TN)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        return precision, recall, f1, fpr

    def _calculate_severity_accuracy(self, predicted: int, expected: int) -> float:
        """Score how close predicted severity is to expected (0.0-1.0)"""
        diff = abs(predicted - expected)

        # Perfect match = 1.0, off by 1 = 0.9, off by 2 = 0.7, etc.
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.9
        elif diff == 2:
            return 0.7
        elif diff == 3:
            return 0.5
        else:
            return 0.3

    def _score_explanation(self, explanation: str, scenario_type: str) -> float:
        """Score explanation quality (simple heuristic)"""
        score = 0.5  # Base score

        explanation_lower = explanation.lower()

        # Check for key terms based on scenario type
        if scenario_type == "spike":
            if any(term in explanation_lower for term in ["spike", "sudden", "burst"]):
                score += 0.2
        elif scenario_type == "drift":
            if any(term in explanation_lower for term in ["drift", "gradual", "trend", "leak"]):
                score += 0.2
        elif scenario_type == "sustained":
            if any(term in explanation_lower for term in ["sustained", "prolonged", "saturat"]):
                score += 0.2
        elif scenario_type == "burst":
            if any(term in explanation_lower for term in ["burst", "intermittent", "multiple"]):
                score += 0.2

        # Check for confidence/evidence mentioned
        if any(term in explanation_lower for term in ["confidence", "evidence", "correlation"]):
            score += 0.15

        # Check for root cause hypothesis
        if any(term in explanation_lower for term in ["root cause", "hypothesis", "caused by"]):
            score += 0.15

        return min(score, 1.0)

    def _create_default_score(self) -> AnomalyEvaluationScore:
        """Create neutral score when ground truth unavailable"""
        return AnomalyEvaluationScore(
            overall=0.5,
            precision=0.5,
            recall=0.5,
            f1_score=0.5,
            false_positive_rate=0.5,
            severity_accuracy=0.5,
            explanation_quality=0.5,
            metrics={},
            details={"note": "No ground truth available"},
            passed=False,
            confidence="low"
        )


def evaluate_all_scenarios(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate all scenario results and generate summary

    Args:
        results: Dict mapping scenario_name -> verdict

    Returns:
        Summary with aggregate metrics
    """
    evaluator = AnomalyDetectionEvaluator()

    scenario_scores = {}
    all_scores = []

    for scenario_name, verdict in results.items():
        score = evaluator.evaluate(
            detected_indices=verdict.get("anomalies_detected", []),
            detected_severity=verdict.get("severity", 0),
            explanation=verdict.get("summary", ""),
            scenario_name=scenario_name,
            total_points=verdict.get("total_points", 0)
        )

        scenario_scores[scenario_name] = score
        all_scores.append(score)

    # Calculate aggregate metrics
    avg_precision = np.mean([s.precision for s in all_scores])
    avg_recall = np.mean([s.recall for s in all_scores])
    avg_f1 = np.mean([s.f1_score for s in all_scores])
    avg_fpr = np.mean([s.false_positive_rate for s in all_scores])

    pass_rate = sum(1 for s in all_scores if s.passed) / len(all_scores)

    return {
        "scenario_scores": {k: asdict(v) for k, v in scenario_scores.items()},
        "aggregate_metrics": {
            "precision": round(avg_precision, 3),
            "recall": round(avg_recall, 3),
            "f1_score": round(avg_f1, 3),
            "false_positive_rate": round(avg_fpr, 3),
            "pass_rate": round(pass_rate, 3)
        },
        "summary": {
            "total_scenarios": len(all_scores),
            "scenarios_passed": sum(1 for s in all_scores if s.passed),
            "overall_quality": "EXCELLENT" if avg_f1 >= 0.85 else "GOOD" if avg_f1 >= 0.7 else "NEEDS_IMPROVEMENT"
        }
    }


# Quick test
if __name__ == "__main__":
    evaluator = AnomalyDetectionEvaluator()

    # Test case: Network loss scenario
    score = evaluator.evaluate(
        detected_indices=list(range(100, 116)) + list(range(200, 211)) + list(range(320, 351)),
        detected_severity=9,
        explanation="Multiple spike clusters detected. Root cause hypothesis: Hardware failure causing intermittent packet loss.",
        scenario_name="data_network_loss.csv",
        total_points=400
    )

    print("Network Loss Evaluation:")
    print(f"  Precision: {score.precision:.2%}")
    print(f"  Recall: {score.recall:.2%}")
    print(f"  F1 Score: {score.f1_score:.2%}")
    print(f"  FPR: {score.false_positive_rate:.2%}")
    print(f"  Overall: {score.overall:.2%}")
    print(f"  Passed: {score.passed}")

"""
Autonomous Continuous Learning System
Self-improvement through feedback loops and pattern recognition
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class AutonomousLearner:
    """
    Autonomous Learning Engine

    Continuously improves detection accuracy by:
    1. Tracking agent performance over time
    2. Adjusting confidence weights based on outcomes
    3. Learning from user feedback (implicit/explicit)
    4. Storing successful detection strategies
    """

    def __init__(self, cache_dir: str = "backend/cache/learning"):
        """Initialize autonomous learner"""

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.performance_log = self.cache_dir / "agent_performance.json"
        self.strategy_cache = self.cache_dir / "successful_strategies.json"

        # Load historical performance
        self.agent_stats = self._load_performance_log()
        self.successful_strategies = self._load_strategies()

        print("[LEARNING] 🧠 Autonomous learning engine initialized")
        print(f"[LEARNING]   └─ Historical detections: {self.agent_stats.get('total_detections', 0)}")

    def _load_performance_log(self) -> Dict[str, Any]:
        """Load agent performance history"""
        if self.performance_log.exists():
            with open(self.performance_log, 'r') as f:
                return json.load(f)
        return {
            "total_detections": 0,
            "agents": {
                "pattern_analyst": {"correct": 0, "total": 0, "avg_confidence": 0.8},
                "change_detective": {"correct": 0, "total": 0, "avg_confidence": 0.9},
                "root_cause": {"correct": 0, "total": 0, "avg_confidence": 0.75}
            }
        }

    def _load_strategies(self) -> List[Dict[str, Any]]:
        """Load successful detection strategies"""
        if self.strategy_cache.exists():
            with open(self.strategy_cache, 'r') as f:
                return json.load(f)
        return []

    def compute_adaptive_weights(self, current_findings: List[Any]) -> Dict[str, float]:
        """
        Compute adaptive confidence weights based on historical performance

        Better-performing agents get higher weights over time
        """

        weights = {}
        total_performance = 0

        for finding in current_findings:
            agent_name = finding.agent_name
            stats = self.agent_stats["agents"].get(agent_name, {})

            # Calculate performance score
            total = stats.get("total", 1)
            correct = stats.get("correct", 0)
            accuracy = correct / total if total > 0 else 0.5

            # Weight = historical accuracy * current confidence
            adaptive_weight = accuracy * finding.confidence
            weights[agent_name] = adaptive_weight
            total_performance += adaptive_weight

        # Normalize weights
        if total_performance > 0:
            weights = {k: v/total_performance for k, v in weights.items()}

        print(f"[LEARNING] 📊 Adaptive weights computed:")
        for agent, weight in weights.items():
            print(f"[LEARNING]   └─ {agent}: {weight:.3f}")

        return weights

    def learn_from_outcome(self, verdict: Any, user_feedback: Optional[str] = None,
                          was_correct: Optional[bool] = None) -> None:
        """
        Learn from detection outcome

        Args:
            verdict: Detection verdict
            user_feedback: Optional user feedback
            was_correct: Whether the detection was accurate (if known)
        """

        # Update total detections
        self.agent_stats["total_detections"] += 1

        # Update per-agent stats
        for finding in verdict.agent_findings:
            agent_name = finding.agent_name
            agent_stats = self.agent_stats["agents"][agent_name]

            agent_stats["total"] += 1

            # If we know the outcome was correct, update accuracy
            if was_correct is not None:
                if was_correct:
                    agent_stats["correct"] += 1

            # Update average confidence (exponential moving average)
            alpha = 0.1  # Learning rate
            old_avg = agent_stats["avg_confidence"]
            agent_stats["avg_confidence"] = old_avg * (1 - alpha) + finding.confidence * alpha

        # Save updated stats
        self._save_performance_log()

        # Extract successful strategy if high confidence
        if verdict.confidence > 0.85:
            self._extract_successful_strategy(verdict)

        print(f"[LEARNING] ✅ Learned from detection #{self.agent_stats['total_detections']}")

    def _extract_successful_strategy(self, verdict: Any) -> None:
        """Extract and store successful detection strategy"""

        strategy = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": verdict.severity,
            "confidence": verdict.confidence,
            "pattern": {
                "anomaly_count": len(verdict.anomalies_detected),
                "agent_agreement": self._compute_agent_agreement(verdict),
            },
            "approach": verdict.summary[:200]  # Store successful approach
        }

        self.successful_strategies.append(strategy)

        # Keep only last 100 strategies
        if len(self.successful_strategies) > 100:
            self.successful_strategies = self.successful_strategies[-100:]

        self._save_strategies()
        print(f"[LEARNING] 💾 Stored successful strategy (total: {len(self.successful_strategies)})")

    def _compute_agent_agreement(self, verdict: Any) -> float:
        """Compute how much agents agreed on severity"""

        severities = [f.severity for f in verdict.agent_findings]
        if not severities:
            return 0.0

        mean_severity = sum(severities) / len(severities)
        variance = sum((s - mean_severity) ** 2 for s in severities) / len(severities)

        # Low variance = high agreement
        agreement = 1.0 / (1.0 + variance)
        return agreement

    def suggest_improvements(self) -> List[str]:
        """
        Analyze performance and suggest improvements

        Returns:
            List of improvement suggestions
        """

        suggestions = []

        # Analyze agent performance
        for agent_name, stats in self.agent_stats["agents"].items():
            total = stats.get("total", 0)
            if total < 10:
                continue  # Not enough data

            accuracy = stats["correct"] / total if total > 0 else 0

            if accuracy < 0.7:
                suggestions.append(
                    f"⚠️  {agent_name} has low accuracy ({accuracy:.1%}). "
                    f"Consider adjusting thresholds or model parameters."
                )

            if stats["avg_confidence"] < 0.6:
                suggestions.append(
                    f"📉 {agent_name} shows low confidence ({stats['avg_confidence']:.1%}). "
                    f"May need additional training data or context."
                )

        # Check detection volume
        total = self.agent_stats["total_detections"]
        if total > 50:
            suggestions.append(
                f"📈 System has processed {total} detections. "
                f"Consider analyzing patterns for automation opportunities."
            )

        return suggestions

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""

        summary = {
            "total_detections": self.agent_stats["total_detections"],
            "agents": {},
            "learning_status": "active",
            "strategies_learned": len(self.successful_strategies)
        }

        for agent_name, stats in self.agent_stats["agents"].items():
            total = stats.get("total", 0)
            accuracy = stats["correct"] / total if total > 0 else 0

            summary["agents"][agent_name] = {
                "accuracy": accuracy,
                "confidence": stats["avg_confidence"],
                "total_inferences": total
            }

        return summary

    def _save_performance_log(self):
        """Save performance log to disk"""
        with open(self.performance_log, 'w') as f:
            json.dump(self.agent_stats, f, indent=2)

    def _save_strategies(self):
        """Save successful strategies to disk"""
        with open(self.strategy_cache, 'w') as f:
            json.dump(self.successful_strategies, f, indent=2)

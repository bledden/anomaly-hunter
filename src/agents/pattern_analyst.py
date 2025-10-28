"""
Pattern Analyst Agent
Role: Statistical anomaly detection using GPT-4
"""

import numpy as np
from typing import Dict, Any, Optional
from scipy import stats
import sentry_sdk

# Import Weave decorator from orchestrator
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestrator import weave_op_if_available


class PatternAnalyst:
    """
    Agent 1: Pattern Analyst

    Specialization: Statistical anomaly detection
    - Z-score analysis
    - Baseline comparison
    - Distribution analysis

    Model: GPT-4 Turbo (via StackAI)
    """

    def __init__(self, stackai_client=None):
        """
        Initialize Pattern Analyst

        Args:
            stackai_client: StackAI gateway for model routing
        """
        self.stackai = stackai_client
        self.model = "openai/gpt-5-pro"  # GPT-5 Pro via Stack AI
        self.name = "pattern_analyst"

    @weave_op_if_available()
    @sentry_sdk.trace
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data for statistical anomalies

        Args:
            context: Shared context with data, timestamps, metadata

        Returns:
            Finding dict with agent_name, finding, confidence, severity, evidence
        """
        with sentry_sdk.start_span(
            op="ai.agent.analyze",
            description="Pattern Analyst - Statistical Analysis"
        ) as agent_span:
            agent_span.set_data("agent", "pattern_analyst")
            agent_span.set_data("model", self.model)

            data = context.get("data")
            if data is None:
                return self._error_result("No data provided")

            agent_span.set_data("data_points", len(data))

            # Statistical analysis
            with sentry_sdk.start_span(
                op="statistics",
                description="Z-score and baseline analysis"
            ) as stats_span:
                stats_result = self._statistical_analysis(data)
                stats_span.set_data("anomalies_found", stats_result["anomaly_count"])
                stats_span.set_data("mean", stats_result["mean"])
                stats_span.set_data("std", stats_result["std"])

            # Build prompt for LLM
            prompt = self._build_prompt(stats_result, context)

            # Get LLM analysis (if StackAI available)
            with sentry_sdk.start_span(
                op="ai.llm.call",
                description=f"LLM analysis via {self.model}"
            ) as llm_span:
                llm_span.set_data("model", self.model)
                llm_span.set_data("prompt_length", len(prompt))

                llm_analysis = await self._get_llm_analysis(prompt)

                llm_span.set_data("response_length", len(llm_analysis))

            # Extract severity and confidence
            severity = self._extract_severity(llm_analysis)
            confidence = self._calculate_confidence(stats_result)

            agent_span.set_data("severity", severity)
            agent_span.set_data("confidence", confidence)

            return {
                "agent_name": self.name,
                "finding": self._format_finding(stats_result, llm_analysis),
                "confidence": confidence,
                "severity": severity,
                "evidence": {
                    "anomaly_indices": stats_result["anomaly_indices"],
                    "z_scores": stats_result["max_z_scores"],
                    "statistical_summary": stats_result["summary"]
                }
            }

    def _statistical_analysis(self, data: np.ndarray) -> Dict[str, Any]:
        """Perform statistical anomaly detection"""

        mean = float(np.mean(data))
        std = float(np.std(data))
        median = float(np.median(data))

        # Z-score analysis (threshold: 3 standard deviations)
        z_scores = np.abs((data - mean) / std) if std > 0 else np.zeros_like(data)
        anomaly_mask = z_scores > 3
        anomaly_indices = np.where(anomaly_mask)[0].tolist()

        # Max z-scores for top anomalies
        max_z_indices = np.argsort(z_scores)[-5:][::-1]  # Top 5
        max_z_scores = [(int(idx), float(z_scores[idx])) for idx in max_z_indices]

        return {
            "mean": mean,
            "std": std,
            "median": median,
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "anomaly_count": len(anomaly_indices),
            "anomaly_indices": anomaly_indices,
            "max_z_scores": max_z_scores,
            "summary": f"Mean: {mean:.2f}, Std: {std:.2f}, {len(anomaly_indices)} anomalies detected"
        }

    def _build_prompt(self, stats: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build prompt for GPT-4 analysis"""

        senso_context = context.get("senso_context", "")

        prompt = f"""You are a Pattern Analyst specializing in statistical anomaly detection.

DATA STATISTICS:
- Mean: {stats['mean']:.2f}
- Std Dev: {stats['std']:.2f}
- Median: {stats['median']:.2f}
- Range: [{stats['min']:.2f}, {stats['max']:.2f}]

ANOMALIES DETECTED: {stats['anomaly_count']} points
Indices: {stats['anomaly_indices'][:10]}  # Show first 10

TOP DEVIATIONS (Z-scores):
"""

        for idx, z_score in stats['max_z_scores'][:3]:
            prompt += f"- Index {idx}: Z-score = {z_score:.2f}\n"

        if senso_context:
            prompt += f"\nKNOWLEDGE BASE CONTEXT:\n{senso_context}\n"

        prompt += """
ANALYSIS REQUIRED:
1. Describe the anomaly pattern (spike, dip, drift, outlier)
2. Assess severity (1-10 scale)
3. Note if pattern matches known issues from knowledge base

Provide concise analysis (2-3 sentences) focusing on:
- Pattern type
- Severity justification
- Likely impact

Format:
Severity: [1-10]
Pattern: [description]
Impact: [description]
"""

        return prompt

    async def _get_llm_analysis(self, prompt: str) -> str:
        """Get analysis from GPT-4 via StackAI"""

        if not self.stackai:
            # Fallback: rule-based analysis
            return "Severity: 7\nPattern: Statistical anomalies detected\nImpact: Moderate deviation from baseline"

        try:
            response = await self.stackai.complete(
                model=self.model,
                prompt=prompt,
                temperature=0.7,
                max_tokens=500
            )
            return response
        except Exception as e:
            print(f"[WARN] StackAI call failed: {e}")
            return "Severity: 5\nPattern: Analysis unavailable\nImpact: Unable to determine"

    def _extract_severity(self, llm_response: str) -> int:
        """Extract severity score from LLM response"""

        import re
        match = re.search(r'severity[:\s]+(\d+)', llm_response.lower())
        if match:
            return min(10, max(1, int(match.group(1))))
        return 5  # Default

    def _calculate_confidence(self, stats: Dict[str, Any]) -> float:
        """Calculate confidence based on statistical evidence"""

        # Higher confidence if:
        # - More anomalies detected
        # - Higher z-scores
        # - Lower standard deviation (clearer signal)

        anomaly_count = stats["anomaly_count"]
        max_z = max([z for _, z in stats["max_z_scores"]], default=0)

        confidence = 0.5  # Base

        # Boost for strong z-scores
        if max_z > 5:
            confidence += 0.3
        elif max_z > 3:
            confidence += 0.2

        # Boost for multiple anomalies
        if anomaly_count > 3:
            confidence += 0.1

        return min(1.0, confidence)

    def _format_finding(self, stats: Dict[str, Any], llm_analysis: str) -> str:
        """Format final finding"""

        # Extract pattern line from LLM
        pattern_match = llm_analysis.split("Pattern:")
        if len(pattern_match) > 1:
            pattern = pattern_match[1].split("\n")[0].strip()
        else:
            pattern = "Statistical anomalies detected"

        finding = (
            f"{stats['anomaly_count']} anomalies detected. "
            f"{pattern}. "
            f"Top deviation: {stats['max_z_scores'][0][1]:.2f}σ above baseline."
        )

        return finding

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Return error result"""
        return {
            "agent_name": self.name,
            "finding": f"Error: {error_msg}",
            "confidence": 0.0,
            "severity": 0,
            "evidence": {}
        }

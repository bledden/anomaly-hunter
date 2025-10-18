"""
Change Detective Agent
Role: Time-series drift analysis using Claude
"""

import numpy as np
from typing import Dict, Any, Optional, List


class ChangeDetective:
    """
    Agent 2: Change Detective

    Specialization: Time-series change detection
    - Drift analysis
    - Change point detection
    - Trend analysis

    Model: Claude Sonnet 3.5 (via StackAI)
    """

    def __init__(self, stackai_client=None):
        """
        Initialize Change Detective

        Args:
            stackai_client: StackAI gateway for model routing
        """
        self.stackai = stackai_client
        self.model = "anthropic/claude-sonnet-4-5"  # Claude 4.5 Sonnet
        self.name = "change_detective"

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data for time-series changes

        Args:
            context: Shared context with data, timestamps, metadata

        Returns:
            Finding dict with agent_name, finding, confidence, severity, evidence
        """

        data = context.get("data")
        if data is None:
            return self._error_result("No data provided")

        # Time-series analysis
        change_result = self._change_point_analysis(data)

        # Build prompt for LLM
        prompt = self._build_prompt(change_result, context)

        # Get LLM analysis
        llm_analysis = await self._get_llm_analysis(prompt)

        # Extract severity and confidence
        severity = self._extract_severity(llm_analysis)
        confidence = self._calculate_confidence(change_result)

        return {
            "agent_name": self.name,
            "finding": self._format_finding(change_result, llm_analysis),
            "confidence": confidence,
            "severity": severity,
            "evidence": {
                "anomaly_indices": change_result["change_points"],
                "drift_detected": change_result["drift_detected"],
                "trend": change_result["trend"]
            }
        }

    def _change_point_analysis(self, data: np.ndarray) -> Dict[str, Any]:
        """Detect change points in time series"""

        # Simple moving average approach
        window = min(5, len(data) // 10)  # Adaptive window
        if window < 2:
            window = 2

        # Calculate moving average
        moving_avg = self._moving_average(data, window)

        # Detect abrupt changes (derivative analysis)
        changes = np.diff(moving_avg)
        change_threshold = 2 * np.std(changes) if np.std(changes) > 0 else 0.5

        change_points = []
        for i in range(len(changes)):
            if abs(changes[i]) > change_threshold:
                change_points.append(i + 1)  # +1 to account for diff offset

        # Drift detection (trend analysis)
        first_half = data[:len(data)//2]
        second_half = data[len(data)//2:]

        mean_first = float(np.mean(first_half))
        mean_second = float(np.mean(second_half))
        drift_percentage = ((mean_second - mean_first) / mean_first * 100) if mean_first != 0 else 0

        drift_detected = abs(drift_percentage) > 20  # 20% threshold

        # Overall trend
        if drift_percentage > 10:
            trend = "upward"
        elif drift_percentage < -10:
            trend = "downward"
        else:
            trend = "stable"

        return {
            "change_points": change_points[:10],  # Top 10
            "change_count": len(change_points),
            "drift_detected": drift_detected,
            "drift_percentage": drift_percentage,
            "trend": trend,
            "mean_first_half": mean_first,
            "mean_second_half": mean_second
        }

    def _moving_average(self, data: np.ndarray, window: int) -> np.ndarray:
        """Calculate simple moving average"""
        return np.convolve(data, np.ones(window)/window, mode='valid')

    def _build_prompt(self, change_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build prompt for Claude analysis"""

        senso_context = context.get("senso_context", "")

        prompt = f"""You are a Change Detective specializing in time-series drift analysis.

TIME-SERIES ANALYSIS:
- Change Points Detected: {change_result['change_count']}
- Drift: {"YES" if change_result['drift_detected'] else "NO"}
- Drift Magnitude: {change_result['drift_percentage']:.1f}%
- Overall Trend: {change_result['trend']}

COMPARATIVE METRICS:
- First Half Mean: {change_result['mean_first_half']:.2f}
- Second Half Mean: {change_result['mean_second_half']:.2f}

CHANGE POINT INDICES: {change_result['change_points'][:5]}  # Show first 5
"""

        if senso_context:
            prompt += f"\nKNOWLEDGE BASE CONTEXT:\n{senso_context}\n"

        prompt += """
ANALYSIS REQUIRED:
1. Characterize the change pattern (sudden spike, gradual drift, oscillation)
2. Assess severity (1-10 scale) based on:
   - Magnitude of change
   - Number of change points
   - Drift percentage
3. Correlate with potential causes

Provide concise analysis (2-3 sentences):
- Change pattern description
- Severity justification
- Potential trigger/cause

Format:
Severity: [1-10]
Pattern: [description]
Cause: [hypothesis]
"""

        return prompt

    async def _get_llm_analysis(self, prompt: str) -> str:
        """Get analysis from Claude via StackAI"""

        if not self.stackai:
            # Fallback: rule-based analysis
            return "Severity: 6\nPattern: Time-series changes detected\nCause: Unknown trigger event"

        try:
            response = await self.stackai.complete(
                model=self.model,
                prompt=prompt,
                temperature=0.5,
                max_tokens=400
            )
            return response
        except Exception as e:
            print(f"[WARN] StackAI call failed: {e}")
            return "Severity: 5\nPattern: Analysis unavailable\nCause: Unable to determine"

    def _extract_severity(self, llm_response: str) -> int:
        """Extract severity score from LLM response"""

        import re
        match = re.search(r'severity[:\s]+(\d+)', llm_response.lower())
        if match:
            return min(10, max(1, int(match.group(1))))
        return 5  # Default

    def _calculate_confidence(self, change_result: Dict[str, Any]) -> float:
        """Calculate confidence based on change evidence"""

        confidence = 0.5  # Base

        # Boost for strong drift
        if change_result["drift_detected"]:
            confidence += 0.2

        # Boost for multiple change points
        if change_result["change_count"] > 5:
            confidence += 0.2
        elif change_result["change_count"] > 2:
            confidence += 0.1

        # Boost for large drift percentage
        if abs(change_result["drift_percentage"]) > 50:
            confidence += 0.2
        elif abs(change_result["drift_percentage"]) > 30:
            confidence += 0.1

        return min(1.0, confidence)

    def _format_finding(self, change_result: Dict[str, Any], llm_analysis: str) -> str:
        """Format final finding"""

        # Extract pattern line from LLM
        pattern_match = llm_analysis.split("Pattern:")
        if len(pattern_match) > 1:
            pattern = pattern_match[1].split("\n")[0].strip()
        else:
            pattern = "Time-series changes detected"

        drift_status = "with drift" if change_result["drift_detected"] else "stable baseline"

        finding = (
            f"{change_result['change_count']} change points detected, {drift_status}. "
            f"{pattern}. "
            f"Drift magnitude: {change_result['drift_percentage']:.1f}%."
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

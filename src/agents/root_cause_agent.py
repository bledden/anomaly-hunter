"""
Root Cause Agent
Role: Hypothesis generation and root cause analysis using o1-mini
"""

import numpy as np
from typing import Dict, Any, Optional, List

# Import Weave decorator from orchestrator
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestrator import weave_op_if_available


class RootCauseAgent:
    """
    Agent 3: Root Cause Investigator

    Specialization: Root cause reasoning
    - Hypothesis generation
    - Evidence correlation
    - Confidence scoring

    Model: OpenAI o1-mini (via StackAI)
    """

    def __init__(self, stackai_client=None):
        """
        Initialize Root Cause Agent

        Args:
            stackai_client: StackAI gateway for model routing
        """
        self.stackai = stackai_client
        self.model = "anthropic/claude-sonnet-4-5"  # Claude 4.5 Sonnet via Stack AI
        self.name = "root_cause"

    @weave_op_if_available()
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze root cause of anomalies

        Args:
            context: Shared context with data, timestamps, metadata

        Returns:
            Finding dict with agent_name, finding, confidence, severity, evidence
        """

        data = context.get("data")
        if data is None:
            return self._error_result("No data provided")

        # Root cause analysis
        rc_result = self._root_cause_analysis(data, context)

        # Build prompt for LLM
        prompt = self._build_prompt(rc_result, context)

        # Get LLM analysis
        llm_analysis = await self._get_llm_analysis(prompt)

        # Extract severity and confidence
        severity = self._extract_severity(llm_analysis)
        confidence = self._calculate_confidence(rc_result, llm_analysis)

        return {
            "agent_name": self.name,
            "finding": self._format_finding(rc_result, llm_analysis),
            "confidence": confidence,
            "severity": severity,
            "evidence": {
                "anomaly_indices": rc_result["anomaly_clusters"],
                "hypotheses": rc_result["hypotheses"],
                "correlation_strength": rc_result["correlation_strength"]
            }
        }

    def _root_cause_analysis(self, data: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform root cause analysis"""

        # Cluster anomalies (temporal proximity)
        anomaly_indices = self._identify_anomalies(data)
        clusters = self._cluster_anomalies(anomaly_indices)

        # Correlation analysis
        correlation_strength = self._correlation_analysis(data)

        # Generate hypotheses based on patterns
        hypotheses = self._generate_hypotheses(data, clusters, context)

        return {
            "anomaly_clusters": clusters,
            "cluster_count": len(clusters),
            "hypotheses": hypotheses,
            "correlation_strength": correlation_strength
        }

    def _identify_anomalies(self, data: np.ndarray) -> List[int]:
        """Identify anomaly indices using IQR method"""

        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomalies = []
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                anomalies.append(i)

        return anomalies

    def _cluster_anomalies(self, anomaly_indices: List[int]) -> List[int]:
        """Cluster anomalies by temporal proximity"""

        if not anomaly_indices:
            return []

        # Simple clustering: anomalies within 5 indices are in same cluster
        clusters = []
        current_cluster = [anomaly_indices[0]]

        for i in range(1, len(anomaly_indices)):
            if anomaly_indices[i] - anomaly_indices[i-1] <= 5:
                current_cluster.append(anomaly_indices[i])
            else:
                clusters.append(current_cluster[0])  # Representative index
                current_cluster = [anomaly_indices[i]]

        if current_cluster:
            clusters.append(current_cluster[0])

        return clusters[:10]  # Top 10 clusters

    def _correlation_analysis(self, data: np.ndarray) -> float:
        """Analyze auto-correlation strength"""

        if len(data) < 10:
            return 0.0

        # Simple lag-1 autocorrelation
        data_mean = np.mean(data)
        numerator = np.sum((data[:-1] - data_mean) * (data[1:] - data_mean))
        denominator = np.sum((data - data_mean) ** 2)

        if denominator == 0:
            return 0.0

        correlation = numerator / denominator
        return float(abs(correlation))

    def _generate_hypotheses(
        self,
        data: np.ndarray,
        clusters: List[int],
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate root cause hypotheses"""

        hypotheses = []

        # Hypothesis 1: Based on anomaly pattern
        if len(clusters) == 1:
            hypotheses.append("Isolated incident - likely single event trigger")
        elif len(clusters) > 5:
            hypotheses.append("Recurring pattern - systematic issue or cyclic load")
        else:
            hypotheses.append("Multiple incidents - correlated events or cascading failure")

        # Hypothesis 2: Based on data characteristics
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val / mean_val > 0.5:  # High coefficient of variation
            hypotheses.append("High variance - resource contention or unstable system")
        else:
            hypotheses.append("Low variance - external trigger or input spike")

        # Hypothesis 3: From metadata (if available)
        metadata = context.get("metadata", {})
        if "source" in metadata:
            source = metadata["source"]
            hypotheses.append(f"Source: {source} - check upstream dependencies")

        return hypotheses

    def _build_prompt(self, rc_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build prompt for o1-mini reasoning"""

        senso_context = context.get("senso_context", "")

        prompt = f"""You are a Root Cause Investigator specializing in anomaly analysis.

ANOMALY CLUSTERS: {rc_result['cluster_count']} distinct clusters detected
Cluster Indices: {rc_result['anomaly_clusters']}

CORRELATION STRENGTH: {rc_result['correlation_strength']:.2f}
{'(Strong temporal correlation - likely systemic)' if rc_result['correlation_strength'] > 0.7 else '(Weak correlation - likely independent events)'}

INITIAL HYPOTHESES:
"""

        for i, hyp in enumerate(rc_result['hypotheses'], 1):
            prompt += f"{i}. {hyp}\n"

        if senso_context:
            prompt += f"\nKNOWLEDGE BASE CONTEXT:\n{senso_context}\n"

        prompt += """
REASONING TASK:
1. Evaluate the initial hypotheses against the evidence
2. Generate your strongest root cause hypothesis
3. Assign confidence score (0.0-1.0) based on:
   - Evidence strength
   - Pattern consistency
   - Knowledge base alignment
4. Assess severity (1-10) based on:
   - Impact scope
   - Recurrence likelihood
   - Urgency of resolution

Provide step-by-step reasoning (2-3 sentences):
1. Primary hypothesis
2. Supporting evidence
3. Confidence justification

Format:
Severity: [1-10]
Hypothesis: [your hypothesis]
Evidence: [supporting points]
Confidence: [0.0-1.0]
"""

        return prompt

    async def _get_llm_analysis(self, prompt: str) -> str:
        """Get reasoning from o1-mini via StackAI"""

        if not self.stackai:
            # Fallback: rule-based hypothesis
            return "Severity: 7\nHypothesis: System resource spike\nEvidence: Temporal clustering\nConfidence: 0.6"

        try:
            response = await self.stackai.complete(
                model=self.model,
                prompt=prompt,
                temperature=0.3,  # Lower for reasoning
                max_tokens=600
            )
            return response
        except Exception as e:
            print(f"[WARN] StackAI call failed: {e}")
            return "Severity: 5\nHypothesis: Unable to determine\nEvidence: Analysis failed\nConfidence: 0.3"

    def _extract_severity(self, llm_response: str) -> int:
        """Extract severity score from LLM response"""

        import re
        match = re.search(r'severity[:\s]+(\d+)', llm_response.lower())
        if match:
            return min(10, max(1, int(match.group(1))))
        return 6  # Default slightly higher (root cause = more serious)

    def _calculate_confidence(self, rc_result: Dict[str, Any], llm_response: str) -> float:
        """Calculate confidence based on evidence strength"""

        # Try to extract confidence from LLM response
        import re
        conf_match = re.search(r'confidence[:\s]+([\d.]+)', llm_response.lower())
        if conf_match:
            llm_confidence = float(conf_match.group(1))
        else:
            llm_confidence = 0.5

        # Adjust based on correlation strength
        correlation = rc_result["correlation_strength"]
        if correlation > 0.7:
            llm_confidence += 0.1
        elif correlation < 0.3:
            llm_confidence -= 0.1

        # Adjust based on hypothesis count (more = less confident)
        if len(rc_result["hypotheses"]) > 4:
            llm_confidence -= 0.1

        return min(1.0, max(0.0, llm_confidence))

    def _format_finding(self, rc_result: Dict[str, Any], llm_analysis: str) -> str:
        """Format final finding"""

        # Extract hypothesis from LLM
        hyp_match = llm_analysis.split("Hypothesis:")
        if len(hyp_match) > 1:
            hypothesis = hyp_match[1].split("\n")[0].strip()
        else:
            hypothesis = rc_result["hypotheses"][0] if rc_result["hypotheses"] else "Unknown root cause"

        finding = (
            f"Root cause hypothesis: {hypothesis}. "
            f"Evidence: {rc_result['cluster_count']} anomaly clusters, "
            f"correlation strength {rc_result['correlation_strength']:.2f}."
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

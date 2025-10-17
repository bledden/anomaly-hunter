"""
Anomaly Detection Orchestrator
Coordinates 3 specialized agents for autonomous anomaly investigation
Based on Corch sequential collaboration (73% quality pass rate)
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np

# Environment
from dotenv import load_dotenv
load_dotenv()

# Autonomous Learning
from learning.autonomous_learner import AutonomousLearner


@dataclass
class AnomalyContext:
    """Context for anomaly investigation"""
    data: np.ndarray
    timestamps: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    severity_threshold: int = 7  # 1-10 scale


@dataclass
class AgentFinding:
    """Result from a single agent"""
    agent_name: str
    finding: str
    confidence: float  # 0.0-1.0
    severity: int  # 1-10
    evidence: Dict[str, Any]
    timestamp: str


@dataclass
class AnomalyVerdict:
    """Final synthesized verdict"""
    severity: int  # 1-10
    summary: str
    confidence: float
    anomalies_detected: List[int]  # indices
    agent_findings: List[AgentFinding]
    recommendation: str
    timestamp: str


class AnomalyOrchestrator:
    """
    Orchestrates 3 specialized agents for anomaly detection

    Workflow:
    1. Pattern Analyst (GPT-4) - Statistical analysis
    2. Change Detective (Claude) - Time-series drift
    3. Root Cause Agent (o1-mini) - Hypothesis generation
    4. Synthesis - Confidence-weighted voting
    """

    def __init__(self, stackai_client=None):
        """
        Initialize orchestrator

        Args:
            stackai_client: StackAI gateway for model routing (optional)
        """
        self.stackai = stackai_client
        self.agents = []
        self.learner = AutonomousLearner()  # Autonomous learning engine
        self._load_agents()

    def _load_agents(self):
        """Lazy load agents to avoid import issues"""
        try:
            from agents.pattern_analyst import PatternAnalyst
            from agents.change_detective import ChangeDetective
            from agents.root_cause_agent import RootCauseAgent

            self.agents = [
                PatternAnalyst(self.stackai),
                ChangeDetective(self.stackai),
                RootCauseAgent(self.stackai)
            ]
            print(f"[OK] Loaded {len(self.agents)} agents")
        except ImportError as e:
            print(f"[WARN] Could not load agents: {e}")
            print("[INFO] Agents will be loaded when first needed")

    async def investigate(
        self,
        context: AnomalyContext,
        senso_context: Optional[str] = None
    ) -> AnomalyVerdict:
        """
        Run full anomaly investigation with all 3 agents

        Args:
            context: Anomaly detection context
            senso_context: Optional context from Senso knowledge base

        Returns:
            AnomalyVerdict with synthesized findings
        """
        print(f"\n[ORCHESTRATOR] Starting investigation of {len(context.data)} data points")

        # Step 1: Run all agents in parallel
        print("[STEP 1/3] Running agents in parallel...")
        findings = await self._run_agents_parallel(context, senso_context)

        # Step 2: Synthesize findings
        print("[STEP 2/3] Synthesizing findings...")
        verdict = self._synthesize_findings(findings, context)

        # Step 3: Generate recommendation
        print("[STEP 3/3] Generating recommendation...")
        verdict.recommendation = self._generate_recommendation(verdict)

        # Step 4: AUTONOMOUS LEARNING - Learn from this detection
        print("[STEP 4/4] Learning from detection...")
        self.learner.learn_from_outcome(verdict, was_correct=None)  # Will improve with feedback

        print(f"[ORCHESTRATOR] Investigation complete. Severity: {verdict.severity}/10")
        return verdict

    async def _run_agents_parallel(
        self,
        context: AnomalyContext,
        senso_context: Optional[str]
    ) -> List[AgentFinding]:
        """Run all agents in parallel"""

        if not self.agents:
            print("[ERROR] No agents loaded")
            return []

        # Prepare shared context
        shared_context = {
            "data": context.data,
            "timestamps": context.timestamps,
            "metadata": context.metadata,
            "senso_context": senso_context
        }

        # Run agents concurrently
        tasks = [
            agent.analyze(shared_context)
            for agent in self.agents
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"[ERROR] Agent execution failed: {e}")
            return []

        # Convert results to AgentFindings
        findings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[WARN] Agent {i} failed: {result}")
                continue

            if isinstance(result, dict):
                findings.append(AgentFinding(
                    agent_name=result.get("agent_name", f"agent_{i}"),
                    finding=result.get("finding", ""),
                    confidence=result.get("confidence", 0.5),
                    severity=result.get("severity", 5),
                    evidence=result.get("evidence", {}),
                    timestamp=datetime.now().isoformat()
                ))

        return findings

    def _synthesize_findings(
        self,
        findings: List[AgentFinding],
        context: AnomalyContext
    ) -> AnomalyVerdict:
        """
        Synthesize agent findings using confidence-weighted voting

        Uses Corch's proven synthesis pattern:
        - Weight by agent confidence
        - Aggregate severity scores
        - Combine evidence
        """

        if not findings:
            return AnomalyVerdict(
                severity=0,
                summary="No findings - investigation failed",
                confidence=0.0,
                anomalies_detected=[],
                agent_findings=[],
                recommendation="Check system logs",
                timestamp=datetime.now().isoformat()
            )

        # AUTONOMOUS LEARNING: Compute adaptive weights based on historical performance
        adaptive_weights = self.learner.compute_adaptive_weights(findings)

        # Confidence-weighted severity with adaptive learning
        total_weight = 0
        weighted_severity_sum = 0

        for finding in findings:
            # Combine agent confidence with learned performance weight
            adaptive_conf = adaptive_weights.get(finding.agent_name, finding.confidence)
            weight = finding.confidence * (0.5 + 0.5 * adaptive_conf)  # Blend original + learned

            total_weight += weight
            weighted_severity_sum += finding.severity * weight

        if total_weight > 0:
            weighted_severity = weighted_severity_sum / total_weight
        else:
            weighted_severity = sum(f.severity for f in findings) / len(findings)

        final_severity = int(round(weighted_severity))

        # Aggregate anomaly indices (union of all detected)
        anomaly_indices = set()
        for finding in findings:
            if "anomaly_indices" in finding.evidence:
                anomaly_indices.update(finding.evidence["anomaly_indices"])

        # Combine findings into summary
        summary_parts = []
        for finding in findings:
            summary_parts.append(f"{finding.agent_name}: {finding.finding}")

        summary = " | ".join(summary_parts)

        # Overall confidence (average)
        avg_confidence = sum(f.confidence for f in findings) / len(findings)

        return AnomalyVerdict(
            severity=final_severity,
            summary=summary,
            confidence=avg_confidence,
            anomalies_detected=sorted(list(anomaly_indices)),
            agent_findings=findings,
            recommendation="",  # Set in next step
            timestamp=datetime.now().isoformat()
        )

    def _generate_recommendation(self, verdict: AnomalyVerdict) -> str:
        """Generate actionable recommendation based on severity"""

        if verdict.severity >= 9:
            return (
                "🚨 CRITICAL: Immediate action required. "
                "Alert on-call team, investigate root cause, prepare rollback plan."
            )
        elif verdict.severity >= 7:
            return (
                "⚠️ HIGH: Investigate within 1 hour. "
                "Monitor closely, prepare mitigation steps."
            )
        elif verdict.severity >= 5:
            return (
                "📊 MEDIUM: Review within 4 hours. "
                "Log for trending analysis, check if pattern persists."
            )
        elif verdict.severity >= 3:
            return (
                "ℹ️ LOW: Note for future reference. "
                "May be normal variance, continue monitoring."
            )
        else:
            return (
                "✅ MINIMAL: No immediate action needed. "
                "Data within normal parameters."
            )

    def to_dict(self, verdict: AnomalyVerdict) -> Dict[str, Any]:
        """Convert verdict to dictionary for serialization"""
        return {
            "severity": verdict.severity,
            "summary": verdict.summary,
            "confidence": verdict.confidence,
            "anomalies_detected": verdict.anomalies_detected,
            "agent_findings": [
                {
                    "agent_name": f.agent_name,
                    "finding": f.finding,
                    "confidence": f.confidence,
                    "severity": f.severity,
                    "evidence": f.evidence
                }
                for f in verdict.agent_findings
            ],
            "recommendation": verdict.recommendation,
            "timestamp": verdict.timestamp
        }


# Quick test/demo
async def demo():
    """Quick demo of orchestrator"""

    # Generate sample data with anomaly
    np.random.seed(42)
    data = np.random.normal(100, 10, 50)
    data[25] = 250  # Spike anomaly

    context = AnomalyContext(
        data=data,
        timestamps=[f"2024-10-17T{i:02d}:00:00Z" for i in range(50)],
        metadata={"source": "demo"}
    )

    orchestrator = AnomalyOrchestrator()

    print("\n" + "="*60)
    print("ANOMALY HUNTER - Demo Mode")
    print("="*60)

    verdict = await orchestrator.investigate(context)

    print("\n" + "="*60)
    print("VERDICT")
    print("="*60)
    print(f"Severity: {verdict.severity}/10")
    print(f"Confidence: {verdict.confidence:.2%}")
    print(f"Anomalies at indices: {verdict.anomalies_detected}")
    print(f"Summary: {verdict.summary}")
    print(f"Recommendation: {verdict.recommendation}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(demo())

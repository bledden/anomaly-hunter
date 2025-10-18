"""
TrueFoundry Deployment Integration
ML platform for model deployment, scaling, and monitoring
"""

import os
from typing import Optional, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, REGISTRY


class TrueFoundryDeployment:
    """
    TrueFoundry ML Platform

    Handles deployment metadata and performance tracking
    for production anomaly detection service
    """

    # Class-level metrics (shared across all instances)
    _metrics_initialized = False
    _inference_count = None
    _inference_latency = None
    _anomaly_severity = None
    _anomaly_confidence = None

    def __init__(self):
        """Initialize TrueFoundry client with Prometheus metrics"""

        self.api_key = os.getenv("TRUEFOUNDRY_API_KEY")
        self.workspace = os.getenv("TRUEFOUNDRY_WORKSPACE", "sfhack")
        self.enabled = False

        # Initialize metrics once at class level (shared across instances)
        if not TrueFoundryDeployment._metrics_initialized:
            TrueFoundryDeployment._inference_count = Counter(
                'anomaly_hunter_inference_total',
                'Total number of anomaly detection inferences',
                ['workspace', 'deployment_id']
            )

            TrueFoundryDeployment._inference_latency = Histogram(
                'anomaly_hunter_inference_duration_seconds',
                'Time spent processing inference requests',
                ['workspace', 'deployment_id']
            )

            TrueFoundryDeployment._anomaly_severity = Gauge(
                'anomaly_hunter_severity_score',
                'Current anomaly severity score (0-10)',
                ['workspace', 'deployment_id']
            )

            TrueFoundryDeployment._anomaly_confidence = Gauge(
                'anomaly_hunter_confidence_score',
                'Detection confidence percentage',
                ['workspace', 'deployment_id']
            )

            TrueFoundryDeployment._metrics_initialized = True

        # Use class-level metrics
        self.inference_count = TrueFoundryDeployment._inference_count
        self.inference_latency = TrueFoundryDeployment._inference_latency
        self.anomaly_severity = TrueFoundryDeployment._anomaly_severity
        self.anomaly_confidence = TrueFoundryDeployment._anomaly_confidence

        if not self.api_key:
            print("[WARN] TrueFoundry API key missing - deployment tracking disabled")
            return

        self.enabled = True
        self.deployment_id = "anomaly-hunter-v1"
        print(f"[TRUEFOUNDRY] ✅ Deployment tracking initialized (workspace: {self.workspace})")
        if not TrueFoundryDeployment._metrics_initialized:
            print(f"[TRUEFOUNDRY] 📊 Prometheus metrics initialized")
        else:
            print(f"[TRUEFOUNDRY] 📊 Using existing Prometheus metrics")

    def log_inference(self, verdict: Any) -> bool:
        """
        Log inference metrics to TrueFoundry via Prometheus

        Args:
            verdict: Anomaly detection verdict

        Returns:
            True if logged successfully
        """

        if not self.enabled:
            return False

        try:
            # Increment inference counter
            self.inference_count.labels(
                workspace=self.workspace,
                deployment_id=self.deployment_id
            ).inc()

            # Update severity gauge
            self.anomaly_severity.labels(
                workspace=self.workspace,
                deployment_id=self.deployment_id
            ).set(verdict.severity)

            # Update confidence gauge
            self.anomaly_confidence.labels(
                workspace=self.workspace,
                deployment_id=self.deployment_id
            ).set(verdict.confidence * 100)

            print(f"[TRUEFOUNDRY] 📈 Logged inference: severity={verdict.severity}/10, confidence={verdict.confidence:.1%}")
            print(f"[TRUEFOUNDRY] ✅ Prometheus metrics updated (inference #{int(self.inference_count.labels(workspace=self.workspace, deployment_id=self.deployment_id)._value.get())})")

            return True

        except Exception as e:
            print(f"[WARN] TrueFoundry logging failed: {e}")
            return False

    def log_performance(self, duration_ms: float, agent_timings: Dict[str, float]) -> bool:
        """
        Log performance metrics to Prometheus histogram

        Args:
            duration_ms: Total inference duration in milliseconds
            agent_timings: Per-agent execution times

        Returns:
            True if logged successfully
        """

        if not self.enabled:
            return False

        try:
            # Record latency in seconds
            duration_seconds = duration_ms / 1000.0
            self.inference_latency.labels(
                workspace=self.workspace,
                deployment_id=self.deployment_id
            ).observe(duration_seconds)

            print(f"[TRUEFOUNDRY] ⏱️  Performance: {duration_ms:.0f}ms total ({duration_seconds:.3f}s)")
            for agent, timing in agent_timings.items():
                print(f"[TRUEFOUNDRY]   └─ {agent}: {timing:.0f}ms")
            print(f"[TRUEFOUNDRY] ✅ Latency metric recorded")

            return True

        except Exception as e:
            print(f"[WARN] TrueFoundry performance logging failed: {e}")
            return False

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment status and health metrics"""

        if not self.enabled:
            return {"status": "disabled"}

        return {
            "status": "active",
            "deployment_id": self.deployment_id,
            "workspace": self.workspace,
            "environment": "production",
            "version": "1.0.0"
        }

    def get_metrics(self) -> str:
        """
        Export Prometheus metrics in text format

        Returns:
            Prometheus metrics in exposition format
        """
        if not self.enabled:
            return "# TrueFoundry metrics disabled"

        from prometheus_client import generate_latest
        return generate_latest(REGISTRY).decode('utf-8')

    def print_metrics_summary(self):
        """Print a human-readable summary of current metrics"""
        if not self.enabled:
            print("[TRUEFOUNDRY] Metrics disabled")
            return

        try:
            inference_count = self.inference_count.labels(
                workspace=self.workspace,
                deployment_id=self.deployment_id
            )._value.get()

            severity = self.anomaly_severity.labels(
                workspace=self.workspace,
                deployment_id=self.deployment_id
            )._value.get()

            confidence = self.anomaly_confidence.labels(
                workspace=self.workspace,
                deployment_id=self.deployment_id
            )._value.get()

            print("\n[TRUEFOUNDRY] 📊 Metrics Summary")
            print(f"  Workspace: {self.workspace}")
            print(f"  Deployment: {self.deployment_id}")
            print(f"  Total Inferences: {int(inference_count)}")
            print(f"  Latest Severity: {severity}/10")
            print(f"  Latest Confidence: {confidence:.1f}%")
            print()

        except Exception as e:
            print(f"[WARN] Could not print metrics summary: {e}")

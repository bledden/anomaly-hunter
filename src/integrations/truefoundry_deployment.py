"""
TrueFoundry Deployment Integration
ML platform for model deployment, scaling, and monitoring
"""

import os
from typing import Optional, Dict, Any

try:
    import truefoundry.ml as tfm
    TRUEFOUNDRY_AVAILABLE = True
except ImportError:
    TRUEFOUNDRY_AVAILABLE = False


class TrueFoundryDeployment:
    """
    TrueFoundry ML Platform

    Handles deployment metadata and performance tracking
    for production anomaly detection service
    """

    def __init__(self):
        """Initialize TrueFoundry ML client"""

        # Check for TFY_API_KEY (standard) or TRUEFOUNDRY_API_KEY (fallback)
        self.api_key = os.getenv("TFY_API_KEY") or os.getenv("TRUEFOUNDRY_API_KEY")
        self.workspace = os.getenv("TRUEFOUNDRY_WORKSPACE", "sfhack")
        self.ml_repo = "anomaly-hunter"
        self.enabled = False
        self.client = None
        self.run = None
        self.inference_count = 0

        if not TRUEFOUNDRY_AVAILABLE:
            print("[WARN] TrueFoundry SDK not installed - deployment tracking disabled")
            return

        if not self.api_key:
            print("[WARN] TrueFoundry API key missing (set TFY_API_KEY env var) - deployment tracking disabled")
            return

        try:
            # Set API key for SDK
            os.environ["TFY_API_KEY"] = self.api_key

            # Initialize TrueFoundry client
            self.client = tfm.get_client()

            # Create ML repo if it doesn't exist
            try:
                self.client.create_ml_repo(self.ml_repo)
            except Exception as e:
                # Repo might already exist - that's okay
                if "already exists" not in str(e).lower():
                    raise

            # Create a run for this session
            self.run = self.client.create_run(
                ml_repo=self.ml_repo,
                run_name=f"detection-session-{self.workspace}"
            )

            self.enabled = True
            print(f"[TRUEFOUNDRY] ✅ ML tracking initialized (workspace: {self.workspace})")
            print(f"[TRUEFOUNDRY] 📊 Run created: {self.run.run_name}")
            print(f"[TRUEFOUNDRY] 🔗 View metrics at TrueFoundry dashboard")

        except Exception as e:
            print(f"[WARN] TrueFoundry initialization failed: {e}")
            print(f"[WARN] To enable: Set TFY_API_KEY environment variable with your TrueFoundry token")
            self.enabled = False

    def log_inference(self, verdict: Any) -> bool:
        """
        Log inference metrics to TrueFoundry ML platform

        Args:
            verdict: Anomaly detection verdict

        Returns:
            True if logged successfully
        """

        if not self.enabled or not self.run:
            return False

        try:
            self.inference_count += 1

            # Log metrics to TrueFoundry
            self.run.log_metrics({
                "severity": float(verdict.severity),
                "confidence": float(verdict.confidence * 100),
                "anomaly_count": float(len(verdict.anomalies_detected)),
                "agent_count": float(len(verdict.agent_findings))
            }, step=self.inference_count)

            print(f"[TRUEFOUNDRY] 📈 Logged inference: severity={verdict.severity}/10, confidence={verdict.confidence:.1%}")
            print(f"[TRUEFOUNDRY]   └─ Action: Tracked metrics to ML platform (run: {self.run.run_name})")
            print(f"[TRUEFOUNDRY] ✅ Metrics logged (inference #{self.inference_count})")

            return True

        except Exception as e:
            print(f"[WARN] TrueFoundry logging failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def log_performance(self, duration_ms: float, agent_timings: Dict[str, float]) -> bool:
        """
        Log performance metrics to TrueFoundry

        Args:
            duration_ms: Total inference duration in milliseconds
            agent_timings: Per-agent execution times

        Returns:
            True if logged successfully
        """

        if not self.enabled or not self.run:
            return False

        try:
            # Log latency metrics
            self.run.log_metrics({
                "latency_ms": float(duration_ms),
                "latency_seconds": float(duration_ms / 1000.0)
            }, step=self.inference_count)

            # Log per-agent timings
            for agent_name, timing in agent_timings.items():
                self.run.log_metrics({
                    f"agent_{agent_name}_ms": float(timing)
                }, step=self.inference_count)

            print(f"[TRUEFOUNDRY] ⏱️  Performance: {duration_ms:.0f}ms total")
            for agent, timing in agent_timings.items():
                print(f"[TRUEFOUNDRY]   └─ {agent}: {timing:.0f}ms")
            print(f"[TRUEFOUNDRY] ✅ Performance metrics logged")

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
            "run_name": self.run.run_name if self.run else "unknown",
            "workspace": self.workspace,
            "ml_repo": self.ml_repo,
            "inference_count": self.inference_count
        }

    def end_run(self):
        """End the current TrueFoundry run"""
        if self.enabled and self.run:
            try:
                self.run.end()
                print(f"[TRUEFOUNDRY] ✅ Run ended: {self.run.run_name}")
            except Exception as e:
                print(f"[WARN] Failed to end TrueFoundry run: {e}")

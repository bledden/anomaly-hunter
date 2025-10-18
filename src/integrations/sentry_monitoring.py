"""
Sentry Integration
Application monitoring, error tracking, and performance metrics
"""

import os
import sentry_sdk
from typing import Dict, Any


def initialize_sentry():
    """Initialize Sentry SDK for error tracking and performance monitoring"""

    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        print("[WARN] SENTRY_DSN not set - monitoring disabled")
        return False

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,  # 100% transaction sampling for demo
            profiles_sample_rate=1.0,  # 100% profiling for demo
            environment="production",
            release="anomaly-hunter@1.0.0"
        )
        print("[SENTRY] ✅ Monitoring initialized")
        return True

    except Exception as e:
        print(f"[ERROR] Sentry initialization failed: {e}")
        return False


def track_anomaly_detection(verdict: Any):
    """Track anomaly detection event in Sentry"""

    try:
        with sentry_sdk.configure_scope() as scope:
            # Add custom context
            scope.set_context("anomaly", {
                "severity": verdict.severity,
                "confidence": verdict.confidence,
                "anomaly_count": len(verdict.anomalies_detected),
                "recommendation": verdict.recommendation
            })

            # Track as custom event
            sentry_sdk.capture_message(
                f"Anomaly Detected: Severity {verdict.severity}/10",
                level="warning" if verdict.severity < 8 else "error"
            )

        level_name = "ERROR" if verdict.severity >= 8 else "WARNING"
        print(f"[SENTRY] 📊 Tracked anomaly event (severity {verdict.severity}/10)")
        print(f"[SENTRY]   └─ Action: Logged {level_name} event with {len(verdict.anomalies_detected)} anomalies to monitoring dashboard")
        print(f"[SENTRY]   └─ Result: Event visible at https://sentry.io/organizations/anomaly-hunter/issues/")

    except Exception as e:
        print(f"[ERROR] Sentry tracking failed: {e}")


def track_agent_performance(agent_name: str, confidence: float, duration_ms: float):
    """Track individual agent performance metrics"""

    try:
        with sentry_sdk.start_transaction(op="agent", name=agent_name):
            sentry_sdk.set_measurement("confidence", confidence * 100, "percent")
            sentry_sdk.set_measurement("duration", duration_ms, "millisecond")

    except Exception:
        pass  # Silent fail for performance tracking

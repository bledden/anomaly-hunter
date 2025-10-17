"""
Redpanda Event Streaming Integration
Real-time anomaly event streaming to Kafka-compatible broker
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime


class RedpandaStreaming:
    """
    Redpanda Event Streaming

    Publishes anomaly detection events to Redpanda broker
    for real-time monitoring and downstream processing
    """

    def __init__(self):
        """Initialize Redpanda producer"""

        self.broker = os.getenv("REDPANDA_BROKER")
        self.username = os.getenv("REDPANDA_USERNAME")
        self.password = os.getenv("REDPANDA_PASSWORD")
        self.sasl_mechanism = os.getenv("REDPANDA_SASL_MECHANISM", "SCRAM-SHA-256")

        self.producer = None
        self.enabled = False

        if not all([self.broker, self.username, self.password]):
            print("[WARN] Redpanda credentials incomplete - streaming disabled")
            return

        try:
            from kafka import KafkaProducer

            self.producer = KafkaProducer(
                bootstrap_servers=self.broker,
                security_protocol='SASL_SSL',
                sasl_mechanism=self.sasl_mechanism,
                sasl_plain_username=self.username,
                sasl_plain_password=self.password,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )

            self.enabled = True
            print("[REDPANDA] ✅ Event streaming initialized")

        except ImportError:
            print("[WARN] kafka-python not installed - run: pip install kafka-python")
        except Exception as e:
            print(f"[ERROR] Redpanda initialization failed: {e}")

    def publish_anomaly_event(self, verdict: Any, topic: str = "anomaly-hunter-events") -> bool:
        """
        Publish anomaly detection event to Redpanda

        Args:
            verdict: Anomaly detection verdict
            topic: Kafka topic name

        Returns:
            True if published successfully
        """

        if not self.enabled or not self.producer:
            return False

        try:
            # Construct event payload
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "severity": verdict.severity,
                "confidence": verdict.confidence,
                "anomaly_count": len(verdict.anomalies_detected),
                "anomalies": verdict.anomalies_detected[:20],  # First 20
                "summary": verdict.summary[:500],  # Truncate for streaming
                "recommendation": verdict.recommendation,
                "agent_findings": [
                    {
                        "agent": f.agent_name,
                        "confidence": f.confidence,
                        "severity": f.severity
                    }
                    for f in verdict.agent_findings
                ]
            }

            # Send to Redpanda
            future = self.producer.send(topic, value=event)
            future.get(timeout=10)  # Block until sent

            print(f"[REDPANDA] 📡 Event published to {topic} (severity {verdict.severity}/10)")
            return True

        except Exception as e:
            print(f"[ERROR] Redpanda publish failed: {e}")
            return False

    def close(self):
        """Close producer connection"""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
            except Exception:
                pass

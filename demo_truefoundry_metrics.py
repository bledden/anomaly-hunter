#!/usr/bin/env python3
"""
TrueFoundry Live Metrics Demo
Shows real-time Prometheus metrics collection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrations.truefoundry_deployment import TrueFoundryDeployment
from dataclasses import dataclass

# Mock verdict for demonstration
@dataclass
class MockVerdict:
    severity: int
    confidence: float
    anomalies_detected: list
    agent_findings: list

def main():
    print("="*70)
    print("  TrueFoundry Live Prometheus Metrics Demonstration")
    print("="*70)
    print()

    # Initialize TrueFoundry
    print("[1] Initializing TrueFoundry deployment tracker...")
    tf = TrueFoundryDeployment()

    if not tf.enabled:
        print("[ERROR] TrueFoundry not enabled. Set TRUEFOUNDRY_API_KEY in .env")
        return

    print()
    print("[2] Simulating 5 anomaly detections...")
    print("-"*70)

    # Simulate detections
    scenarios = [
        ("Network packet loss", 8, 0.92, [96, 97, 98, 99]),
        ("Database spike", 6, 0.75, [45, 46, 47]),
        ("Memory leak", 9, 0.95, [120, 121, 122, 123, 124]),
        ("API latency drift", 5, 0.68, [30, 31]),
        ("Critical error spike", 10, 0.98, [200, 201, 202, 203, 204, 205]),
    ]

    for i, (scenario, severity, confidence, anomalies) in enumerate(scenarios, 1):
        verdict = MockVerdict(
            severity=severity,
            confidence=confidence,
            anomalies_detected=anomalies,
            agent_findings=[]
        )

        print(f"\n[Detection #{i}] {scenario}")
        tf.log_inference(verdict)

        # Simulate timing
        import random
        duration_ms = random.uniform(800, 2000)
        agent_timings = {
            'pattern_analyst': random.uniform(250, 700),
            'change_detective': random.uniform(250, 700),
            'root_cause': random.uniform(250, 700)
        }
        tf.log_performance(duration_ms, agent_timings)

    print()
    print("="*70)
    print("[3] Viewing accumulated metrics...")
    print("="*70)

    # Show summary
    tf.print_metrics_summary()

    # Show Prometheus export
    print("[4] Prometheus Export (for monitoring systems):")
    print("-"*70)
    metrics = tf.get_metrics()

    # Filter to just our metrics
    for line in metrics.split('\n'):
        if 'anomaly_hunter' in line:
            print(line)

    print("-"*70)
    print()
    print("✅ TrueFoundry is now logging live metrics!")
    print("   These can be scraped by Prometheus or TrueFoundry's monitoring.")
    print()

if __name__ == "__main__":
    main()

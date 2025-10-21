#!/usr/bin/env python3
"""
Quick test script for Weave integration
"""

import sys
sys.path.insert(0, 'src')

import asyncio
import numpy as np
from orchestrator import AnomalyOrchestrator, AnomalyContext

async def test_weave():
    print("="*60)
    print("WEAVE INTEGRATION TEST")
    print("="*60)

    # Initialize orchestrator
    print("\n[1/3] Initializing orchestrator...")
    orch = AnomalyOrchestrator()
    print(f"      Weave enabled: {orch.weave_enabled}")

    # Create simple test data with obvious anomaly
    print("\n[2/3] Creating test data...")
    data = np.array([10, 12, 11, 13, 12, 100, 11, 12, 13])  # 100 is obvious anomaly

    context = AnomalyContext(
        data=data,
        timestamps=[str(i) for i in range(len(data))],
        metadata={"source": "test_metrics"}
    )

    print(f"      Data points: {len(data)}")
    print(f"      Anomaly at index 5: value={data[5]}")

    # Run investigation
    print("\n[3/3] Running investigation with Weave tracing...")
    result = await orch.investigate(context)

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Summary: {result.summary}")
    print(f"Confidence: {result.confidence*100:.1f}%")
    print(f"Severity: {result.severity}/10")
    print(f"Recommendation: {result.recommendation}")
    print(f"Anomalies detected at indices: {result.anomalies_detected}")

    if orch.weave_enabled:
        print("\n" + "="*60)
        print("WEAVE TRACE")
        print("="*60)
        print("View trace at: https://wandb.ai/facilitair/anomaly-hunter/weave")
        print("")
        print("Expected traces:")
        print("  ├─ investigate() - orchestrator level")
        print("  ├─ analyze() - pattern_analyst")
        print("  ├─ analyze() - change_detective")
        print("  └─ analyze() - root_cause")

    return result

if __name__ == "__main__":
    result = asyncio.run(test_weave())
    print("\n✓ Test complete!")

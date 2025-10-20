#!/usr/bin/env python3
"""
Anomaly Detection Efficacy Test Suite
Tests the system against anomalies of varying difficulty levels
"""

import asyncio
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator import AnomalyOrchestrator, AnomalyContext
from integrations.stackai_gateway import StackAIGateway


def generate_test_data(difficulty: str, size: int = 100) -> tuple:
    """
    Generate test data with anomalies of varying difficulty

    Args:
        difficulty: 'easy', 'medium', or 'hard'
        size: Number of data points

    Returns:
        (data, ground_truth_indices, description)
    """

    np.random.seed(42)
    baseline = np.random.normal(100, 5, size)
    ground_truth = []

    if difficulty == 'easy':
        # EASY: Obvious spike anomaly (10x normal)
        baseline[50] = 1000  # Massive spike
        ground_truth = [50]
        description = "Obvious 10x spike at index 50"

    elif difficulty == 'medium':
        # MEDIUM: Subtle drift + small spikes
        # Gradual drift over time
        drift = np.linspace(0, 20, size)
        baseline = baseline + drift

        # Add subtle spikes (3-4 sigma)
        baseline[30] = 135  # 3.5σ spike
        baseline[60] = 140  # 4σ spike
        baseline[80] = 138  # 3.8σ spike

        ground_truth = [30, 60, 80]
        description = "Gradual drift + 3 subtle spikes (3-4σ)"

    elif difficulty == 'hard':
        # HARD: Noisy data with very subtle pattern
        # High variance baseline
        baseline = np.random.normal(100, 15, size)

        # Very subtle cyclic pattern (hard to detect)
        cycle = 3 * np.sin(np.linspace(0, 4*np.pi, size))
        baseline = baseline + cycle

        # Tiny anomalies hidden in noise (barely 2σ)
        baseline[25] = 135  # 2.3σ
        baseline[55] = 133  # 2.2σ
        baseline[75] = 137  # 2.5σ

        ground_truth = [25, 55, 75]
        description = "High noise + tiny anomalies (2-2.5σ) + cyclic pattern"

    else:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    return baseline, ground_truth, description


async def run_test(difficulty: str, orchestrator: AnomalyOrchestrator):
    """Run single test at given difficulty level"""

    print("\n" + "="*70)
    print(f"  TEST: {difficulty.upper()} DIFFICULTY")
    print("="*70)

    # Generate test data
    data, ground_truth, description = generate_test_data(difficulty)

    print(f"\n[INFO] {description}")
    print(f"[INFO] Ground truth anomalies: {ground_truth}")
    print(f"[INFO] Data points: {len(data)}")

    # Create context
    context = AnomalyContext(
        data=data,
        timestamps=[f"2024-10-20T{i:02d}:00:00Z" for i in range(len(data))],
        metadata={"difficulty": difficulty, "test": True}
    )

    # Run detection
    print(f"\n[DETECTING] Running 3-agent analysis...")
    verdict = await orchestrator.investigate(context, senso_context=None)

    # Analyze results
    detected = set(verdict.anomalies_detected)
    expected = set(ground_truth)

    true_positives = len(detected & expected)
    false_positives = len(detected - expected)
    false_negatives = len(expected - detected)

    # Calculate metrics
    precision = true_positives / len(detected) if detected else 0
    recall = true_positives / len(expected) if expected else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Display results
    print("\n" + "-"*70)
    print("  RESULTS")
    print("-"*70)
    print(f"Severity:         {verdict.severity}/10")
    print(f"Confidence:       {verdict.confidence:.1%}")
    print(f"Detected:         {len(detected)} anomalies at {sorted(list(detected))[:10]}")
    print(f"Expected:         {len(expected)} anomalies at {ground_truth}")
    print()
    print(f"True Positives:   {true_positives}")
    print(f"False Positives:  {false_positives}")
    print(f"False Negatives:  {false_negatives}")
    print()
    print(f"Precision:        {precision:.1%}")
    print(f"Recall:           {recall:.1%}")
    print(f"F1 Score:         {f1_score:.1%}")
    print("-"*70)

    return {
        "difficulty": difficulty,
        "severity": verdict.severity,
        "confidence": verdict.confidence,
        "detected": len(detected),
        "expected": len(expected),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "verdict": verdict
    }


async def main():
    """Run full efficacy test suite"""

    print("\n" + "="*70)
    print("  ANOMALY HUNTER - EFFICACY TEST SUITE")
    print("  Testing Detection Across Difficulty Levels")
    print("="*70)

    # Initialize
    stackai = StackAIGateway()
    orchestrator = AnomalyOrchestrator(stackai_client=stackai)

    # Run tests
    results = []

    for difficulty in ['easy', 'medium', 'hard']:
        result = await run_test(difficulty, orchestrator)
        results.append(result)

    # Summary
    print("\n" + "="*70)
    print("  OVERALL EFFICACY SUMMARY")
    print("="*70)
    print()
    print(f"{'Difficulty':<12} {'Severity':<10} {'Confidence':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-"*70)

    for r in results:
        print(f"{r['difficulty'].upper():<12} {r['severity']}/10{'':<6} {r['confidence']:<11.1%} {r['precision']:<11.1%} {r['recall']:<11.1%} {r['f1_score']:<11.1%}")

    # Average metrics
    avg_precision = sum(r['precision'] for r in results) / len(results)
    avg_recall = sum(r['recall'] for r in results) / len(results)
    avg_f1 = sum(r['f1_score'] for r in results) / len(results)

    print("-"*70)
    print(f"{'AVERAGE':<12} {'':<10} {'':<12} {avg_precision:<11.1%} {avg_recall:<11.1%} {avg_f1:<11.1%}")
    print("="*70)

    # Interpretation
    print("\n📊 INTERPRETATION:")
    print(f"  • Precision: {avg_precision:.1%} - How many detected anomalies were real")
    print(f"  • Recall:    {avg_recall:.1%} - How many real anomalies were detected")
    print(f"  • F1 Score:  {avg_f1:.1%} - Overall detection quality")

    if avg_f1 >= 0.8:
        print("\n✅ EXCELLENT - System performs very well across all difficulty levels")
    elif avg_f1 >= 0.6:
        print("\n✅ GOOD - System handles most anomalies effectively")
    elif avg_f1 >= 0.4:
        print("\n⚠️  MODERATE - System detects obvious anomalies but struggles with subtle ones")
    else:
        print("\n❌ NEEDS IMPROVEMENT - System has difficulty with accurate detection")

    print()

    # Cleanup
    await stackai.close()


if __name__ == "__main__":
    asyncio.run(main())

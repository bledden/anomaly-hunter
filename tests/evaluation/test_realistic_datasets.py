#!/usr/bin/env python3
"""
Realistic Dataset Efficacy Test
Tests system against pre-generated realistic production scenarios
Includes confidence-based flagging of potential false positives
"""

import asyncio
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator import AnomalyOrchestrator, AnomalyContext
from integrations.stackai_gateway import StackAIGateway


# Ground truth for each realistic dataset
GROUND_TRUTH = {
    "data_network_loss.csv": {
        "description": "Network packet loss spike - Three-wave cascade failure",
        "expected_anomalies": [100, 200, 320],  # Major cascade events
        "severity": 9,
        "pattern": "cascade"
    },
    "data_database_spike.csv": {
        "description": "Database query spike - Sudden 12% latency increase",
        "expected_anomalies": [150],  # Main spike
        "severity": 7,
        "pattern": "spike"
    },
    "data_memory_leak.csv": {
        "description": "Memory leak - Gradual 40% increase over time",
        "expected_anomalies": list(range(200, 401, 50)),  # Drift points
        "severity": 8,
        "pattern": "drift"
    },
    "data_api_latency_drift.csv": {
        "description": "API latency drift - 46.7% degradation",
        "expected_anomalies": list(range(180, 271, 30)),  # Degradation window
        "severity": 8,
        "pattern": "drift"
    },
    "data_cache_miss.csv": {
        "description": "Cache miss rate spike - Temporary performance hit",
        "expected_anomalies": [120, 140],  # Cache invalidation events
        "severity": 6,
        "pattern": "spike"
    }
}


def classify_detection_confidence(detected, expected, agent_findings):
    """
    Classify detected anomalies by confidence level

    Returns:
        dict with 'true_positives', 'likely_false_positives', 'uncertain'
    """

    detected_set = set(detected)
    expected_set = set(expected)

    # True positives: detected and expected
    true_positives = detected_set & expected_set

    # Potential false positives
    potential_fps = detected_set - expected_set

    # Classify FPs by proximity to expected anomalies
    likely_fps = set()
    uncertain = set()

    for fp in potential_fps:
        # Check if it's adjacent to a true anomaly (within 5 indices)
        is_adjacent = any(abs(fp - tp) <= 5 for tp in expected_set)

        if is_adjacent:
            uncertain.add(fp)  # Could be related to real anomaly
        else:
            likely_fps.add(fp)  # Likely unrelated false positive

    # Get average agent confidence
    avg_confidence = sum(f.confidence for f in agent_findings) / len(agent_findings) if agent_findings else 0

    return {
        "true_positives": sorted(list(true_positives)),
        "likely_false_positives": sorted(list(likely_fps)),
        "uncertain": sorted(list(uncertain)),
        "avg_confidence": avg_confidence
    }


async def test_realistic_dataset(dataset_name: str, orchestrator: AnomalyOrchestrator):
    """Test on a realistic production dataset"""

    print("\n" + "="*70)
    print(f"  DATASET: {dataset_name}")
    print("="*70)

    # Load dataset
    file_path = Path("demo") / dataset_name
    if not file_path.exists():
        print(f"[ERROR] Dataset not found: {file_path}")
        return None

    df = pd.read_csv(file_path)
    data = df["value"].values
    timestamps = df["timestamp"].tolist() if "timestamp" in df.columns else None

    # Get ground truth
    truth = GROUND_TRUTH.get(dataset_name, {})
    expected = truth.get("expected_anomalies", [])
    description = truth.get("description", "Unknown")
    expected_severity = truth.get("severity", 5)
    pattern = truth.get("pattern", "unknown")

    print(f"\n[INFO] {description}")
    print(f"[INFO] Expected anomalies: {expected}")
    print(f"[INFO] Expected severity: {expected_severity}/10")
    print(f"[INFO] Pattern type: {pattern}")
    print(f"[INFO] Data points: {len(data)}")

    # Create context
    context = AnomalyContext(
        data=data,
        timestamps=timestamps,
        metadata={
            "source": dataset_name,
            "test": "realistic",
            "pattern": pattern
        }
    )

    # Run detection
    print(f"\n[DETECTING] Running 3-agent analysis...")
    verdict = await orchestrator.investigate(context, senso_context=None)

    # Classify detections
    classification = classify_detection_confidence(
        verdict.anomalies_detected,
        expected,
        verdict.agent_findings
    )

    # Calculate metrics
    true_positives = len(classification["true_positives"])
    false_positives = len(classification["likely_false_positives"])
    uncertain = len(classification["uncertain"])
    false_negatives = len(set(expected) - set(verdict.anomalies_detected))

    precision = true_positives / len(verdict.anomalies_detected) if verdict.anomalies_detected else 0
    recall = true_positives / len(expected) if expected else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Display results
    print("\n" + "-"*70)
    print("  RESULTS")
    print("-"*70)
    print(f"Severity:              {verdict.severity}/10 (expected: {expected_severity}/10)")
    print(f"Confidence:            {verdict.confidence:.1%}")
    print(f"Agent Avg Confidence:  {classification['avg_confidence']:.1%}")
    print()
    print(f"Total Detected:        {len(verdict.anomalies_detected)}")
    print(f"  ✅ True Positives:    {true_positives} - {classification['true_positives']}")
    print(f"  ⚠️  Uncertain:         {uncertain} - {classification['uncertain']}")
    print(f"  ❌ Likely False Pos:  {false_positives} - {classification['likely_false_positives']}")
    print(f"  ❌ False Negatives:   {false_negatives}")
    print()
    print(f"Precision:             {precision:.1%}")
    print(f"Recall:                {recall:.1%}")
    print(f"F1 Score:              {f1_score:.1%}")
    print()
    print(f"Severity Match:        {verdict.severity == expected_severity}")
    print("-"*70)

    # Agent breakdown
    print("\n[AGENT BREAKDOWN]")
    for finding in verdict.agent_findings:
        print(f"  {finding.agent_name}: Confidence={finding.confidence:.1%}, Severity={finding.severity}/10")

    return {
        "dataset": dataset_name,
        "severity": verdict.severity,
        "expected_severity": expected_severity,
        "confidence": verdict.confidence,
        "agent_confidence": classification['avg_confidence'],
        "true_positives": true_positives,
        "false_positives": false_positives,
        "uncertain": uncertain,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "pattern": pattern,
        "classification": classification
    }


async def main():
    """Run realistic dataset test suite"""

    print("\n" + "="*70)
    print("  ANOMALY HUNTER - REALISTIC DATASET EFFICACY TEST")
    print("  Testing Against Production-Like Scenarios")
    print("="*70)

    # Initialize
    stackai = StackAIGateway()
    orchestrator = AnomalyOrchestrator(stackai_client=stackai)

    # Run tests on available datasets
    results = []

    for dataset_name in GROUND_TRUTH.keys():
        result = await test_realistic_dataset(dataset_name, orchestrator)
        if result:
            results.append(result)

    # Summary
    print("\n" + "="*70)
    print("  OVERALL PERFORMANCE SUMMARY")
    print("="*70)
    print()
    print(f"{'Dataset':<30} {'F1 Score':<12} {'Precision':<12} {'Recall':<12} {'Uncertain':<10}")
    print("-"*70)

    for r in results:
        print(f"{r['dataset']:<30} {r['f1_score']:<11.1%} {r['precision']:<11.1%} {r['recall']:<11.1%} {r['uncertain']:<10}")

    # Calculate averages
    avg_precision = sum(r['precision'] for r in results) / len(results) if results else 0
    avg_recall = sum(r['recall'] for r in results) / len(results) if results else 0
    avg_f1 = sum(r['f1_score'] for r in results) / len(results) if results else 0
    total_uncertain = sum(r['uncertain'] for r in results)

    print("-"*70)
    print(f"{'AVERAGE':<30} {avg_f1:<11.1%} {avg_precision:<11.1%} {avg_recall:<11.1%} {total_uncertain:<10}")
    print("="*70)

    # Interpretation
    print("\n📊 INTERPRETATION:")
    print(f"  • Precision: {avg_precision:.1%} - How many detected anomalies were real")
    print(f"  • Recall:    {avg_recall:.1%} - How many real anomalies were detected")
    print(f"  • F1 Score:  {avg_f1:.1%} - Overall detection quality")
    print(f"  • Uncertain: {total_uncertain} total - Detections near true anomalies (may be related)")
    print()
    print("💡 NOTES:")
    print("  • 'Uncertain' detections are within 5 indices of true anomalies")
    print("  • These could be legitimate related anomalies or propagation effects")
    print("  • In production, these would be flagged for human review")

    # Pattern analysis
    print("\n" + "="*70)
    print("  PATTERN-SPECIFIC PERFORMANCE")
    print("="*70)

    patterns = {}
    for r in results:
        pattern = r['pattern']
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(r)

    for pattern, pattern_results in patterns.items():
        avg_f1 = sum(r['f1_score'] for r in pattern_results) / len(pattern_results)
        print(f"  {pattern.upper()}: F1={avg_f1:.1%} ({len(pattern_results)} datasets)")

    print("="*70)

    # Autonomous learning status
    print("\n🧠 AUTONOMOUS LEARNING STATUS:")
    print(f"  • Total detections processed: {orchestrator.learner.agent_stats['total_detections']}")
    print(f"  • System is continuously learning from each detection")
    print(f"  • Agent weights adjust based on historical performance")

    print()

    # Cleanup
    await stackai.close()


if __name__ == "__main__":
    asyncio.run(main())

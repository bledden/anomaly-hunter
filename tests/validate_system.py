#!/usr/bin/env python3
"""
Validation Script - Run all 7 scenarios and generate evaluation report
"""

import asyncio
import csv
import os
import json
from pathlib import Path
import numpy as np
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator import AnomalyOrchestrator, AnomalyContext
from evaluation.anomaly_evaluator import AnomalyDetectionEvaluator, evaluate_all_scenarios


DEMO_DIR = Path(__file__).parent / "demo"

SCENARIOS = [
    "data_database_spike.csv",
    "data_api_latency_drift.csv",
    "data_cache_miss.csv",
    "data_disk_saturation.csv",
    "data_network_loss.csv",
    "data_error_spike.csv",
    "data_memory_leak.csv"
]


def load_csv_data(filepath: Path):
    """Load CSV data and return values array"""
    values = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append(float(row['value']))
    return np.array(values)


async def run_single_scenario(orchestrator, scenario_name: str):
    """Run detection on a single scenario"""
    print(f"\n{'='*60}")
    print(f"Testing: {scenario_name}")
    print('='*60)

    filepath = DEMO_DIR / scenario_name
    data = load_csv_data(filepath)

    context = AnomalyContext(
        data=data,
        metadata={"scenario": scenario_name}
    )

    # Run detection
    verdict = await orchestrator.investigate(context)

    result = {
        "scenario": scenario_name,
        "severity": verdict.severity,
        "confidence": verdict.confidence,
        "anomalies_detected": verdict.anomalies_detected,
        "summary": verdict.summary,
        "recommendation": verdict.recommendation,
        "total_points": len(data)
    }

    print(f"\n[RESULT] Severity: {verdict.severity}/10")
    print(f"[RESULT] Anomalies: {len(verdict.anomalies_detected)} detected")
    print(f"[RESULT] Confidence: {verdict.confidence:.1%}")

    return scenario_name, result


async def run_all_scenarios():
    """Run all 7 scenarios and collect results"""
    print("\n" + "="*60)
    print("ANOMALY HUNTER - SYSTEM VALIDATION")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scenarios: {len(SCENARIOS)}")
    print("="*60)

    orchestrator = AnomalyOrchestrator()

    results = {}

    for scenario in SCENARIOS:
        try:
            scenario_name, result = await run_single_scenario(orchestrator, scenario)
            results[scenario_name] = result
        except Exception as e:
            print(f"[ERROR] Failed on {scenario}: {e}")
            results[scenario] = {
                "error": str(e),
                "severity": 0,
                "anomalies_detected": [],
                "summary": "",
                "total_points": 0
            }

    return results


def generate_report(results: dict, evaluation_summary: dict):
    """Generate markdown report"""

    report = f"""# Anomaly Hunter - Validation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Scenarios Tested:** {len(results)}

---

## 📊 Aggregate Metrics

| Metric | Score |
|--------|-------|
| **Precision** | {evaluation_summary['aggregate_metrics']['precision']:.1%} |
| **Recall** | {evaluation_summary['aggregate_metrics']['recall']:.1%} |
| **F1 Score** | {evaluation_summary['aggregate_metrics']['f1_score']:.1%} |
| **False Positive Rate** | {evaluation_summary['aggregate_metrics']['false_positive_rate']:.1%} |
| **Pass Rate** | {evaluation_summary['aggregate_metrics']['pass_rate']:.1%} |

**Overall Quality:** {evaluation_summary['summary']['overall_quality']}

---

## 🧪 Scenario Results

"""

    for scenario_name in SCENARIOS:
        if scenario_name not in results:
            continue

        result = results[scenario_name]
        eval_score = evaluation_summary['scenario_scores'].get(scenario_name, {})

        status = "✅ PASS" if eval_score.get('passed', False) else "❌ FAIL"

        report += f"""### {scenario_name} {status}

| Metric | Value |
|--------|-------|
| Detected Severity | {result.get('severity', 0)}/10 |
| Anomalies Detected | {len(result.get('anomalies_detected', []))} |
| Precision | {eval_score.get('precision', 0):.1%} |
| Recall | {eval_score.get('recall', 0):.1%} |
| F1 Score | {eval_score.get('f1_score', 0):.1%} |
| Overall Score | {eval_score.get('overall', 0):.1%} |

**Finding:** {result.get('summary', 'N/A')[:200]}...

**Recommendation:** {result.get('recommendation', 'N/A')[:150]}...

---

"""

    report += f"""## 🎯 Summary

- **Scenarios Passed:** {evaluation_summary['summary']['scenarios_passed']}/{evaluation_summary['summary']['total_scenarios']}
- **Production Ready:** {"✅ YES" if evaluation_summary['summary']['overall_quality'] in ['EXCELLENT', 'GOOD'] else "⚠️ NEEDS IMPROVEMENT"}

---

*Built on Corch orchestration framework - proven 73% quality pass rate*
"""

    return report


async def main():
    """Main validation flow"""

    # Run all scenarios
    results = await run_all_scenarios()

    # Evaluate results
    print("\n" + "="*60)
    print("EVALUATION")
    print("="*60)

    evaluator = AnomalyDetectionEvaluator()
    evaluation_summary = evaluate_all_scenarios(results)

    # Print summary
    print("\n📊 AGGREGATE METRICS:")
    for metric, value in evaluation_summary['aggregate_metrics'].items():
        print(f"  {metric}: {value:.1%}")

    print(f"\n🎯 OVERALL: {evaluation_summary['summary']['overall_quality']}")
    print(f"Pass Rate: {evaluation_summary['summary']['scenarios_passed']}/{evaluation_summary['summary']['total_scenarios']}")

    # Generate report
    report = generate_report(results, evaluation_summary)

    # Save report
    report_path = Path(__file__).parent / "VALIDATION_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n✅ Report saved to: {report_path}")

    # Save JSON results
    json_path = Path(__file__).parent / "validation_results.json"
    with open(json_path, 'w') as f:
        json.dump({
            "results": results,
            "evaluation": evaluation_summary,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)

    print(f"✅ JSON results saved to: {json_path}")

    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)

    return evaluation_summary


if __name__ == "__main__":
    summary = asyncio.run(main())

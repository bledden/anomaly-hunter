#!/usr/bin/env python3
"""
Anomaly Hunter CLI
Simple command-line interface for anomaly detection
"""

import asyncio
import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator import AnomalyOrchestrator, AnomalyContext
from integrations.stackai_gateway import StackAIGateway


def print_banner():
    """Print CLI banner"""
    print("\n" + "="*70)
    print("  ANOMALY HUNTER - Autonomous Data Quality Monitor")
    print("  3 Agents | 8 Sponsors | Real-time Investigation")
    print("="*70 + "\n")


async def detect_command(data_path: str):
    """
    Detect anomalies in CSV file

    Args:
        data_path: Path to CSV file with columns: timestamp, value
    """

    print(f"[LOAD] Reading data from: {data_path}")

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        return

    # Validate columns
    if "value" not in df.columns:
        print("[ERROR] CSV must have 'value' column")
        return

    data = df["value"].values
    timestamps = df["timestamp"].tolist() if "timestamp" in df.columns else None

    print(f"[OK] Loaded {len(data)} data points")

    # Create context
    context = AnomalyContext(
        data=data,
        timestamps=timestamps,
        metadata={"source": data_path}
    )

    # Initialize StackAI gateway
    print("[INIT] Initializing StackAI gateway...")
    stackai = StackAIGateway()

    # Create orchestrator
    print("[INIT] Starting anomaly orchestrator...")
    orchestrator = AnomalyOrchestrator(stackai_client=stackai)

    # Run investigation
    print("\n" + "-"*70)
    verdict = await orchestrator.investigate(context)
    print("-"*70)

    # Display results
    print("\n" + "="*70)
    print("  VERDICT")
    print("="*70)
    print(f"Severity:    {verdict.severity}/10")
    print(f"Confidence:  {verdict.confidence:.1%}")
    print(f"Anomalies:   {len(verdict.anomalies_detected)} detected at indices {verdict.anomalies_detected[:10]}")
    print(f"\nSummary:")
    print(f"  {verdict.summary}")
    print(f"\nRecommendation:")
    print(f"  {verdict.recommendation}")
    print("="*70)

    # Agent details
    print("\n" + "="*70)
    print("  AGENT FINDINGS")
    print("="*70)
    for finding in verdict.agent_findings:
        print(f"\n[{finding.agent_name.upper()}]")
        print(f"  Finding:    {finding.finding}")
        print(f"  Confidence: {finding.confidence:.1%}")
        print(f"  Severity:   {finding.severity}/10")

    print("\n" + "="*70)

    # Cleanup
    await stackai.close()


def demo_command():
    """Generate demo dataset and run detection"""

    print("[DEMO] Generating sample anomaly dataset...")

    # Generate data
    sys.path.insert(0, str(Path(__file__).parent / "demo"))
    from sample_anomalies import generate_sample_data

    data_path = "demo/sample_anomalies.csv"
    generate_sample_data(data_path)

    print("\n[DEMO] Running anomaly detection...")

    # Run detection
    asyncio.run(detect_command(data_path))


def help_command():
    """Show help"""

    print("""
USAGE:
  python3 cli.py <command> [options]

COMMANDS:
  detect <file>   Detect anomalies in CSV file
  demo            Generate demo dataset and run detection
  help            Show this help message

EXAMPLES:
  # Run demo
  python3 cli.py demo

  # Detect anomalies in your data
  python3 cli.py detect data/metrics.csv

CSV FORMAT:
  Required columns:
    - value: numeric data points

  Optional columns:
    - timestamp: ISO format timestamps
    - source: data source identifier

SPONSORS:
  - OpenAI (GPT-4, o1-mini)
  - StackAI (Multi-model gateway)
  - TrueFoundry (ML platform)
  - Sentry (Monitoring)
  - Redpanda (Event streaming)
  - ElevenLabs (Voice alerts)
  - Airia (Workflow orchestration)
  - Senso (Knowledge base)
""")


def main():
    """Main CLI entry point"""

    print_banner()

    if len(sys.argv) < 2:
        print("[ERROR] No command specified")
        help_command()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "detect":
        if len(sys.argv) < 3:
            print("[ERROR] Missing file path")
            print("Usage: python3 cli.py detect <file>")
            sys.exit(1)

        data_path = sys.argv[2]
        asyncio.run(detect_command(data_path))

    elif command == "demo":
        demo_command()

    elif command == "help" or command == "--help" or command == "-h":
        help_command()

    else:
        print(f"[ERROR] Unknown command: {command}")
        help_command()
        sys.exit(1)


if __name__ == "__main__":
    main()

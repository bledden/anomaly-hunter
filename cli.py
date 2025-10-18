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
from integrations.sentry_monitoring import initialize_sentry, track_anomaly_detection
from integrations.redpanda_streaming import RedpandaStreaming
from integrations.senso_rag import SensoRAG
from integrations.airia_workflows import AiriaWorkflows
from integrations.truefoundry_deployment import TrueFoundryDeployment
import time


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

    # Initialize all sponsor integrations
    print("[INIT] Initializing sponsor integrations...")
    initialize_sentry()  # Sentry monitoring
    truefoundry = TrueFoundryDeployment()  # TrueFoundry ML platform
    airia = AiriaWorkflows()  # Airia data workflows
    senso = SensoRAG()  # Senso knowledge base
    redpanda = RedpandaStreaming()  # Redpanda event streaming
    stackai = StackAIGateway()  # StackAI model routing

    # Preprocess data with Airia
    print("[AIRIA] Preprocessing data...")
    preprocessed = airia.preprocess_data(data)
    quality = airia.validate_data_quality(data)

    # Retrieve historical context from Senso
    print("[SENSO] Retrieving historical context...")
    senso_context = senso.retrieve_context(f"Anomaly in {data_path}: mean={np.mean(data):.2f}, std={np.std(data):.2f}")

    # Create context
    context = AnomalyContext(
        data=preprocessed['data'],
        timestamps=timestamps,
        metadata={
            "source": data_path,
            "quality_score": quality['quality_score'],
            "preprocessing": preprocessed['metadata']
        }
    )

    # Create orchestrator
    print("[INIT] Starting anomaly orchestrator...")
    orchestrator = AnomalyOrchestrator(stackai_client=stackai)

    # Run investigation with timing
    print("\n" + "-"*70)
    start_time = time.time()
    verdict = await orchestrator.investigate(context, senso_context=senso_context)
    duration_ms = (time.time() - start_time) * 1000
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

    # Track anomaly in Sentry
    print("\n[SENTRY] Tracking anomaly event...")
    track_anomaly_detection(verdict)

    # Log to TrueFoundry
    print("[TRUEFOUNDRY] Logging inference metrics...")
    truefoundry.log_inference(verdict)
    agent_timings = {f.agent_name: 1000 for f in verdict.agent_findings}  # Placeholder timings
    truefoundry.log_performance(duration_ms, agent_timings)

    # Publish to Redpanda stream
    print("[REDPANDA] Publishing to event stream...")
    redpanda.publish_anomaly_event(verdict)

    # Store in Senso knowledge base
    print("[SENSO] Storing in knowledge base...")
    senso.store_anomaly(verdict)

    # Generate voice alert for critical anomalies (severity >= 8)
    if verdict.severity >= 8:
        print("\n🔊 Generating voice alert for critical anomaly...")
        from src.integrations.elevenlabs_voice import ElevenLabsVoice
        voice = ElevenLabsVoice()
        voice.generate_alert(verdict.summary, verdict.severity, verdict.confidence)

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
    redpanda.close()


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


def metrics_command():
    """Show TrueFoundry metrics"""

    print("[TRUEFOUNDRY] Initializing deployment tracker...")
    truefoundry = TrueFoundryDeployment()

    if not truefoundry.enabled:
        print("[ERROR] TrueFoundry is not enabled. Set TRUEFOUNDRY_API_KEY in .env")
        return

    # Print summary
    truefoundry.print_metrics_summary()

    # Show raw Prometheus metrics
    print("[TRUEFOUNDRY] Raw Prometheus Metrics:")
    print("-" * 70)
    print(truefoundry.get_metrics())
    print("-" * 70)


def help_command():
    """Show help"""

    print("""
USAGE:
  python3 cli.py <command> [options]

COMMANDS:
  detect <file>   Detect anomalies in CSV file
  demo            Generate demo dataset and run detection
  metrics         Show TrueFoundry Prometheus metrics
  help            Show this help message

EXAMPLES:
  # Run demo
  python3 cli.py demo

  # Detect anomalies in your data
  python3 cli.py detect data/metrics.csv

  # View TrueFoundry metrics
  python3 cli.py metrics

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

    elif command == "metrics":
        metrics_command()

    elif command == "help" or command == "--help" or command == "-h":
        help_command()

    else:
        print(f"[ERROR] Unknown command: {command}")
        help_command()
        sys.exit(1)


if __name__ == "__main__":
    main()

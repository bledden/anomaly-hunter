"""
Generate realistic anomaly datasets for different scenarios
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os


def scenario_1_database_spike():
    """
    Scenario 1: Database Connection Spike
    Real-world pattern: Deployment causes connection pool exhaustion
    """
    np.random.seed(42)

    n_points = 200
    baseline = 150  # Average connections
    noise = 15

    # Normal baseline with hourly pattern
    hours = np.arange(n_points)
    daily_pattern = 20 * np.sin(2 * np.pi * hours / 24)  # Daily cycle
    data = baseline + daily_pattern + np.random.normal(0, noise, n_points)

    # Deployment event at hour 100 - sudden spike
    deployment_time = 100
    spike_duration = 15
    for i in range(deployment_time, deployment_time + spike_duration):
        if i < n_points:
            # Exponential spike then decay
            factor = np.exp(-(i - deployment_time) / 5)
            data[i] += 300 * factor

    # Create timestamps (hourly data)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [(start_time + timedelta(hours=i)).isoformat() for i in range(n_points)]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': data,
        'metric': 'database_connections',
        'source': 'prod_db_01'
    })

    path = 'demo/data_database_spike.csv'
    os.makedirs('demo', exist_ok=True)
    df.to_csv(path, index=False)

    print(f"✅ Scenario 1: Database Connection Spike")
    print(f"   Location: {path}")
    print(f"   Anomaly: Spike at hour {deployment_time} (deployment event)")
    print(f"   Severity: HIGH (connection pool exhaustion)")
    print()

    return df


def scenario_2_api_latency_drift():
    """
    Scenario 2: Gradual API Latency Degradation
    Real-world pattern: Memory leak causing gradual performance decline
    """
    np.random.seed(123)

    n_points = 300
    baseline = 50  # ms latency
    noise = 5

    # Normal baseline
    data = np.random.normal(baseline, noise, n_points)

    # Gradual drift starting at point 150 (memory leak)
    leak_start = 150
    for i in range(leak_start, n_points):
        # Linear increase (memory leak)
        data[i] += (i - leak_start) * 0.3

    # Add occasional spikes (GC pauses)
    gc_pauses = [180, 210, 240, 270]
    for pause_idx in gc_pauses:
        if pause_idx < n_points:
            data[pause_idx] += np.random.uniform(50, 100)

    # Create timestamps (every 5 minutes)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [(start_time + timedelta(minutes=i*5)).isoformat() for i in range(n_points)]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': data,
        'metric': 'api_latency_p95',
        'source': 'api_gateway'
    })

    path = 'demo/data_api_latency_drift.csv'
    df.to_csv(path, index=False)

    print(f"✅ Scenario 2: API Latency Degradation")
    print(f"   Location: {path}")
    print(f"   Anomaly: Gradual drift starting at point {leak_start} (memory leak)")
    print(f"   Severity: MEDIUM (performance degradation)")
    print()

    return df


def scenario_3_cache_miss_pattern():
    """
    Scenario 3: Cache Invalidation Event
    Real-world pattern: Cache clear causes sudden traffic spike to database
    """
    np.random.seed(456)

    n_points = 250
    baseline = 5  # Cache miss rate (%)
    noise = 1

    # Normal baseline
    data = np.random.normal(baseline, noise, n_points)

    # Cache invalidation events
    cache_clears = [80, 170]
    for clear_idx in cache_clears:
        # Sudden spike then gradual recovery
        recovery_period = 30
        for i in range(clear_idx, min(clear_idx + recovery_period, n_points)):
            # Exponential decay back to baseline
            factor = np.exp(-(i - clear_idx) / 10)
            data[i] += 40 * factor

    # Create timestamps (every 10 minutes)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [(start_time + timedelta(minutes=i*10)).isoformat() for i in range(n_points)]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': data,
        'metric': 'cache_miss_rate',
        'source': 'redis_cluster'
    })

    path = 'demo/data_cache_miss.csv'
    df.to_csv(path, index=False)

    print(f"✅ Scenario 3: Cache Invalidation Pattern")
    print(f"   Location: {path}")
    print(f"   Anomaly: Spikes at indices {cache_clears} (cache clears)")
    print(f"   Severity: MEDIUM (temporary performance impact)")
    print()

    return df


def scenario_4_disk_io_saturation():
    """
    Scenario 4: Disk I/O Saturation
    Real-world pattern: Batch job causes disk contention
    """
    np.random.seed(789)

    n_points = 180
    baseline = 30  # % disk utilization
    noise = 5

    # Normal baseline with daily pattern
    hours = np.arange(n_points)
    business_hours = 10 * np.sin(2 * np.pi * hours / 24 - np.pi/2)  # Peak during day
    data = baseline + business_hours + np.random.normal(0, noise, n_points)

    # Batch job at night (hour 120-140) causes saturation
    batch_start = 120
    batch_duration = 20
    for i in range(batch_start, min(batch_start + batch_duration, n_points)):
        data[i] = np.random.uniform(85, 98)  # Near saturation

    # Create timestamps (hourly)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [(start_time + timedelta(hours=i)).isoformat() for i in range(n_points)]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': data,
        'metric': 'disk_io_util',
        'source': 'app_server_03'
    })

    path = 'demo/data_disk_saturation.csv'
    df.to_csv(path, index=False)

    print(f"✅ Scenario 4: Disk I/O Saturation")
    print(f"   Location: {path}")
    print(f"   Anomaly: Saturation at hours {batch_start}-{batch_start+batch_duration} (batch job)")
    print(f"   Severity: HIGH (impacts all operations)")
    print()

    return df


def scenario_5_network_packet_loss():
    """
    Scenario 5: Network Packet Loss Bursts
    Real-world pattern: Network equipment failure causing intermittent drops
    """
    np.random.seed(321)

    n_points = 400
    baseline = 0.1  # % packet loss (normal)
    noise = 0.05

    # Normal baseline (very low loss)
    data = np.random.normal(baseline, noise, n_points)
    data = np.clip(data, 0, None)  # Can't be negative

    # Network issues - burst of packet loss
    issue_periods = [
        (100, 115),  # First incident
        (200, 210),  # Second incident
        (320, 350),  # Extended outage
    ]

    for start, end in issue_periods:
        for i in range(start, min(end, n_points)):
            # Random high packet loss
            data[i] = np.random.uniform(2, 8)

    # Create timestamps (every minute)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [(start_time + timedelta(minutes=i)).isoformat() for i in range(n_points)]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': data,
        'metric': 'packet_loss_pct',
        'source': 'network_switch_02'
    })

    path = 'demo/data_network_loss.csv'
    df.to_csv(path, index=False)

    print(f"✅ Scenario 5: Network Packet Loss")
    print(f"   Location: {path}")
    print(f"   Anomaly: Bursts at {len(issue_periods)} time periods (network failure)")
    print(f"   Severity: CRITICAL (data loss)")
    print()

    return df


def scenario_6_error_rate_spike():
    """
    Scenario 6: Error Rate Spike
    Real-world pattern: API rate limiting causing 429 errors
    """
    np.random.seed(654)

    n_points = 300
    baseline = 0.5  # % error rate (normal)
    noise = 0.2

    # Normal baseline
    data = np.random.normal(baseline, noise, n_points)
    data = np.clip(data, 0, None)

    # Rate limiting kicks in
    rate_limit_start = 150
    rate_limit_duration = 40
    for i in range(rate_limit_start, min(rate_limit_start + rate_limit_duration, n_points)):
        # Exponential spike then decay as clients back off
        factor = np.exp(-(i - rate_limit_start) / 15)
        data[i] += 20 * factor

    # Create timestamps (every 2 minutes)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [(start_time + timedelta(minutes=i*2)).isoformat() for i in range(n_points)]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': data,
        'metric': 'error_rate_pct',
        'source': 'api_gateway'
    })

    path = 'demo/data_error_spike.csv'
    df.to_csv(path, index=False)

    print(f"✅ Scenario 6: Error Rate Spike")
    print(f"   Location: {path}")
    print(f"   Anomaly: Spike at point {rate_limit_start} (rate limiting)")
    print(f"   Severity: HIGH (service degradation)")
    print()

    return df


def scenario_7_memory_leak():
    """
    Scenario 7: Memory Leak (Gradual Increase)
    Real-world pattern: Slow memory leak eventually causing OOM
    """
    np.random.seed(987)

    n_points = 500
    baseline = 2.5  # GB memory usage
    noise = 0.1

    # Start normal
    data = np.random.normal(baseline, noise, 200)

    # Leak starts at point 200
    leak_start = 200
    for i in range(leak_start, n_points):
        # Quadratic growth (leak accelerates)
        leak_factor = ((i - leak_start) / 100) ** 1.5
        data = np.append(data, baseline + leak_factor + np.random.normal(0, noise))

    # OOM restart at point 480
    if len(data) > 480:
        data[480:] = np.random.normal(baseline, noise, len(data) - 480)

    # Create timestamps (every 5 minutes)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [(start_time + timedelta(minutes=i*5)).isoformat() for i in range(n_points)]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': data,
        'metric': 'memory_usage_gb',
        'source': 'app_server_01'
    })

    path = 'demo/data_memory_leak.csv'
    df.to_csv(path, index=False)

    print(f"✅ Scenario 7: Memory Leak")
    print(f"   Location: {path}")
    print(f"   Anomaly: Gradual increase from point {leak_start}, restart at 480 (OOM)")
    print(f"   Severity: CRITICAL (service crash)")
    print()

    return df


def generate_all_scenarios():
    """Generate all realistic scenario datasets"""

    print("\n" + "="*70)
    print("  GENERATING REALISTIC ANOMALY DATASETS")
    print("="*70 + "\n")

    scenarios = [
        scenario_1_database_spike,
        scenario_2_api_latency_drift,
        scenario_3_cache_miss_pattern,
        scenario_4_disk_io_saturation,
        scenario_5_network_packet_loss,
        scenario_6_error_rate_spike,
        scenario_7_memory_leak,
    ]

    dfs = []
    for scenario_func in scenarios:
        df = scenario_func()
        dfs.append(df)

    print("="*70)
    print(f"✅ Generated {len(scenarios)} realistic datasets")
    print("="*70)

    # Create summary
    summary = pd.DataFrame({
        'Scenario': [
            '1. Database Connection Spike',
            '2. API Latency Degradation',
            '3. Cache Invalidation',
            '4. Disk I/O Saturation',
            '5. Network Packet Loss',
            '6. Error Rate Spike',
            '7. Memory Leak'
        ],
        'File': [
            'data_database_spike.csv',
            'data_api_latency_drift.csv',
            'data_cache_miss.csv',
            'data_disk_saturation.csv',
            'data_network_loss.csv',
            'data_error_spike.csv',
            'data_memory_leak.csv'
        ],
        'Severity': [
            'HIGH',
            'MEDIUM',
            'MEDIUM',
            'HIGH',
            'CRITICAL',
            'HIGH',
            'CRITICAL'
        ],
        'Points': [len(df) for df in dfs]
    })

    print("\nSUMMARY:")
    print(summary.to_string(index=False))

    summary_path = 'demo/SCENARIO_SUMMARY.csv'
    summary.to_csv(summary_path, index=False)
    print(f"\nSaved summary to: {summary_path}")

    return dfs


if __name__ == "__main__":
    generate_all_scenarios()

    print("\n" + "="*70)
    print("  USAGE")
    print("="*70)
    print("\n# Test individual scenarios:")
    print("python3 cli.py detect demo/data_database_spike.csv")
    print("python3 cli.py detect demo/data_api_latency_drift.csv")
    print("python3 cli.py detect demo/data_memory_leak.csv")
    print("\n# Or run the simple demo:")
    print("python3 cli.py demo")
    print()

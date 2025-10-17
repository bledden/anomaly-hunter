"""
Generate sample anomaly dataset for demo
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

def generate_sample_data(output_path: str = "demo/sample_anomalies.csv"):
    """
    Generate sample time-series data with obvious anomalies

    Anomalies injected:
    1. Spike at index 20 (2.5x baseline)
    2. Dip at indices 45-50 (30% of baseline)
    3. Extreme spike at index 75 (-50 value)
    4. Gradual drift in second half (20% increase)
    """

    np.random.seed(42)

    # Generate 100 data points
    n_points = 100
    baseline = 100
    noise = 10

    # Normal data with noise
    data = np.random.normal(baseline, noise, n_points)

    # Inject anomalies
    data[20] = 250  # Spike (2.5x)
    data[45:50] = 30  # Dip
    data[75] = -50  # Extreme negative spike

    # Gradual drift in second half
    for i in range(50, 100):
        data[i] += (i - 50) * 0.4  # 20% increase over 50 points

    # Generate timestamps (hourly data)
    start_time = datetime(2024, 10, 17, 0, 0, 0)
    timestamps = [
        (start_time + timedelta(hours=i)).isoformat()
        for i in range(n_points)
    ]

    # Create DataFrame
    df = pd.DataFrame({
        "timestamp": timestamps,
        "value": data,
        "source": "demo_sensor"
    })

    # Ensure demo directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)

    print(f"[OK] Generated {n_points} data points with {4} anomalies")
    print(f"[OK] Saved to: {output_path}")
    print(f"\nAnomalies:")
    print(f"  - Index 20: Spike to {data[20]:.1f}")
    print(f"  - Indices 45-50: Dip to ~{np.mean(data[45:50]):.1f}")
    print(f"  - Index 75: Extreme spike to {data[75]:.1f}")
    print(f"  - Indices 50-100: Gradual drift (+20%)")

    return df


if __name__ == "__main__":
    df = generate_sample_data()
    print("\nFirst 10 rows:")
    print(df.head(10))
    print("\nStatistics:")
    print(df["value"].describe())

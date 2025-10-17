# Demo Scenarios - Realistic Anomaly Datasets

## Overview

7 production-ready datasets simulating real-world anomaly patterns that occur in production systems.

---

## Scenario 1: Database Connection Spike 🔴

**File:** `demo/data_database_spike.csv`
**Severity:** HIGH
**Points:** 200 (hourly data over 8+ days)

### Pattern
- **Normal baseline:** 150 connections with daily cycle
- **Anomaly at hour 100:** Sudden spike to 450+ connections
- **Cause:** Deployment event triggers connection pool exhaustion
- **Duration:** 15 hours with exponential decay

### Real-World Context
```
Timeline:
00:00 - Normal operations (140-160 connections)
04:00 - Deployment begins
04:15 - Connection spike detected (450 connections)
04:30 - Pool exhaustion, new requests queuing
05:00 - Gradual recovery as connections close
06:00 - Back to baseline
```

### Expected Agent Findings
- **Pattern Analyst:** "Z-score 15.2σ - extreme statistical anomaly"
- **Change Detective:** "Sudden change point at hour 100, 200% spike"
- **Root Cause:** "Hypothesis: Deployment caused connection leak"

### Test Command
```bash
python3 cli.py detect demo/data_database_spike.csv
```

---

## Scenario 2: API Latency Degradation 🟡

**File:** `demo/data_api_latency_drift.csv`
**Severity:** MEDIUM
**Points:** 300 (5-min intervals over 25 hours)

### Pattern
- **Normal baseline:** 50ms P95 latency
- **Anomaly at point 150:** Gradual drift begins
- **Cause:** Memory leak causing performance degradation
- **Duration:** 150 points (12.5 hours) of increasing latency
- **Secondary:** GC pause spikes at points 180, 210, 240, 270

### Real-World Context
```
Timeline:
00:00 - Normal 50ms latency
12:30 - Drift begins (memory leak)
13:00 - 60ms latency (+20%)
15:00 - 75ms latency (+50%)
16:00 - GC pauses causing 150ms spikes
18:00 - 95ms latency (+90%)
```

### Expected Agent Findings
- **Pattern Analyst:** "Multiple outliers with gradual baseline shift"
- **Change Detective:** "Strong upward drift (+90%), correlation 0.85"
- **Root Cause:** "Hypothesis: Memory leak causing GC pressure"

### Test Command
```bash
python3 cli.py detect demo/data_api_latency_drift.csv
```

---

## Scenario 3: Cache Invalidation Pattern 🟡

**File:** `demo/data_cache_miss.csv`
**Severity:** MEDIUM
**Points:** 250 (10-min intervals over ~41 hours)

### Pattern
- **Normal baseline:** 5% cache miss rate
- **Anomalies at:** Points 80 and 170
- **Cause:** Cache clear events causing traffic spikes
- **Duration:** 30-point recovery period (5 hours)

### Real-World Context
```
Timeline:
Event 1 (Hour 13):
- Cache cleared for deployment
- Miss rate spikes to 45%
- Backend database load increases 9x
- Gradual cache warm-up over 5 hours

Event 2 (Hour 28):
- Similar pattern repeats
- Second deployment cache clear
```

### Expected Agent Findings
- **Pattern Analyst:** "2 distinct spike clusters, Z-score 4.5σ each"
- **Change Detective:** "2 change points with recovery patterns"
- **Root Cause:** "Hypothesis: Scheduled cache invalidation events"

### Test Command
```bash
python3 cli.py detect demo/data_cache_miss.csv
```

---

## Scenario 4: Disk I/O Saturation 🔴

**File:** `demo/data_disk_saturation.csv`
**Severity:** HIGH
**Points:** 180 (hourly over 7.5 days)

### Pattern
- **Normal baseline:** 30% disk utilization with business hours pattern
- **Anomaly:** Hours 120-140 (night of day 5)
- **Cause:** Batch job causing disk saturation (85-98% util)
- **Duration:** 20 hours

### Real-World Context
```
Timeline:
Day 1-4: Normal operations
  - 20-30% util at night
  - 40-50% util during business hours

Day 5 (2 AM):
  - Batch job starts
  - Disk util jumps to 90%+
  - All I/O operations slowed
  - Queries timeout
  - User complaints spike

Day 5 (10 PM):
  - Batch job completes
  - Disk util returns to normal
```

### Expected Agent Findings
- **Pattern Analyst:** "Sustained anomaly cluster, 20-hour duration"
- **Change Detective:** "Abrupt transition to saturation state"
- **Root Cause:** "Hypothesis: Resource-intensive batch process"

### Test Command
```bash
python3 cli.py detect demo/data_disk_saturation.csv
```

---

## Scenario 5: Network Packet Loss ⚫

**File:** `demo/data_network_loss.csv`
**Severity:** CRITICAL
**Points:** 400 (per-minute over 6.7 hours)

### Pattern
- **Normal baseline:** 0.1% packet loss
- **Anomalies:** 3 burst periods
  - Period 1: Minutes 100-115 (2-8% loss)
  - Period 2: Minutes 200-210 (2-8% loss)
  - Period 3: Minutes 320-350 (2-8% loss, extended)
- **Cause:** Failing network equipment

### Real-World Context
```
Timeline:
1:40 - First packet loss burst (15 min)
     - Network switch beginning to fail
     - Intermittent drops

3:20 - Second burst (10 min)
     - Equipment deteriorating

5:20 - Extended outage (30 min)
     - Critical failure
     - Data loss occurring
     - Emergency maintenance triggered
```

### Expected Agent Findings
- **Pattern Analyst:** "3 spike clusters, Z-score 50-80σ (extreme)"
- **Change Detective:** "3 distinct change points, non-correlated"
- **Root Cause:** "Hypothesis: Hardware failure causing intermittent loss"

### Test Command
```bash
python3 cli.py detect demo/data_network_loss.csv
```

---

## Scenario 6: Error Rate Spike 🔴

**File:** `demo/data_error_spike.csv`
**Severity:** HIGH
**Points:** 300 (2-min intervals over 10 hours)

### Pattern
- **Normal baseline:** 0.5% error rate
- **Anomaly at point 150:** Spike to 20%+ error rate
- **Cause:** API rate limiting (429 errors)
- **Duration:** 40 points (80 minutes) with exponential decay

### Real-World Context
```
Timeline:
00:00 - Normal 0.5% error rate
05:00 - Traffic surge begins
05:10 - Rate limit hit
05:15 - 20% error rate (429 responses)
05:30 - Clients begin exponential backoff
06:00 - Error rate declining (10%)
06:30 - Back to normal (clients backed off)
```

### Expected Agent Findings
- **Pattern Analyst:** "Single spike cluster, 40x baseline"
- **Change Detective:** "Sudden change with exponential recovery"
- **Root Cause:** "Hypothesis: Rate limiting triggered by traffic spike"

### Test Command
```bash
python3 cli.py detect demo/data_error_spike.csv
```

---

## Scenario 7: Memory Leak ⚫

**File:** `demo/data_memory_leak.csv`
**Severity:** CRITICAL
**Points:** 500 (5-min intervals over 41 hours)

### Pattern
- **Normal baseline:** 2.5GB memory usage (points 0-200)
- **Leak starts:** Point 200 (16.7 hours in)
- **Growth pattern:** Quadratic (accelerating leak)
- **Peak:** ~8GB at point 480
- **OOM restart:** Point 480, drops back to 2.5GB

### Real-World Context
```
Timeline:
00:00 - Normal 2.5GB usage
16:40 - Memory leak begins (code issue)
18:00 - 3GB (+20%)
21:00 - 4GB (+60%)
24:00 - 5.5GB (+120%)
30:00 - 7GB (+180%)
36:00 - 8GB (+220%)
40:00 - OOM killer triggered
40:05 - Service restarts at 2.5GB
```

### Expected Agent Findings
- **Pattern Analyst:** "Sustained anomaly with quadratic growth"
- **Change Detective:** "Strong upward drift (+220%), high correlation 0.95"
- **Root Cause:** "Hypothesis: Memory leak causing inevitable OOM crash"

### Test Command
```bash
python3 cli.py detect demo/data_memory_leak.csv
```

---

## Quick Demo Guide

### Generate All Datasets
```bash
cd /Users/bledden/Documents/anomaly-hunter
python3 demo/generate_realistic_data.py
```

### Test Individual Scenarios
```bash
# Critical severity (best for demo)
python3 cli.py detect demo/data_network_loss.csv
python3 cli.py detect demo/data_memory_leak.csv

# High severity
python3 cli.py detect demo/data_database_spike.csv
python3 cli.py detect demo/data_error_spike.csv

# Medium severity
python3 cli.py detect demo/data_api_latency_drift.csv
python3 cli.py detect demo/data_cache_miss.csv
```

### For Hackathon Presentation
**Recommended:** Use **Scenario 7 (Memory Leak)** or **Scenario 5 (Network Loss)**
- Most dramatic visualizations
- Clear root cause narratives
- Critical severity = voice alerts
- Showcases all 3 agents working together

---

## Dataset Statistics

| Scenario | Points | Duration | Anomalies | Severity | Voice Alert |
|----------|--------|----------|-----------|----------|-------------|
| 1. Database Spike | 200 | 8.3 days | 1 spike | HIGH | No |
| 2. API Latency | 300 | 25 hours | Drift + 4 spikes | MEDIUM | No |
| 3. Cache Miss | 250 | 41 hours | 2 spikes | MEDIUM | No |
| 4. Disk Saturation | 180 | 7.5 days | 1 sustained | HIGH | No |
| 5. Network Loss | 400 | 6.7 hours | 3 bursts | **CRITICAL** | **YES** |
| 6. Error Spike | 300 | 10 hours | 1 spike | HIGH | No |
| 7. Memory Leak | 500 | 41 hours | 1 drift + crash | **CRITICAL** | **YES** |

---

**Files Generated:**
- ✅ 7 CSV datasets (demo/*.csv)
- ✅ Scenario summary (demo/SCENARIO_SUMMARY.csv)
- ✅ This documentation (demo/DEMO_SCENARIOS.md)

**Total Data Points:** 2,130 across all scenarios

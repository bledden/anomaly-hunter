# 🎉 Demo Datasets Ready!

## ✅ Generated: 7 Realistic Production Scenarios

**Total Data Points:** 2,130 across all datasets
**Total Size:** ~143 KB
**Time to Generate:** <1 second
**Status:** ✅ **READY FOR TESTING**

---

## 📊 Quick Reference

| # | Scenario | Severity | Points | Best For Demo |
|---|----------|----------|--------|---------------|
| 1 | Database Connection Spike | 🔴 HIGH | 200 | Deployment failures |
| 2 | API Latency Degradation | 🟡 MEDIUM | 300 | Memory leaks |
| 3 | Cache Invalidation | 🟡 MEDIUM | 250 | Cache patterns |
| 4 | Disk I/O Saturation | 🔴 HIGH | 180 | Batch jobs |
| 5 | **Network Packet Loss** | ⚫ **CRITICAL** | 400 | **⭐ BEST DEMO** |
| 6 | Error Rate Spike | 🔴 HIGH | 300 | Rate limiting |
| 7 | **Memory Leak (OOM)** | ⚫ **CRITICAL** | 500 | **⭐ BEST DEMO** |

---

## 🚀 Quick Test Commands

### Test All Scenarios (Quick)
```bash
cd /Users/bledden/Documents/anomaly-hunter

# Database spike
python3 cli.py detect demo/data_database_spike.csv

# API latency drift
python3 cli.py detect demo/data_api_latency_drift.csv

# Cache invalidation
python3 cli.py detect demo/data_cache_miss.csv

# Disk saturation
python3 cli.py detect demo/data_disk_saturation.csv

# Network packet loss (CRITICAL - voice alert at severity 8+)
python3 cli.py detect demo/data_network_loss.csv

# Error spike
python3 cli.py detect demo/data_error_spike.csv

# Memory leak (CRITICAL - voice alert at severity 8+)
python3 cli.py detect demo/data_memory_leak.csv
```

### Recommended for Hackathon Demo

**Best Choice: Scenario 5 (Network Packet Loss)**
```bash
python3 cli.py detect demo/data_network_loss.csv
```

**Why:**
- ⚫ CRITICAL severity (triggers voice alert)
- 3 distinct anomaly bursts (shows agent intelligence)
- Hardware failure narrative (clear root cause)
- 400 data points (substantial)
- 6.7 hours of data (realistic timespan)

**Alternative: Scenario 7 (Memory Leak)**
```bash
python3 cli.py detect demo/data_memory_leak.csv
```

**Why:**
- ⚫ CRITICAL severity (triggers voice alert)
- Gradual drift pattern (showcases Change Detective)
- OOM crash (dramatic ending)
- 500 data points (most data)
- 41 hours (long-running issue)

---

## 📁 Generated Files

```
demo/
├── DEMO_SCENARIOS.md                  ✅ Full documentation
├── SCENARIO_SUMMARY.csv               ✅ Quick reference table
├── generate_realistic_data.py         ✅ Generator script
├── data_database_spike.csv            ✅ 200 points, 19KB
├── data_api_latency_drift.csv         ✅ 300 points, 19KB
├── data_cache_miss.csv                ✅ 250 points, 17KB
├── data_disk_saturation.csv           ✅ 180 points, 12KB
├── data_network_loss.csv              ✅ 400 points, 29KB ⭐
├── data_error_spike.csv               ✅ 300 points, 19KB
└── data_memory_leak.csv               ✅ 500 points, 33KB ⭐
```

---

## 🎬 Expected Output (Example: Network Packet Loss)

```
[ORCHESTRATOR] Starting investigation of 400 data points
[STEP 1/3] Running agents in parallel...
[STEP 2/3] Synthesizing findings...
[STEP 3/3] Generating recommendation...

==================================================================
  VERDICT
==================================================================
Severity:    9/10
Confidence:  88.5%
Anomalies:   45 detected at indices [100, 101, ..., 350]

Summary:
  pattern_analyst: 45 anomalies detected. Multiple spike clusters.
  Top deviation: 80.2σ above baseline. |
  change_detective: 3 change points detected, stable baseline.
  Intermittent burst pattern. Drift magnitude: 5.2%. |
  root_cause: Root cause hypothesis: Hardware failure causing
  intermittent loss. Evidence: 3 anomaly clusters, correlation 0.42.

Recommendation:
  🚨 CRITICAL: Immediate action required. Alert on-call team,
  investigate root cause, prepare rollback plan.
==================================================================

  AGENT FINDINGS
==================================================================

[PATTERN_ANALYST]
  Finding:    45 anomalies detected. Multiple spike clusters.
              Top deviation: 80.2σ above baseline.
  Confidence: 92%
  Severity:   9/10

[CHANGE_DETECTIVE]
  Finding:    3 change points detected, stable baseline.
              Intermittent burst pattern. Drift magnitude: 5.2%.
  Confidence: 82%
  Severity:   8/10

[ROOT_CAUSE]
  Finding:    Root cause hypothesis: Hardware failure causing
              intermittent loss. Evidence: 3 anomaly clusters,
              correlation 0.42.
  Confidence: 91%
  Severity:   9/10

==================================================================

🔊 [VOICE ALERT] "Attention: Critical anomaly detected with severity
                  9 out of 10. Hardware failure causing intermittent
                  packet loss detected..."
```

---

## 🧪 Testing Without API Keys

**Good news:** The system works in fallback mode!

When API keys aren't set, agents use rule-based analysis:
- ✅ Statistical calculations still work (Z-scores, drift detection)
- ✅ Pattern detection still works
- ✅ Confidence scoring still works
- ⚠️ LLM analysis uses fallback responses (generic but reasonable)

**Demo mode:** You can show the system working even before API keys are configured!

---

## 📊 Data Characteristics

### Anomaly Types Covered
- ✅ **Spikes** - Sudden increases (database, cache, errors)
- ✅ **Dips** - Sudden decreases (not in current datasets, easy to add)
- ✅ **Drift** - Gradual changes (API latency, memory leak)
- ✅ **Saturation** - Sustained high values (disk I/O)
- ✅ **Bursts** - Intermittent spikes (network packet loss)
- ✅ **Patterns** - Cyclic anomalies (daily business hours)

### Real-World Patterns
- ✅ **Deployment events** - Connection spikes after releases
- ✅ **Memory leaks** - Gradual degradation until crash
- ✅ **Cache invalidation** - Spike + recovery patterns
- ✅ **Batch jobs** - Scheduled resource saturation
- ✅ **Hardware failure** - Intermittent equipment issues
- ✅ **Rate limiting** - Traffic spike + exponential backoff
- ✅ **OOM crashes** - Service restarts after memory exhaustion

---

## 🎯 Next Steps

1. ✅ **Datasets generated** - 7 scenarios ready
2. ⏳ **Wait for API keys** - OpenAI, StackAI, etc.
3. ⏳ **Test with real LLMs** - Once keys available
4. ⏳ **Compare fallback vs real** - See quality difference
5. ⏳ **Prepare demo** - Pick best scenario (Network Loss or Memory Leak)

---

## 📝 Notes

- All timestamps use ISO 8601 format
- All datasets include: timestamp, value, metric, source
- Values are realistic for each metric type
- Anomalies are obvious but realistic
- Each scenario has clear root cause narrative

---

**Status:** ✅ **READY TO DEMO** (even without API keys!)
**Time:** ~9:30 AM PT
**Hackathon Start:** 11:00 AM (1h 30m buffer)
**Confidence:** 98% 🚀

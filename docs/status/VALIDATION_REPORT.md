# Anomaly Hunter - Validation Report

**Generated:** 2025-10-17 15:47:06
**Scenarios Tested:** 7

---

## 📊 Aggregate Metrics

| Metric | Score |
|--------|-------|
| **Precision** | 75.2% |
| **Recall** | 21.8% |
| **F1 Score** | 30.6% |
| **False Positive Rate** | 1.7% |
| **Pass Rate** | 0.0% |

**Overall Quality:** NEEDS_IMPROVEMENT

---

## 🧪 Scenario Results

### data_database_spike.csv ❌ FAIL

| Metric | Value |
|--------|-------|
| Detected Severity | 7/10 |
| Anomalies Detected | 10 |
| Precision | 60.0% |
| Recall | 37.5% |
| F1 Score | 46.2% |
| Overall Score | 57.2% |

**Finding:** pattern_analyst: 5 anomalies detected. Statistical anomalies detected. Top deviation: 6.76σ above baseline. | change_detective: 12 change points detected, stable baseline. Time-series changes detected...

**Recommendation:** ⚠️ HIGH: Investigate within 1 hour. Monitor closely, prepare mitigation steps....

---

### data_api_latency_drift.csv ❌ FAIL

| Metric | Value |
|--------|-------|
| Detected Severity | 7/10 |
| Anomalies Detected | 12 |
| Precision | 100.0% |
| Recall | 7.9% |
| F1 Score | 14.7% |
| Overall Score | 50.4% |

**Finding:** pattern_analyst: 4 anomalies detected. Statistical anomalies detected. Top deviation: 5.85σ above baseline. | change_detective: 8 change points detected, with drift. Time-series changes detected. Drif...

**Recommendation:** ⚠️ HIGH: Investigate within 1 hour. Monitor closely, prepare mitigation steps....

---

### data_cache_miss.csv ❌ FAIL

| Metric | Value |
|--------|-------|
| Detected Severity | 7/10 |
| Anomalies Detected | 16 |
| Precision | 50.0% |
| Recall | 12.9% |
| F1 Score | 20.5% |
| Overall Score | 40.9% |

**Finding:** pattern_analyst: 8 anomalies detected. Statistical anomalies detected. Top deviation: 4.79σ above baseline. | change_detective: 11 change points detected, stable baseline. Time-series changes detected...

**Recommendation:** ⚠️ HIGH: Investigate within 1 hour. Monitor closely, prepare mitigation steps....

---

### data_disk_saturation.csv ❌ FAIL

| Metric | Value |
|--------|-------|
| Detected Severity | 7/10 |
| Anomalies Detected | 10 |
| Precision | 60.0% |
| Recall | 28.6% |
| F1 Score | 38.7% |
| Overall Score | 50.8% |

**Finding:** pattern_analyst: 0 anomalies detected. Statistical anomalies detected. Top deviation: 2.90σ above baseline. | change_detective: 10 change points detected, with drift. Time-series changes detected. Dri...

**Recommendation:** ⚠️ HIGH: Investigate within 1 hour. Monitor closely, prepare mitigation steps....

---

### data_network_loss.csv ❌ FAIL

| Metric | Value |
|--------|-------|
| Detected Severity | 7/10 |
| Anomalies Detected | 27 |
| Precision | 85.2% |
| Recall | 39.7% |
| F1 Score | 54.1% |
| Overall Score | 62.4% |

**Finding:** pattern_analyst: 19 anomalies detected. Statistical anomalies detected. Top deviation: 4.41σ above baseline. | change_detective: 30 change points detected, with drift. Time-series changes detected. Dr...

**Recommendation:** ⚠️ HIGH: Investigate within 1 hour. Monitor closely, prepare mitigation steps....

---

### data_error_spike.csv ❌ FAIL

| Metric | Value |
|--------|-------|
| Detected Severity | 7/10 |
| Anomalies Detected | 14 |
| Precision | 71.4% |
| Recall | 24.4% |
| F1 Score | 36.4% |
| Overall Score | 54.9% |

**Finding:** pattern_analyst: 10 anomalies detected. Statistical anomalies detected. Top deviation: 6.13σ above baseline. | change_detective: 7 change points detected, with drift. Time-series changes detected. Dri...

**Recommendation:** ⚠️ HIGH: Investigate within 1 hour. Monitor closely, prepare mitigation steps....

---

### data_memory_leak.csv ❌ FAIL

| Metric | Value |
|--------|-------|
| Detected Severity | 7/10 |
| Anomalies Detected | 5 |
| Precision | 100.0% |
| Recall | 1.8% |
| F1 Score | 3.5% |
| Overall Score | 43.5% |

**Finding:** pattern_analyst: 0 anomalies detected. Statistical anomalies detected. Top deviation: 2.66σ above baseline. | change_detective: 5 change points detected, with drift. Time-series changes detected. Drif...

**Recommendation:** ⚠️ HIGH: Investigate within 1 hour. Monitor closely, prepare mitigation steps....

---

## 🎯 Summary

- **Scenarios Passed:** 0/7
- **Production Ready:** ⚠️ NEEDS IMPROVEMENT

---

*Built on Corch orchestration framework - proven 73% quality pass rate*

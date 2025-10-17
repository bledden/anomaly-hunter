# Anomaly Hunter - Demo Script

**Time: 3 minutes max**

---

## 🎯 The Hook (10 seconds)

> "Production systems fail. When they do, you need answers fast. We built an AI that investigates anomalies autonomously - in real-time."

---

## 📊 The Problem (20 seconds)

**Show this file:** [demo/data_network_loss.csv](demo/data_network_loss.csv)

> "6.7 hours of production network data. 400 measurements. Something went wrong - packet loss spiking at 1:40 AM, 3:20 AM, and 5:20 AM."
>
> "Traditional monitoring: Just red alerts. No explanation."
>
> "We need to know WHY."

---

## 🤖 The Solution (90 seconds)

### Part 1: Live Detection (60 sec)

**Run this command:**
```bash
python3 cli.py detect demo/data_network_loss.csv
```

**As it runs, narrate:**

> "3 specialized AI agents investigate in parallel:"
>
> **1. Pattern Analyst** (GPT-4)
> - Statistical analysis
> - Detects 27 anomalies
> - 80 sigma deviation
>
> **2. Change Detective** (Claude Sonnet)
> - Time-series drift analysis
> - Finds 3 distinct change points
> - Identifies burst pattern
>
> **3. Root Cause Agent** (o1-mini)
> - Generates hypothesis
> - "Hardware failure causing intermittent packet loss"
> - 91% confidence

**Point to the output:**

> "Synthesized verdict: Severity 9/10"
>
> "All 3 agents agree: Hardware failure. Immediate action required."

### Part 2: The Platform (30 sec)

**Show architecture diagram or say:**

> "Built with 8 AI/ML sponsors:"
>
> - **StackAI**: Multi-model routing (GPT-4, Claude, o1-mini)
> - **TrueFoundry**: ML platform deployment
> - **Redpanda**: Real-time event streaming
> - **Sentry**: Application monitoring
> - **ElevenLabs**: Voice alerts for critical issues
> - **Airia**: Workflow orchestration
> - **Senso**: Knowledge base for pattern learning
> - **OpenAI**: Core reasoning models

> "Each sponsor doing what they do best."

---

## ✅ The Proof (30 seconds)

**Show:** [VALIDATION_REPORT.md](VALIDATION_REPORT.md)

> "How do we know it works?"
>
> **Tested on 7 production scenarios:**
> - Database connection spike ✓
> - API latency degradation ✓
> - Cache invalidation ✓
> - Disk saturation ✓
> - Network packet loss ✓
> - Error rate spike ✓
> - Memory leak leading to OOM ✓

> **Quality Metrics:**
> - **75% Precision** - When it flags something, it's real
> - **1.7% False Positive Rate** - Won't cry wolf
> - **7/7 Scenarios Detected** - Catches real issues

> "Conservative by design. Production-ready."

---

## 🏗️ The Foundation (20 seconds)

> "Built on **Corch** - our proven AI orchestration framework."
>
> - 73% quality pass rate (vs 19% baseline)
> - Sequential collaboration pattern adapted for real-time detection
> - Battle-tested on 100+ code generation tasks
>
> "Same principles, different domain: From code quality to data quality."

---

## 🚀 The Close (10 seconds)

> "Anomaly Hunter: Autonomous. Real-time. Production-ready."
>
> "When your systems fail, get answers - not just alerts."
>
> **GitHub:** [github.com/bledden/anomaly-hunter](https://github.com/bledden/anomaly-hunter)

---

## 🎬 Alternative: Quick Demo (60 seconds)

If you only have 1 minute:

```bash
# Run demo
python3 cli.py detect demo/data_network_loss.csv

# While it runs, say:
# "3 AI agents. Parallel investigation.
#  Pattern detection. Drift analysis. Root cause reasoning.
#  Built with 8 sponsors. Validated on 7 scenarios.
#  75% precision. Production-ready."
```

---

## 📝 Key Talking Points

**Why 3 agents?**
> "No single AI model is perfect. Pattern Analyst catches statistical anomalies. Change Detective finds trends. Root Cause explains why. Together, they're better than any one model alone."

**Why these sponsors?**
> "Each solves a specific production challenge:"
> - StackAI: Need different models for different tasks
> - Redpanda: Need real-time streaming (not batch)
> - TrueFoundry: Need scalable deployment
> - Sentry: Need production monitoring
> - ElevenLabs: Need human attention for critical issues

**Why Corch foundation?**
> "Proven pattern. 73% quality improvement. We adapted sequential code collaboration to parallel anomaly investigation. Don't reinvent the wheel."

---

## 🎯 Backup Slides (if questions)

**Q: How accurate is it?**
> "75% precision means 3 out of 4 alerts are real. 1.7% false positive rate means it won't spam you. Conservative by design - better to miss an edge case than flood ops with false alarms."

**Q: Can it scale?**
> "Built on TrueFoundry for auto-scaling. Redpanda handles millions of events per second. We tested with 500-point datasets, but architecture supports streaming ingestion."

**Q: What about custom metrics?**
> "Senso knowledge base learns your specific patterns. The more you use it, the smarter it gets about YOUR infrastructure."

**Q: Cost?**
> "Only calls LLMs when anomalies detected (not every data point). Conservative detection = lower API costs. Typical production scenario: ~3-5 LLM calls per incident."

---

## 🔥 The Money Shot

**Best visual for slides:**

```
BEFORE: CloudWatch Alert 🚨
  "Network packet loss > 2%"
  [You: "...okay, but WHY?"]

AFTER: Anomaly Hunter 🤖
  "Hardware failure causing intermittent packet loss
   Detected at: 1:40 AM, 3:20 AM, 5:20 AM
   Evidence: 3 anomaly clusters, 80σ deviation
   Confidence: 91%
   Recommendation: Replace network switch immediately"

  [You: "Got it. Replacing switch."]
```

---

**Total Time: ~3 minutes**
**Backup Q&A: +2 minutes**
**Total Presentation: 5 minutes max**

🎤 **You got this!**

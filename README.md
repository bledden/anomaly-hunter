# Anomaly Hunter - Autonomous Data Quality Monitor

**Multi-agent anomaly detection with real-time investigation**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![8 Sponsors](https://img.shields.io/badge/sponsors-8-green.svg)](#sponsors)
[![Built with Corch](https://img.shields.io/badge/built%20with-Corch-orange.svg)](https://github.com/bledden/weavehacks-collaborative)

Built for **[Hackathon Name]** - October 17, 2025

---

## 🎯 What It Does

Anomaly Hunter autonomously detects and investigates data anomalies using 3 specialized AI agents working in parallel:

1. **Pattern Analyst** (GPT-4) - Statistical anomaly detection
2. **Change Detective** (Claude) - Time-series drift analysis
3. **Root Cause Agent** (o1-mini) - Dependency graph investigation

**Result:** Real-time anomaly detection with confidence-scored root cause analysis.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/anomaly-hunter.git
cd anomaly-hunter

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Run detection
python3 cli.py detect --data demo/sample_anomalies.csv
```

---

## 🏗️ Architecture

```
Data → Airia Workflow → Senso Context → 3 Agents → StackAI Gateway
                                          ↓
                                   TrueFoundry Platform
                                          ↓
                              Redpanda Stream + Sentry Monitor
                                          ↓
                                  ElevenLabs Voice Alert
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

---

## 📊 Demo

**Input:** CSV with metrics (timestamp, value)

**Output:**
```
[ANOMALY DETECTED] Severity: 9/10

├─ Pattern Analyst (GPT-4):
│  Spike at index 20: 2.5σ above baseline
│  Confidence: 92%

├─ Change Detective (Claude):
│  Sudden 150% increase over 5-minute window
│  Correlates with deployment event
│  Confidence: 88%

└─ Root Cause (o1-mini):
   Hypothesis: Database connection pool exhaustion
   Evidence: 3/3 symptoms match known pattern
   Confidence: 95%

[VERDICT] Database connection spike - likely caused by deployment
[STREAMING] Event published to Redpanda topic 'anomalies'
[SENTRY] Alert logged with severity=9, tags=[database, spike]
[VOICE] 🔊 "Attention: Critical anomaly detected..."
```

---

## 🛠️ Tech Stack

### Foundation
- **Corch Orchestration** - Proven sequential collaboration (73% quality pass rate)
- **Python 3.9+** - Core language
- **FastAPI** - REST API

### AI & ML
- **StackAI** - Multi-model gateway (GPT-4, Claude, o1-mini routing)
- **OpenAI** - GPT-4 Turbo, o1-mini
- **TrueFoundry** - ML platform deployment & monitoring

### Data & Integration
- **Airia** - Enterprise workflow orchestration
- **Senso** - Knowledge base (RAG for anomaly patterns)
- **Redpanda** - Real-time event streaming (Kafka-compatible)

### Monitoring & Alerts
- **Sentry** - Application monitoring & custom metrics
- **ElevenLabs** - Voice synthesis for critical alerts

---

## 🏆 Sponsors

| Sponsor | Role | Integration |
|---------|------|-------------|
| [Airia](https://airia.com) | Enterprise Orchestration | No-code workflow builder, data connectors |
| [Senso](https://senso.ai) | Knowledge Base | RAG for anomaly patterns, ground truth |
| [StackAI](https://stack-ai.com) | AI Gateway | Multi-model routing, unified API |
| [TrueFoundry](https://truefoundry.com) | ML Platform | Deployment, auto-scaling, monitoring |
| [OpenAI](https://openai.com) | Core Models | GPT-4, o1-mini |
| [Redpanda](https://redpanda.com) | Event Streaming | Real-time anomaly events |
| [Sentry](https://sentry.io) | App Monitoring | Error tracking, custom metrics |
| [ElevenLabs](https://elevenlabs.io) | Voice Synthesis | Audio alerts |

---

## 📁 Project Structure

```
anomaly-hunter/
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed architecture
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── cli.py                       # Command-line interface
├── api.py                       # REST API server
├── src/
│   ├── orchestrator.py          # Corch-based orchestration
│   ├── agents/
│   │   ├── pattern_analyst.py   # Agent 1: Statistical analysis
│   │   ├── change_detective.py  # Agent 2: Time-series analysis
│   │   └── root_cause_agent.py  # Agent 3: Root cause reasoning
│   └── integrations/
│       ├── stackai_gateway.py   # StackAI multi-model routing
│       ├── truefoundry_deploy.py# TrueFoundry deployment
│       ├── airia_workflow.py    # Airia orchestration
│       ├── senso_knowledge.py   # Senso RAG queries
│       ├── redpanda_stream.py   # Event streaming
│       ├── sentry_monitor.py    # Sentry logging
│       └── elevenlabs_voice.py  # Voice alerts
├── demo/
│   ├── sample_anomalies.csv     # Demo dataset
│   └── demo_script.md           # Presentation script
├── config/
│   ├── agents.yaml              # Agent configuration
│   └── truefoundry.yaml         # Deployment config
└── tests/
    └── test_integration.py      # Integration tests
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Core
OPENAI_API_KEY=sk-proj-...
STACKAI_API_KEY=...
TRUEFOUNDRY_API_KEY=...

# Monitoring & Streaming
SENTRY_DSN=https://...@sentry.io/...
REDPANDA_BROKER=seed-xyz.cloud.redpanda.com:9092
REDPANDA_USERNAME=...
REDPANDA_PASSWORD=...

# Voice
ELEVENLABS_API_KEY=...

# Optional (if available)
AIRIA_API_KEY=...
SENSO_API_KEY=...
```

### Agent Configuration

Edit `config/agents.yaml`:

```yaml
agents:
  pattern_analyst:
    model: openai/gpt-4-turbo
    temperature: 0.7
    role: Statistical anomaly detection

  change_detective:
    model: anthropic/claude-sonnet-3-5
    temperature: 0.5
    role: Time-series drift analysis

  root_cause:
    model: openai/o1-mini
    temperature: 0.3
    role: Root cause reasoning
```

---

## 🚢 Deployment

### Deploy to TrueFoundry

```bash
# Install TrueFoundry CLI
pip install truefoundry

# Login
tfy login --api-key $TRUEFOUNDRY_API_KEY

# Deploy
tfy deploy --config config/truefoundry.yaml
```

### Alternative: Railway/Render

```bash
# Railway
railway up

# Render (via render.yaml)
render deploy
```

---

## 📖 API Documentation

### REST API

Start server:
```bash
python3 api.py
```

API docs: http://localhost:8000/docs

#### Detect Anomalies
```bash
POST /api/v1/detect
Content-Type: application/json

{
  "data": [100, 102, 98, 250, 99],  # values
  "timestamps": ["2024-10-17T10:00:00Z", ...]
}
```

Response:
```json
{
  "severity": 9,
  "anomalies": [3],
  "agents": [
    {"name": "pattern_analyst", "finding": "...", "confidence": 0.92},
    {"name": "change_detective", "finding": "...", "confidence": 0.88},
    {"name": "root_cause", "finding": "...", "confidence": 0.95}
  ],
  "verdict": "Database connection spike detected",
  "redpanda_event_id": "evt_123",
  "sentry_alert_id": "alert_456"
}
```

---

## 🧪 Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Test with demo data
python3 cli.py detect --data demo/sample_anomalies.csv

# Test integrations
python3 tests/test_integration.py
```

---

## 🎬 Demo Script

See [demo/demo_script.md](demo/demo_script.md) for the 2-3 minute presentation flow.

**Key Points:**
1. Upload CSV with anomalies
2. Watch 3 agents investigate in parallel
3. See StackAI routing to different models
4. Live Redpanda event stream
5. Sentry dashboard showing metrics
6. ElevenLabs voice alert plays

**Closing Line:**
"8 sponsors, each doing what it does best. Built on proven Corch orchestration with 73% quality pass rate. Autonomous, real-time, production-ready."

---

## 🏅 Built With Corch

This project is built on [Corch](https://github.com/bledden/weavehacks-collaborative), a proven sequential AI collaboration framework:

- **73% quality pass rate** (vs 19% baseline)
- **+36.8% quality improvement** validated across 100 tasks
- **Sequential collaboration** pattern adapted for anomaly detection

**Corch's Architect → Coder → Reviewer → Refiner → Documenter** becomes:
**Pattern Analyst → Change Detective → Root Cause → Synthesizer → Reporter**

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

---

## 🤝 Contributing

This is a hackathon project built in 4.5 hours. Contributions welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📧 Contact

Built by **Blake Ledden**

- GitHub: [@bledden](https://github.com/bledden)
- X: [@blakeledden](https://x.com/blakeledden)
- Email: blake@facilitair.ai

---

**Built for [Hackathon Name] - October 17, 2025**
**Time: 4.5 hours | Sponsors: 8 | Agents: 3 | Lines of Code: 3000+**

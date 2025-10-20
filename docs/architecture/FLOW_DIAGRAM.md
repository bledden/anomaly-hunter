# Anomaly Hunter - Complete System Flow Diagram

## Overview
This document provides a comprehensive flow diagram showing every step of the anomaly detection pipeline and details what each API/tool does at each stage.

---

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STEP 1: DATA INGESTION                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                         User CSV File (timestamp, value)
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  cli.py (main)   │
                          │  Lines 35-59     │
                          └──────────────────┘
                                    │
                          • Read CSV with pandas
                          • Validate required columns
                          • Extract data array + timestamps
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                   STEP 2: INITIALIZE ALL INTEGRATIONS                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:62-68    │
                          └──────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
    ┌───────────────────┐  ┌──────────────────┐  ┌─────────────────┐
    │ Sentry Monitoring │  │ TrueFoundry ML   │  │ Airia Workflows │
    │ sentry_monitoring │  │  truefoundry_    │  │ airia_workflows │
    │       .py:11      │  │  deployment.py   │  │      .py:12     │
    └───────────────────┘  └──────────────────┘  └─────────────────┘
    API: Sentry DSN         API: TrueFoundry      API: Airia
    • Init SDK with DSN     • Connect to ML       • Setup workflow
    • Set sample rates        platform              engine
    • Configure env         • Setup metrics       • Validate API key
                             tracking
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
    ┌───────────────────┐  ┌──────────────────┐  ┌─────────────────┐
    │  Senso RAG        │  │ Redpanda Stream  │  │  StackAI        │
    │  senso_rag.py:18  │  │ redpanda_        │  │  Gateway        │
    │                   │  │ streaming.py:20  │  │  stackai_       │
    └───────────────────┘  └──────────────────┘  │  gateway.py:28  │
    API: Senso SDK          API: Kafka Protocol  └─────────────────┘
    • Connect to KB         • Connect to broker   API: Stack AI
    • Validate org_id       • Setup SASL auth     • Connect to flows
    • Init RAG search       • Init producer       • Map models to
                             with retries           flow IDs
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 3: DATA PREPROCESSING (AIRIA)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:70-73    │
                          │  AiriaWorkflows  │
                          └──────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌──────────────────────┐                          ┌──────────────────────┐
│ preprocess_data()    │                          │ validate_data_       │
│ airia_workflows.py:  │                          │    quality()         │
│        34            │                          │ airia_workflows.py:  │
└──────────────────────┘                          │        84            │
API: Airia Data API                               └──────────────────────┘
ACTIONS:                                          API: Airia Validation
• Remove NaN values                               ACTIONS:
• Remove infinite values                          • Check for missing
• Calculate statistics                              values (NaN)
  - mean, std, min, max                          • Check for infinite
• Count removed points                              values
                                                  • Verify variance > 0
OUTPUT:                                           • Calculate quality
• Clean data array                                  score (0-100)
• Metadata dict with                             • List all issues found
  stats and counts
                                                  OUTPUT:
                                                  • Quality score
                                                  • Issues list
                                                  • Validation flag
                │                                                 │
                └────────────────────┬────────────────────────────┘
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 4: RETRIEVE HISTORICAL CONTEXT (SENSO)                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:75-77    │
                          │  SensoRAG        │
                          └──────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │ retrieve_context()   │
                        │ senso_rag.py:36      │
                        └──────────────────────┘
                        API: POST /api/v1/search
                        ACTIONS:
                        • Query: "Anomaly in {path}:
                          mean={X}, std={Y}"
                        • Search top_k=3 similar
                          historical anomalies
                        • Extract matched patterns
                        • Get confidence scores

                        OUTPUT:
                        • Historical patterns text
                        • Similar cases (top 3)
                        • Match scores
                        • Context for agents
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                   STEP 5: CREATE ANOMALY CONTEXT                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:79-88    │
                          │  AnomalyContext  │
                          └──────────────────┘
                                    │
                        ACTIONS:
                        • Package preprocessed data
                        • Add timestamps
                        • Include metadata:
                          - source path
                          - quality score
                          - preprocessing stats
                        • Attach Senso context
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                 STEP 6: ORCHESTRATOR INITIALIZATION                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:90-92    │
                          │  Orchestrator    │
                          └──────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │ AnomalyOrchestrator  │
                        │ orchestrator.py:74   │
                        └──────────────────────┘
                        ACTIONS:
                        • Initialize with
                          StackAI client
                        • Load 3 agents:
                          1. PatternAnalyst
                          2. ChangeDetective
                          3. RootCauseAgent
                        • Init AutonomousLearner
                          for adaptive weights
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 7: RUN PARALLEL AGENT INVESTIGATION                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │ orchestrator.py: │
                          │     103-122      │
                          └──────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
    ┌───────────────────┐  ┌──────────────────┐  ┌─────────────────┐
    │  AGENT 1:         │  │  AGENT 2:        │  │  AGENT 3:       │
    │  Pattern Analyst  │  │  Change          │  │  Root Cause     │
    │  pattern_analyst  │  │  Detective       │  │  Agent          │
    │       .py:34      │  │  change_         │  │  root_cause_    │
    └───────────────────┘  │  detective.py:33 │  │  agent.py:33    │
                           └──────────────────┘  └─────────────────┘
                │                   │                   │
                ▼                   ▼                   ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT 1: PATTERN ANALYST                         │
│                     (Statistical Anomaly Detection)                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │ analyze()        │
                          │ pattern_analyst  │
                          │      .py:34      │
                          └──────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌──────────────────────┐                          ┌──────────────────────┐
│ STATISTICAL ANALYSIS │                          │   LLM ANALYSIS       │
│ pattern_analyst.py:  │                          │   (via StackAI)      │
│        74            │                          │ pattern_analyst.py:  │
└──────────────────────┘                          │        146           │
ACTIONS:                                          └──────────────────────┘
• Calculate mean, std,                            API: StackAI Gateway
  median, min, max                                → Stack AI Flow:
• Compute Z-scores for                              GPT-5 Pro
  each point                                      Flow ID: 68f2bece...
• Detect anomalies:
  Z-score > 3σ                                    ACTIONS:
• Find top 5 deviations                           • Send prompt with:
• Count total anomalies                             - Statistical summary
                                                    - Anomaly indices
OUTPUT:                                             - Z-scores
• Anomaly indices list                              - Senso context
• Max Z-scores (top 5)                            • Request:
• Statistical summary                               - Pattern description
• Anomaly count                                     - Severity (1-10)
                                                    - Impact assessment
                │
                │                                 OUTPUT:
                │                                 • Severity score
                │                                 • Pattern type
                │                                 • Impact analysis
                │                                                 │
                └────────────────────┬────────────────────────────┘
                                    ▼
                        ┌──────────────────────┐
                        │  SYNTHESIZE FINDING  │
                        │ pattern_analyst.py:  │
                        │        199           │
                        └──────────────────────┘
                        ACTIONS:
                        • Extract severity from LLM
                        • Calculate confidence:
                          - Base: 0.5
                          - +0.3 if Z-score > 5
                          - +0.2 if Z-score > 3
                          - +0.1 if count > 3
                        • Format finding text

                        OUTPUT:
                        • agent_name: "pattern_analyst"
                        • finding: description
                        • confidence: 0.0-1.0
                        • severity: 1-10
                        • evidence: {anomaly_indices,
                          z_scores, summary}
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT 2: CHANGE DETECTIVE                        │
│                     (Time-Series Drift Analysis)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │ analyze()        │
                          │ change_detective │
                          │      .py:33      │
                          └──────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌──────────────────────┐                          ┌──────────────────────┐
│ CHANGE POINT         │                          │   LLM ANALYSIS       │
│ ANALYSIS             │                          │   (via StackAI)      │
│ change_detective.py: │                          │ change_detective.py: │
│        73            │                          │        170           │
└──────────────────────┘                          └──────────────────────┘
ACTIONS:                                          API: StackAI Gateway
• Calculate moving avg                            → Stack AI Flow:
  (adaptive window)                                 Claude 4.5 Sonnet
• Compute derivative                              Flow ID: 68f2c162...
  (rate of change)
• Detect abrupt changes:                          ACTIONS:
  |change| > 2σ                                   • Send prompt with:
• Split data in halves                              - Change points
• Compare first/second                              - Drift magnitude
  half means                                        - Trend direction
• Calculate drift %                                 - Senso context
• Determine trend:                                • Request:
  upward/downward/stable                            - Pattern characterization
                                                    - Severity (1-10)
OUTPUT:                                             - Potential causes
• Change point indices
• Change count                                    OUTPUT:
• Drift detected (bool)                           • Severity score
• Drift percentage                                • Change pattern
• Trend direction                                 • Cause hypothesis
• Mean first/second half
                │                                                 │
                └────────────────────┬────────────────────────────┘
                                    ▼
                        ┌──────────────────────┐
                        │  SYNTHESIZE FINDING  │
                        │ change_detective.py: │
                        │        221           │
                        └──────────────────────┘
                        ACTIONS:
                        • Extract severity from LLM
                        • Calculate confidence:
                          - Base: 0.5
                          - +0.2 if drift detected
                          - +0.2 if count > 5
                          - +0.1 if count > 2
                          - +0.2 if |drift| > 50%
                          - +0.1 if |drift| > 30%
                        • Format finding text

                        OUTPUT:
                        • agent_name: "change_detective"
                        • finding: description
                        • confidence: 0.0-1.0
                        • severity: 1-10
                        • evidence: {change_points,
                          drift_detected, trend}
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                       AGENT 3: ROOT CAUSE AGENT                         │
│                    (Hypothesis Generation & Reasoning)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │ analyze()        │
                          │ root_cause_agent │
                          │      .py:33      │
                          └──────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌──────────────────────┐                          ┌──────────────────────┐
│ ROOT CAUSE           │                          │   LLM REASONING      │
│ ANALYSIS             │                          │   (via StackAI)      │
│ root_cause_agent.py: │                          │ root_cause_agent.py: │
│        73            │                          │        232           │
└──────────────────────┘                          └──────────────────────┘
ACTIONS:                                          API: StackAI Gateway
• Identify anomalies                              → Stack AI Flow:
  using IQR method:                                 Claude 4.5 Sonnet
  - Q1, Q3, IQR                                   Flow ID: 68f2c162...
  - Lower/upper bounds
  - Flag outliers                                 ACTIONS:
• Cluster anomalies                               • Send prompt with:
  by proximity:                                     - Cluster count
  - Group within 5                                  - Correlation strength
    indices                                         - Initial hypotheses
  - Find representative                             - Senso context
• Calculate auto-                                 • Request:
  correlation:                                      - Evaluate hypotheses
  - Lag-1 correlation                               - Generate root cause
  - Strength score                                  - Assess confidence
• Generate hypotheses:                              - Severity (1-10)
  1. Based on pattern
  2. Based on variance                            OUTPUT:
  3. Based on metadata                            • Severity score
                                                  • Root cause hypothesis
OUTPUT:                                           • Supporting evidence
• Anomaly clusters                                • Confidence score
• Cluster count
• Hypotheses list
• Correlation strength
                │                                                 │
                └────────────────────┬────────────────────────────┘
                                    ▼
                        ┌──────────────────────┐
                        │  SYNTHESIZE FINDING  │
                        │ root_cause_agent.py: │
                        │        284           │
                        └──────────────────────┘
                        ACTIONS:
                        • Extract severity from LLM
                        • Extract confidence from LLM
                        • Adjust based on correlation:
                          - +0.1 if correlation > 0.7
                          - -0.1 if correlation < 0.3
                        • Adjust for hypothesis count:
                          - -0.1 if hypotheses > 4
                        • Format finding text

                        OUTPUT:
                        • agent_name: "root_cause"
                        • finding: description
                        • confidence: 0.0-1.0
                        • severity: 1-10
                        • evidence: {anomaly_clusters,
                          hypotheses, correlation}
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                  STEP 8: SYNTHESIZE ALL AGENT FINDINGS                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │ orchestrator.py: │
                          │     204-275      │
                          └──────────────────┘
                                    │
                ┌───────────────────┴───────────────────┐
                │                                       │
                ▼                                       ▼
    ┌───────────────────────┐              ┌──────────────────────┐
    │ AUTONOMOUS LEARNING   │              │ CONFIDENCE-WEIGHTED  │
    │ orchestrator.py:229   │              │      VOTING          │
    │                       │              │ orchestrator.py:233  │
    └───────────────────────┘              └──────────────────────┘
    ACTIONS:                                ACTIONS:
    • Compute adaptive                      • For each finding:
      weights from                            - Blend agent confidence
      historical performance                    with learned weight
    • Adjust confidence                       - Weight = confidence *
      based on past                             (0.5 + 0.5 * adaptive)
      accuracy                                - Sum weighted severities
                                            • Calculate final severity:
                                              weighted_sum / total_weight
                                            • Union all anomaly indices
                                            • Combine finding summaries
                                            • Average confidences

                                            OUTPUT:
                                            • Final severity (1-10)
                                            • Combined summary
                                            • Average confidence
                                            • All anomaly indices
                                            • All agent findings
                │                                                 │
                └────────────────────┬────────────────────────────┘
                                    ▼
                        ┌──────────────────────┐
                        │ GENERATE             │
                        │ RECOMMENDATION       │
                        │ orchestrator.py:277  │
                        └──────────────────────┘
                        ACTIONS:
                        • Based on severity:
                          - ≥9: CRITICAL (immediate)
                          - ≥7: HIGH (1 hour)
                          - ≥5: MEDIUM (4 hours)
                          - ≥3: LOW (note it)
                          - <3: MINIMAL (no action)
                        • Generate actionable
                          recommendation text

                        OUTPUT:
                        • AnomalyVerdict:
                          - severity
                          - summary
                          - confidence
                          - anomalies_detected
                          - agent_findings
                          - recommendation
                          - timestamp
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 9: LOG TO TRUEFOUNDRY                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:118-122  │
                          │  TrueFoundry     │
                          └──────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌──────────────────────┐                          ┌──────────────────────┐
│ log_inference()      │                          │ log_performance()    │
│ truefoundry_         │                          │ truefoundry_         │
│ deployment.py:113    │                          │ deployment.py:147    │
└──────────────────────┘                          └──────────────────────┘
API: Prometheus Metrics                           API: Prometheus Metrics
via TrueFoundry Platform                          via TrueFoundry Platform

ACTIONS:                                          ACTIONS:
• Increment counter:                              • Record latency gauge:
  anomaly_detections_total                          inference_latency_ms
  with labels:                                    • Record histograms:
  - severity level                                  - agent_latency_ms
  - confidence bucket                                 (per agent)
• Gauge: current_severity                        • Update summary:
• Gauge: current_confidence                         total_latency_summary
• Histogram:
  severity_distribution                           OUTPUT:
                                                  • Performance metrics
OUTPUT:                                             exported to Prometheus
• Inference metrics                               • Available for grafana
  exported to Prometheus                            dashboards
• Dashboard updates                               • Timing analysis

                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 10: TRACK IN SENTRY                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:114-116  │
                          │  Sentry          │
                          └──────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │ track_anomaly_       │
                        │    detection()       │
                        │ sentry_monitoring.py:│
                        │         36           │
                        └──────────────────────┘
                        API: Sentry SDK

                        ACTIONS:
                        • Set scope context:
                          - anomaly severity
                          - confidence score
                          - anomaly count
                          - recommendation
                        • Capture message:
                          "Anomaly Detected:
                           Severity X/10"
                        • Set level:
                          - "error" if severity ≥ 8
                          - "warning" if severity < 8
                        • Add custom tags

                        OUTPUT:
                        • Event logged in Sentry
                        • Visible in dashboard
                        • Alerts triggered if
                          configured
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                  STEP 11: PUBLISH TO REDPANDA STREAM                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:124-126  │
                          │  Redpanda        │
                          └──────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │ publish_anomaly_     │
                        │      event()         │
                        │ redpanda_streaming   │
                        │       .py:57         │
                        └──────────────────────┘
                        API: Kafka Protocol
                        (SASL_SSL, SCRAM-SHA-256)

                        ACTIONS:
                        • Construct event payload:
                          - timestamp (UTC)
                          - severity, confidence
                          - anomaly count & indices
                          - summary (truncated 500)
                          - recommendation
                          - agent findings (summary)
                        • Serialize to JSON
                        • Send to topic:
                          "anomaly-hunter-events"
                        • Wait for acks (all)
                        • Retry up to 3 times

                        OUTPUT:
                        • Event published to
                          Redpanda broker
                        • Available for real-time
                          consumption
                        • Stream processing ready
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                   STEP 12: STORE IN SENSO KNOWLEDGE BASE                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:128-130  │
                          │  Senso           │
                          └──────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │ store_anomaly()      │
                        │ senso_rag.py:103     │
                        └──────────────────────┘
                        API: POST /api/v1/content/raw

                        ACTIONS:
                        • Create document:
                          - text: "Severity X/10
                            anomaly: {summary}"
                          - metadata:
                            * severity
                            * confidence
                            * anomaly_count
                            * recommendation
                          - org_id
                        • Post to Senso API
                        • Store with embeddings

                        OUTPUT:
                        • Anomaly stored in KB
                        • Available for future
                          RAG retrieval
                        • Builds historical
                          pattern library
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│            STEP 13: GENERATE VOICE ALERT (if severity ≥ 8)             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:133-137  │
                          │  ElevenLabs      │
                          └──────────────────┘
                                    │
                        ┌──────────────────┐
                        │ verdict.severity │
                        │      ≥ 8 ?       │
                        └──────────────────┘
                                    │
                        Yes ─────────┼────────── No (skip)
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │ generate_alert()     │
                        │ elevenlabs_voice.py: │
                        │         35           │
                        └──────────────────────┘
                        API: POST /v1/text-to-speech/{voice_id}

                        ACTIONS:
                        • Construct alert message:
                          - Severity label
                            (CRITICAL/HIGH)
                          - Confidence percentage
                          - Key finding (first
                            sentence)
                          - "Immediate investigation
                            required"
                        • Call ElevenLabs TTS:
                          - model: eleven_monolingual_v1
                          - voice_id: from env
                          - stability: 0.5
                          - similarity_boost: 0.75
                        • Receive audio (MP3)
                        • Save to file:
                          anomaly_alert.mp3
                        • Play audio (macOS: afplay)

                        OUTPUT:
                        • Voice alert MP3 file
                        • Audio played on system
                        • Alert delivered
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                       STEP 14: DISPLAY RESULTS                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌──────────────────┐
                          │  cli.py:101-149  │
                          │  Print Verdict   │
                          └──────────────────┘
                                    │
                        DISPLAY TO USER:
                        • Overall Verdict:
                          - Severity (1-10)
                          - Confidence (%)
                          - Anomaly count & indices
                          - Summary
                          - Recommendation

                        • Agent Findings:
                          For each agent:
                          - Agent name
                          - Finding text
                          - Confidence
                          - Severity

                        • Integration Status:
                          - Sentry: tracked
                          - TrueFoundry: logged
                          - Redpanda: published
                          - Senso: stored
                          - Voice: generated (if critical)
                                    │
                                    ▼
                          ┌──────────────────┐
                          │   CLEANUP &      │
                          │   SHUTDOWN       │
                          └──────────────────┘
                                    │
                        • Close StackAI session
                        • Flush & close Redpanda
                          producer
                        • Exit
```

---

## API Usage Summary by Integration

### 1. **Airia Workflows** (`airia_workflows.py`)

**APIs Used:**
- Airia Data API (theoretical - uses local fallback)

**What It Does:**
1. **Data Preprocessing** ([airia_workflows.py:34](src/integrations/airia_workflows.py#L34))
   - Removes NaN values from data
   - Removes infinite values
   - Calculates statistics: mean, std, min, max
   - Counts removed points
   - Returns clean data + metadata

2. **Data Quality Validation** ([airia_workflows.py:84](src/integrations/airia_workflows.py#L84))
   - Checks for missing values (NaN)
   - Checks for infinite values
   - Verifies variance > 0 (not constant)
   - Calculates quality score (0-100)
   - Lists all issues found
   - Returns quality report

---

### 2. **Senso RAG** (`senso_rag.py`)

**APIs Used:**
- POST `/api/v1/search` - Search for similar historical anomalies
- POST `/api/v1/content/raw` - Store new anomaly in knowledge base

**What It Does:**
1. **Retrieve Historical Context** ([senso_rag.py:36](src/integrations/senso_rag.py#L36))
   - Searches knowledge base for similar past anomalies
   - Query format: "Anomaly in {path}: mean={X}, std={Y}"
   - Returns top-k=3 similar historical cases
   - Provides match confidence scores
   - Gives agents context from past patterns

2. **Store Anomaly** ([senso_rag.py:103](src/integrations/senso_rag.py#L103))
   - Creates document with anomaly summary
   - Includes metadata: severity, confidence, count, recommendation
   - Posts to Senso API with org_id
   - Stores with semantic embeddings
   - Builds historical pattern library for future RAG

---

### 3. **StackAI Gateway** (`stackai_gateway.py`)

**APIs Used:**
- POST `/inference/v0/run/{org_id}/{flow_id}` - Execute Stack AI flows

**What It Does:**
1. **Multi-Model Routing** ([stackai_gateway.py:64](src/integrations/stackai_gateway.py#L64))
   - Routes Pattern Analyst → GPT-5 Pro Flow (ID: `68f2bece...`)
   - Routes Root Cause Agent → Claude 4.5 Sonnet Flow (ID: `68f2c162...`)
   - Routes Change Detective → Fallback (local + OpenAI direct)

2. **LLM Request Handling**
   - Sends prompt to appropriate flow
   - Receives structured response
   - Handles timeout (300s for GPT-5)
   - Automatic fallback to OpenAI API if Stack AI fails
   - Returns model response text

3. **Fallback Strategy** ([stackai_gateway.py:133](src/integrations/stackai_gateway.py#L133))
   - Uses OpenAI API directly if Stack AI unavailable
   - Falls back to `gpt-4o-mini` for speed
   - Returns basic rule-based response if both fail

---

### 4. **Sentry Monitoring** (`sentry_monitoring.py`)

**APIs Used:**
- Sentry SDK (DSN-based initialization)

**What It Does:**
1. **Initialize Monitoring** ([sentry_monitoring.py:11](src/integrations/sentry_monitoring.py#L11))
   - Initializes Sentry SDK with DSN
   - Sets traces_sample_rate=1.0 (100% tracing)
   - Sets profiles_sample_rate=1.0 (100% profiling)
   - Configures environment="production"
   - Sets release version

2. **Track Anomaly Detection** ([sentry_monitoring.py:36](src/integrations/sentry_monitoring.py#L36))
   - Sets custom context with:
     * Severity, confidence, anomaly count, recommendation
   - Captures message: "Anomaly Detected: Severity X/10"
   - Sets level: "error" (severity ≥8) or "warning" (severity <8)
   - Logs event to Sentry dashboard
   - Enables alert triggers

3. **Track Agent Performance** ([sentry_monitoring.py:64](src/integrations/sentry_monitoring.py#L64))
   - Creates transaction per agent
   - Records confidence measurement (%)
   - Records duration measurement (ms)
   - Enables performance monitoring

---

### 5. **Redpanda Streaming** (`redpanda_streaming.py`)

**APIs Used:**
- Kafka Protocol (SASL_SSL, SCRAM-SHA-256)

**What It Does:**
1. **Initialize Producer** ([redpanda_streaming.py:20](src/integrations/redpanda_streaming.py#L20))
   - Connects to Redpanda broker via Kafka protocol
   - Configures SASL authentication
   - Sets acks='all' for durability
   - Enables retries=3
   - JSON serializer for events

2. **Publish Anomaly Event** ([redpanda_streaming.py:57](src/integrations/redpanda_streaming.py#L57))
   - Constructs event payload:
     * timestamp (UTC ISO format)
     * severity, confidence
     * anomaly count & indices (first 20)
     * summary (truncated to 500 chars)
     * recommendation
     * agent findings summary
   - Publishes to topic: "anomaly-hunter-events"
   - Blocks until acknowledged (timeout: 10s)
   - Makes event available for real-time stream processing

---

### 6. **TrueFoundry Deployment** (`truefoundry_deployment.py`)

**APIs Used:**
- Prometheus metrics (via TrueFoundry platform)

**What It Does:**
1. **Initialize Metrics** ([truefoundry_deployment.py:20](src/integrations/truefoundry_deployment.py#L20))
   - Creates Prometheus metrics exporters:
     * Counter: `anomaly_detections_total`
     * Gauge: `current_severity`, `current_confidence`
     * Histogram: `severity_distribution`
     * Histogram: `agent_latency_ms`
     * Gauge: `inference_latency_ms`
     * Summary: `total_latency_summary`

2. **Log Inference** ([truefoundry_deployment.py:113](src/integrations/truefoundry_deployment.py#L113))
   - Increments detection counter with labels:
     * severity level (low/medium/high/critical)
     * confidence bucket
   - Updates severity gauge
   - Updates confidence gauge
   - Records severity histogram
   - Exports to Prometheus for dashboards

3. **Log Performance** ([truefoundry_deployment.py:147](src/integrations/truefoundry_deployment.py#L147))
   - Records total inference latency (ms)
   - Records per-agent latency histograms
   - Updates latency summary stats
   - Enables Grafana performance dashboards

---

### 7. **ElevenLabs Voice** (`elevenlabs_voice.py`)

**APIs Used:**
- POST `/v1/text-to-speech/{voice_id}` - Text-to-speech conversion

**What It Does:**
1. **Generate Voice Alert** ([elevenlabs_voice.py:35](src/integrations/elevenlabs_voice.py#L35))
   - Triggers only for severity ≥ 8
   - Constructs alert message:
     * Severity label: CRITICAL (≥9) or HIGH (≥7)
     * Confidence percentage
     * Key finding (first sentence, max 200 chars)
     * "Immediate investigation required"
   - Calls ElevenLabs TTS API:
     * Model: `eleven_monolingual_v1`
     * Voice ID: from environment
     * Stability: 0.5
     * Similarity boost: 0.75
   - Receives MP3 audio
   - Saves to `anomaly_alert.mp3`
   - Plays audio (macOS: `afplay`)
   - Delivers audible critical alert

---

## Agent Workflow Details

### Pattern Analyst (Agent 1)
- **Model:** GPT-5 Pro (via Stack AI Flow `68f2bece...`)
- **Statistical Analysis:**
  - Z-score calculation
  - Anomaly detection (threshold: 3σ)
  - Top 5 deviation identification
- **LLM Analysis:**
  - Pattern classification
  - Severity assessment (1-10)
  - Impact evaluation
- **Confidence Calculation:**
  - Base: 0.5
  - +0.3 if max Z-score > 5
  - +0.2 if max Z-score > 3
  - +0.1 if anomaly count > 3

### Change Detective (Agent 2)
- **Model:** Claude 4.5 Sonnet (via Stack AI Flow `68f2c162...`)
- **Time-Series Analysis:**
  - Moving average calculation
  - Change point detection (threshold: 2σ)
  - Drift analysis (first half vs second half)
  - Trend determination
- **LLM Analysis:**
  - Change pattern characterization
  - Severity assessment (1-10)
  - Cause hypothesis generation
- **Confidence Calculation:**
  - Base: 0.5
  - +0.2 if drift detected
  - +0.2 if change count > 5 (+0.1 if > 2)
  - +0.2 if |drift| > 50% (+0.1 if > 30%)

### Root Cause Agent (Agent 3)
- **Model:** Claude 4.5 Sonnet (via Stack AI Flow `68f2c162...`)
- **Root Cause Analysis:**
  - IQR-based anomaly detection
  - Temporal clustering (proximity: 5 indices)
  - Auto-correlation calculation (lag-1)
  - Hypothesis generation (3 types)
- **LLM Reasoning:**
  - Hypothesis evaluation
  - Root cause determination
  - Confidence self-assessment
  - Severity assessment (1-10)
- **Confidence Calculation:**
  - Extracted from LLM response
  - +0.1 if correlation > 0.7
  - -0.1 if correlation < 0.3
  - -0.1 if hypothesis count > 4

---

## Data Flow Summary

```
Input CSV
  ↓
[Airia] Clean & Validate
  ↓
[Senso] Retrieve Historical Context
  ↓
[Orchestrator] Distribute to 3 Agents
  ↓
  ├─ [Agent 1] Statistical Analysis → [StackAI] GPT-5 Pro
  ├─ [Agent 2] Change Detection → [StackAI] Claude 4.5
  └─ [Agent 3] Root Cause → [StackAI] Claude 4.5
  ↓
[Orchestrator] Confidence-Weighted Voting + Autonomous Learning
  ↓
[AnomalyVerdict] Synthesized Result
  ↓
  ├─ [TrueFoundry] Log Metrics (Prometheus)
  ├─ [Sentry] Track Event
  ├─ [Redpanda] Publish Stream
  ├─ [Senso] Store in KB
  └─ [ElevenLabs] Voice Alert (if critical)
  ↓
Display Results to User
```

---

## Integration Trigger Points

| Integration | Trigger Point | Line Reference |
|-------------|--------------|----------------|
| **Airia** | Data preprocessing | [cli.py:70-73](cli.py#L70-L73) |
| **Senso** (retrieve) | Before agent analysis | [cli.py:75-77](cli.py#L75-L77) |
| **StackAI** | Agent LLM calls | [pattern_analyst.py:146](src/agents/pattern_analyst.py#L146), [change_detective.py:170](src/agents/change_detective.py#L170), [root_cause_agent.py:232](src/agents/root_cause_agent.py#L232) |
| **TrueFoundry** | After verdict | [cli.py:118-122](cli.py#L118-L122) |
| **Sentry** | After verdict | [cli.py:114-116](cli.py#L114-L116) |
| **Redpanda** | After verdict | [cli.py:124-126](cli.py#L124-L126) |
| **Senso** (store) | After verdict | [cli.py:128-130](cli.py#L128-L130) |
| **ElevenLabs** | If severity ≥ 8 | [cli.py:133-137](cli.py#L133-L137) |

---

## Performance Characteristics

- **Total Agents:** 3 (run in parallel)
- **LLM Calls:** 3 (via Stack AI flows)
- **Timeout:** 300s per Stack AI flow (GPT-5 Pro)
- **Retries:** 3 (Redpanda streaming)
- **Sampling:** 100% (Sentry traces & profiles)

---

## End-to-End Latency Breakdown

1. **Data Load & Preprocessing:** ~100ms (Airia)
2. **Senso RAG Retrieval:** ~200ms (HTTP request)
3. **Agent Parallel Analysis:** ~5-15s (Stack AI LLM calls)
   - Pattern Analyst: ~3-5s
   - Change Detective: ~3-5s
   - Root Cause Agent: ~5-10s (reasoning)
4. **Synthesis & Recommendation:** ~10ms
5. **Integration Logging:** ~500ms total
   - TrueFoundry: ~50ms (metrics)
   - Sentry: ~100ms (HTTP)
   - Redpanda: ~200ms (Kafka)
   - Senso: ~100ms (HTTP)
   - ElevenLabs: ~2-3s (TTS, if triggered)
6. **Display:** <10ms

**Total:** ~6-20 seconds (depending on LLM response times)

---

*Generated: 2025-10-17*
*Anomaly Hunter v1.0.0*

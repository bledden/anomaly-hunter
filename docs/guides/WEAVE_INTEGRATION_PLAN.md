# Weave Integration Implementation Plan
## Complete Integration Guide for Anomaly Hunter

**Status:** Implementation-ready
**Estimated Time:** 2-3 hours
**Risk:** Low (optional integration, graceful degradation)

---

## Integration Points

### 1. Core Orchestrator (Primary Integration)

**File:** `src/orchestrator.py`
**Why:** Central coordination point, all agent calls flow through here

**Changes:**
```python
# Add imports
import weave
import os

class AnomalyOrchestrator:
    def __init__(self, stackai_client=None):
        self.stackai = stackai_client
        self.agents = []
        self.learner = AutonomousLearner()

        # Initialize Weave (optional)
        self.weave_enabled = os.getenv("WEAVE_ENABLED", "false").lower() == "true"
        if self.weave_enabled:
            weave_project = os.getenv("WEAVE_PROJECT", "anomaly-hunter")
            weave.init(weave_project)
            print(f"[WEAVE] LLM tracing enabled (project: {weave_project})")

        self._load_agents()

    # Decorate main investigation function
    @weave.op()
    async def investigate(
        self,
        context: AnomalyContext,
        senso_context: Optional[str] = None
    ) -> AnomalyVerdict:
        """Run full anomaly investigation with all 3 agents"""
        # Existing code...
        return verdict
```

**What this does:**
- Automatically traces all `investigate()` calls
- Logs inputs (data, timestamps, metadata)
- Logs outputs (verdict, confidence, severity)
- Tracks latency per detection

---

### 2. Individual Agents (Agent-Level Tracing)

**Files:**
- `src/agents/pattern_analyst.py`
- `src/agents/change_detective.py`
- `src/agents/root_cause_agent.py`

**Changes for each agent:**
```python
import weave

class PatternAnalyst:
    def __init__(self, stackai_client=None):
        self.stackai = stackai_client
        # ... existing code

    @weave.op()
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data for statistical patterns

        Weave tracks:
        - Input: context data
        - Output: finding + confidence
        - Token usage (automatic via OpenAI integration)
        - Latency
        """
        # Existing analysis code...
        return {
            "agent_name": "pattern_analyst",
            "finding": finding,
            "confidence": confidence,
            "severity": severity,
            "evidence": evidence
        }
```

**What this does:**
- Per-agent granular tracing
- Token usage per agent (identify which agent is expensive)
- Latency breakdown (Pattern: 1.2s, Change: 1.4s, Root: 1.8s)
- Agent-specific prompt analysis

---

### 3. Autonomous Learner (Learning Metrics)

**File:** `src/learning/autonomous_learner.py`

**Changes:**
```python
import weave

class AutonomousLearner:
    def __init__(self, cache_dir: str = "backend/cache/learning"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # ... existing code

        # Check if Weave is enabled
        self.weave_enabled = os.getenv("WEAVE_ENABLED", "false").lower() == "true"

    @weave.op()
    def learn_from_outcome(
        self,
        verdict: Any,
        was_correct: Optional[bool] = None
    ):
        """
        Learn from detection outcome

        Weave tracks:
        - Learning events over time
        - Agent performance trends
        - Weight adjustments
        """
        # Existing learning logic...

        # Log to Weave if enabled
        if self.weave_enabled:
            weave.log({
                "detection_id": verdict.timestamp,
                "was_correct": was_correct,
                "confidence": verdict.confidence,
                "severity": verdict.severity,
                "agent_count": len(verdict.agent_findings),
                "adaptive_weights": self.compute_adaptive_weights(verdict.agent_findings)
            })

        # ... rest of existing code
```

**What this does:**
- Track learning metrics over time
- See how agent weights evolve
- Correlate weight adjustments with accuracy improvements

---

### 4. Evaluation Framework (New File)

**File:** `tests/evaluation/weave_eval.py` (NEW)

**Purpose:** Systematic evaluation of detection performance

```python
"""
Weave-based evaluation framework for Anomaly Hunter
Run systematic tests and track results over time
"""

import weave
import asyncio
from pathlib import Path
from src.orchestrator import AnomalyOrchestrator, AnomalyContext
import numpy as np

# Initialize Weave
weave.init("anomaly-hunter-eval")

# Define evaluation scorers
@weave.scorer
def accuracy_scorer(predicted_verdict, ground_truth):
    """
    Score detection accuracy

    Args:
        predicted_verdict: AnomalyVerdict from orchestrator
        ground_truth: {"is_anomaly": bool, "severity": int}

    Returns:
        {"accuracy": 0.0-1.0}
    """
    # True positive: Detected anomaly that exists
    if predicted_verdict.severity >= 7 and ground_truth["is_anomaly"]:
        return {"accuracy": 1.0}

    # True negative: No detection, no anomaly
    if predicted_verdict.severity < 7 and not ground_truth["is_anomaly"]:
        return {"accuracy": 1.0}

    # False positive or false negative
    return {"accuracy": 0.0}


@weave.scorer
def confidence_scorer(predicted_verdict, ground_truth):
    """
    Score confidence calibration

    High score if:
    - High confidence + correct = good
    - Low confidence + incorrect = good (system uncertain)
    - High confidence + incorrect = bad (overconfident)
    """
    is_correct = (
        (predicted_verdict.severity >= 7 and ground_truth["is_anomaly"]) or
        (predicted_verdict.severity < 7 and not ground_truth["is_anomaly"])
    )

    if is_correct and predicted_verdict.confidence > 0.7:
        return {"confidence_score": 1.0}  # Confident and correct
    elif not is_correct and predicted_verdict.confidence < 0.5:
        return {"confidence_score": 0.8}  # Uncertain and wrong (ok)
    elif not is_correct and predicted_verdict.confidence > 0.7:
        return {"confidence_score": 0.0}  # Overconfident and wrong (bad)
    else:
        return {"confidence_score": 0.5}  # Middling


@weave.scorer
def latency_scorer(predicted_verdict, ground_truth):
    """
    Score based on detection latency

    < 3s: Excellent
    3-5s: Good
    5-10s: Acceptable
    > 10s: Poor
    """
    # Note: Would need to track latency in verdict
    # For now, return placeholder
    return {"latency_score": 1.0}


# Define detection wrapper for evaluation
@weave.op()
async def detect_anomaly(data_dict):
    """
    Wrapper for orchestrator.investigate() that Weave can evaluate

    Args:
        data_dict: {"data": array, "timestamps": list, "metadata": dict}

    Returns:
        AnomalyVerdict
    """
    orchestrator = AnomalyOrchestrator()

    context = AnomalyContext(
        data=np.array(data_dict["data"]),
        timestamps=data_dict.get("timestamps"),
        metadata=data_dict.get("metadata")
    )

    verdict = await orchestrator.investigate(context)
    return verdict


# Run evaluation
async def run_evaluation():
    """
    Run systematic evaluation on test dataset
    """
    # Load test dataset (versioned in Weave)
    test_cases = [
        {
            "data": [100, 102, 98, 250, 99],  # Sudden spike
            "timestamps": None,
            "metadata": {"test_name": "sudden_spike"},
            "ground_truth": {"is_anomaly": True, "severity": 9}
        },
        {
            "data": [100, 101, 99, 102, 98],  # Normal variation
            "timestamps": None,
            "metadata": {"test_name": "normal_variation"},
            "ground_truth": {"is_anomaly": False, "severity": 2}
        },
        # ... more test cases
    ]

    # Publish dataset to Weave (versioned)
    dataset = weave.Dataset(
        name="anomaly-test-cases",
        rows=[
            {"input": tc, "output": tc["ground_truth"]}
            for tc in test_cases
        ]
    )
    weave.publish(dataset)

    # Create evaluation
    evaluation = weave.Evaluation(
        dataset=dataset,
        scorers=[accuracy_scorer, confidence_scorer, latency_scorer]
    )

    # Run evaluation
    print("Running evaluation...")
    results = await evaluation.evaluate(detect_anomaly)

    print(f"\nEvaluation Results:")
    print(f"Accuracy: {results['accuracy']['mean']:.2%}")
    print(f"Confidence: {results['confidence_score']['mean']:.2%}")
    print(f"Latency: {results['latency_score']['mean']:.2%}")

    return results


if __name__ == "__main__":
    asyncio.run(run_evaluation())
```

**What this does:**
- Systematic testing framework
- Version-controlled test datasets
- Automated scoring (accuracy, confidence, latency)
- Track performance over time (regression detection)

---

### 5. Environment Configuration

**File:** `.env.example`

**Add:**
```bash
# ============================================
# WEAVE (Optional - LLM Observability)
# ============================================

# Enable Weave tracing (true/false)
WEAVE_ENABLED=false

# Weights & Biases API key
# Get from: https://wandb.ai/authorize
WANDB_API_KEY=your_wandb_api_key_here

# Weave project name (customize per environment)
WEAVE_PROJECT=anomaly-hunter

# Optional: Weave entity (team name)
# WANDB_ENTITY=your_team_name
```

---

### 6. Requirements

**File:** `requirements.txt`

**Add:**
```
# LLM Observability
weave==0.50.0  # Weights & Biases Weave for LLM tracing
```

---

## Integration Testing Plan

### Test 1: Basic Tracing

```bash
# 1. Enable Weave
export WEAVE_ENABLED=true
export WANDB_API_KEY=your_key

# 2. Run single detection
python3 cli.py detect demo/sample_anomalies.csv

# 3. Check Weave UI
# Should see:
# - 1 investigate() trace
# - 3 agent analyze() traces (nested under investigate)
# - Token usage per agent
# - Total latency breakdown
```

**Expected output in terminal:**
```
[WEAVE] LLM tracing enabled (project: anomaly-hunter)
[OK] Loaded 3 agents
[ORCHESTRATOR] Starting investigation of 500 data points
...
[ORCHESTRATOR] Investigation complete. Severity: 8/10
```

**Expected in Weave UI:**
```
Trace: investigate()
├─ Input: {data: array(500 points), timestamps: null}
├─ Duration: 3.2s
├─ Nested calls:
│  ├─ pattern_analyst.analyze() - 1.2s, 1200 tokens
│  ├─ change_detective.analyze() - 1.4s, 1800 tokens
│  └─ root_cause.analyze() - 1.8s, 2200 tokens
└─ Output: {severity: 8, confidence: 0.82, ...}
```

### Test 2: Multi-Detection Tracking

```bash
# Run evaluation
python3 tests/evaluation/weave_eval.py

# Should track:
# - Multiple detections
# - Accuracy metrics
# - Performance trends
```

### Test 3: Graceful Degradation

```bash
# Disable Weave
export WEAVE_ENABLED=false

# Run detection
python3 cli.py detect demo/sample_anomalies.csv

# Should work normally, no Weave logging
# No errors or warnings
```

---

## Implementation Checklist

### Phase 1: Core Integration (1 hour)

- [ ] Add `weave` to `requirements.txt`
- [ ] Update `.env.example` with Weave variables
- [ ] Add Weave initialization to `orchestrator.py`
- [ ] Add `@weave.op()` decorator to `investigate()`
- [ ] Test: Run single detection with Weave enabled

### Phase 2: Agent-Level Tracing (30 minutes)

- [ ] Add `@weave.op()` to `pattern_analyst.py`
- [ ] Add `@weave.op()` to `change_detective.py`
- [ ] Add `@weave.op()` to `root_cause_agent.py`
- [ ] Test: Verify nested traces in Weave UI

### Phase 3: Learning Integration (30 minutes)

- [ ] Update `autonomous_learner.py` with Weave logging
- [ ] Test: Verify learning metrics appear in Weave

### Phase 4: Evaluation Framework (1 hour)

- [ ] Create `tests/evaluation/weave_eval.py`
- [ ] Implement scorers (accuracy, confidence, latency)
- [ ] Create test dataset
- [ ] Test: Run evaluation, verify results

### Phase 5: Documentation (30 minutes)

- [ ] Update README with Weave setup instructions
- [ ] Add to blog post sponsor section
- [ ] Document Weave UI navigation
- [ ] Add screenshots of traces

---

## Expected Benefits After Integration

### 1. Debugging Improvements

**Before:**
```
Detection #23 has low confidence (65%). Why?

Manual debugging:
1. Re-run detection
2. Add print statements
3. Check Sentry logs
4. Guess which agent failed
```

**After:**
```
Detection #23 has low confidence (65%). Why?

Weave UI shows:
- Pattern Analyst: 78% confidence (good)
- Change Detective: 45% confidence (low!) <- problem found
- Trace shows: API timeout, fell back to cached result
- Fix: Increase timeout from 30s to 45s
```

### 2. Cost Optimization

**Before:**
```
Monthly API costs: ~$10 (estimated)
No visibility into which agent is expensive
```

**After:**
```
Weave dashboard shows:
- Pattern Analyst: $0.002/detection (1.2K tokens avg)
- Change Detective: $0.004/detection (1.8K tokens avg)
- Root Cause: $0.008/detection (3.5K tokens avg) <- expensive!

Investigation: Root Cause prompt includes full conversation history
Fix: Remove history, reduce to 1.2K tokens
Savings: $0.008 -> $0.002 (75% reduction on Root Cause)
```

### 3. Prompt Optimization

**Before:**
```
Want to test new prompt for Pattern Analyst
Manual process:
1. Change prompt in code
2. Run 20 detections manually
3. Record results in spreadsheet
4. Compare old vs new
```

**After:**
```
# Create two versions
@weave.op()
def detect_with_prompt_v1(data):
    return orchestrator.investigate(data, prompt_version="v1")

@weave.op()
def detect_with_prompt_v2(data):
    return orchestrator.investigate(data, prompt_version="v2")

# Automated comparison
evaluation = weave.Evaluation(dataset=test_cases, scorers=[accuracy])
results = evaluation.evaluate(detect_with_prompt_v1, detect_with_prompt_v2)

# Output:
# Prompt v1: 78% accuracy, 3.2s avg latency
# Prompt v2: 82% accuracy, 3.5s avg latency (+4% accuracy, +0.3s latency)
```

### 4. Research Paper Data

**For Facilitair multi-agent collaboration paper:**

```python
# Single-agent baseline
@weave.op()
def single_agent_detect(data):
    return pattern_analyst.analyze(data)

# Multi-agent consensus
@weave.op()
def multi_agent_detect(data):
    return orchestrator.investigate(data)

# Automated statistical comparison
evaluation = weave.Evaluation(
    dataset=weave.ref("research-dataset-v1"),  # 100 test cases
    scorers=[accuracy, confidence, latency, cost]
)
results = evaluation.evaluate(single_agent_detect, multi_agent_detect)

# Weave automatically calculates:
# - Mean, std dev, confidence intervals
# - Statistical significance (p-values)
# - Performance breakdown by difficulty
```

**Output for paper:**
```
Single-agent: 77.8% accuracy (CI: [72.3%, 83.3%])
Multi-agent: 84.6% accuracy (CI: [79.8%, 89.4%])
Difference: +6.8% (p=0.003, statistically significant)
```

---

## Post-Integration Monitoring

### Week 1: Validation

**Metrics to check:**
- [ ] Trace collection working (see traces in Weave UI)
- [ ] Token usage tracked per agent
- [ ] No performance degradation (latency within 5% of baseline)
- [ ] No errors in Weave integration

### Month 1: Evaluation

**Success criteria:**
- [ ] Helped debug 1+ LLM issue
- [ ] Identified cost optimization opportunity
- [ ] Enabled A/B testing of prompts

**If not meeting criteria:**
- Re-evaluate if Weave is providing value
- Consider removing if not useful

---

## Rollback Plan

If Weave causes issues:

```bash
# 1. Disable immediately
export WEAVE_ENABLED=false

# 2. Remove from requirements.txt
pip uninstall weave

# 3. Remove decorators from code
# (System works without them - decorators are no-ops if weave not initialized)

# 4. Remove from .env
# Delete WEAVE_* variables
```

**System continues working normally** - Weave is fully optional

---

## Next Steps

1. **Review this plan** - Confirm integration points make sense
2. **Get W&B API key** - Sign up at https://wandb.ai
3. **Implement Phase 1** - Core integration (1 hour)
4. **Test on 5 detections** - Verify traces appear
5. **Decide on Phase 2-4** - Based on Phase 1 results

**Estimated total time:** 3 hours for full integration
**Risk:** Low (optional, graceful degradation, easy rollback)
**Reward:** High (better debugging, cost tracking, research facilitation)

---

**Document Version:** 1.0
**Status:** Implementation-ready
**Last Updated:** October 20, 2025

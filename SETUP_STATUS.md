# Anomaly Hunter - Setup Status
**Last Updated:** October 17, 2025 - 8:45 AM PT
**Time Until Hackathon:** ~2h 15m

---

## ✅ COMPLETED TASKS

### 1. API Keys Checklist ✅
- Location: `/Users/bledden/Documents/Facilitair_v2/HACKATHON_API_KEYS_CHECKLIST.md`
- Contains: Detailed setup instructions for all 8 sponsors
- Estimated time: 47 minutes for Priority 1 keys

### 2. Architecture Design ✅
- Location: `/Users/bledden/Documents/Facilitair_v2/HACKATHON_ARCHITECTURE.md`
- Contains: Complete system design with all sponsor integrations
- Includes: Data flow diagrams, integration strategies, demo script

### 3. GitHub Repo Structure ✅
- Location: `/Users/bledden/Documents/anomaly-hunter/`
- Initialized: Git repository with initial commit
- Structure:
  ```
  anomaly-hunter/
  ├── README.md (comprehensive project documentation)
  ├── .env.example (API key template)
  ├── .gitignore (Python/project ignores)
  ├── requirements.txt (Corch dependencies)
  ├── src/
  │   ├── orchestrators/ (Corch orchestration core)
  │   ├── evaluation/ (quality evaluation system)
  │   ├── middleware/ (evaluation middleware)
  │   ├── utils/ (monitoring, file access)
  │   ├── agents/ (empty - for new anomaly agents)
  │   ├── agents_orig/ (Corch agents as reference)
  │   └── integrations/ (empty - for sponsor integrations)
  ├── demo/
  ├── config/
  │   ├── config.yaml
  │   ├── evaluation.yaml
  │   └── model_strategy_config.yaml
  └── tests/
  ```

### 4. Corch Codebase Copied ✅
- **Source:** `/Users/bledden/Documents/weavehacks-collaborative/`
- **Destination:** `/Users/bledden/Documents/anomaly-hunter/`
- **Method:** rsync (no git history)
- **Files Copied:** 37 Python files (~632KB)
- **What We Have:**
  - ✅ Orchestration core (sequential, collaborative, cached)
  - ✅ Evaluation system (security, static analysis, complexity, LLM judge)
  - ✅ Middleware (evaluation hooks)
  - ✅ Utils (monitoring, file access, web search)
  - ✅ Reference agents (model selector, chunker, hallucination detector)
  - ✅ Config files (agents, evaluation, model strategy)

---

## 🔄 IN PROGRESS

### 5. Strip & Adapt Corch (NEXT TASK)
**Estimated Time:** 45-60 minutes

**To Remove:**
- [ ] W&B Weave integration references
- [ ] Unused orchestrators (keep only `collaborative_orchestrator.py`)
- [ ] Code generation-specific agents
- [ ] Hallucination detection (not needed for anomaly detection)

**To Keep:**
- [ ] Core orchestration logic
- [ ] Evaluation system structure
- [ ] Middleware pattern
- [ ] LLM client infrastructure

**To Adapt:**
- [ ] Create 3 anomaly detection agents:
  - `src/agents/pattern_analyst.py` (GPT-4)
  - `src/agents/change_detective.py` (Claude)
  - `src/agents/root_cause_agent.py` (o1-mini)
- [ ] Modify orchestrator for anomaly detection workflow
- [ ] Update config files for anomaly agents

---

## ⏳ PENDING (After 9:30 AM)

### 6. Get API Keys
**Priority 1 (MUST HAVE):**
- [ ] OpenAI (have key or get from platform.openai.com)
- [ ] StackAI (sign up at stack-ai.com)
- [ ] TrueFoundry (sign up at truefoundry.com)
- [ ] Sentry (create project at sentry.io)
- [ ] Redpanda (create cluster at cloud.redpanda.com)
- [ ] ElevenLabs (sign up at elevenlabs.io)

**Priority 2 (NICE TO HAVE):**
- [ ] Airia (request access at airia.com/request-access)
- [ ] Senso (contact at senso.ai/contact)

**Estimated Time:** 47 minutes (Priority 1 only)

### 7. Test API Keys
- [ ] Run `test_api_keys.sh` script
- [ ] Verify all Priority 1 keys work
- [ ] Document any fallbacks needed

---

## 📅 TIMELINE

**NOW - 9:30 AM (45 mins):**
- Strip & adapt Corch codebase
- Create 3 anomaly detection agent stubs
- Update orchestrator for anomaly workflow

**9:30 AM - 10:00 AM (30 mins):**
- Get all Priority 1 API keys in parallel
- Request Priority 2 access (don't wait for approval)

**10:00 AM - 10:15 AM (15 mins):**
- Test all API keys
- Document fallbacks

**10:15 AM - 11:00 AM (45 mins):**
- Create demo dataset with obvious anomalies
- Write integration skeleton code
- Prepare deployment configs (TrueFoundry, Railway)

**11:00 AM - HACKATHON START ⏰**

---

## 🎯 MINIMUM VIABLE DEMO (By 3:30 PM)

**Must Have:**
1. ✅ 3 agents detecting anomalies (GPT-4, Claude, o1-mini)
2. ⏳ StackAI routing between models
3. ⏳ TrueFoundry deployment (or Railway fallback)
4. ⏳ Redpanda event streaming (or simple logging)
5. ⏳ Sentry monitoring (or JSON logs)
6. ⏳ ElevenLabs voice alert (or pre-recorded)
7. ⏳ Live demo with sample dataset
8. ⏳ Demo video recorded

**Nice to Have:**
9. ⏳ Airia workflow UI (if access granted)
10. ⏳ Senso knowledge base (if access granted)

---

## 🚨 CURRENT BLOCKERS

**None** - All prep tasks on schedule

**Potential Risks:**
- Airia/Senso may not grant immediate access → Have fallback plans
- TrueFoundry signup may take time → Railway/Render as backup
- Redpanda cluster creation may delay → Simple webhook fallback

---

## 📝 NEXT IMMEDIATE STEPS

1. **Strip Corch** (15 mins)
   - Remove W&B Weave references
   - Remove unused code

2. **Create Agent Stubs** (30 mins)
   - Pattern Analyst
   - Change Detective
   - Root Cause Agent

3. **Update Orchestrator** (15 mins)
   - Adapt collaborative_orchestrator for anomaly workflow

4. **START GETTING API KEYS** (can do in parallel while coding)

---

## 📂 KEY FILES TO EDIT

**Priority 1 (Edit Now):**
- `src/orchestrators/collaborative_orchestrator.py` - Adapt for anomaly detection
- `src/agents/pattern_analyst.py` - CREATE NEW
- `src/agents/change_detective.py` - CREATE NEW
- `src/agents/root_cause_agent.py` - CREATE NEW
- `config/config.yaml` - Update for anomaly agents

**Priority 2 (Edit During Hackathon):**
- `src/integrations/stackai_gateway.py` - CREATE NEW
- `src/integrations/truefoundry_deploy.py` - CREATE NEW
- `src/integrations/redpanda_stream.py` - CREATE NEW
- `src/integrations/sentry_monitor.py` - CREATE NEW
- `src/integrations/elevenlabs_voice.py` - CREATE NEW

**Priority 3 (If Time):**
- `src/integrations/airia_workflow.py` - CREATE NEW
- `src/integrations/senso_knowledge.py` - CREATE NEW

---

**Status: ON TRACK ✅**
**Confidence Level: HIGH (90%)**
**Ready for 11 AM start: VERY LIKELY**

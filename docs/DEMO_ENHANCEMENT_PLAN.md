# Sentinel V2 — Demo Enhancement Plan

**Date:** February 22, 2026
**Goal:** Transform static demo into truly agentic experience
**Target:** Goldman Sachs AWM AI Role Interview

---

## Executive Summary

The current Sentinel demo shows **orchestration** but not **autonomy**. Scenarios are hardcoded, there's no visible reasoning, and users can't interact naturally with agents. This plan outlines how to make the demo feel like real AI.

---

## Current State Assessment

### What We Have ✅
- Multi-agent architecture (Drift + Tax + Coordinator)
- Conflict detection and resolution
- Scenario ranking with utility scores
- Merkle chain audit trail (SQLite-backed)
- WebSocket real-time updates
- Approval workflow

### What's Missing ❌
- **No visible reasoning** — Scenarios appear instantly, pre-computed
- **No natural language interaction** — Can't ask questions
- **No proactive behavior** — System only responds to manual triggers
- **Static scenarios** — Same output every time, regardless of portfolio
- **No state machine visualization** — Can't see system transitions
- **No memory** — Each analysis is stateless

---

## Gap Analysis: Architecture Spec vs. Demo

| Spec Feature | Status | Priority |
|--------------|--------|----------|
| Typed Gateway Layer | ❌ Missing | P2 |
| Proactive Inputs (Cron/Heartbeat) | ❌ Missing | P1 |
| State Machine (MONITOR→DETECT→ANALYZE...) | ❌ Missing | P1 |
| Context vs Memory Architecture | ❌ Missing | P2 |
| Dynamic Skill Injection | ❌ Missing | P3 |
| Multi-Persona Routing | ❌ Missing | P2 |
| Session-Based Security (RBAC) | ❌ Missing | P3 |
| Natural Language Chat (Canvas A2UI) | ❌ Missing | P0 |
| Real LLM Reasoning | ❌ Missing | P0 |

---

## The Core Problem

```python
# Current implementation - STATIC
def get_demo_scenarios() -> List[Scenario]:
    return [
        Scenario(
            id="scenario_amd_substitute",
            title="AMD Substitute Strategy",
            score=72.4,  # ← Hardcoded!
        ),
    ]
```

**User experience:**
- Click "Analyze" → Instant results
- Same scenarios every time
- No evidence of AI thinking
- Feels like a mockup, not an AI system

---

## Proposed Solution

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
├────────────────┬─────────────────────┬──────────────────────────┤
│  Portfolio     │  Agent Reasoning    │  Chat Sidebar            │
│  Dashboard     │  Panel              │  (Natural Language)      │
│                │                     │                          │
│  Holdings      │  🔄 Drift Agent     │  > "What's my NVDA       │
│  Allocations   │    "Analyzing..."   │     exposure risk?"      │
│  Risk Metrics  │                     │                          │
│                │  💭 Thinking:       │  🤖 "Based on your       │
│  [Analyze]     │    "NVDA at 17%..." │     17.2% position..."   │
│                │                     │                          │
│                │  ⚡ Conflict!       │  > "Run tax analysis"    │
│                │                     │                          │
│                │  📊 Scenarios       │  🤖 "Checking wash       │
│                │    generating...    │     sale window..."      │
└────────────────┴─────────────────────┴──────────────────────────┘
                              │
                       WebSocket Stream
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                          BACKEND                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Typed Gateway                          │   │
│  │  - Schema validation (Pydantic)                          │   │
│  │  - Per-session queues                                    │   │
│  │  - Priority routing                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────┐    ┌──────────▼──────────┐    ┌───────────┐      │
│  │  Drift    │───▶│    Coordinator      │◀───│   Tax     │      │
│  │  Agent    │    │    (Claude Opus)    │    │  Agent    │      │
│  │ (Sonnet)  │    │                     │    │ (Sonnet)  │      │
│  └─────┬─────┘    └──────────┬──────────┘    └─────┬─────┘      │
│        │                     │                     │             │
│        │         ┌───────────▼───────────┐         │             │
│        └────────▶│   State Machine      │◀────────┘             │
│                  │ MONITOR→DETECT→...   │                        │
│                  └───────────┬───────────┘                       │
│                              │                                   │
│                  ┌───────────▼───────────┐                       │
│                  │   Claude API          │                       │
│                  │   (Streaming)         │                       │
│                  └───────────────────────┘                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Chat Sidebar (P0) — Day 1 Morning

**Goal:** Natural language interaction with real Claude reasoning

**Files to create/modify:**
- `frontend/src/components/ChatSidebar.tsx` (NEW)
- `frontend/src/stores/chatStore.ts` (NEW)
- `backend/routers/chat.py` (ENHANCE)
- `backend/services/agent_executor.py` (NEW)

**Features:**
1. Slide-out chat panel on right side
2. Real Claude API calls with streaming
3. Context-aware (knows current portfolio, page)
4. Quick action buttons ("Analyze risk", "Check tax", "Run scenario")
5. Shows which agents are invoked

**Example interaction:**
```
User: "What's my concentration risk?"

Agent: "Analyzing your portfolio...

Looking at your holdings, I see significant concentration:
- NVDA: 17.2% ($8.5M) — exceeds 15% threshold ⚠️
- Tech sector: 34.2% — above target 25%

This creates single-stock risk. If NVDA drops 20%,
your portfolio loses ~3.4% from that position alone.

Shall I generate rebalancing scenarios?"
```

---

### Phase 2: Reasoning Stream Panel (P0) — Day 1 Afternoon

**Goal:** Visible agent thinking during analysis

**Files to create/modify:**
- `frontend/src/components/ReasoningPanel.tsx` (NEW)
- `frontend/src/pages/WarRoom.tsx` (ENHANCE)
- `backend/routers/events.py` (ENHANCE - stream thinking)

**Features:**
1. Real-time agent thoughts via WebSocket
2. Step-by-step reasoning display
3. Shows data being analyzed
4. Conflict detection visualization
5. Progress through state machine

**Visual flow:**
```
┌─────────────────────────────────────────┐
│ 🔄 Analysis in Progress                 │
├─────────────────────────────────────────┤
│                                         │
│ DRIFT AGENT                             │
│ ├─ ✅ Loading portfolio holdings        │
│ ├─ ✅ Calculating sector allocations    │
│ ├─ 🔄 Checking concentration limits     │
│ │     "NVDA at 17.2%, threshold 15%"   │
│ └─ ⏳ Generating recommendations        │
│                                         │
│ TAX AGENT                               │
│ ├─ ✅ Loading tax lot history           │
│ ├─ 🔄 Checking wash sale window         │
│ │     "NVDA sold Feb 6, 16 days ago"   │
│ └─ ⏳ Calculating tax impact            │
│                                         │
│ ⚡ CONFLICT DETECTED                    │
│    Drift: "Sell NVDA immediately"       │
│    Tax: "Wait 14 days for wash sale"    │
│                                         │
│ 📊 Generating resolution scenarios...   │
└─────────────────────────────────────────┘
```

---

### Phase 3: Dynamic Scenario Generation (P0) — Day 1 Evening

**Goal:** Scenarios generated from actual data, not hardcoded

**Files to create/modify:**
- `backend/services/scenario_generator.py` (NEW)
- `backend/routers/scenarios.py` (ENHANCE)
- `backend/prompts/coordinator.py` (NEW)

**Approach:**
1. Pass real portfolio data to Claude
2. Use structured output (tool use) for scenario schema
3. Calculate utility scores dynamically
4. Stream scenario generation progress

**Prompt structure:**
```python
COORDINATOR_PROMPT = """
You are analyzing a UHNW portfolio for rebalancing.

PORTFOLIO STATE:
{holdings_json}

MARKET EVENT:
{market_event}

DRIFT AGENT FINDINGS:
{drift_analysis}

TAX AGENT FINDINGS:
{tax_analysis}

Generate 3 distinct scenarios to resolve the conflict.
Each must have: title, actions, expected outcomes, trade-offs.

Use the utility function weights:
- Risk Reduction: {risk_weight}
- Tax Savings: {tax_weight}
- Goal Alignment: {goal_weight}
- Transaction Cost: {cost_weight}
- Urgency: {urgency_weight}
"""
```

---

### Phase 4: Proactive Alerts System (P1) — Day 2 Morning

**Goal:** System acts autonomously, not just on manual trigger

**Files to create/modify:**
- `backend/services/scheduler.py` (NEW)
- `backend/services/heartbeat.py` (NEW)
- `frontend/src/components/AlertBanner.tsx` (NEW)

**Features:**
1. Simulated cron jobs (9AM review, 4:30PM tax check)
2. Heartbeat monitoring every N minutes
3. Alert banner when system detects issues
4. "System initiated" vs "User initiated" analysis

**Example alerts:**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ PROACTIVE ALERT — 9:00 AM Daily Review                   │
│                                                              │
│ Overnight market movement detected:                          │
│ • Tech sector -2.3%                                          │
│ • 2 portfolios exceed drift threshold                        │
│                                                              │
│ [Review Now]  [Dismiss]  [Schedule for Later]               │
└─────────────────────────────────────────────────────────────┘
```

---

### Phase 5: State Machine Visualization (P1) — Day 2 Afternoon

**Goal:** Show system state transitions in real-time

**Files to create/modify:**
- `backend/services/state_machine.py` (NEW)
- `frontend/src/components/StateMachineViz.tsx` (NEW)

**States to visualize:**
```
MONITOR → DETECT → ANALYZE → CONFLICT_RESOLUTION → RECOMMEND → AWAIT_REVIEW → APPROVED → EXECUTE
```

**UI component:**
```
┌──────────────────────────────────────────────────────────┐
│  MONITOR ──▶ DETECT ──▶ ANALYZE ──▶ CONFLICT ──▶ ...    │
│     ○          ○          ●           ○                  │
│                        current                           │
└──────────────────────────────────────────────────────────┘
```

---

### Phase 6: Multi-Client Dashboard (P2) — Day 2 Evening

**Goal:** Show advisor managing multiple UHNW clients

**Features:**
1. Client selector dropdown
2. Cross-client opportunity detection
3. "3 clients affected by tech selloff"
4. Batch analysis capability

---

## Technical Requirements

### Backend Dependencies
```toml
# Add to pyproject.toml
anthropic = "^0.39.0"      # Claude API
apscheduler = "^3.10.0"    # Cron jobs
transitions = "^0.9.0"      # State machine
```

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
ENABLE_PROACTIVE_ALERTS=true
HEARTBEAT_INTERVAL_MINUTES=30
```

### API Endpoints to Add

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat/stream` | POST | Streaming chat with Claude |
| `/api/analysis/start` | POST | Trigger analysis with streaming |
| `/api/state` | GET | Current state machine state |
| `/api/alerts` | GET | Pending proactive alerts |
| `/api/alerts/{id}/dismiss` | POST | Dismiss alert |

### WebSocket Message Types to Add

```typescript
type WSMessage =
  | { type: 'agent_thinking', agent: string, thought: string }
  | { type: 'state_transition', from: string, to: string }
  | { type: 'scenario_generating', progress: number }
  | { type: 'proactive_alert', alert: Alert }
  | { type: 'chat_response', content: string, done: boolean }
```

---

## Success Metrics

### Before (Current State)
- ❌ User clicks "Analyze" → Instant hardcoded results
- ❌ Same scenarios every time
- ❌ No evidence of AI reasoning
- ❌ Can't ask questions naturally
- ❌ System only responds to manual actions

### After (Target State)
- ✅ User clicks "Analyze" → Sees agents thinking in real-time
- ✅ Scenarios vary based on actual portfolio state
- ✅ Full reasoning trace visible
- ✅ Natural language chat with real Claude responses
- ✅ Proactive alerts when market moves

---

## Demo Script (Post-Enhancement)

### Scene 1: Proactive Alert (0:00-0:30)
*System shows alert banner*

"Notice the system detected overnight tech selloff affecting 2 clients. This wasn't manually triggered — Sentinel is proactively monitoring."

### Scene 2: Natural Language Query (0:30-1:30)
*Open chat sidebar*

"Let me ask: 'What's my exposure to semiconductor supply chain risk?'"

*Show agent reasoning in real-time*

"Watch how it's analyzing holdings, checking sector correlations, and synthesizing an answer."

### Scene 3: Full Analysis with Reasoning (1:30-3:00)
*Click Analyze on affected portfolio*

"Now watch the agents work. Drift Agent is checking concentration... Tax Agent is checking wash sale windows... and there's a conflict."

*Show conflict resolution generating scenarios*

"It's generating three resolution options, scoring them with our utility function."

### Scene 4: Approval and Audit (3:00-4:00)
*Approve scenario, show Merkle chain*

"Every decision is logged cryptographically. We can verify the entire chain hasn't been tampered with."

---

## File Checklist

### New Files to Create
- [ ] `frontend/src/components/ChatSidebar.tsx`
- [ ] `frontend/src/components/ReasoningPanel.tsx`
- [ ] `frontend/src/components/AlertBanner.tsx`
- [ ] `frontend/src/components/StateMachineViz.tsx`
- [ ] `frontend/src/stores/chatStore.ts`
- [ ] `backend/services/agent_executor.py`
- [ ] `backend/services/scenario_generator.py`
- [ ] `backend/services/scheduler.py`
- [ ] `backend/services/state_machine.py`
- [ ] `backend/prompts/coordinator.py`
- [ ] `backend/prompts/drift_agent.py`
- [ ] `backend/prompts/tax_agent.py`

### Files to Enhance
- [ ] `frontend/src/App.tsx` — Add chat sidebar
- [ ] `frontend/src/pages/WarRoom.tsx` — Add reasoning panel
- [ ] `backend/routers/chat.py` — Real Claude integration
- [ ] `backend/routers/events.py` — Streaming analysis
- [ ] `backend/routers/scenarios.py` — Dynamic generation
- [ ] `backend/main.py` — Add scheduler startup

---

## Notes

- Keep hardcoded scenarios as **fallback** if API fails
- Add loading states everywhere
- Stream everything possible via WebSocket
- Make it feel like watching AI think, not instant magic
- The chat is the centerpiece — invest the most time there

---

*Document created: Feb 22, 2026*
*Next review: Feb 23, 2026 (implementation day)*

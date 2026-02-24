# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sentinel** is a proof-of-concept multi-agent AI system for UHNW ($30M-$80M) portfolio monitoring and tax optimization. Built as interview preparation for a Goldman Sachs MD — Asset & Wealth Management AI role.

**Timeline**: 5-day build in Python 3.12

## Commands

```bash
# Install dependencies
poetry install

# Run golden path demo
poetry run python -m src.main --demo golden_path

# Run all tests
poetry run pytest -v

# Run specific test
poetry run pytest tests/test_golden_path.py -v

# Run with coverage
poetry run pytest --cov=src tests/

# Verify Merkle chain integrity
poetry run python -m src.main --verify-merkle

# Generate synthetic portfolios
poetry run python -m src.data.generate_portfolios
```

## Architecture

### Core Patterns (Adapted from OpenClaw)

1. **Gateway-Mediated Inputs**: Typed gateway with Pydantic validation. Handles proactive inputs (heartbeats every 30 min, cron jobs, webhooks) — not just reactive to market events.

2. **Context vs Memory Split**:
   - Hot Context: Expensive, token-limited, current analysis only
   - Cold Memory: Cheap, unlimited, persistent decisions in markdown
   - Hybrid Search: Semantic (similar drifts) + Keyword (exact tickers)

3. **Session-Based Security**:
   - `advisor:main`: Full portfolio access
   - Analyst: Docker sandboxed, read-only, no PII
   - Client Portal: Own portfolio only

4. **Hub-and-Spoke Agent Communication**: Sub-agents (Drift, Tax) NEVER communicate directly. All coordination through Coordinator Agent. Prevents circular dependencies.

5. **Canvas (Agent-to-UI)**: Agents generate interactive HTML with `a2ui-action` attributes for approve/what-if buttons.

### Agent Flow

```
Market Event → Gateway (Pydantic validation) → State Machine (MONITOR→DETECT)
    → Coordinator dispatches Drift + Tax agents in parallel (asyncio.gather)
    → Conflict Resolution → Utility Function Scoring → Ranked Recommendations
    → Canvas UI → Human Approval → Merkle Chain Audit Log
```

### Utility Function Scoring

5-dimensional weighted scoring: risk_reduction, tax_savings, goal_alignment, transaction_cost, urgency

Weights vary by risk profile:
- Conservative: Risk 0.40, Tax 0.20, Goal 0.20, Cost 0.15, Urgency 0.05
- Moderate Growth: Risk 0.25, Tax 0.30, Goal 0.25, Cost 0.10, Urgency 0.10
- Aggressive: Risk 0.15, Tax 0.20, Goal 0.30, Cost 0.10, Urgency 0.25

## Critical Design Decisions

- **Pre-cached market data** (not live): Deterministic demos for repeatability
- **SQLite + SQLCipher**: Portable single-file encrypted database
- **Merkle chain** (not blockchain): Sufficient for POC audit trails
- **Three agents only**: Drift, Tax, Coordinator — enough for orchestration demo
- **CLI-first with Rich**: Canvas HTML is bonus polish

## Key Constraints

1. **Hub-and-spoke mandatory**: `drift_agent.send_message(tax_agent, ...)` is FORBIDDEN. Only Coordinator dispatches.

2. **Context window management**: Flush facts to markdown before compaction.
   ```python
   if self.token_count + new_tokens > self.max_tokens:
       self._flush_to_memory()
       self._compact_context()
   ```

3. **Security enforcement**: Master key in `.env` only (never hardcoded), RBAC decorator raises PermissionError, Docker sandbox actually isolates.

4. **Merkle chain immutability**: Append-only. Verification detects tampering.

## Golden Path Demo

Portfolio A ($50M) with 17% NVDA concentration. Tech drops 4%.

1. Drift Agent: "Sell NVDA" (concentration risk)
2. Tax Agent: "Wash sale violation" (sold NVDA 15 days ago)
3. Conflict detected → Coordinator generates 3 scenarios
4. Utility scoring: AMD substitute wins (69.6/100)
5. Canvas UI → Advisor approves → Merkle chain logs

## Environment

```bash
# .env (never commit)
ANTHROPIC_API_KEY=sk-ant-...
MASTER_ENCRYPTION_KEY=<openssl rand -base64 32>
```

## Tech Stack

- anthropic 0.39.0 (Sonnet for sub-agents, Opus for Coordinator)
- transitions 0.9.0 (state machine)
- sqlcipher3 0.5.0 (encrypted SQLite)
- chromadb 0.4.0 (vector search)
- cryptography 42.0.0 (AES-256-GCM envelope encryption)
- rich 13.7.0 (CLI output)
- pydantic 2.x (schema validation)
- apscheduler 3.x (cron jobs)

## Success Criteria

1. Golden path demo runs end-to-end
2. Utility function: AMD substitute ranks #1 (69.6/100)
3. Merkle chain integrity verified
4. Canvas UI renders with interactive sliders
5. Proactive heartbeat detects drift without external event
6. Session boundaries enforced (analyst can't access PII)

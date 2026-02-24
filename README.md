# Sentinel

**Multi-Agent UHNW Portfolio Monitoring & Tax Optimization System**

A proof-of-concept AI system demonstrating enterprise-grade multi-agent orchestration for ultra-high-net-worth ($30M-$80M) wealth management. Built as interview preparation for a Goldman Sachs MD — Asset & Wealth Management AI role.

---

## Features

- **Multi-Agent Orchestration** — Coordinator dispatches Drift and Tax agents in parallel with conflict resolution
- **Explainable AI** — 5-dimensional utility function scoring with weighted risk profiles
- **Enterprise Security** — AES-256-GCM encryption, RBAC sessions, Docker sandboxing
- **Immutable Audit Trail** — Merkle chain for tamper-proof decision logging
- **Proactive Monitoring** — Heartbeat-driven drift detection, scheduled jobs, webhook triggers
- **Interactive UI** — Canvas HTML with `a2ui-action` attributes for human-in-the-loop approval

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────────┐   │
│  │  Market  │  │  Cron    │  │ Heartbeat │  │ Webhooks (SEC,   │   │
│  │  Events  │  │  Jobs    │  │  (30min)  │  │ Earnings, Fed)   │   │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └────────┬─────────┘   │
└───────┼─────────────┼──────────────┼─────────────────┼─────────────┘
        └─────────────┴──────────────┴─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GATEWAY & ROUTING LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Typed Gateway (Pydantic Validation + Queue Management)     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Multi-Persona Router (Conservative / Growth / Liquidity)   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Advisor    │    │   Analyst    │    │   Client     │
│   Session    │    │   Session    │    │   Portal     │
│  (Full PII)  │    │  (Sandboxed) │    │ (Own Only)   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       └───────────────────┴───────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT REASONING LAYER                           │
│                                                                      │
│              ┌─────────────────────────────┐                        │
│              │    Coordinator Agent        │                        │
│              │    (Claude Opus)            │                        │
│              └──────────┬──────────────────┘                        │
│                         │ asyncio.gather()                          │
│              ┌──────────┴──────────┐                                │
│              ▼                     ▼                                │
│    ┌──────────────────┐  ┌──────────────────┐                      │
│    │  Drift Agent     │  │  Tax Agent       │                      │
│    │  (Sonnet)        │  │  (Sonnet)        │                      │
│    │  - Concentration │  │  - Wash Sales    │                      │
│    │  - Allocation    │  │  - Loss Harvest  │                      │
│    └──────────────────┘  └──────────────────┘                      │
│                                                                      │
│              ┌─────────────────────────────┐                        │
│              │   Conflict Resolution       │                        │
│              │   Utility Scoring (5-dim)   │                        │
│              └─────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                                 │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐     │
│  │  SQLCipher  │  │  ChromaDB       │  │  Merkle Chain       │     │
│  │  (Encrypted)│  │  (Vector Store) │  │  (Audit Trail)      │     │
│  └─────────────┘  └─────────────────┘  └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      HUMAN INTERFACE LAYER                           │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │  Canvas UI (HTML + a2ui)   │  │  Rich CLI                    │  │
│  │  Interactive Sliders       │  │  Ranked Recommendations      │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry (package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sentinel.git
cd sentinel

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your keys:
# ANTHROPIC_API_KEY=sk-ant-...
# MASTER_ENCRYPTION_KEY=<openssl rand -base64 32>
```

### Run the Golden Path Demo

```bash
poetry run python -m src.main --demo golden_path
```

This demonstrates:
1. Portfolio A ($50M) with 17% NVDA concentration
2. Tech sector drops 4%
3. Drift Agent recommends: "Sell NVDA" (concentration risk)
4. Tax Agent flags: "Wash sale violation" (sold NVDA 15 days ago)
5. Conflict resolution generates 3 scenarios
6. Utility scoring: **AMD substitute wins (69.6/100)**
7. Human approval → Merkle chain audit log

---

## Usage

```bash
# Run all tests (250+ passing)
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=src tests/

# Verify Merkle chain integrity
poetry run python -m src.main --verify-merkle

# Run proactive heartbeat demo
poetry run python -m src.main --demo heartbeat

# Run webhook trigger demo
poetry run python -m src.main --demo webhook
```

---

## Utility Function Scoring

Recommendations are scored across 5 dimensions with weights varying by risk profile:

| Dimension | Conservative | Moderate | Aggressive |
|-----------|--------------|----------|------------|
| Risk Reduction | 0.40 | 0.25 | 0.15 |
| Tax Savings | 0.20 | 0.30 | 0.20 |
| Goal Alignment | 0.20 | 0.25 | 0.30 |
| Transaction Cost | 0.15 | 0.10 | 0.10 |
| Urgency | 0.05 | 0.10 | 0.25 |

---

## Project Structure

```
sentinel/
├── src/
│   ├── agents/           # Drift, Tax, Coordinator agents
│   ├── contracts/        # Pydantic interfaces & stubs
│   ├── data/             # Market cache, vector store, models
│   ├── demos/            # Golden path, heartbeat, webhook demos
│   ├── gateway/          # Typed gateway with validation
│   ├── memory/           # Hot context / cold memory split
│   ├── routing/          # Persona router (risk profiles)
│   ├── security/         # Encryption, RBAC, sessions, Merkle
│   ├── skills/           # Dynamic skill registry
│   ├── state/            # State machine, utility scoring
│   ├── ui/               # Canvas generator, components
│   └── main.py           # CLI entry point
├── tests/                # 250+ test cases
├── data/
│   ├── portfolios/       # Portfolio A ($50M), B ($80M), C ($30M)
│   └── market_cache/     # Pre-cached market data (deterministic)
├── sentinel-web/         # React + Vite frontend (bonus)
├── docs/                 # Architecture specification
├── pyproject.toml        # Poetry dependencies
└── CLAUDE.md             # AI assistant instructions
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Agent Orchestration | Anthropic Claude (Opus/Sonnet) | Multi-agent reasoning |
| State Machine | transitions 0.9.0 | MONITOR → DETECT → ANALYZE → RECOMMEND |
| Database | SQLite + SQLCipher | Encrypted client data |
| Vector Search | ChromaDB 0.4.0 | Semantic + keyword hybrid search |
| Encryption | cryptography 42.0.0 | AES-256-GCM envelope encryption |
| CLI Output | Rich 13.7.0 | Beautiful terminal rendering |
| Validation | Pydantic 2.x | Schema validation at gateway |
| Scheduling | APScheduler 3.x | Cron jobs, heartbeats |
| Frontend | React + Vite | Interactive Canvas UI (bonus) |

---

## Security Architecture

### Session Boundaries

| Session | Access Level | Use Case |
|---------|--------------|----------|
| `advisor:main` | Full PII, all portfolios | Primary advisor workflow |
| `analyst` | Read-only, Docker sandboxed | Research, no PII exposure |
| `client` | Own portfolio only | Client self-service portal |

### Key Security Features

- **Envelope Encryption**: AES-256-GCM with per-record data keys
- **RBAC Decorators**: `@requires_permission("portfolio:read")`
- **Merkle Chain**: Append-only, tamper-evident audit trail
- **Docker Sandbox**: Analyst sessions run in isolated containers
- **Environment Variables**: Secrets never hardcoded (`.env` only)

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Pre-cached market data | Deterministic demos for repeatability |
| Hub-and-spoke agents | Sub-agents never communicate directly; prevents circular dependencies |
| Merkle chain (not blockchain) | Sufficient for POC audit trails |
| Three agents only | Enough for orchestration demo |
| CLI-first with Rich | Canvas HTML is bonus polish |
| Context/Memory split | Hot tokens expensive; cold storage cheap |

---

## Success Criteria

- [x] Golden path demo runs end-to-end
- [x] Utility function: AMD substitute ranks #1 (69.6/100)
- [x] Merkle chain integrity verified
- [x] Canvas UI renders with interactive sliders
- [x] Proactive heartbeat detects drift without external event
- [x] Session boundaries enforced (analyst can't access PII)
- [x] 250+ tests passing

---

## Sample Portfolios

| Portfolio | AUM | Strategy | Key Holdings |
|-----------|-----|----------|--------------|
| Portfolio A | $50M | Growth | NVDA (17%), AAPL, MSFT, GOOGL |
| Portfolio B | $80M | Conservative | AGG, BND, VEA, GLD |
| Portfolio C | $30M | Liquidity | Money market, short-term bonds |

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

## Author

**Shubham Upadhyay**
Built with Claude Code in 5 days

---

*Sentinel demonstrates production-grade patterns for AI-driven wealth management while maintaining explainability, security, and regulatory compliance.*

# Sentinel

**Multi-Agent UHNW Portfolio Monitoring & Tax Optimization System**

A production-grade AI system demonstrating enterprise multi-agent orchestration for ultra-high-net-worth ($30M-$80M) wealth management. Sentinel coordinates specialized AI agents to detect portfolio drift, identify tax optimization opportunities, resolve conflicting recommendations, and present ranked scenarios to human advisors — all with cryptographic audit trails and role-based access control.

---

## Table of Contents

- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Web Dashboard](#web-dashboard)
- [Golden Path Demo](#golden-path-demo)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Agent System](#agent-system)
- [Utility Function Scoring](#utility-function-scoring)
- [Security Architecture](#security-architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Sample Portfolios](#sample-portfolios)
- [Design Decisions](#design-decisions)

---

## Key Features

### Multi-Agent Orchestration
- **Coordinator Agent** (Claude Opus) dispatches Drift and Tax agents in parallel via `asyncio.gather()`
- **Hub-and-spoke topology** — sub-agents never communicate directly, preventing circular dependencies
- **Conflict resolution** when agents disagree (e.g., "sell NVDA" vs "wash sale violation")
- **Offline fallbacks** — rule-based analysis when LLM API is unavailable

### Explainable AI
- **5-dimensional utility function** scoring: risk reduction, tax savings, goal alignment, transaction cost, urgency
- **Three risk profiles** with distinct weight vectors (Conservative, Moderate, Aggressive)
- Every recommendation includes a numeric score breakdown so advisors understand the "why"

### Real-Time Web Dashboard
- **4-page React application** with live WebSocket updates
- Portfolio metrics, agent debate visualization, scenario comparison, and full audit trail
- Command palette (Cmd+K), keyboard shortcuts, toast notifications

### Proactive Monitoring
- **Heartbeat-driven** drift detection every 30 minutes — not just reactive to market events
- Scheduled cron jobs for routine portfolio health checks
- Webhook triggers for SEC filings, earnings reports, and Fed announcements

### Enterprise Security
- **AES-256-GCM** envelope encryption with per-record data keys
- **RBAC sessions** — advisor (full PII), analyst (sandboxed, read-only), client (own portfolio only)
- **Merkle chain** — append-only, tamper-evident audit trail with cryptographic verification
- Secrets exclusively via environment variables, never hardcoded

### Immutable Audit Trail
- Every agent decision, conflict resolution, and approval logged to a Merkle chain
- Tamper detection via hash verification
- Searchable and filterable in the web dashboard

---

## Architecture Overview

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
│  │  Typed Gateway (Pydantic Validation + Priority Queue)       │   │
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
│    │  - Sector Drift  │  │  - Lot Selection │                      │
│    └──────────────────┘  └──────────────────┘                      │
│                                                                      │
│              ┌─────────────────────────────┐                        │
│              │   Conflict Resolution       │                        │
│              │   Utility Scoring (5-dim)   │                        │
│              │   Scenario Generation       │                        │
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
│  ┌──────────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │  Web Dashboard       │  │  Canvas UI     │  │  Rich CLI     │  │
│  │  (React + WebSocket) │  │  (HTML + a2ui) │  │  (Terminal)   │  │
│  └──────────────────────┘  └────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Market Event → Gateway (Pydantic validation, priority queue)
  → State Machine (MONITOR → DETECT → ANALYZE → RECOMMEND → REVIEW → APPROVE → AUDIT)
  → Coordinator dispatches Drift + Tax agents in parallel
  → Conflict Resolution (if agents disagree)
  → Utility Function Scoring → Ranked Scenarios
  → Web Dashboard / Canvas UI → Advisor Approval
  → Merkle Chain Audit Log
```

---

## Web Dashboard

The web dashboard is a full-featured React application providing real-time visibility into Sentinel's agent operations.

### Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Portfolio overview with live metrics, holdings visualization, active agent status, event injector, and WebSocket connection indicator |
| **War Room** | Agent debate visualization — watch Drift and Tax agents argue their positions in real time with confidence scores, key points, and phase tracking |
| **Scenarios** | Multi-scenario comparison with utility score breakdowns, risk radar charts, action steps, and one-click approval with Merkle hash verification |
| **Audit Trail** | Block explorer for the Merkle chain — filter by event type, actor, session, and date range with full-text search and tamper detection |

### Frontend Stack

| Technology | Purpose |
|------------|---------|
| React 18 + TypeScript | Component framework |
| Vite 5 | Build tooling and HMR |
| TailwindCSS 3.4 | Utility-first styling |
| Zustand | Lightweight state management |
| Framer Motion | Animations and transitions |
| React Flow | Agent graph visualization |
| Recharts | Portfolio charts and radar plots |
| React Table | Sortable, filterable data tables |

### Backend API

| Router | Endpoints | Description |
|--------|-----------|-------------|
| `portfolios` | `GET /api/portfolios`, `GET /api/portfolios/{id}` | Portfolio data, holdings, allocation, risk profile |
| `chat` | `POST /api/chat` | Claude-powered conversational advisor interface |
| `scenarios` | `GET/POST /api/scenarios` | Dynamic scenario generation, approval workflow |
| `events` | Market event routing | Event type detection, priority assessment, sector impact |
| `audit` | `GET /api/audit/blocks` | Merkle chain query with filtering, search, pagination |

WebSocket endpoint at `/ws/activity` streams agent thinking, debate progress, and Merkle chain updates in real time.

---

## Golden Path Demo

The golden path demonstrates Sentinel's core value proposition — resolving conflicting agent recommendations through explainable utility scoring.

**Setup**: Portfolio A ($50M) with 17% NVDA concentration. Tech sector drops 4%.

```
Step 1: Drift Agent detects concentration risk
        → Recommends: "Sell NVDA to reduce from 17% to target 10%"

Step 2: Tax Agent flags wash sale violation
        → Warning: "NVDA was sold 15 days ago — selling again triggers
           wash sale under IRS 30-day rule"

Step 3: Conflict detected — Coordinator generates 3 scenarios:
        ┌──────────────────────────┬────────┐
        │ Scenario                 │ Score  │
        ├──────────────────────────┼────────┤
        │ AMD Substitute (buy AMD  │ 69.6   │ ← Winner
        │ to hedge, avoid wash)    │        │
        ├──────────────────────────┼────────┤
        │ Wait 16 Days (sell NVDA  │ 58.2   │
        │ after wash window)       │        │
        ├──────────────────────────┼────────┤
        │ Sell Anyway (accept wash │ 45.1   │
        │ sale penalty)            │        │
        └──────────────────────────┴────────┘

Step 4: Advisor reviews in Dashboard → Approves AMD substitute

Step 5: Decision logged to Merkle chain with cryptographic hash
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for web dashboard)
- Poetry (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sentinel.git
cd sentinel

# Install Python dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   MASTER_ENCRYPTION_KEY=<openssl rand -base64 32>
```

### Run the Core Demo

```bash
# Golden path — the primary demo scenario
poetry run python -m src.main --demo golden_path
```

### Run the Web Dashboard

```bash
# Terminal 1: Start the backend
cd sentinel-web/backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start the frontend
cd sentinel-web/frontend
npm install && npm run dev
```

Open `http://localhost:5173` to access the dashboard.

---

## Usage

### CLI Commands

```bash
# Run all tests (250+ passing)
python -m pytest -v

# Run with coverage
python -m pytest --cov=src tests/

# Run a specific test file
python -m pytest tests/test_golden_path.py -v

# Verify Merkle chain integrity
poetry run python -m src.main --verify-merkle

# Run proactive heartbeat demo
poetry run python -m src.main --demo heartbeat

# Run webhook trigger demo
poetry run python -m src.main --demo webhook

# Generate synthetic portfolios
poetry run python -m src.data.generate_portfolios
```

### Available Demos

| Demo | Command | What It Shows |
|------|---------|---------------|
| **Golden Path** | `--demo golden_path` | Full conflict resolution pipeline with NVDA/AMD scenario |
| **Heartbeat** | `--demo heartbeat` | Proactive drift detection without external market trigger |
| **Webhook** | `--demo webhook` | Event-driven processing from SEC filings or earnings |

---

## Agent System

### Hub-and-Spoke Architecture

Sentinel uses a strict hub-and-spoke topology. The Coordinator Agent is the sole orchestrator — sub-agents (Drift, Tax) **never** communicate directly with each other.

```
                    ┌─────────────────┐
                    │   Coordinator   │
                    │  (Claude Opus)  │
                    └────┬───────┬────┘
          asyncio.gather │       │ asyncio.gather
                    ┌────▼──┐ ┌──▼────┐
                    │ Drift │ │  Tax  │
                    │Sonnet │ │Sonnet │
                    └───────┘ └───────┘
```

### Agent Responsibilities

| Agent | Model | Capabilities |
|-------|-------|-------------|
| **Coordinator** | Claude Opus | Parallel dispatch, conflict resolution, scenario generation, utility scoring |
| **Drift Agent** | Claude Sonnet | Concentration risk detection, allocation drift analysis, sector exposure, urgency classification |
| **Tax Agent** | Claude Sonnet | Wash sale detection (IRS 30-day rule), tax-loss harvesting opportunities, lot selection optimization |

### Agent Factory

Agents are created via `AgentFactory` which injects:
- Session context (RBAC permissions, portfolio scope)
- Merkle chain reference (for audit logging)
- Risk profile configuration (weight vectors)

### Offline Mode

When the Anthropic API key is not configured, Sentinel falls back to rule-based analysis. Offline responses are clearly labeled with `[Offline Mode]` prefix and include `context_used: ["offline_mode"]` metadata.

### State Machine

The system progresses through 7 states with 14 valid transitions:

```
MONITOR → DETECT → ANALYZE → RECOMMEND → REVIEW → APPROVE → AUDIT
                                           │
                                           └→ REJECT → MONITOR
```

Powered by the `transitions` library with strict state validation.

---

## Utility Function Scoring

Every recommendation is scored across 5 dimensions. Weights vary by the client's risk profile:

| Dimension | Conservative | Moderate | Aggressive | What It Measures |
|-----------|:------------:|:--------:|:----------:|------------------|
| Risk Reduction | 0.40 | 0.25 | 0.15 | How much portfolio risk decreases |
| Tax Savings | 0.20 | 0.30 | 0.20 | Tax efficiency of the action |
| Goal Alignment | 0.20 | 0.25 | 0.30 | Fit with client's investment goals |
| Transaction Cost | 0.15 | 0.10 | 0.10 | Trading costs, market impact |
| Urgency | 0.05 | 0.10 | 0.25 | Time sensitivity of the action |

**Score formula**: `score = sum(dimension_score * weight for each dimension)` where each dimension is rated 0-10.

**Example** (Golden Path, Moderate Growth profile):
```
AMD Substitute:  (8×0.25) + (9×0.30) + (7×0.25) + (6×0.10) + (5×0.10) = 69.6
Wait 16 Days:    (6×0.25) + (8×0.30) + (5×0.25) + (8×0.10) + (3×0.10) = 58.2
Sell Anyway:     (9×0.25) + (2×0.30) + (6×0.25) + (4×0.10) + (7×0.10) = 45.1
```

---

## Security Architecture

### Session Boundaries

| Session | Access Level | Use Case |
|---------|-------------|----------|
| `advisor:main` | Full PII, all portfolios | Primary advisor workflow |
| `analyst` | Read-only, Docker sandboxed | Research and analysis, no PII exposure |
| `client` | Own portfolio only | Client self-service portal |

### Security Features

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| **Envelope Encryption** | AES-256-GCM with per-record data keys | Client data at rest |
| **RBAC Decorators** | `@requires_permission("portfolio:read")` | Endpoint authorization |
| **Merkle Chain** | SHA-256, append-only, hash-linked blocks | Tamper-evident audit trail |
| **Docker Sandbox** | Isolated containers for analyst sessions | Process-level isolation |
| **Environment Variables** | `.env` only, never hardcoded | Secret management |

### Merkle Chain Audit Trail

Every decision flows through the Merkle chain:

```
Block N-1                    Block N                      Block N+1
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ hash: a3f2...    │◄───│ prev: a3f2...    │◄───│ prev: 7b1c...    │
│ action: detect   │    │ hash: 7b1c...    │    │ hash: e9d4...    │
│ agent: drift     │    │ action: approve  │    │ action: execute  │
│ timestamp: ...   │    │ agent: advisor   │    │ agent: system    │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

Verification command: `poetry run python -m src.main --verify-merkle`

---

## Project Structure

```
sentinel/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── base.py          # BaseAgent with LLM integration
│   │   ├── coordinator.py   # Orchestrator (Opus) — dispatch, conflict resolution
│   │   ├── drift_agent.py   # Drift detection (Sonnet) — concentration, allocation
│   │   └── tax_agent.py     # Tax optimization (Sonnet) — wash sales, harvesting
│   ├── contracts/           # Pydantic schemas and interfaces
│   │   ├── schemas.py       # Event, Recommendation, Scenario models
│   │   └── interfaces.py   # Agent, Gateway, Storage protocols
│   ├── data/                # Data layer
│   │   ├── models.py        # Portfolio, Holding, Transaction models
│   │   ├── market_cache.py  # Pre-cached deterministic market data
│   │   └── vector_store.py  # ChromaDB hybrid search (semantic + keyword)
│   ├── demos/               # Runnable demo scenarios
│   │   ├── golden_path.py   # NVDA concentration → AMD substitute
│   │   ├── proactive_heartbeat.py  # Scheduled drift detection
│   │   └── webhook_trigger.py      # Event-driven processing
│   ├── gateway/             # Input processing
│   │   └── gateway.py       # Pydantic validation, priority queue
│   ├── memory/              # Context management
│   │   └── context.py       # Hot context / cold memory split
│   ├── routing/             # Request routing
│   │   └── persona_router.py  # Risk profile routing
│   ├── security/            # Security infrastructure
│   │   ├── encryption.py    # AES-256-GCM envelope encryption
│   │   ├── rbac.py          # Role-based access control decorators
│   │   ├── sessions.py      # Session management and boundaries
│   │   └── merkle.py        # Append-only Merkle chain
│   ├── state/               # State management
│   │   ├── machine.py       # 7-state FSM (transitions library)
│   │   └── utility.py       # 5-dimensional utility scoring
│   ├── skills/              # Dynamic skill registry
│   ├── ui/                  # Canvas UI generation
│   └── main.py              # CLI entry point
│
├── sentinel-web/            # Full-stack web dashboard
│   ├── backend/             # FastAPI + WebSocket server
│   │   ├── main.py          # App initialization, CORS, WebSocket
│   │   ├── config.py        # Environment-based configuration
│   │   ├── routers/         # API route handlers
│   │   │   ├── portfolios.py  # Portfolio CRUD
│   │   │   ├── chat.py        # Conversational advisor
│   │   │   ├── scenarios.py   # Scenario generation and approval
│   │   │   ├── events.py      # Market event processing
│   │   │   └── audit.py       # Merkle chain explorer
│   │   └── services/         # Business logic
│   │       ├── agent_runner.py    # LLM agent orchestration
│   │       ├── activity_stream.py # WebSocket event broadcasting
│   │       └── debate_runner.py   # Multi-agent debate simulation
│   └── frontend/            # React + Vite + TypeScript
│       └── src/
│           ├── pages/       # Dashboard, WarRoom, Scenarios, AuditTrail
│           ├── components/  # 30+ reusable UI components
│           └── stores/      # Zustand state (activity, chat)
│
├── tests/                   # 250+ test cases
│   ├── test_agents.py       # Agent behavior tests
│   ├── test_golden_path.py  # End-to-end golden path
│   ├── test_merkle.py       # Chain integrity verification
│   ├── test_encryption.py   # Encryption round-trip tests
│   ├── test_rbac.py         # Permission enforcement
│   ├── test_state_machine.py # State transition validation
│   └── ...                  # Gateway, E2E, Phase 3 tests
│
├── data/
│   ├── portfolios/          # Portfolio A ($50M), B ($80M), C ($30M)
│   └── market_cache/        # Pre-cached market data (deterministic)
│
├── pyproject.toml           # Poetry dependencies
├── CLAUDE.md                # AI assistant instructions
└── .env                     # Secrets (never committed)
```

---

## Tech Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Agent Orchestration | Anthropic Claude | Opus + Sonnet | Multi-agent reasoning and coordination |
| State Machine | transitions | 0.9.0 | 7-state FSM with 14 valid transitions |
| Database | SQLite + SQLCipher | 0.5.0 | Portable encrypted client data storage |
| Vector Search | ChromaDB | 0.4.0 | Semantic + keyword hybrid search |
| Encryption | cryptography | 42.0.0 | AES-256-GCM envelope encryption |
| Validation | Pydantic | 2.x | Schema validation at every boundary |
| Scheduling | APScheduler | 3.x | Cron jobs, heartbeats (30-min intervals) |
| CLI Output | Rich | 13.7.0 | Terminal rendering for demos |
| Web Framework | FastAPI + Uvicorn | latest | REST API + WebSocket server |
| Async I/O | aiofiles | 23.2.0 | Non-blocking file operations |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React + TypeScript | 18.2 / 5.3 | Component architecture |
| Build Tool | Vite | 5.1 | Fast builds and HMR |
| Styling | TailwindCSS | 3.4 | Utility-first CSS |
| State | Zustand | 4.5 | Lightweight global state |
| Animations | Framer Motion | 11.0 | Page transitions, agent activity |
| Charts | Recharts | 2.15 | Portfolio allocation, radar plots |
| Graphs | React Flow | 11.11 | Agent relationship visualization |
| Tables | React Table | 8.21 | Sortable, filterable audit data |
| Icons | Lucide React | 0.330 | Consistent iconography |

---

## Sample Portfolios

| Portfolio | AUM | Strategy | Risk Profile | Key Holdings |
|-----------|-----|----------|-------------|--------------|
| Portfolio A | $50M | Growth | Aggressive | NVDA (17%), AAPL, MSFT, GOOGL |
| Portfolio B | $80M | Conservative | Conservative | AGG, BND, VEA, GLD |
| Portfolio C | $30M | Liquidity | Conservative | Money market, short-term bonds |

All portfolio data is pre-cached in `data/portfolios/` for deterministic demo behavior.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Pre-cached market data** | Deterministic demos — no external API dependency, fully reproducible |
| **Hub-and-spoke agents** | Sub-agents never communicate directly; prevents circular dependencies and simplifies reasoning about agent behavior |
| **Merkle chain (not blockchain)** | Sufficient for audit trails in a single-organization context; avoids unnecessary consensus overhead |
| **Three agents only** | Drift + Tax + Coordinator is the minimal set that demonstrates parallel dispatch, conflict resolution, and orchestration |
| **Context/Memory split** | Hot context (token-limited, expensive) vs cold memory (markdown, unlimited) — mirrors production cost optimization |
| **Offline fallbacks** | Rule-based analysis ensures the system degrades gracefully without LLM access |
| **SQLCipher over Postgres** | Single-file encrypted database — portable, zero-config, suitable for POC |
| **WebSocket for real-time** | Streaming agent thinking and debate progress requires push semantics |
| **Pydantic at every boundary** | Gateway, inter-agent messages, API responses — type safety catches integration bugs early |

---

## Testing

250+ tests covering all system layers:

| Test Category | File | What It Validates |
|--------------|------|-------------------|
| Agent Behavior | `test_agents.py` | Agent responses, dispatch logic, conflict detection |
| Golden Path E2E | `test_golden_path.py` | Full pipeline: event → agents → scoring → approval |
| Merkle Chain | `test_merkle.py` | Append-only integrity, tamper detection |
| Encryption | `test_encryption.py` | AES-256-GCM round-trip, key rotation |
| RBAC | `test_rbac.py` | Permission enforcement, session boundaries |
| State Machine | `test_state_machine.py` | Valid/invalid transitions, state persistence |
| Gateway | `test_gateway.py` | Pydantic validation, priority queue ordering |
| End-to-End | `test_e2e.py` | Cross-component integration |

```bash
# Run all tests
python -m pytest -v

# Run with coverage report
python -m pytest --cov=src tests/

# Run a single test file
python -m pytest tests/test_golden_path.py -v
```

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

## Author

**Shubham Upadhyay**

---

*Sentinel demonstrates production-grade patterns for AI-driven wealth management — multi-agent orchestration, explainable scoring, cryptographic audit trails, and human-in-the-loop approval workflows — while maintaining security, transparency, and regulatory compliance.*

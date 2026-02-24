# Sentinel V2 — Interactive Web Application

## Implementation Plan

> **Objective**: Transform Sentinel from a CLI demo into a fully interactive web application that showcases real-time multi-agent coordination, designed to impress Goldman Sachs interviewers.

---

## Design Philosophy: "Terminal Luxe"

A fusion of Bloomberg Terminal's data density with modern fintech elegance. This isn't another generic dashboard — it's a **command center** for wealth management.

### Aesthetic Pillars

| Pillar | Execution |
|--------|-----------|
| **Dark Canvas** | Deep charcoal (#0C0C0E) with subtle noise texture — reduces eye strain, feels premium |
| **Data Typography** | Monospace for numbers (JetBrains Mono), geometric sans for UI (Geist) |
| **Accent Strategy** | Electric Cyan (#00E5CC) as primary action color, Amber (#F5A524) for warnings |
| **Motion Philosophy** | Purposeful animations — data streams, not decorations |
| **Information Density** | Bloomberg-level density with modern hierarchy |

### Color System

```css
/* SENTINEL V2 — Terminal Luxe Palette */
:root {
  /* Foundations */
  --s-void: #050506;
  --s-charcoal: #0C0C0E;
  --s-graphite: #141416;
  --s-slate: #1C1C1F;
  --s-ash: #2A2A2E;
  --s-smoke: #3D3D42;
  --s-mist: #6B6B73;
  --s-cloud: #A0A0A8;
  --s-pearl: #E8E8EC;
  --s-white: #FAFAFA;

  /* Accents */
  --s-cyan: #00E5CC;
  --s-cyan-dim: #00E5CC40;
  --s-cyan-glow: #00E5CC20;
  --s-amber: #F5A524;
  --s-amber-dim: #F5A52440;
  --s-red: #FF4757;
  --s-red-dim: #FF475720;
  --s-green: #2ED573;
  --s-green-dim: #2ED57320;

  /* Semantic */
  --s-surface-0: var(--s-void);
  --s-surface-1: var(--s-charcoal);
  --s-surface-2: var(--s-graphite);
  --s-surface-3: var(--s-slate);
  --s-border: var(--s-ash);
  --s-text-primary: var(--s-pearl);
  --s-text-secondary: var(--s-cloud);
  --s-text-muted: var(--s-mist);
}
```

### Typography System

```css
/* Fonts */
--s-font-display: 'Geist', system-ui, sans-serif;
--s-font-mono: 'JetBrains Mono', 'SF Mono', monospace;
--s-font-data: 'JetBrains Mono', monospace;

/* Scale */
--s-text-xs: 0.6875rem;    /* 11px - labels */
--s-text-sm: 0.75rem;      /* 12px - secondary */
--s-text-base: 0.875rem;   /* 14px - body */
--s-text-lg: 1rem;         /* 16px - emphasis */
--s-text-xl: 1.25rem;      /* 20px - headings */
--s-text-2xl: 1.5rem;      /* 24px - titles */
--s-text-3xl: 2rem;        /* 32px - hero */
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SENTINEL V2 WEB                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         REACT FRONTEND                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │  Dashboard  │ │   Agent     │ │   Chat      │ │  Scenario   │      │ │
│  │  │   View      │ │  Timeline   │ │   Panel     │ │   Builder   │      │ │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘      │ │
│  │         │               │               │               │              │ │
│  │         └───────────────┴───────────────┴───────────────┘              │ │
│  │                                   │                                     │ │
│  │                          WebSocket + REST                               │ │
│  └──────────────────────────────────┬─────────────────────────────────────┘ │
│                                     │                                        │
│  ┌──────────────────────────────────┴─────────────────────────────────────┐ │
│  │                         FASTAPI BACKEND                                 │ │
│  │                                                                         │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │  /api/      │ │  /api/      │ │  /api/      │ │  /ws/       │      │ │
│  │  │  events     │ │  chat       │ │  portfolios │ │  activity   │      │ │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘      │ │
│  │         │               │               │               │              │ │
│  │         └───────────────┴───────────────┴───────────────┘              │ │
│  │                                   │                                     │ │
│  │                        Sentinel Bridge Layer                            │ │
│  └──────────────────────────────────┬─────────────────────────────────────┘ │
│                                     │                                        │
│  ┌──────────────────────────────────┴─────────────────────────────────────┐ │
│  │                      EXISTING SENTINEL CORE                             │ │
│  │                                                                         │ │
│  │     src/agents/    src/security/    src/routing/    src/state/         │ │
│  │     (Drift, Tax,   (Merkle,         (Persona        (Utility           │ │
│  │      Coordinator)   RBAC)            Router)         Scoring)          │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Progress Tracker

### Phase Overview

| Phase | Name | Status | Duration | Dependencies |
|-------|------|--------|----------|--------------|
| 0 | Project Setup | ✅ Complete | 0.5 day | None |
| 1 | Backend API | ✅ Complete | 1 day | Phase 0 |
| 2 | Frontend Shell | ✅ Complete | 1 day | Phase 0 |
| 3 | Live Agent Timeline | ✅ Complete | 1 day | Phase 1, 2 |
| 4 | Chat Integration | ✅ Complete | 0.5 day | Phase 1, 2 |
| 5 | Scenario System | ✅ Complete | 1 day | Phase 3 |
| 6 | Polish & Effects | ✅ Complete | 1 day | Phase 5 |
| 7 | **AI/Agentic Wow Features** | 🟢 85% Complete | 2 days | Phase 3, 4 |

```
Legend: 🔴 Not Started | 🟡 In Progress | 🟢 Mostly Complete | ✅ Complete | ⏸️ Blocked
```

### AI/Agentic Features Summary

| Feature | Description | Wow Factor |
|---------|-------------|------------|
| Agent Debate Mode | Watch agents argue and reach consensus in real-time | 🔥🔥🔥🔥🔥 |
| Autonomous Chain Reaction | Agents spawn sub-agents automatically based on findings | 🔥🔥🔥🔥🔥 |
| Thinking Out Loud | Stream Claude's reasoning process live | 🔥🔥🔥🔥 |
| Proactive Agent Alerts | Agents interrupt with important findings | 🔥🔥🔥🔥 |
| Multi-Agent War Room | Mission control view of all agents communicating | 🔥🔥🔥🔥🔥 |

---

## Phase 0: Project Setup

**Goal**: Initialize the web application structure with proper tooling.

### Step 0.1: Create Directory Structure

```bash
sentinel-web/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Environment config
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── events.py            # Market event injection
│   │   ├── chat.py              # Claude chat endpoint
│   │   ├── portfolios.py        # Portfolio CRUD
│   │   └── scenarios.py         # Scenario management
│   ├── websocket/
│   │   ├── __init__.py
│   │   └── manager.py           # WebSocket connection manager
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sentinel_bridge.py   # Bridge to existing agents
│   │   ├── activity_stream.py   # Real-time activity events
│   │   └── chat_service.py      # Claude conversation handler
│   └── models/
│       ├── __init__.py
│       └── api_models.py        # Pydantic API schemas
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Shell.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── PortfolioCard.tsx
│   │   │   │   ├── HoldingsTable.tsx
│   │   │   │   └── RiskIndicator.tsx
│   │   │   ├── agents/
│   │   │   │   ├── AgentTimeline.tsx
│   │   │   │   ├── AgentNode.tsx
│   │   │   │   ├── ActivityFeed.tsx
│   │   │   │   └── MerkleVisualizer.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatPanel.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   └── ChatInput.tsx
│   │   │   ├── scenarios/
│   │   │   │   ├── ScenarioCard.tsx
│   │   │   │   ├── ScenarioComparison.tsx
│   │   │   │   ├── UtilityRadar.tsx
│   │   │   │   └── WhatIfSliders.tsx
│   │   │   ├── events/
│   │   │   │   ├── EventSimulator.tsx
│   │   │   │   └── EventButton.tsx
│   │   │   └── ui/
│   │   │       ├── Button.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Badge.tsx
│   │   │       ├── Progress.tsx
│   │   │       └── Tooltip.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useAgentActivity.ts
│   │   │   ├── usePortfolio.ts
│   │   │   └── useChat.ts
│   │   ├── stores/
│   │   │   ├── portfolioStore.ts
│   │   │   ├── activityStore.ts
│   │   │   └── scenarioStore.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   ├── styles/
│   │   │   └── globals.css
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── src/                          # Existing Sentinel core (unchanged)
└── requirements.txt              # Updated with web deps
```

| Step | Task | Status |
|------|------|--------|
| 0.1 | Create directory structure | ✅ |
| 0.2 | Initialize frontend (Vite + React + TypeScript) | ✅ |
| 0.3 | Configure Tailwind with design tokens | ✅ |
| 0.4 | Install backend dependencies (FastAPI, websockets) | ✅ |
| 0.5 | Create development scripts | ✅ |

**Phase 0 Progress Notes:**
- ✅ Created `sentinel-web/backend/` with routers (events, chat, portfolios, scenarios)
- ✅ Created `sentinel-web/frontend/` with Vite, React 18, TypeScript
- ✅ Implemented "Terminal Luxe" design system in `tailwind.config.js` and `index.css`
- ✅ Created WebSocket connection manager with real-time streaming
- ✅ Built core pages: Dashboard, Scenarios, WarRoom, AuditTrail
- ✅ Built core components: Layout, ChatPanel, AgentActivityFeed, EventInjector
- ✅ Implemented Zustand stores for state management

### Step 0.2: Frontend Initialization

```bash
cd sentinel-web/frontend
npm create vite@latest . -- --template react-ts
npm install tailwindcss postcss autoprefixer
npm install framer-motion zustand @tanstack/react-query
npm install lucide-react recharts
npx tailwindcss init -p
```

### Step 0.3: Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        sentinel: {
          void: '#050506',
          charcoal: '#0C0C0E',
          graphite: '#141416',
          slate: '#1C1C1F',
          ash: '#2A2A2E',
          smoke: '#3D3D42',
          mist: '#6B6B73',
          cloud: '#A0A0A8',
          pearl: '#E8E8EC',
          cyan: '#00E5CC',
          amber: '#F5A524',
          red: '#FF4757',
          green: '#2ED573',
        }
      },
      fontFamily: {
        display: ['Geist', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'glow': 'glow 2s ease-in-out infinite',
      }
    }
  }
}
```

### Step 0.4: Backend Dependencies

```txt
# requirements.txt (additions)
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
websockets>=12.0
python-multipart>=0.0.6
```

---

## Phase 1: Backend API

**Goal**: Create FastAPI backend with WebSocket support for real-time agent activity streaming.

### Step 1.1: FastAPI Application Core

| Step | Task | Status | File |
|------|------|--------|------|
| 1.1 | FastAPI app with CORS | ✅ | `backend/main.py` |
| 1.2 | WebSocket connection manager | ✅ | `backend/websocket/manager.py` |
| 1.3 | Sentinel bridge service | ✅ | `backend/services/sentinel_bridge.py` |
| 1.4 | Activity stream service | ✅ | `backend/services/activity_stream.py` |
| 1.5 | Events router | ✅ | `backend/routers/events.py` |
| 1.6 | Portfolios router | ✅ | `backend/routers/portfolios.py` |
| 1.7 | Chat router | ✅ | `backend/routers/chat.py` |
| 1.8 | API models | ✅ | `backend/models/api_models.py` |

### Step 1.1: Main Application

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import events, portfolios, chat, scenarios
from .websocket.manager import ConnectionManager

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Sentinel V2 Starting...")
    yield
    # Shutdown
    print("👋 Sentinel V2 Shutting down...")

app = FastAPI(
    title="Sentinel V2 API",
    description="Multi-Agent UHNW Portfolio Monitoring",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(portfolios.router, prefix="/api/portfolios", tags=["Portfolios"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenarios"])

@app.websocket("/ws/activity")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Step 1.2: WebSocket Manager

```python
# backend/websocket/manager.py
from fastapi import WebSocket
from typing import List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast activity to all connected clients"""
        for connection in self.active_connections:
            await connection.send_json(message)

    async def send_agent_activity(self, activity: dict):
        """Send agent activity update"""
        await self.broadcast({
            "type": "agent_activity",
            "data": activity
        })

    async def send_merkle_block(self, block: dict):
        """Send new Merkle block"""
        await self.broadcast({
            "type": "merkle_block",
            "data": block
        })

    async def send_scenario_update(self, scenarios: list):
        """Send scenario updates"""
        await self.broadcast({
            "type": "scenarios",
            "data": scenarios
        })
```

### Step 1.3: Sentinel Bridge

```python
# backend/services/sentinel_bridge.py
"""
Bridge between FastAPI and existing Sentinel agents.
Wraps the existing OfflineCoordinator with real-time event emission.
"""

from typing import Callable, Optional
import asyncio
from datetime import datetime, timezone

# Import existing Sentinel components
from src.agents import OfflineCoordinator
from src.contracts.schemas import Portfolio, MarketEventInput
from src.security import MerkleChain
from src.data import load_portfolio

class SentinelBridge:
    def __init__(self, activity_callback: Callable):
        self.activity_callback = activity_callback
        self.merkle_chain = MerkleChain()
        self.coordinator = None

    async def emit(self, event_type: str, data: dict):
        """Emit activity event to WebSocket"""
        await self.activity_callback({
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        })

    async def process_market_event(
        self,
        portfolio_id: str,
        event: MarketEventInput
    ) -> dict:
        """Process market event through Sentinel pipeline with live updates"""

        # Step 1: Gateway receives event
        await self.emit("gateway_received", {
            "agent": "gateway",
            "status": "active",
            "message": f"Event received: {event.description}"
        })
        await asyncio.sleep(0.5)  # Simulate processing

        # Step 2: Load portfolio
        portfolio = load_portfolio(portfolio_id)
        await self.emit("portfolio_loaded", {
            "agent": "gateway",
            "status": "complete",
            "message": f"Portfolio loaded: {portfolio.name}"
        })

        # Step 3: Coordinator starts
        await self.emit("coordinator_started", {
            "agent": "coordinator",
            "status": "active",
            "message": "Dispatching specialist agents..."
        })
        await asyncio.sleep(0.3)

        # Step 4: Parallel agent dispatch
        await self.emit("agents_dispatched", {
            "agent": "coordinator",
            "status": "active",
            "message": "Drift Agent and Tax Agent running in parallel"
        })

        # Step 5: Drift Agent
        await self.emit("drift_started", {
            "agent": "drift",
            "status": "active",
            "message": "Analyzing portfolio drift..."
        })
        await asyncio.sleep(0.8)

        # Step 6: Tax Agent (parallel)
        await self.emit("tax_started", {
            "agent": "tax",
            "status": "active",
            "message": "Checking tax implications..."
        })
        await asyncio.sleep(0.6)

        # Execute actual analysis
        self.coordinator = OfflineCoordinator(merkle_chain=self.merkle_chain)
        result = self.coordinator.execute_analysis(
            portfolio=portfolio,
            transactions=[],
            context={"market_event": event.model_dump()}
        )

        # Step 7: Drift results
        await self.emit("drift_complete", {
            "agent": "drift",
            "status": "complete",
            "message": f"Found {len(result.drift_findings.concentration_risks)} concentration risks",
            "findings": {
                "concentration_risks": [r.model_dump() for r in result.drift_findings.concentration_risks],
                "recommended_trades": [t.model_dump() for t in result.drift_findings.recommended_trades]
            }
        })

        # Step 8: Tax results
        await self.emit("tax_complete", {
            "agent": "tax",
            "status": "complete",
            "message": f"Found {len(result.tax_findings.wash_sale_violations)} wash sale risks",
            "findings": {
                "wash_sales": [w.model_dump() for w in result.tax_findings.wash_sale_violations],
                "opportunities": [o.model_dump() for o in result.tax_findings.tax_opportunities]
            }
        })
        await asyncio.sleep(0.3)

        # Step 9: Conflict detection
        if result.conflicts_detected:
            await self.emit("conflicts_detected", {
                "agent": "coordinator",
                "status": "warning",
                "message": f"Detected {len(result.conflicts_detected)} conflicts",
                "conflicts": [c.model_dump() for c in result.conflicts_detected]
            })
            await asyncio.sleep(0.4)

        # Step 10: Scenario generation
        await self.emit("scenarios_generating", {
            "agent": "coordinator",
            "status": "active",
            "message": f"Generating {len(result.scenarios)} scenarios..."
        })
        await asyncio.sleep(0.5)

        # Step 11: Utility scoring
        await self.emit("utility_scoring", {
            "agent": "coordinator",
            "status": "active",
            "message": "Scoring scenarios with 5-dimensional utility function..."
        })
        await asyncio.sleep(0.4)

        # Step 12: Complete
        await self.emit("analysis_complete", {
            "agent": "coordinator",
            "status": "complete",
            "message": f"Analysis complete. Recommended: {result.recommended_scenario_id}",
            "scenarios": [s.model_dump() for s in result.scenarios],
            "recommended_id": result.recommended_scenario_id,
            "merkle_hash": result.merkle_hash
        })

        # Emit Merkle blocks
        for block in self.merkle_chain._blocks[-10:]:
            await self.emit("merkle_block", {
                "agent": "merkle",
                "block": {
                    "event_type": block.event_type,
                    "hash": block.current_hash[:16] + "...",
                    "timestamp": block.timestamp.isoformat()
                }
            })
            await asyncio.sleep(0.1)

        return result.model_dump()
```

### Step 1.5: Events Router

```python
# backend/routers/events.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Literal
from datetime import datetime, timezone
import uuid

router = APIRouter()

class MarketEventRequest(BaseModel):
    event_type: Literal["tech_crash", "earnings_beat", "fed_rate", "custom"]
    portfolio_id: str = "portfolio_a"
    magnitude: float = -0.04
    description: str = ""

PRESET_EVENTS = {
    "tech_crash": {
        "affected_sectors": ["Technology"],
        "magnitude": -0.04,
        "description": "Technology sector drops 4% on semiconductor concerns"
    },
    "earnings_beat": {
        "affected_sectors": ["Technology"],
        "magnitude": 0.08,
        "affected_tickers": ["NVDA"],
        "description": "NVIDIA beats earnings estimates by 15%"
    },
    "fed_rate": {
        "affected_sectors": ["Fixed Income", "Financials"],
        "magnitude": -0.02,
        "description": "Federal Reserve signals rate hike concerns"
    }
}

@router.post("/inject")
async def inject_event(request: MarketEventRequest, background_tasks: BackgroundTasks):
    """Inject a market event and trigger analysis"""

    # Get preset or use custom
    if request.event_type in PRESET_EVENTS:
        event_data = PRESET_EVENTS[request.event_type].copy()
    else:
        event_data = {
            "affected_sectors": ["Technology"],
            "magnitude": request.magnitude,
            "description": request.description or "Custom market event"
        }

    event = MarketEventInput(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        event_type="market_event",
        timestamp=datetime.now(timezone.utc),
        session_id=f"session_{uuid.uuid4().hex[:8]}",
        priority=8,
        **event_data
    )

    # Process in background while streaming updates
    background_tasks.add_task(
        process_event_with_streaming,
        request.portfolio_id,
        event
    )

    return {
        "status": "processing",
        "event_id": event.event_id,
        "message": "Event injected. Watch the activity stream for updates."
    }

@router.get("/presets")
async def get_presets():
    """Get available event presets"""
    return {
        "presets": [
            {"id": "tech_crash", "name": "Tech Crash -4%", "icon": "trending-down", "color": "red"},
            {"id": "earnings_beat", "name": "NVDA Earnings +8%", "icon": "trending-up", "color": "green"},
            {"id": "fed_rate", "name": "Fed Rate Concern", "icon": "landmark", "color": "amber"},
        ]
    }
```

---

## Phase 2: Frontend Shell

**Goal**: Create the application shell with navigation, layout, and design system components.

### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 2.1 | Global styles and fonts | ✅ | `src/index.css` |
| 2.2 | UI primitives (Button, Card, Badge) | ✅ | `src/index.css` (Tailwind components) |
| 2.3 | Application shell layout | ✅ | `components/Layout.tsx` |
| 2.4 | Sidebar navigation | ✅ | `components/Layout.tsx` (integrated) |
| 2.5 | Header with portfolio selector | ✅ | `components/Layout.tsx` (integrated) |
| 2.6 | Dashboard grid layout | ✅ | `pages/Dashboard.tsx` |
| 2.7 | WebSocket hook | ✅ | `hooks/useWebSocket.ts` |
| 2.8 | Zustand stores | ✅ | `stores/activityStore.ts`, `stores/chatStore.ts` |

**Phase 2 Progress Notes:**
- ✅ Created comprehensive Terminal Luxe CSS with component classes
- ✅ Built unified Layout component with sidebar + header
- ✅ Implemented Dashboard with metrics grid, holdings table, activity feed
- ✅ Created all four main pages (Dashboard, Scenarios, WarRoom, AuditTrail)
- ✅ WebSocket hook with auto-reconnect and message handling
- ✅ Zustand stores for activity, chat, and agent state

### Step 2.1: Global Styles

```css
/* frontend/src/styles/globals.css */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

/* Geist font - self-hosted or use Vercel's CDN */
@font-face {
  font-family: 'Geist';
  src: url('/fonts/Geist-Regular.woff2') format('woff2');
  font-weight: 400;
}
@font-face {
  font-family: 'Geist';
  src: url('/fonts/Geist-Medium.woff2') format('woff2');
  font-weight: 500;
}
@font-face {
  font-family: 'Geist';
  src: url('/fonts/Geist-SemiBold.woff2') format('woff2');
  font-weight: 600;
}

@layer base {
  * {
    @apply border-sentinel-ash;
  }

  body {
    @apply bg-sentinel-void text-sentinel-pearl antialiased;
    font-family: 'Geist', system-ui, sans-serif;
  }

  /* Custom scrollbar */
  ::-webkit-scrollbar {
    @apply w-2 h-2;
  }
  ::-webkit-scrollbar-track {
    @apply bg-sentinel-charcoal;
  }
  ::-webkit-scrollbar-thumb {
    @apply bg-sentinel-smoke rounded-full;
  }
  ::-webkit-scrollbar-thumb:hover {
    @apply bg-sentinel-mist;
  }
}

@layer components {
  /* Data display */
  .data-value {
    @apply font-mono text-sentinel-cyan tabular-nums;
  }

  .data-label {
    @apply text-xs uppercase tracking-wider text-sentinel-mist;
  }

  /* Glow effects */
  .glow-cyan {
    box-shadow: 0 0 20px rgba(0, 229, 204, 0.15);
  }

  .glow-amber {
    box-shadow: 0 0 20px rgba(245, 165, 36, 0.15);
  }

  /* Surface cards */
  .surface-1 {
    @apply bg-sentinel-charcoal border border-sentinel-ash rounded-lg;
  }

  .surface-2 {
    @apply bg-sentinel-graphite border border-sentinel-ash rounded-lg;
  }

  /* Agent status indicators */
  .agent-idle {
    @apply bg-sentinel-smoke;
  }

  .agent-active {
    @apply bg-sentinel-cyan animate-pulse;
  }

  .agent-complete {
    @apply bg-sentinel-green;
  }

  .agent-warning {
    @apply bg-sentinel-amber;
  }

  .agent-error {
    @apply bg-sentinel-red;
  }
}

@layer utilities {
  /* Noise texture overlay */
  .noise-overlay {
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.03;
  }

  /* Terminal cursor blink */
  .cursor-blink::after {
    content: '▊';
    @apply animate-pulse text-sentinel-cyan;
  }
}
```

### Step 2.3: Application Shell

```tsx
// frontend/src/components/layout/Shell.tsx
import { ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

interface ShellProps {
  children: ReactNode
}

export function Shell({ children }: ShellProps) {
  return (
    <div className="flex h-screen bg-sentinel-void">
      {/* Noise overlay for texture */}
      <div className="fixed inset-0 noise-overlay pointer-events-none" />

      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

### Step 2.4: Sidebar

```tsx
// frontend/src/components/layout/Sidebar.tsx
import {
  LayoutDashboard,
  Activity,
  MessageSquare,
  GitBranch,
  Settings,
  Zap
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', icon: LayoutDashboard, href: '/', active: true },
  { name: 'Agent Activity', icon: Activity, href: '/activity' },
  { name: 'Chat', icon: MessageSquare, href: '/chat' },
  { name: 'Scenarios', icon: GitBranch, href: '/scenarios' },
  { name: 'Audit Trail', icon: Zap, href: '/audit' },
]

export function Sidebar() {
  return (
    <aside className="w-64 bg-sentinel-charcoal border-r border-sentinel-ash flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-sentinel-ash">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-sentinel-cyan to-sentinel-cyan/50 flex items-center justify-center">
            <span className="font-mono font-bold text-sentinel-void">S</span>
          </div>
          <div>
            <h1 className="font-semibold text-sentinel-pearl">SENTINEL</h1>
            <p className="text-[10px] text-sentinel-mist tracking-widest">PORTFOLIO INTELLIGENCE</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all",
              item.active
                ? "bg-sentinel-cyan/10 text-sentinel-cyan border border-sentinel-cyan/20"
                : "text-sentinel-cloud hover:bg-sentinel-slate hover:text-sentinel-pearl"
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.name}
          </a>
        ))}
      </nav>

      {/* System Status */}
      <div className="p-4 border-t border-sentinel-ash">
        <div className="surface-2 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-sentinel-mist">System Status</span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-sentinel-green animate-pulse" />
              <span className="text-xs text-sentinel-green">Online</span>
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-sentinel-mist">Merkle Blocks</span>
            <span className="text-xs font-mono text-sentinel-cloud">1,247</span>
          </div>
        </div>
      </div>

      {/* Settings */}
      <div className="p-4 border-t border-sentinel-ash">
        <a
          href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-sentinel-mist hover:bg-sentinel-slate hover:text-sentinel-pearl transition-all"
        >
          <Settings className="w-4 h-4" />
          Settings
        </a>
      </div>
    </aside>
  )
}
```

---

## Phase 3: Live Agent Timeline

**Goal**: Build the real-time agent execution visualization — the core "wow" feature.

### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 3.1 | Activity store (Zustand) | ✅ | `stores/activityStore.ts` |
| 3.2 | WebSocket hook | ✅ | `hooks/useWebSocket.ts` |
| 3.3 | Agent Timeline component | ✅ | `components/agents/AgentTimeline.tsx` |
| 3.4 | Agent Node with animations | ✅ | `components/agents/AgentNode.tsx` |
| 3.5 | Activity Feed | ✅ | `components/AgentActivityFeed.tsx` |
| 3.6 | Event Simulator panel | ✅ | `components/EventInjector.tsx` |
| 3.7 | Merkle Chain Visualizer | ✅ | `components/agents/MerkleVisualizer.tsx` |

**Phase 3 Progress Notes:**
- ✅ AgentTimeline with animated flow indicators and real-time status
- ✅ AgentNode with pulsing animations for active agents, thinking state visualization
- ✅ MerkleVisualizer showing chain blocks with verification status
- ✅ All components connected to Zustand stores for real-time updates

### Step 3.3: Agent Timeline

```tsx
// frontend/src/components/agents/AgentTimeline.tsx
import { motion, AnimatePresence } from 'framer-motion'
import { useActivityStore } from '@/stores/activityStore'
import { AgentNode } from './AgentNode'
import { cn } from '@/lib/utils'

const AGENTS = [
  { id: 'gateway', name: 'Gateway', description: 'Event ingestion & validation' },
  { id: 'coordinator', name: 'Coordinator', description: 'Orchestration & dispatch' },
  { id: 'drift', name: 'Drift Agent', description: 'Portfolio drift analysis' },
  { id: 'tax', name: 'Tax Agent', description: 'Tax optimization' },
  { id: 'merkle', name: 'Merkle Chain', description: 'Audit trail' },
]

export function AgentTimeline() {
  const { activities, isProcessing } = useActivityStore()

  // Derive agent states from activities
  const getAgentState = (agentId: string) => {
    const agentActivities = activities.filter(a => a.agent === agentId)
    if (agentActivities.length === 0) return 'idle'
    const latest = agentActivities[agentActivities.length - 1]
    return latest.status
  }

  const getAgentMessage = (agentId: string) => {
    const agentActivities = activities.filter(a => a.agent === agentId)
    if (agentActivities.length === 0) return null
    return agentActivities[agentActivities.length - 1].message
  }

  return (
    <div className="surface-1 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-sentinel-pearl">Agent Pipeline</h2>
          <p className="text-sm text-sentinel-mist">Real-time execution status</p>
        </div>

        {isProcessing && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 px-3 py-1.5 bg-sentinel-cyan/10 border border-sentinel-cyan/30 rounded-full"
          >
            <span className="w-2 h-2 rounded-full bg-sentinel-cyan animate-pulse" />
            <span className="text-xs font-medium text-sentinel-cyan">Processing</span>
          </motion.div>
        )}
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Connection line */}
        <div className="absolute left-6 top-8 bottom-8 w-px bg-gradient-to-b from-sentinel-ash via-sentinel-smoke to-sentinel-ash" />

        {/* Agent nodes */}
        <div className="space-y-4">
          {AGENTS.map((agent, index) => (
            <AgentNode
              key={agent.id}
              agent={agent}
              state={getAgentState(agent.id)}
              message={getAgentMessage(agent.id)}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>

      {/* Activity Log */}
      <div className="border-t border-sentinel-ash pt-4">
        <h3 className="text-xs uppercase tracking-wider text-sentinel-mist mb-3">Activity Log</h3>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          <AnimatePresence>
            {activities.slice(-10).reverse().map((activity, index) => (
              <motion.div
                key={`${activity.timestamp}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-start gap-3 text-sm"
              >
                <span className="font-mono text-[10px] text-sentinel-mist whitespace-nowrap">
                  {new Date(activity.timestamp).toLocaleTimeString()}
                </span>
                <span className={cn(
                  "font-mono text-xs px-1.5 py-0.5 rounded",
                  activity.status === 'active' && "bg-sentinel-cyan/20 text-sentinel-cyan",
                  activity.status === 'complete' && "bg-sentinel-green/20 text-sentinel-green",
                  activity.status === 'warning' && "bg-sentinel-amber/20 text-sentinel-amber",
                  activity.status === 'error' && "bg-sentinel-red/20 text-sentinel-red",
                )}>
                  {activity.agent}
                </span>
                <span className="text-sentinel-cloud">{activity.message}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
```

### Step 3.4: Agent Node

```tsx
// frontend/src/components/agents/AgentNode.tsx
import { motion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, Loader2, Circle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AgentNodeProps {
  agent: { id: string; name: string; description: string }
  state: 'idle' | 'active' | 'complete' | 'warning' | 'error'
  message: string | null
  delay: number
}

export function AgentNode({ agent, state, message, delay }: AgentNodeProps) {
  const icons = {
    idle: Circle,
    active: Loader2,
    complete: CheckCircle2,
    warning: AlertTriangle,
    error: AlertTriangle,
  }

  const Icon = icons[state]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={cn(
        "relative flex items-center gap-4 p-4 rounded-lg transition-all duration-300",
        state === 'idle' && "bg-transparent",
        state === 'active' && "bg-sentinel-cyan/5 border border-sentinel-cyan/20 glow-cyan",
        state === 'complete' && "bg-sentinel-green/5 border border-sentinel-green/20",
        state === 'warning' && "bg-sentinel-amber/5 border border-sentinel-amber/20",
        state === 'error' && "bg-sentinel-red/5 border border-sentinel-red/20",
      )}
    >
      {/* Status indicator */}
      <div className={cn(
        "w-12 h-12 rounded-lg flex items-center justify-center transition-all duration-300",
        state === 'idle' && "bg-sentinel-slate",
        state === 'active' && "bg-sentinel-cyan/20",
        state === 'complete' && "bg-sentinel-green/20",
        state === 'warning' && "bg-sentinel-amber/20",
        state === 'error' && "bg-sentinel-red/20",
      )}>
        <Icon className={cn(
          "w-5 h-5 transition-all duration-300",
          state === 'idle' && "text-sentinel-mist",
          state === 'active' && "text-sentinel-cyan animate-spin",
          state === 'complete' && "text-sentinel-green",
          state === 'warning' && "text-sentinel-amber",
          state === 'error' && "text-sentinel-red",
        )} />
      </div>

      {/* Agent info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn(
            "font-medium transition-colors duration-300",
            state === 'idle' && "text-sentinel-mist",
            state !== 'idle' && "text-sentinel-pearl",
          )}>
            {agent.name}
          </span>
          {state === 'active' && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-[10px] font-mono text-sentinel-cyan"
            >
              RUNNING
            </motion.span>
          )}
        </div>
        <p className={cn(
          "text-sm transition-colors duration-300",
          state === 'idle' && "text-sentinel-smoke",
          state !== 'idle' && "text-sentinel-cloud",
        )}>
          {message || agent.description}
        </p>
      </div>

      {/* Progress bar for active state */}
      {state === 'active' && (
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 2, ease: "linear" }}
          className="absolute bottom-0 left-0 right-0 h-0.5 bg-sentinel-cyan origin-left"
        />
      )}
    </motion.div>
  )
}
```

---

## Phase 4: Chat Integration

**Goal**: Add Claude-powered conversational interface.

### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 4.1 | Chat service (backend) | ✅ | `backend/routers/chat.py` (integrated) |
| 4.2 | Chat router | ✅ | `backend/routers/chat.py` |
| 4.3 | Chat store | ✅ | `stores/chatStore.ts` |
| 4.4 | Chat Panel component | ✅ | `components/ChatPanel.tsx` |
| 4.5 | Message bubbles | ✅ | `components/ChatPanel.tsx` (integrated) |
| 4.6 | Streaming response | ✅ | `backend/routers/chat.py` (POST /stream) |

**Phase 4 Progress Notes:**
- ✅ Chat router with Claude integration and streaming endpoint
- ✅ Mock responses when API key not available
- ✅ Chat store with message history
- ✅ Slide-in ChatPanel with suggestions

### Step 4.4: Chat Panel

```tsx
// frontend/src/components/chat/ChatPanel.tsx
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'
import { MessageBubble } from './MessageBubble'

const SUGGESTED_QUESTIONS = [
  "Why is NVDA flagged?",
  "Explain the wash sale conflict",
  "What are my tax-loss harvesting options?",
  "Compare the top two scenarios",
]

export function ChatPanel() {
  const [input, setInput] = useState('')
  const { messages, isLoading, sendMessage } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    sendMessage(input)
    setInput('')
  }

  return (
    <div className="surface-1 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-sentinel-ash">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sentinel-cyan to-sentinel-cyan/50 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-sentinel-void" />
          </div>
          <div>
            <h2 className="font-semibold text-sentinel-pearl">Ask Sentinel</h2>
            <p className="text-xs text-sentinel-mist">Powered by Claude</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Sparkles className="w-12 h-12 text-sentinel-mist mb-4" />
            <p className="text-sentinel-cloud mb-6">
              Ask me anything about your portfolio, scenarios, or recommendations.
            </p>
            <div className="grid grid-cols-2 gap-2 w-full max-w-md">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => {
                    setInput(q)
                    sendMessage(q)
                  }}
                  className="text-left text-sm p-3 rounded-lg bg-sentinel-slate hover:bg-sentinel-ash text-sentinel-cloud hover:text-sentinel-pearl transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))}
          </AnimatePresence>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-sentinel-ash">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Sentinel..."
            className="flex-1 bg-sentinel-slate border border-sentinel-ash rounded-lg px-4 py-3 text-sentinel-pearl placeholder:text-sentinel-mist focus:outline-none focus:border-sentinel-cyan focus:ring-1 focus:ring-sentinel-cyan/30"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="w-12 h-12 rounded-lg bg-sentinel-cyan text-sentinel-void flex items-center justify-center hover:bg-sentinel-cyan/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}
```

---

## Phase 5: Scenario System

**Goal**: Build interactive scenario cards with utility scoring visualization.

### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 5.1 | Scenario store | ✅ | `pages/Scenarios.tsx` (local state) |
| 5.2 | Scenario Card component | ✅ | `pages/Scenarios.tsx` (integrated) |
| 5.3 | Utility Radar chart | ✅ | `pages/Scenarios.tsx` (MetricPills) |
| 5.4 | Scenario Comparison view | ✅ | `backend/routers/scenarios.py` (API) |
| 5.5 | What-If Sliders | ✅ | `backend/routers/scenarios.py` (API) |
| 5.6 | Approval workflow | ✅ | `pages/Scenarios.tsx` + API |

**Phase 5 Progress Notes:**
- ✅ Full Scenarios page with card selection, metrics visualization
- ✅ Scenario approval with Merkle chain logging
- ✅ What-if analysis API endpoint
- ✅ Comparison API endpoint

### Step 5.2: Scenario Card

```tsx
// frontend/src/components/scenarios/ScenarioCard.tsx
import { motion } from 'framer-motion'
import { Star, TrendingUp, TrendingDown, Clock, DollarSign } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ScenarioCardProps {
  scenario: {
    id: string
    title: string
    description: string
    score: number
    isRecommended: boolean
    metrics: {
      riskReduction: number
      taxSavings: number
      goalAlignment: number
      transactionCost: number
      urgency: number
    }
    actions: Array<{
      type: 'buy' | 'sell' | 'hold'
      ticker: string
      quantity: number
    }>
  }
  onApprove: () => void
  onCompare: () => void
}

export function ScenarioCard({ scenario, onApprove, onCompare }: ScenarioCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className={cn(
        "surface-1 p-5 space-y-4 cursor-pointer transition-all",
        scenario.isRecommended && "ring-2 ring-sentinel-cyan/50 glow-cyan"
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {scenario.isRecommended && (
            <span className="flex items-center gap-1 px-2 py-0.5 bg-sentinel-cyan/20 text-sentinel-cyan text-xs rounded-full">
              <Star className="w-3 h-3" />
              Recommended
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-mono font-bold text-sentinel-pearl">
            {scenario.score.toFixed(1)}
          </div>
          <div className="text-[10px] text-sentinel-mist uppercase tracking-wider">
            Utility Score
          </div>
        </div>
      </div>

      {/* Title & Description */}
      <div>
        <h3 className="text-lg font-semibold text-sentinel-pearl">{scenario.title}</h3>
        <p className="text-sm text-sentinel-cloud mt-1">{scenario.description}</p>
      </div>

      {/* Score Breakdown */}
      <div className="space-y-2">
        <ScoreBar label="Risk Reduction" value={scenario.metrics.riskReduction} color="cyan" />
        <ScoreBar label="Tax Savings" value={scenario.metrics.taxSavings} color="green" />
        <ScoreBar label="Goal Alignment" value={scenario.metrics.goalAlignment} color="amber" />
      </div>

      {/* Actions Preview */}
      <div className="flex flex-wrap gap-2">
        {scenario.actions.slice(0, 3).map((action, i) => (
          <span
            key={i}
            className={cn(
              "flex items-center gap-1 px-2 py-1 rounded text-xs font-mono",
              action.type === 'sell' && "bg-sentinel-red/10 text-sentinel-red",
              action.type === 'buy' && "bg-sentinel-green/10 text-sentinel-green",
              action.type === 'hold' && "bg-sentinel-mist/10 text-sentinel-mist",
            )}
          >
            {action.type === 'sell' && <TrendingDown className="w-3 h-3" />}
            {action.type === 'buy' && <TrendingUp className="w-3 h-3" />}
            {action.ticker} {action.quantity.toLocaleString()}
          </span>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-2 border-t border-sentinel-ash">
        <button
          onClick={onApprove}
          className="flex-1 py-2 rounded-lg bg-sentinel-cyan text-sentinel-void font-medium hover:bg-sentinel-cyan/90 transition-colors"
        >
          Approve
        </button>
        <button
          onClick={onCompare}
          className="flex-1 py-2 rounded-lg bg-sentinel-slate text-sentinel-cloud font-medium hover:bg-sentinel-ash hover:text-sentinel-pearl transition-colors"
        >
          Compare
        </button>
      </div>
    </motion.div>
  )
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: 'cyan' | 'green' | 'amber' }) {
  const colors = {
    cyan: 'bg-sentinel-cyan',
    green: 'bg-sentinel-green',
    amber: 'bg-sentinel-amber',
  }

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-sentinel-mist">{label}</span>
        <span className="font-mono text-sentinel-cloud">{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 bg-sentinel-slate rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${(value / 10) * 100}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className={cn("h-full rounded-full", colors[color])}
        />
      </div>
    </div>
  )
}
```

---

## Phase 6: Polish & Effects

**Goal**: Add finishing touches, animations, and enterprise-grade polish.

### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 6.1 | Loading states & skeletons | ✅ | Components (terminal-cursor animations) |
| 6.2 | Error boundaries | ✅ | `components/ErrorBoundary.tsx` |
| 6.3 | Toast notifications | ✅ | `components/ui/Toast.tsx` |
| 6.4 | Keyboard shortcuts | ✅ | `hooks/useKeyboard.ts` |
| 6.5 | Responsive design | ✅ | Tailwind responsive classes |
| 6.6 | Sound effects (optional) | ⏭️ | Skipped |
| 6.7 | Merkle chain visualizer | ✅ | `components/agents/MerkleVisualizer.tsx` |
| 6.8 | Portfolio quick-switch | ✅ | `components/PortfolioSelector.tsx` |
| 6.9 | Final testing & QA | 🟡 | Pending

### Step 6.7: Merkle Visualizer

```tsx
// frontend/src/components/agents/MerkleVisualizer.tsx
import { motion, AnimatePresence } from 'framer-motion'
import { Link, Lock } from 'lucide-react'
import { useActivityStore } from '@/stores/activityStore'

export function MerkleVisualizer() {
  const { merkleBlocks } = useActivityStore()

  return (
    <div className="surface-1 p-4">
      <div className="flex items-center gap-2 mb-4">
        <Lock className="w-4 h-4 text-sentinel-cyan" />
        <h3 className="font-semibold text-sentinel-pearl">Merkle Audit Chain</h3>
        <span className="ml-auto font-mono text-xs text-sentinel-mist">
          {merkleBlocks.length} blocks
        </span>
      </div>

      <div className="flex items-center gap-1 overflow-x-auto pb-2">
        <AnimatePresence>
          {merkleBlocks.slice(-12).map((block, index) => (
            <motion.div
              key={block.hash}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="flex items-center"
            >
              {/* Block */}
              <div className="group relative">
                <div className="w-8 h-8 rounded bg-sentinel-slate hover:bg-sentinel-ash flex items-center justify-center cursor-pointer transition-colors">
                  <span className="font-mono text-[10px] text-sentinel-cyan">
                    {block.hash.slice(0, 4)}
                  </span>
                </div>

                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                  <div className="bg-sentinel-graphite border border-sentinel-ash rounded-lg p-2 text-xs whitespace-nowrap">
                    <div className="text-sentinel-mist">{block.event_type}</div>
                    <div className="font-mono text-sentinel-cloud">{block.hash}</div>
                  </div>
                </div>
              </div>

              {/* Chain link */}
              {index < merkleBlocks.length - 1 && (
                <Link className="w-4 h-4 text-sentinel-smoke mx-1" />
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
```

---

## Phase 7: AI/Agentic Wow Features

**Goal**: Implement the showstopper AI features that demonstrate true multi-agent intelligence and make Goldman interviewers say "wow."

### Architecture Enhancement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENHANCED AGENT SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      AGENT COMMUNICATION BUS                           │ │
│  │                                                                         │ │
│  │    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐        │ │
│  │    │  Drift  │◄───►│   Tax   │◄───►│  News   │◄───►│  Risk   │        │ │
│  │    │  Agent  │     │  Agent  │     │  Agent  │     │  Agent  │        │ │
│  │    └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘        │ │
│  │         │               │               │               │              │ │
│  │         └───────────────┴───────┬───────┴───────────────┘              │ │
│  │                                 │                                       │ │
│  │                          ┌──────▼──────┐                                │ │
│  │                          │ COORDINATOR │                                │ │
│  │                          │   (Opus)    │                                │ │
│  │                          └──────┬──────┘                                │ │
│  │                                 │                                       │ │
│  │    ┌────────────────────────────┼────────────────────────────┐         │ │
│  │    │                            │                            │         │ │
│  │    ▼                            ▼                            ▼         │ │
│  │ ┌──────────┐            ┌──────────────┐            ┌──────────┐       │ │
│  │ │ Debate   │            │   Thinking   │            │ Proactive│       │ │
│  │ │ Manager  │            │   Streamer   │            │ Monitor  │       │ │
│  │ └──────────┘            └──────────────┘            └──────────┘       │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Feature 7.1: Agent Debate Mode

**The "wow" moment**: Watch AI agents argue with each other and reach consensus.

#### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 7.1.1 | Debate orchestrator service | ✅ | `backend/services/sentinel_bridge.py` (run_agent_debate) |
| 7.1.2 | Agent opinion generator | ✅ | `backend/routers/events.py` (run_agent_debate) |
| 7.1.3 | Consensus resolver (Opus) | ✅ | `backend/services/sentinel_bridge.py` |
| 7.1.4 | Debate WebSocket events | ✅ | `backend/websocket/manager.py` (send_debate_message) |
| 7.1.5 | DebatePanel component | ✅ | `frontend/src/pages/WarRoom.tsx` |
| 7.1.6 | AgentAvatar component | ✅ | `components/agents/AgentAvatar.tsx` |
| 7.1.7 | DebateMessage component | ✅ | `frontend/src/pages/WarRoom.tsx` (DebateMessageCard) |
| 7.1.8 | ConsensusAnimation | ✅ | `components/agents/ConsensusAnimation.tsx` |

#### Step 7.1.1: Debate Orchestrator Service

```python
# backend/services/debate_orchestrator.py
"""
Orchestrates multi-agent debates when conflicts are detected.
Agents take turns presenting arguments, then Coordinator synthesizes.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

class DebatePhase(Enum):
    OPENING = "opening"           # Initial positions
    REBUTTAL = "rebuttal"         # Counter-arguments
    NEGOTIATION = "negotiation"   # Finding common ground
    SYNTHESIS = "synthesis"       # Coordinator resolves
    CONSENSUS = "consensus"       # Final agreement

@dataclass
class DebateMessage:
    agent_id: str
    agent_name: str
    phase: DebatePhase
    position: str               # "for" | "against" | "neutral"
    message: str
    confidence: float           # 0-100
    key_points: List[str]
    timestamp: str

@dataclass
class DebateResult:
    topic: str
    rounds: int
    messages: List[DebateMessage]
    consensus_reached: bool
    final_decision: str
    synthesis_reasoning: str
    agent_agreements: Dict[str, bool]  # agent_id -> agreed

class DebateOrchestrator:
    def __init__(self, activity_callback):
        self.activity_callback = activity_callback
        self.max_rounds = 3

    async def initiate_debate(
        self,
        topic: str,
        drift_position: dict,
        tax_position: dict,
        context: dict
    ) -> DebateResult:
        """
        Run a full debate between agents on a conflict.

        Example topic: "Should we sell NVDA now?"
        drift_position: {"action": "sell", "reasoning": "concentration risk"}
        tax_position: {"action": "hold", "reasoning": "wash sale window"}
        """

        messages = []

        # Phase 1: Opening Statements
        await self.emit_phase("opening", topic)

        drift_opening = await self._get_agent_argument(
            agent="drift",
            phase=DebatePhase.OPENING,
            topic=topic,
            position=drift_position,
            context=context
        )
        messages.append(drift_opening)
        await self.emit_message(drift_opening)
        await asyncio.sleep(1.5)  # Dramatic pause

        tax_opening = await self._get_agent_argument(
            agent="tax",
            phase=DebatePhase.OPENING,
            topic=topic,
            position=tax_position,
            context=context,
            previous_messages=messages
        )
        messages.append(tax_opening)
        await self.emit_message(tax_opening)
        await asyncio.sleep(1.5)

        # Phase 2: Rebuttals
        await self.emit_phase("rebuttal", topic)

        drift_rebuttal = await self._get_agent_argument(
            agent="drift",
            phase=DebatePhase.REBUTTAL,
            topic=topic,
            position=drift_position,
            context=context,
            previous_messages=messages
        )
        messages.append(drift_rebuttal)
        await self.emit_message(drift_rebuttal)
        await asyncio.sleep(1.2)

        tax_rebuttal = await self._get_agent_argument(
            agent="tax",
            phase=DebatePhase.REBUTTAL,
            topic=topic,
            position=tax_position,
            context=context,
            previous_messages=messages
        )
        messages.append(tax_rebuttal)
        await self.emit_message(tax_rebuttal)
        await asyncio.sleep(1.2)

        # Phase 3: Coordinator Synthesis
        await self.emit_phase("synthesis", topic)

        synthesis = await self._coordinator_synthesis(
            topic=topic,
            messages=messages,
            context=context
        )
        messages.append(synthesis)
        await self.emit_message(synthesis)
        await asyncio.sleep(0.5)

        # Phase 4: Consensus Check
        await self.emit_phase("consensus", topic)

        agreements = await self._check_consensus(
            synthesis=synthesis,
            agents=["drift", "tax"],
            context=context
        )

        await self.emit_consensus(agreements, synthesis)

        return DebateResult(
            topic=topic,
            rounds=2,
            messages=messages,
            consensus_reached=all(agreements.values()),
            final_decision=synthesis.message,
            synthesis_reasoning=synthesis.key_points,
            agent_agreements=agreements
        )

    async def emit_message(self, message: DebateMessage):
        await self.activity_callback({
            "type": "debate_message",
            "data": {
                "agent_id": message.agent_id,
                "agent_name": message.agent_name,
                "phase": message.phase.value,
                "position": message.position,
                "message": message.message,
                "confidence": message.confidence,
                "key_points": message.key_points,
                "timestamp": message.timestamp
            }
        })

    async def emit_phase(self, phase: str, topic: str):
        await self.activity_callback({
            "type": "debate_phase",
            "data": {"phase": phase, "topic": topic}
        })

    async def emit_consensus(self, agreements: dict, synthesis: DebateMessage):
        await self.activity_callback({
            "type": "debate_consensus",
            "data": {
                "consensus_reached": all(agreements.values()),
                "agreements": agreements,
                "final_decision": synthesis.message
            }
        })
```

#### Step 7.1.5: DebatePanel Component

```tsx
// frontend/src/components/agents/DebatePanel.tsx
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Swords, Scale, CheckCircle2, MessageSquare } from 'lucide-react'
import { useDebateStore } from '@/stores/debateStore'
import { AgentAvatar } from './AgentAvatar'
import { DebateMessage } from './DebateMessage'
import { ConsensusAnimation } from './ConsensusAnimation'

const PHASE_CONFIG = {
  opening: { label: 'Opening Statements', icon: MessageSquare, color: 'cyan' },
  rebuttal: { label: 'Rebuttals', icon: Swords, color: 'amber' },
  synthesis: { label: 'Coordinator Synthesis', icon: Scale, color: 'cyan' },
  consensus: { label: 'Consensus', icon: CheckCircle2, color: 'green' },
}

export function DebatePanel() {
  const {
    isDebating,
    currentPhase,
    topic,
    messages,
    consensusReached,
    agreements
  } = useDebateStore()

  if (!isDebating && messages.length === 0) {
    return null
  }

  const PhaseIcon = PHASE_CONFIG[currentPhase]?.icon || MessageSquare

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="surface-1 p-6 space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-sentinel-amber to-sentinel-red flex items-center justify-center">
            <Swords className="w-5 h-5 text-sentinel-void" />
          </div>
          <div>
            <h2 className="font-semibold text-sentinel-pearl">Agent Debate</h2>
            <p className="text-sm text-sentinel-mist">{topic}</p>
          </div>
        </div>

        {/* Phase Indicator */}
        <motion.div
          key={currentPhase}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
            PHASE_CONFIG[currentPhase]?.color === 'cyan'
              ? 'bg-sentinel-cyan/10 border-sentinel-cyan/30 text-sentinel-cyan'
              : PHASE_CONFIG[currentPhase]?.color === 'amber'
              ? 'bg-sentinel-amber/10 border-sentinel-amber/30 text-sentinel-amber'
              : 'bg-sentinel-green/10 border-sentinel-green/30 text-sentinel-green'
          }`}
        >
          <PhaseIcon className="w-4 h-4" />
          <span className="text-xs font-medium">
            {PHASE_CONFIG[currentPhase]?.label}
          </span>
        </motion.div>
      </div>

      {/* Debate Arena */}
      <div className="relative">
        {/* Agent Avatars */}
        <div className="flex justify-between mb-6">
          <AgentAvatar
            agent="drift"
            position="left"
            isActive={messages[messages.length - 1]?.agent_id === 'drift'}
          />
          <div className="flex flex-col items-center justify-center">
            <span className="text-2xl font-bold text-sentinel-mist">VS</span>
          </div>
          <AgentAvatar
            agent="tax"
            position="right"
            isActive={messages[messages.length - 1]?.agent_id === 'tax'}
          />
        </div>

        {/* Messages */}
        <div className="space-y-4 max-h-96 overflow-y-auto">
          <AnimatePresence>
            {messages.map((message, index) => (
              <DebateMessage
                key={`${message.agent_id}-${index}`}
                message={message}
                index={index}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Consensus Animation */}
        {currentPhase === 'consensus' && (
          <ConsensusAnimation
            reached={consensusReached}
            agreements={agreements}
          />
        )}
      </div>

      {/* Typing Indicator */}
      {isDebating && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-2 text-sentinel-mist"
        >
          <div className="flex gap-1">
            <span className="w-2 h-2 rounded-full bg-sentinel-cyan animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 rounded-full bg-sentinel-cyan animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 rounded-full bg-sentinel-cyan animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-sm">Agents deliberating...</span>
        </motion.div>
      )}
    </motion.div>
  )
}
```

---

### Feature 7.2: Autonomous Agent Chain Reaction

**The "wow" moment**: Agents automatically spawn sub-agents based on their findings.

#### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 7.2.1 | Agent spawner service | ✅ | `backend/services/sentinel_bridge.py` (process_market_event) |
| 7.2.2 | Task decomposition engine | ✅ | `backend/services/sentinel_bridge.py` (agents sequence) |
| 7.2.3 | Agent registry | ✅ | `backend/services/activity_stream.py` (agent tracking) |
| 7.2.4 | Chain reaction WebSocket events | ✅ | `backend/websocket/manager.py` (send_chain_event) |
| 7.2.5 | AgentTree component | ✅ | `frontend/src/components/agents/AgentTimeline.tsx` |
| 7.2.6 | SpawnAnimation component | ✅ | `frontend/src/components/agents/AgentNode.tsx` (animations) |
| 7.2.7 | ChainMetrics component | 🟡 | Pending (optional enhancement) |

#### Step 7.2.1: Agent Spawner Service

```python
# backend/services/agent_spawner.py
"""
Manages autonomous agent spawning based on analysis findings.
Agents can request sub-agents to handle specialized tasks.
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid

class AgentCapability(Enum):
    CONCENTRATION_ANALYSIS = "concentration_analysis"
    WASH_SALE_SCAN = "wash_sale_scan"
    LOSS_HARVESTING = "loss_harvesting"
    CORRELATION_CHECK = "correlation_check"
    NEWS_SENTIMENT = "news_sentiment"
    SECTOR_ANALYSIS = "sector_analysis"
    LIQUIDITY_CHECK = "liquidity_check"
    TAX_LOT_OPTIMIZER = "tax_lot_optimizer"

@dataclass
class SpawnedAgent:
    agent_id: str
    capability: AgentCapability
    parent_id: str
    status: str  # "spawning" | "running" | "complete" | "error"
    input_data: dict
    output_data: Optional[dict] = None
    depth: int = 0  # How many levels deep in the spawn chain

@dataclass
class ChainMetrics:
    total_agents_spawned: int
    max_depth: int
    tasks_completed: int
    time_elapsed_ms: int

class AgentSpawner:
    def __init__(self, activity_callback: Callable):
        self.activity_callback = activity_callback
        self.active_agents: Dict[str, SpawnedAgent] = {}
        self.max_depth = 3  # Prevent infinite spawning
        self.max_agents = 10  # Safety limit

    async def process_with_chain_reaction(
        self,
        initial_task: str,
        context: dict
    ) -> Dict:
        """
        Process a task, allowing agents to spawn sub-agents as needed.
        Returns complete chain results.
        """

        chain_id = f"chain_{uuid.uuid4().hex[:8]}"
        start_time = asyncio.get_event_loop().time()

        await self.emit_chain_start(chain_id, initial_task)

        # Start with coordinator
        coordinator_id = await self.spawn_agent(
            capability=None,  # Coordinator is special
            parent_id=None,
            input_data={"task": initial_task, **context},
            depth=0
        )

        # Process coordinator's analysis
        coordinator_result = await self._run_coordinator_analysis(
            coordinator_id, context
        )

        # Coordinator decides what sub-agents to spawn
        spawn_requests = coordinator_result.get("spawn_requests", [])

        for request in spawn_requests:
            if len(self.active_agents) >= self.max_agents:
                break

            await self.spawn_agent(
                capability=AgentCapability(request["capability"]),
                parent_id=coordinator_id,
                input_data=request["input_data"],
                depth=1
            )

        # Wait for all spawned agents to complete
        await self._wait_for_completion()

        # Collect results
        elapsed = int((asyncio.get_event_loop().time() - start_time) * 1000)

        metrics = ChainMetrics(
            total_agents_spawned=len(self.active_agents),
            max_depth=max(a.depth for a in self.active_agents.values()),
            tasks_completed=sum(1 for a in self.active_agents.values() if a.status == "complete"),
            time_elapsed_ms=elapsed
        )

        await self.emit_chain_complete(chain_id, metrics)

        return {
            "chain_id": chain_id,
            "agents": {k: v.__dict__ for k, v in self.active_agents.items()},
            "metrics": metrics.__dict__
        }

    async def spawn_agent(
        self,
        capability: Optional[AgentCapability],
        parent_id: Optional[str],
        input_data: dict,
        depth: int
    ) -> str:
        """Spawn a new agent and emit the event."""

        if depth > self.max_depth:
            return None

        agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        agent = SpawnedAgent(
            agent_id=agent_id,
            capability=capability,
            parent_id=parent_id,
            status="spawning",
            input_data=input_data,
            depth=depth
        )

        self.active_agents[agent_id] = agent

        await self.emit_agent_spawn(agent, parent_id)

        # Start the agent's work
        asyncio.create_task(self._run_agent(agent))

        return agent_id

    async def _run_agent(self, agent: SpawnedAgent):
        """Execute an agent's task and potentially spawn sub-agents."""

        agent.status = "running"
        await self.emit_agent_status(agent)

        # Simulate agent work with realistic timing
        await asyncio.sleep(0.8 + (agent.depth * 0.3))

        # Generate findings based on capability
        findings = await self._generate_findings(agent)
        agent.output_data = findings

        # Check if this agent wants to spawn sub-agents
        if agent.depth < self.max_depth and findings.get("needs_deeper_analysis"):
            for sub_task in findings.get("sub_tasks", []):
                await self.spawn_agent(
                    capability=AgentCapability(sub_task["capability"]),
                    parent_id=agent.agent_id,
                    input_data=sub_task["input"],
                    depth=agent.depth + 1
                )

        agent.status = "complete"
        await self.emit_agent_complete(agent)

    async def emit_agent_spawn(self, agent: SpawnedAgent, parent_id: str):
        await self.activity_callback({
            "type": "agent_spawn",
            "data": {
                "agent_id": agent.agent_id,
                "capability": agent.capability.value if agent.capability else "coordinator",
                "parent_id": parent_id,
                "depth": agent.depth,
                "status": agent.status
            }
        })

    async def emit_agent_complete(self, agent: SpawnedAgent):
        await self.activity_callback({
            "type": "agent_complete",
            "data": {
                "agent_id": agent.agent_id,
                "capability": agent.capability.value if agent.capability else "coordinator",
                "findings_summary": agent.output_data.get("summary", ""),
                "spawned_count": sum(1 for a in self.active_agents.values() if a.parent_id == agent.agent_id)
            }
        })

    async def emit_chain_complete(self, chain_id: str, metrics: ChainMetrics):
        await self.activity_callback({
            "type": "chain_complete",
            "data": {
                "chain_id": chain_id,
                "total_agents": metrics.total_agents_spawned,
                "max_depth": metrics.max_depth,
                "tasks_completed": metrics.tasks_completed,
                "time_ms": metrics.time_elapsed_ms
            }
        })
```

#### Step 7.2.5: AgentTree Component

```tsx
// frontend/src/components/agents/AgentTree.tsx
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, GitBranch, Zap, CheckCircle2, Loader2 } from 'lucide-react'
import { useChainStore } from '@/stores/chainStore'
import { cn } from '@/lib/utils'

interface AgentNode {
  agent_id: string
  capability: string
  parent_id: string | null
  status: 'spawning' | 'running' | 'complete'
  depth: number
  findings_summary?: string
}

export function AgentTree() {
  const { agents, metrics, isProcessing } = useChainStore()

  // Build tree structure from flat list
  const rootAgents = agents.filter(a => !a.parent_id)

  const getChildren = (parentId: string) =>
    agents.filter(a => a.parent_id === parentId)

  return (
    <div className="surface-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-sentinel-green to-sentinel-cyan flex items-center justify-center">
            <GitBranch className="w-5 h-5 text-sentinel-void" />
          </div>
          <div>
            <h2 className="font-semibold text-sentinel-pearl">Agent Chain Reaction</h2>
            <p className="text-sm text-sentinel-mist">Autonomous task decomposition</p>
          </div>
        </div>

        {/* Metrics */}
        {metrics && (
          <div className="flex items-center gap-4">
            <Metric label="Agents" value={metrics.total_agents} />
            <Metric label="Depth" value={metrics.max_depth} />
            <Metric label="Time" value={`${metrics.time_ms}ms`} />
          </div>
        )}
      </div>

      {/* Tree Visualization */}
      <div className="relative pl-4">
        {rootAgents.map(agent => (
          <TreeNode
            key={agent.agent_id}
            agent={agent}
            getChildren={getChildren}
            depth={0}
          />
        ))}
      </div>

      {/* Processing Indicator */}
      {isProcessing && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-2 text-sentinel-cyan"
        >
          <Zap className="w-4 h-4 animate-pulse" />
          <span className="text-sm">Chain reaction in progress...</span>
        </motion.div>
      )}
    </div>
  )
}

function TreeNode({
  agent,
  getChildren,
  depth
}: {
  agent: AgentNode
  getChildren: (id: string) => AgentNode[]
  depth: number
}) {
  const children = getChildren(agent.agent_id)

  const statusConfig = {
    spawning: { icon: Loader2, color: 'text-sentinel-amber', animate: 'animate-spin' },
    running: { icon: Loader2, color: 'text-sentinel-cyan', animate: 'animate-spin' },
    complete: { icon: CheckCircle2, color: 'text-sentinel-green', animate: '' },
  }

  const { icon: StatusIcon, color, animate } = statusConfig[agent.status]

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: depth * 0.1 }}
      className="relative"
    >
      {/* Connection Line */}
      {depth > 0 && (
        <div className="absolute left-0 top-4 w-4 h-px bg-sentinel-ash" />
      )}

      {/* Node */}
      <div className={cn(
        "flex items-center gap-3 p-3 rounded-lg mb-2 ml-4 transition-all",
        agent.status === 'running' && "bg-sentinel-cyan/5 border border-sentinel-cyan/20",
        agent.status === 'complete' && "bg-sentinel-green/5 border border-sentinel-green/20",
        agent.status === 'spawning' && "bg-sentinel-amber/5 border border-sentinel-amber/20",
      )}>
        {/* Icon */}
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center",
          agent.status === 'complete' ? "bg-sentinel-green/20" : "bg-sentinel-slate"
        )}>
          <StatusIcon className={cn("w-4 h-4", color, animate)} />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm text-sentinel-pearl">
              {agent.capability.replace(/_/g, ' ')}
            </span>
            {agent.status === 'complete' && children.length > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-sentinel-cyan/20 text-sentinel-cyan">
                +{children.length} spawned
              </span>
            )}
          </div>
          {agent.findings_summary && (
            <p className="text-xs text-sentinel-cloud truncate">
              {agent.findings_summary}
            </p>
          )}
        </div>
      </div>

      {/* Children */}
      {children.length > 0 && (
        <div className="ml-8 border-l border-sentinel-ash pl-4">
          {children.map(child => (
            <TreeNode
              key={child.agent_id}
              agent={child}
              getChildren={getChildren}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </motion.div>
  )
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="text-center">
      <div className="text-lg font-mono font-bold text-sentinel-pearl">{value}</div>
      <div className="text-[10px] text-sentinel-mist uppercase tracking-wider">{label}</div>
    </div>
  )
}
```

---

### Feature 7.3: Thinking Out Loud Mode

**The "wow" moment**: Stream Claude's actual reasoning process in real-time.

#### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 7.3.1 | Thinking stream service | ✅ | `backend/services/activity_stream.py` (integrated) |
| 7.3.2 | Claude streaming integration | ✅ | `backend/routers/chat.py` (POST /stream) |
| 7.3.3 | Thinking WebSocket events | ✅ | `backend/websocket/manager.py` (send_thinking) |
| 7.3.4 | ThinkingPanel component | ✅ | `frontend/src/components/agents/ThinkingPanel.tsx` |
| 7.3.5 | ThoughtBubble component | ✅ | `frontend/src/components/agents/ThinkingPanel.tsx` (ThoughtStream) |
| 7.3.6 | ThinkingToggle component | 🟡 | Pending (optional) |

#### Step 7.3.1: Thinking Stream Service

```python
# backend/services/thinking_stream.py
"""
Streams Claude's reasoning process as "thinking out loud" messages.
Uses Claude's response to break down reasoning into digestible steps.
"""

from typing import AsyncGenerator, List
from dataclasses import dataclass
from enum import Enum
import anthropic
import asyncio
import re

class ThoughtType(Enum):
    OBSERVATION = "observation"    # "I notice that..."
    ANALYSIS = "analysis"          # "Let me analyze..."
    CALCULATION = "calculation"    # "Calculating..."
    CONSIDERATION = "consideration" # "I should consider..."
    CONCLUSION = "conclusion"       # "Therefore..."
    UNCERTAINTY = "uncertainty"     # "I'm not sure about..."

@dataclass
class Thought:
    thought_type: ThoughtType
    content: str
    confidence: float  # 0-100
    references: List[str]  # Data points referenced

class ThinkingStreamer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def stream_thinking(
        self,
        agent_name: str,
        task: str,
        context: dict
    ) -> AsyncGenerator[Thought, None]:
        """
        Stream an agent's thinking process for a given task.
        Yields Thought objects as the agent "thinks."
        """

        system_prompt = f"""You are the {agent_name} agent in a wealth management system.

You are about to analyze a task. Think through it step-by-step, showing your reasoning.

Format your thinking as a series of thoughts, each on a new line starting with one of these prefixes:
- [OBSERVE] - When you notice something in the data
- [ANALYZE] - When you're analyzing implications
- [CALCULATE] - When computing numbers
- [CONSIDER] - When weighing options
- [CONCLUDE] - When reaching a conclusion
- [UNCERTAIN] - When something is unclear

Be specific, reference actual data, and show your confidence level (HIGH/MEDIUM/LOW) at the end of each thought.

Example:
[OBSERVE] The client sold NVDA on Feb 6, 2024. That was 15 days ago. HIGH
[ANALYZE] This means we're inside the 30-day wash sale window. HIGH
[CONSIDER] If we sell more NVDA now, the prior loss gets disallowed. HIGH
[CALCULATE] The disallowed loss would be approximately $25,000. MEDIUM
[CONCLUDE] We should either wait 16 more days or find a substitute security. HIGH
"""

        user_prompt = f"""Task: {task}

Context:
{self._format_context(context)}

Think through this step-by-step, showing your reasoning process."""

        # Stream the response
        with self.client.messages.stream(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            current_thought = ""

            for text in stream.text_stream:
                current_thought += text

                # Check if we have a complete thought (ends with confidence marker)
                if re.search(r'(HIGH|MEDIUM|LOW)\s*$', current_thought):
                    thought = self._parse_thought(current_thought.strip())
                    if thought:
                        yield thought
                    current_thought = ""
                    await asyncio.sleep(0.1)  # Small delay for effect

    def _parse_thought(self, text: str) -> Thought:
        """Parse a thought string into a Thought object."""

        type_mapping = {
            "[OBSERVE]": ThoughtType.OBSERVATION,
            "[ANALYZE]": ThoughtType.ANALYSIS,
            "[CALCULATE]": ThoughtType.CALCULATION,
            "[CONSIDER]": ThoughtType.CONSIDERATION,
            "[CONCLUDE]": ThoughtType.CONCLUSION,
            "[UNCERTAIN]": ThoughtType.UNCERTAINTY,
        }

        confidence_mapping = {
            "HIGH": 90,
            "MEDIUM": 70,
            "LOW": 40,
        }

        thought_type = ThoughtType.OBSERVATION
        for prefix, ttype in type_mapping.items():
            if text.startswith(prefix):
                thought_type = ttype
                text = text[len(prefix):].strip()
                break

        confidence = 70
        for marker, conf in confidence_mapping.items():
            if text.endswith(marker):
                confidence = conf
                text = text[:-len(marker)].strip()
                break

        return Thought(
            thought_type=thought_type,
            content=text,
            confidence=confidence,
            references=self._extract_references(text)
        )

    def _extract_references(self, text: str) -> List[str]:
        """Extract data references from thought text."""
        references = []
        # Look for ticker symbols
        tickers = re.findall(r'\b[A-Z]{2,5}\b', text)
        references.extend(tickers)
        # Look for dollar amounts
        amounts = re.findall(r'\$[\d,]+', text)
        references.extend(amounts)
        # Look for percentages
        percentages = re.findall(r'\d+(?:\.\d+)?%', text)
        references.extend(percentages)
        return list(set(references))

    def _format_context(self, context: dict) -> str:
        """Format context dict for the prompt."""
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
```

#### Step 7.3.4: ThinkingPanel Component

```tsx
// frontend/src/components/agents/ThinkingPanel.tsx
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Eye, Calculator, Scale, CheckCircle2, HelpCircle, Lightbulb } from 'lucide-react'
import { useThinkingStore } from '@/stores/thinkingStore'
import { ThoughtBubble } from './ThoughtBubble'
import { cn } from '@/lib/utils'

const THOUGHT_ICONS = {
  observation: Eye,
  analysis: Brain,
  calculation: Calculator,
  consideration: Scale,
  conclusion: CheckCircle2,
  uncertainty: HelpCircle,
}

const THOUGHT_COLORS = {
  observation: 'cyan',
  analysis: 'cyan',
  calculation: 'amber',
  consideration: 'amber',
  conclusion: 'green',
  uncertainty: 'red',
}

export function ThinkingPanel() {
  const { isThinking, currentAgent, thoughts, isEnabled, toggleEnabled } = useThinkingStore()
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="surface-1 overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 border-b border-sentinel-ash cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center transition-all",
            isThinking
              ? "bg-sentinel-cyan/20 animate-pulse"
              : "bg-sentinel-slate"
          )}>
            <Brain className={cn(
              "w-5 h-5",
              isThinking ? "text-sentinel-cyan" : "text-sentinel-mist"
            )} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-semibold text-sentinel-pearl">Thinking Out Loud</h2>
              {isThinking && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-sentinel-cyan/20 text-sentinel-cyan animate-pulse">
                  LIVE
                </span>
              )}
            </div>
            <p className="text-sm text-sentinel-mist">
              {currentAgent ? `${currentAgent} reasoning...` : 'Agent reasoning process'}
            </p>
          </div>
        </div>

        {/* Toggle */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            toggleEnabled()
          }}
          className={cn(
            "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
            isEnabled
              ? "bg-sentinel-cyan text-sentinel-void"
              : "bg-sentinel-slate text-sentinel-mist"
          )}
        >
          {isEnabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>

      {/* Thoughts Stream */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
              {thoughts.length === 0 ? (
                <div className="text-center py-8 text-sentinel-mist">
                  <Lightbulb className="w-8 h-8 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">Inject an event to see agent reasoning</p>
                </div>
              ) : (
                <AnimatePresence>
                  {thoughts.map((thought, index) => (
                    <ThoughtBubble
                      key={index}
                      thought={thought}
                      index={index}
                    />
                  ))}
                </AnimatePresence>
              )}

              {/* Typing indicator */}
              {isThinking && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-2 text-sentinel-mist pl-4"
                >
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-sentinel-cyan animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-sentinel-cyan animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-sentinel-cyan animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </span>
                  <span className="text-xs italic">thinking...</span>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
```

---

### Feature 7.4: Proactive Agent Alerts

**The "wow" moment**: Agents interrupt with important findings without being asked.

#### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 7.4.1 | Background monitor service | ✅ | `backend/services/activity_stream.py` (emit_alert) |
| 7.4.2 | Alert priority engine | 🟡 | Pending (demo uses severity levels) |
| 7.4.3 | Proactive insights generator | 🟡 | Pending (optional enhancement) |
| 7.4.4 | Alert WebSocket events | ✅ | `backend/websocket/manager.py` (send_alert) |
| 7.4.5 | AlertToast component | ✅ | `frontend/src/components/alerts/AlertPanel.tsx` (AlertToast) |
| 7.4.6 | AlertPanel component | ✅ | `frontend/src/components/alerts/AlertPanel.tsx` |
| 7.4.7 | AlertAction component | ✅ | `frontend/src/components/alerts/AlertPanel.tsx` (integrated) |

#### Step 7.4.5: AlertToast Component

```tsx
// frontend/src/components/alerts/AlertToast.tsx
import { motion, AnimatePresence } from 'framer-motion'
import { X, Bell, AlertTriangle, TrendingUp, Calendar, DollarSign } from 'lucide-react'
import { useAlertStore } from '@/stores/alertStore'
import { cn } from '@/lib/utils'

const ALERT_CONFIG = {
  wash_sale_window: {
    icon: Calendar,
    color: 'amber',
    title: 'Wash Sale Window Alert',
  },
  concentration_breach: {
    icon: AlertTriangle,
    color: 'red',
    title: 'Concentration Limit Alert',
  },
  tax_opportunity: {
    icon: DollarSign,
    color: 'green',
    title: 'Tax Opportunity Found',
  },
  price_movement: {
    icon: TrendingUp,
    color: 'cyan',
    title: 'Significant Price Movement',
  },
}

interface Alert {
  id: string
  type: keyof typeof ALERT_CONFIG
  agent: string
  message: string
  detail: string
  actions: Array<{
    label: string
    action: string
  }>
  timestamp: string
}

export function AlertToast({ alert, onDismiss }: { alert: Alert; onDismiss: () => void }) {
  const config = ALERT_CONFIG[alert.type]
  const Icon = config.icon

  const colorClasses = {
    amber: 'border-sentinel-amber/50 bg-sentinel-amber/10',
    red: 'border-sentinel-red/50 bg-sentinel-red/10',
    green: 'border-sentinel-green/50 bg-sentinel-green/10',
    cyan: 'border-sentinel-cyan/50 bg-sentinel-cyan/10',
  }

  const iconClasses = {
    amber: 'bg-sentinel-amber/20 text-sentinel-amber',
    red: 'bg-sentinel-red/20 text-sentinel-red',
    green: 'bg-sentinel-green/20 text-sentinel-green',
    cyan: 'bg-sentinel-cyan/20 text-sentinel-cyan',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      className={cn(
        "w-96 rounded-xl border shadow-2xl overflow-hidden",
        colorClasses[config.color]
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3 p-4">
        <div className={cn(
          "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0",
          iconClasses[config.color]
        )}>
          <Icon className="w-5 h-5" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-sentinel-mist">
              {alert.agent.toUpperCase()} AGENT
            </span>
            <button
              onClick={onDismiss}
              className="text-sentinel-mist hover:text-sentinel-pearl transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <h3 className="font-semibold text-sentinel-pearl mt-1">
            {config.title}
          </h3>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-4">
        <p className="text-sm text-sentinel-pearl mb-2">{alert.message}</p>
        <p className="text-xs text-sentinel-cloud">{alert.detail}</p>
      </div>

      {/* Actions */}
      {alert.actions.length > 0 && (
        <div className="flex border-t border-sentinel-ash/50">
          {alert.actions.map((action, index) => (
            <button
              key={action.action}
              className={cn(
                "flex-1 py-3 text-sm font-medium transition-colors",
                index === 0
                  ? "text-sentinel-cyan hover:bg-sentinel-cyan/10"
                  : "text-sentinel-mist hover:bg-sentinel-slate"
              )}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* Animated border */}
      <motion.div
        initial={{ scaleX: 1 }}
        animate={{ scaleX: 0 }}
        transition={{ duration: 10, ease: "linear" }}
        className={cn(
          "h-1 origin-left",
          config.color === 'amber' && "bg-sentinel-amber",
          config.color === 'red' && "bg-sentinel-red",
          config.color === 'green' && "bg-sentinel-green",
          config.color === 'cyan' && "bg-sentinel-cyan",
        )}
      />
    </motion.div>
  )
}

export function AlertContainer() {
  const { alerts, dismissAlert } = useAlertStore()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3">
      <AnimatePresence>
        {alerts.slice(0, 3).map((alert) => (
          <AlertToast
            key={alert.id}
            alert={alert}
            onDismiss={() => dismissAlert(alert.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}
```

---

### Feature 7.5: Multi-Agent War Room

**The "wow" moment**: Mission control view of all agents working and communicating.

#### Step Overview

| Step | Task | Status | File |
|------|------|--------|------|
| 7.5.1 | Agent communication bus | ✅ | `backend/services/sentinel_bridge.py` (integrated) |
| 7.5.2 | Inter-agent message protocol | ✅ | `backend/models/api_models.py` (DebateMessage) |
| 7.5.3 | War room WebSocket events | ✅ | `backend/websocket/manager.py` (send_war_room_update) |
| 7.5.4 | WarRoom component | ✅ | `frontend/src/pages/WarRoom.tsx` |
| 7.5.5 | AgentStatusCard component | ✅ | `frontend/src/pages/WarRoom.tsx` (integrated) |
| 7.5.6 | CommunicationBus component | 🟡 | Pending (optional enhancement) |
| 7.5.7 | CoordinatorPanel component | 🟡 | Pending (optional enhancement) |
| 7.5.8 | SystemMetrics component | 🟡 | Pending (optional enhancement) |

#### Step 7.5.4: WarRoom Component

```tsx
// frontend/src/components/warroom/WarRoom.tsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Radio, Users, Activity, Shield } from 'lucide-react'
import { useWarRoomStore } from '@/stores/warRoomStore'
import { AgentStatusCard } from './AgentStatusCard'
import { CommunicationBus } from './CommunicationBus'
import { CoordinatorPanel } from './CoordinatorPanel'
import { SystemMetrics } from './SystemMetrics'

const AGENTS = [
  { id: 'drift', name: 'Drift Agent', icon: '🔍', description: 'Portfolio drift analysis' },
  { id: 'tax', name: 'Tax Agent', icon: '💰', description: 'Tax optimization' },
  { id: 'news', name: 'News Agent', icon: '📰', description: 'News sentiment analysis' },
  { id: 'risk', name: 'Risk Agent', icon: '⚠️', description: 'Risk assessment' },
]

export function WarRoom() {
  const {
    agentStatuses,
    messages,
    coordinatorState,
    metrics,
    isLive
  } = useWarRoomStore()

  return (
    <div className="h-full flex flex-col bg-sentinel-void">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-sentinel-ash">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-sentinel-red to-sentinel-amber flex items-center justify-center">
            <Radio className="w-5 h-5 text-sentinel-void" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-sentinel-pearl">Agent War Room</h1>
            <p className="text-sm text-sentinel-mist">Multi-agent mission control</p>
          </div>
        </div>

        {/* Live Indicator */}
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
          isLive
            ? 'bg-sentinel-red/20 border border-sentinel-red/50'
            : 'bg-sentinel-slate'
        }`}>
          <span className={`w-2 h-2 rounded-full ${
            isLive ? 'bg-sentinel-red animate-pulse' : 'bg-sentinel-mist'
          }`} />
          <span className={`text-sm font-medium ${
            isLive ? 'text-sentinel-red' : 'text-sentinel-mist'
          }`}>
            {isLive ? 'LIVE' : 'STANDBY'}
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-4 p-4 overflow-hidden">
        {/* Agent Cards - Left Side */}
        <div className="col-span-3 space-y-3 overflow-y-auto">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-sentinel-mist" />
            <span className="text-xs uppercase tracking-wider text-sentinel-mist">
              Active Agents
            </span>
          </div>
          {AGENTS.map((agent) => (
            <AgentStatusCard
              key={agent.id}
              agent={agent}
              status={agentStatuses[agent.id] || 'idle'}
              lastMessage={messages.filter(m => m.from === agent.id).pop()?.content}
            />
          ))}
        </div>

        {/* Communication Bus - Center */}
        <div className="col-span-6 flex flex-col overflow-hidden">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-sentinel-mist" />
            <span className="text-xs uppercase tracking-wider text-sentinel-mist">
              Communication Bus
            </span>
          </div>
          <div className="flex-1 surface-1 rounded-lg overflow-hidden">
            <CommunicationBus messages={messages} />
          </div>
        </div>

        {/* Right Panel - Coordinator & Metrics */}
        <div className="col-span-3 flex flex-col gap-4 overflow-y-auto">
          {/* Coordinator */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-sentinel-mist" />
              <span className="text-xs uppercase tracking-wider text-sentinel-mist">
                Coordinator
              </span>
            </div>
            <CoordinatorPanel state={coordinatorState} />
          </div>

          {/* Metrics */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-sentinel-mist" />
              <span className="text-xs uppercase tracking-wider text-sentinel-mist">
                System Metrics
              </span>
            </div>
            <SystemMetrics metrics={metrics} />
          </div>
        </div>
      </div>
    </div>
  )
}
```

#### Step 7.5.6: CommunicationBus Component

```tsx
// frontend/src/components/warroom/CommunicationBus.tsx
import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  timestamp: string
  from: string
  to: string
  type: 'request' | 'response' | 'alert' | 'info'
  content: string
}

const AGENT_COLORS = {
  coordinator: 'cyan',
  drift: 'green',
  tax: 'amber',
  news: 'blue',
  risk: 'red',
}

export function CommunicationBus({ messages }: { messages: Message[] }) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto p-4 space-y-2 font-mono text-sm">
      <AnimatePresence>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-start gap-2"
          >
            {/* Timestamp */}
            <span className="text-[10px] text-sentinel-smoke whitespace-nowrap pt-0.5">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>

            {/* From Agent */}
            <span className={cn(
              "px-1.5 py-0.5 rounded text-[10px] font-bold uppercase",
              `bg-sentinel-${AGENT_COLORS[message.from] || 'mist'}/20`,
              `text-sentinel-${AGENT_COLORS[message.from] || 'mist'}`
            )}>
              {message.from}
            </span>

            {/* Arrow */}
            <ArrowRight className="w-3 h-3 text-sentinel-smoke flex-shrink-0 mt-1" />

            {/* To Agent */}
            <span className={cn(
              "px-1.5 py-0.5 rounded text-[10px] font-bold uppercase",
              `bg-sentinel-${AGENT_COLORS[message.to] || 'mist'}/20`,
              `text-sentinel-${AGENT_COLORS[message.to] || 'mist'}`
            )}>
              {message.to}
            </span>

            {/* Message Type Icon */}
            {message.type === 'alert' && (
              <AlertTriangle className="w-3 h-3 text-sentinel-amber flex-shrink-0 mt-1" />
            )}
            {message.type === 'response' && (
              <CheckCircle2 className="w-3 h-3 text-sentinel-green flex-shrink-0 mt-1" />
            )}

            {/* Content */}
            <span className="text-sentinel-cloud flex-1">
              {message.content}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Blinking cursor */}
      <motion.span
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.8, repeat: Infinity }}
        className="text-sentinel-cyan"
      >
        █
      </motion.span>
    </div>
  )
}
```

---

## Success Criteria: Phase 7

### Phase 7 Complete When:

- [ ] **Agent Debate Mode**
  - [ ] Agents present opposing viewpoints
  - [ ] Messages stream in real-time
  - [ ] Coordinator synthesizes solution
  - [ ] Consensus animation plays
  - [ ] Debate transcript exportable

- [ ] **Autonomous Chain Reaction**
  - [ ] Coordinator spawns sub-agents automatically
  - [ ] Tree visualization updates in real-time
  - [ ] Spawn animations are smooth
  - [ ] Metrics display correctly
  - [ ] Chain completes within 10 seconds

- [ ] **Thinking Out Loud**
  - [ ] Claude's reasoning streams live
  - [ ] Thought types correctly categorized
  - [ ] Confidence levels display
  - [ ] Toggle enables/disables feature
  - [ ] References highlight on hover

- [ ] **Proactive Alerts**
  - [ ] Alerts appear without user action
  - [ ] Toast animations are polished
  - [ ] Actions trigger correctly
  - [ ] Auto-dismiss after timeout
  - [ ] Alert history viewable

- [ ] **Multi-Agent War Room**
  - [ ] All agents visible simultaneously
  - [ ] Communication bus streams messages
  - [ ] Coordinator panel shows state
  - [ ] Metrics update in real-time
  - [ ] Live indicator pulses when active

---

## Updated Demo Script (Goldman Interview)

1. **Open Dashboard** — Show portfolio overview
2. **Inject Event** — "Tech Crash -4%"
3. **Watch Agent Timeline** — See parallel execution
4. **🆕 Trigger Debate** — "Watch the agents argue about what to do"
5. **🆕 See Thinking Process** — "Here's exactly how Tax Agent is reasoning"
6. **🆕 Chain Reaction** — "Coordinator is spawning sub-agents automatically"
7. **Review Scenarios** — Show generated options
8. **Chat Interaction** — "Why is this the best option?"
9. **🆕 Receive Alert** — "Tax Agent just found something important"
10. **🆕 War Room View** — "Here's the full mission control"
11. **Approve** — Sign off on recommendation

**Total Demo Time**: 8-10 minutes

---

## Development Commands

```bash
# Backend
cd sentinel-web/backend
uvicorn main:app --reload --port 8000

# Frontend
cd sentinel-web/frontend
npm run dev

# Run both (using concurrently)
npm run dev:all

# Build for production
npm run build

# Run tests
npm run test
pytest backend/tests/
```

---

## Success Criteria

### Phase 0 Complete When:
- [ ] Directory structure created
- [ ] Frontend builds without errors
- [ ] Tailwind configured with design tokens
- [ ] Backend starts and serves health check

### Phase 1 Complete When:
- [ ] WebSocket connection established
- [ ] `/api/events/inject` triggers analysis
- [ ] Activity events stream to frontend
- [ ] Sentinel bridge calls existing agents

### Phase 2 Complete When:
- [ ] App shell renders with sidebar
- [ ] Navigation works
- [ ] Design system consistent
- [ ] Portfolio data displays

### Phase 3 Complete When:
- [ ] Agent Timeline shows real-time updates
- [ ] Animations are smooth
- [ ] Activity log scrolls correctly
- [ ] Event injection triggers full pipeline

### Phase 4 Complete When:
- [ ] Chat interface functional
- [ ] Claude responses stream
- [ ] Context from portfolio/scenarios included
- [ ] Suggested questions work

### Phase 5 Complete When:
- [ ] Scenario cards render
- [ ] Utility scores display
- [ ] Comparison view works
- [ ] Approve action logs to Merkle

### Phase 6 Complete When:
- [ ] No loading flicker
- [ ] Errors handled gracefully
- [ ] Keyboard shortcuts work
- [ ] Mobile responsive
- [ ] Demo runs smoothly end-to-end

---

## Demo Script (Goldman Interview)

### The Full Demo Flow (8-10 minutes)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DEMO TIMELINE                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  0:00 ─── OPEN DASHBOARD ─────────────────────────────────────────────────  │
│           "Here's a $50M UHNW portfolio. Notice NVDA is flagged red."       │
│                                                                              │
│  0:30 ─── INJECT EVENT ───────────────────────────────────────────────────  │
│           Click "Tech Crash -4%"                                             │
│           "Let's see what happens when the market moves..."                 │
│                                                                              │
│  1:00 ─── WATCH AGENT TIMELINE ───────────────────────────────────────────  │
│           Gateway → Coordinator → Drift + Tax (parallel)                     │
│           "See how they're running simultaneously?"                          │
│                                                                              │
│  1:30 ─── 🆕 THINKING OUT LOUD ───────────────────────────────────────────  │
│           Toggle on "Thinking Mode"                                          │
│           "Watch the Tax Agent's actual reasoning process..."                │
│           Claude streams: "I notice a sale 15 days ago... wash sale risk"   │
│                                                                              │
│  2:30 ─── 🆕 CONFLICT → DEBATE MODE ─────────────────────────────────────  │
│           Conflict detected! Agents start debating.                          │
│           Drift: "We MUST sell, concentration is too high"                   │
│           Tax: "But the wash sale window..."                                 │
│           Coordinator: "I propose a synthesis: AMD substitute"               │
│           "Watch them actually argue and reach consensus."                   │
│                                                                              │
│  4:00 ─── 🆕 CHAIN REACTION ──────────────────────────────────────────────  │
│           Show Agent Tree expanding                                          │
│           "The coordinator is spawning sub-agents automatically..."          │
│           Concentration Analyzer → Loss Harvesting Finder → etc.             │
│                                                                              │
│  5:00 ─── REVIEW SCENARIOS ───────────────────────────────────────────────  │
│           3-4 scenario cards appear with utility scores                      │
│           "AMD Substitute scores 72.4 — optimal balance."                    │
│                                                                              │
│  5:30 ─── CHAT INTERACTION ───────────────────────────────────────────────  │
│           Type: "Explain this to a client in simple terms"                   │
│           Claude responds with plain-English explanation                     │
│                                                                              │
│  6:00 ─── 🆕 PROACTIVE ALERT ─────────────────────────────────────────────  │
│           Toast appears: "Tax Agent: Wash sale window closes in 16 days"     │
│           "Agents proactively surface important information."                │
│                                                                              │
│  6:30 ─── 🆕 WAR ROOM VIEW ───────────────────────────────────────────────  │
│           Switch to War Room tab                                             │
│           "Here's mission control — all agents, all communication."          │
│           Point to Communication Bus showing inter-agent messages            │
│                                                                              │
│  7:30 ─── MERKLE CHAIN ───────────────────────────────────────────────────  │
│           Show audit blocks                                                  │
│           "Every decision is cryptographically signed."                      │
│                                                                              │
│  8:00 ─── APPROVE SCENARIO ───────────────────────────────────────────────  │
│           Click "Approve" on recommended scenario                            │
│           Merkle signature recorded                                          │
│           "Compliance-ready audit trail."                                    │
│                                                                              │
│  8:30 ─── WRAP UP ────────────────────────────────────────────────────────  │
│           "Questions?"                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Talking Points

| Moment | What to Say |
|--------|-------------|
| Thinking Out Loud | "Complete transparency — you can see exactly how the AI reasons" |
| Agent Debate | "They don't just run in parallel — they negotiate and resolve conflicts" |
| Chain Reaction | "True autonomy — agents decide what sub-tasks need to happen" |
| Proactive Alerts | "The system is always watching, always helping" |
| War Room | "Enterprise-grade visibility into AI operations" |

### Backup Demos (if questions arise)

- **"How does it handle edge cases?"** → Inject "NVDA Earnings +15%" → Different scenario
- **"Is this secure?"** → Show Merkle chain, explain RBAC
- **"Can advisors customize?"** → Show What-If sliders
- **"What about compliance?"** → Export audit report PDF

---

*Last Updated*: 2026-02-22
*Plan Version*: 2.1 (AI/Agentic Features Added)

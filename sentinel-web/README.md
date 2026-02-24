# Sentinel V2 — Web Application

Real-time multi-agent portfolio intelligence platform with "Terminal Luxe" aesthetic.

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- pnpm (recommended) or npm

### Backend Setup

```bash
cd sentinel-web/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp ../.env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd sentinel-web/frontend

# Install dependencies
pnpm install  # or: npm install

# Start development server
pnpm dev  # or: npm run dev
```

### Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture

```
sentinel-web/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Environment configuration
│   ├── routers/             # API route handlers
│   │   ├── events.py        # Market event injection
│   │   ├── chat.py          # Claude AI chat
│   │   ├── portfolios.py    # Portfolio data
│   │   └── scenarios.py     # Scenario management
│   ├── websocket/
│   │   └── manager.py       # Real-time connection manager
│   └── models/
│       └── api_models.py    # Pydantic schemas
│
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── pages/           # Page components
    │   ├── hooks/           # Custom React hooks
    │   ├── stores/          # Zustand state stores
    │   └── types/           # TypeScript types
    ├── tailwind.config.js   # Terminal Luxe design tokens
    └── index.html
```

## Features

### Dashboard
- Portfolio overview with concentration alerts
- Real-time agent activity feed
- Top scenario recommendations
- Event injection for demos

### Scenario Analysis
- AI-generated rebalancing strategies
- Utility score breakdown (risk, tax, goals, cost, urgency)
- Side-by-side scenario comparison
- Approval workflow with Merkle chain logging

### Multi-Agent War Room
- Agent debate visualization
- Consensus tracking
- Real-time thinking streams

### Audit Trail
- Merkle chain visualization
- Cryptographic verification
- Decision history

### AI Chat
- Claude-powered conversational interface
- Portfolio context awareness
- Suggested questions

## Design System: Terminal Luxe

- **Background**: Deep charcoal (#0A0A0F)
- **Accent**: Electric Cyan (#00E5CC)
- **Typography**: JetBrains Mono (mono), Geist (sans)
- **Motion**: Framer Motion for purposeful animations

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portfolios/` | GET | List portfolios |
| `/api/portfolios/{id}` | GET | Get portfolio details |
| `/api/scenarios/` | GET | List scenarios |
| `/api/scenarios/approve` | POST | Approve scenario |
| `/api/events/inject` | POST | Inject market event |
| `/api/chat/message` | POST | Send chat message |
| `/ws/activity` | WS | Real-time agent activity |

## Development

### Running Tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && pnpm test
```

### Building for Production

```bash
# Frontend
cd frontend && pnpm build

# The build output will be in frontend/dist/
```

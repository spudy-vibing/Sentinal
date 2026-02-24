"""
SENTINEL V2 — Main Application
FastAPI entry point with WebSocket support.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_settings
from routers import events, portfolios, chat, scenarios, audit
from websocket.manager import ConnectionManager

settings = get_settings()
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print()
    print("=" * 60)
    print("  SENTINEL V2 — Starting...")
    print("=" * 60)
    print(f"  Debug Mode: {settings.debug}")
    print(f"  CORS Origins: {settings.cors_origins}")
    print()
    yield
    print()
    print("  SENTINEL V2 — Shutting down...")
    print()


app = FastAPI(
    title="Sentinel V2 API",
    description="Multi-Agent UHNW Portfolio Monitoring System",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(portfolios.router, prefix="/api/portfolios", tags=["Portfolios"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenarios"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Trail"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Sentinel V2 API",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "api": "online",
            "websocket": "online",
            "agents": "ready"
        }
    }


@app.websocket("/ws/activity")
async def websocket_activity(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent activity streaming.

    Clients connect here to receive:
    - Agent status updates
    - Thinking stream
    - Debate messages
    - Chain reaction updates
    - Proactive alerts
    - Merkle chain blocks
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            # Echo back for now (can be extended for bidirectional comms)
            await websocket.send_json({"type": "ack", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Make manager available to routers
app.state.ws_manager = manager


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

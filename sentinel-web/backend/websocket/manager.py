"""
SENTINEL V2 — WebSocket Connection Manager
Handles real-time streaming to connected clients.
"""

from fastapi import WebSocket
from typing import List, Dict, Any
import json
from datetime import datetime, timezone


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_count: int = 0

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        print(f"  [WS] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"  [WS] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"  [WS] Error sending to client: {e}")

    async def send_agent_activity(self, activity: Dict[str, Any]):
        """Send agent activity update."""
        # Normalize agent field names for frontend compatibility
        normalized = {**activity}
        if "agent" in normalized and "agent_name" not in normalized:
            agent_key = normalized.pop("agent")
            agent_names = {
                "gateway": "Gateway",
                "coordinator": "Coordinator",
                "drift": "Drift Agent",
                "tax": "Tax Agent",
                "compliance": "Compliance Agent",
                "scenario": "Scenario Agent",
            }
            normalized["agent_name"] = agent_names.get(agent_key, agent_key.title())
            normalized["agent_type"] = agent_key
        # Add timestamp if missing
        if "timestamp" not in normalized:
            normalized["timestamp"] = datetime.now(timezone.utc).isoformat()
        await self.broadcast({
            "type": "agent_activity",
            "data": normalized
        })

    async def send_thinking(self, thought: Dict[str, Any]):
        """Send thinking stream update."""
        # Normalize for frontend - convert content to chunk format
        normalized = {**thought}
        if "agent" in normalized and "agent_name" not in normalized:
            agent_key = normalized.pop("agent")
            agent_names = {
                "drift": "Drift Agent",
                "tax": "Tax Agent",
                "compliance": "Compliance Agent",
                "coordinator": "Coordinator",
            }
            normalized["agent_name"] = agent_names.get(agent_key, agent_key.title())
        # Convert content to chunk format expected by frontend
        if "content" in normalized and "chunk" not in normalized:
            normalized["chunk"] = normalized.pop("content") + " "
            normalized["is_complete"] = False
        await self.broadcast({
            "type": "thinking",
            "data": normalized
        })

    async def send_debate_message(self, message: Dict[str, Any]):
        """Send debate message."""
        await self.broadcast({
            "type": "debate_message",
            "data": message
        })

    async def send_debate_phase(self, phase: str, topic: str):
        """Send debate phase change."""
        await self.broadcast({
            "type": "debate_phase",
            "data": {"phase": phase, "topic": topic}
        })

    async def send_chain_event(self, event: Dict[str, Any]):
        """Send chain reaction event."""
        await self.broadcast({
            "type": "chain_event",
            "data": event
        })

    async def send_alert(self, alert: Dict[str, Any]):
        """Send proactive alert."""
        await self.broadcast({
            "type": "alert",
            "data": alert
        })

    async def send_merkle_block(self, block: Dict[str, Any]):
        """Send new Merkle block."""
        await self.broadcast({
            "type": "merkle_block",
            "data": block
        })

    async def send_scenarios(self, scenarios: List[Dict[str, Any]]):
        """Send scenario updates."""
        print(f"  [WS] Sending {len(scenarios)} scenarios to {len(self.active_connections)} clients", flush=True)
        for s in scenarios:
            print(f"  [WS]   - {s.get('id')}: {s.get('title')} (score: {s.get('score')})", flush=True)
        await self.broadcast({
            "type": "scenarios",
            "data": scenarios
        })

    async def send_war_room_update(self, update: Dict[str, Any]):
        """Send war room status update."""
        await self.broadcast({
            "type": "war_room",
            "data": update
        })

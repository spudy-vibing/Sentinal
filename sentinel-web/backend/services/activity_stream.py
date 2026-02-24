"""
SENTINEL V2 — Activity Stream Service
Manages real-time activity streaming with thinking mode and chain reactions.
"""

from typing import Callable, Optional, Dict, Any, List, AsyncGenerator
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum


class StreamType(str, Enum):
    """Types of stream events."""
    AGENT_ACTIVITY = "agent_activity"
    THINKING = "thinking"
    DEBATE = "debate_message"
    CHAIN_EVENT = "chain_event"
    ALERT = "alert"
    MERKLE = "merkle_block"
    SCENARIO = "scenarios"


@dataclass
class ThinkingState:
    """State for an agent's thinking stream."""
    agent_name: str
    thoughts: List[str] = field(default_factory=list)
    is_complete: bool = False
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ActivityStream:
    """
    Manages real-time activity streaming to connected WebSocket clients.
    Supports multiple stream types including thinking mode and debates.
    """

    def __init__(self, broadcast_callback: Callable):
        """
        Initialize the activity stream.

        Args:
            broadcast_callback: Async function to broadcast to all clients
        """
        self.broadcast = broadcast_callback
        self.active_thinking: Dict[str, ThinkingState] = {}
        self.chain_depth = 0
        self.max_chain_depth = 5

    async def emit(self, stream_type: StreamType, data: Dict[str, Any]):
        """
        Emit a stream event to all connected clients.

        Args:
            stream_type: Type of stream event
            data: Event data
        """
        await self.broadcast({
            "type": stream_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        })

    async def emit_agent_status(
        self,
        agent_name: str,
        agent_type: str,
        status: str,
        message: str,
        data: Optional[Dict] = None,
        progress: Optional[float] = None
    ):
        """Emit an agent status update."""
        payload = {
            "agent_name": agent_name,
            "agent_type": agent_type,
            "status": status,
            "message": message
        }
        if data:
            payload["data"] = data
        if progress is not None:
            payload["progress"] = progress

        await self.emit(StreamType.AGENT_ACTIVITY, payload)

    # =========================================================================
    # Thinking Stream
    # =========================================================================

    async def start_thinking(self, agent_name: str) -> ThinkingState:
        """
        Start a thinking stream for an agent.

        Args:
            agent_name: Name of the thinking agent

        Returns:
            ThinkingState object
        """
        state = ThinkingState(agent_name=agent_name)
        self.active_thinking[agent_name] = state

        await self.emit(StreamType.THINKING, {
            "agent_name": agent_name,
            "chunk": "",
            "is_complete": False,
            "thought_type": "start"
        })

        return state

    async def stream_thought(
        self,
        agent_name: str,
        chunk: str,
        thought_type: Optional[str] = None
    ):
        """
        Stream a thought chunk from an agent.

        Args:
            agent_name: Name of the thinking agent
            chunk: Thought text chunk
            thought_type: Optional type (analysis, hypothesis, conclusion)
        """
        if agent_name in self.active_thinking:
            self.active_thinking[agent_name].thoughts.append(chunk)

        await self.emit(StreamType.THINKING, {
            "agent_name": agent_name,
            "chunk": chunk,
            "is_complete": False,
            "thought_type": thought_type
        })

    async def end_thinking(self, agent_name: str, conclusion: Optional[str] = None):
        """
        End a thinking stream.

        Args:
            agent_name: Name of the thinking agent
            conclusion: Optional final conclusion
        """
        if agent_name in self.active_thinking:
            self.active_thinking[agent_name].is_complete = True

        await self.emit(StreamType.THINKING, {
            "agent_name": agent_name,
            "chunk": conclusion or "",
            "is_complete": True,
            "thought_type": "conclusion"
        })

        # Clean up
        if agent_name in self.active_thinking:
            del self.active_thinking[agent_name]

    async def stream_thinking_simulation(
        self,
        agent_name: str,
        thoughts: List[str],
        delay: float = 0.1
    ):
        """
        Simulate a thinking stream with predefined thoughts.
        Useful for demos.

        Args:
            agent_name: Name of the thinking agent
            thoughts: List of thought chunks to stream
            delay: Delay between chunks in seconds
        """
        await self.start_thinking(agent_name)

        for i, thought in enumerate(thoughts):
            thought_type = "analysis"
            if i == 0:
                thought_type = "hypothesis"
            elif i == len(thoughts) - 1:
                thought_type = "conclusion"

            await self.stream_thought(agent_name, thought, thought_type)
            await asyncio.sleep(delay)

        await self.end_thinking(agent_name)

    # =========================================================================
    # Agent Debate
    # =========================================================================

    async def emit_debate_message(
        self,
        agent_name: str,
        position: str,
        argument: str,
        confidence: float,
        references: Optional[List[str]] = None
    ):
        """
        Emit a debate message from an agent.

        Args:
            agent_name: Name of the debating agent
            position: Position (pro, con, neutral)
            argument: The argument text
            confidence: Confidence level (0-1)
            references: Optional list of references
        """
        await self.emit(StreamType.DEBATE, {
            "agent_name": agent_name,
            "position": position,
            "argument": argument,
            "confidence": confidence,
            "references": references or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # =========================================================================
    # Chain Reactions
    # =========================================================================

    async def emit_chain_event(
        self,
        trigger_agent: str,
        spawned_agent: str,
        reason: str,
        parent_event_id: Optional[str] = None
    ):
        """
        Emit a chain reaction event (one agent spawning another).

        Args:
            trigger_agent: Agent that triggered the spawn
            spawned_agent: Agent being spawned
            reason: Reason for spawning
            parent_event_id: ID of parent event in the chain
        """
        self.chain_depth += 1

        await self.emit(StreamType.CHAIN_EVENT, {
            "trigger_agent": trigger_agent,
            "spawned_agent": spawned_agent,
            "reason": reason,
            "chain_depth": self.chain_depth,
            "parent_event_id": parent_event_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def reset_chain_depth(self):
        """Reset the chain depth counter."""
        self.chain_depth = 0

    # =========================================================================
    # Proactive Alerts
    # =========================================================================

    async def emit_alert(
        self,
        alert_id: str,
        agent_name: str,
        severity: str,
        title: str,
        description: str,
        portfolio_id: str,
        suggested_action: Optional[str] = None
    ):
        """
        Emit a proactive alert from an agent.

        Args:
            alert_id: Unique alert identifier
            agent_name: Agent raising the alert
            severity: Severity level (info, warning, critical)
            title: Alert title
            description: Alert description
            portfolio_id: Related portfolio
            suggested_action: Optional suggested action
        """
        await self.emit(StreamType.ALERT, {
            "alert_id": alert_id,
            "agent_name": agent_name,
            "severity": severity,
            "title": title,
            "description": description,
            "portfolio_id": portfolio_id,
            "suggested_action": suggested_action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "acknowledged": False
        })

    # =========================================================================
    # Merkle Chain
    # =========================================================================

    async def emit_merkle_block(
        self,
        block_hash: str,
        event_type: str,
        event_data: Optional[Dict] = None
    ):
        """
        Emit a new Merkle block notification.

        Args:
            block_hash: Hash of the new block
            event_type: Type of event being logged
            event_data: Optional event data
        """
        await self.emit(StreamType.MERKLE, {
            "block_hash": block_hash,
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # =========================================================================
    # Scenarios
    # =========================================================================

    async def emit_scenarios(self, scenarios: List[Dict[str, Any]]):
        """
        Emit scenario updates.

        Args:
            scenarios: List of scenario objects
        """
        await self.emit(StreamType.SCENARIO, {
            "scenarios": scenarios,
            "count": len(scenarios),
            "recommended": next(
                (s["id"] for s in scenarios if s.get("is_recommended")),
                None
            )
        })

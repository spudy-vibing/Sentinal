"""
SENTINEL V2 — API Models
WebSocket message types and API schemas.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Types of agents in the system."""
    DRIFT = "drift"
    TAX = "tax"
    COMPLIANCE = "compliance"
    SCENARIO = "scenario"
    COORDINATOR = "coordinator"


class AgentStatus(str, Enum):
    """Agent status states."""
    IDLE = "idle"
    ANALYZING = "analyzing"
    THINKING = "thinking"
    DEBATING = "debating"
    COMPLETE = "complete"
    ERROR = "error"


class AgentActivity(BaseModel):
    """Real-time agent activity update."""
    agent_name: str
    agent_type: AgentType
    status: AgentStatus
    message: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None  # 0-100


class ThinkingChunk(BaseModel):
    """Streaming thought chunk from agent."""
    agent_name: str
    chunk: str
    is_complete: bool = False
    thought_type: Optional[str] = None  # "analysis", "hypothesis", "conclusion"


class DebateMessage(BaseModel):
    """Message in an agent debate."""
    agent_name: str
    position: str  # "pro", "con", "neutral"
    argument: str
    confidence: float  # 0-1
    references: List[str] = []
    timestamp: str


class DebateResult(BaseModel):
    """Final result of a debate."""
    winner: Optional[str] = None
    consensus: str
    key_points: List[str]
    final_recommendation: str
    vote_breakdown: Dict[str, float]


class ChainEvent(BaseModel):
    """Agent chain reaction event."""
    trigger_agent: str
    spawned_agent: str
    reason: str
    timestamp: str
    chain_depth: int
    parent_event_id: Optional[str] = None


class AlertMessage(BaseModel):
    """Proactive agent alert."""
    alert_id: str
    agent_name: str
    severity: str  # "info", "warning", "critical"
    title: str
    description: str
    portfolio_id: str
    suggested_action: Optional[str] = None
    timestamp: str
    acknowledged: bool = False


class MerkleBlock(BaseModel):
    """Merkle chain block for audit trail."""
    block_hash: str
    previous_hash: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: str
    signature: Optional[str] = None


class WarRoomUpdate(BaseModel):
    """War room session update."""
    session_id: str
    active_agents: List[str]
    current_focus: str
    consensus_level: float  # 0-1
    pending_decisions: List[str]
    timestamp: str


class PortfolioSnapshot(BaseModel):
    """Point-in-time portfolio state."""
    portfolio_id: str
    aum_usd: float
    holdings_count: int
    concentration_alerts: int
    drift_score: float
    timestamp: str


class ScenarioResult(BaseModel):
    """Scenario analysis result."""
    scenario_id: str
    title: str
    score: float
    is_recommended: bool
    actions_summary: str
    risk_summary: str


class WebSocketMessage(BaseModel):
    """Generic WebSocket message wrapper."""
    type: str
    data: Dict[str, Any]
    timestamp: str = None

    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)

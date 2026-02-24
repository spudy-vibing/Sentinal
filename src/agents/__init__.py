"""
SENTINEL AGENTS MODULE

AI agents for portfolio analysis using Claude.

Agents:
- Coordinator: Hub agent for orchestration
- DriftAgent: Portfolio drift and concentration risk detection
- TaxAgent: Tax optimization and wash sale detection
- BaseAgent: Base class for all agents

All agents follow the hub-and-spoke pattern:
- Never communicate directly with other agents
- Report to Coordinator only
- Use structured output for consistency
"""

from .base import (
    # Base classes
    BaseAgent,
    AgentFactory,
    # Configuration
    DEFAULT_MODEL,
    REASONING_MODEL,
    ANTHROPIC_API_KEY_ENV,
)

from .drift_agent import (
    DriftAgent,
    OfflineDriftAnalyzer,
    DRIFT_AGENT_SYSTEM_PROMPT,
)

from .tax_agent import (
    TaxAgent,
    OfflineTaxAnalyzer,
    TAX_AGENT_SYSTEM_PROMPT,
)

from .coordinator import (
    Coordinator,
    OfflineCoordinator,
    ConflictDetector,
    ScenarioGenerator,
    COORDINATOR_SYSTEM_PROMPT,
)

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentFactory",
    # Configuration
    "DEFAULT_MODEL",
    "REASONING_MODEL",
    "ANTHROPIC_API_KEY_ENV",
    # Coordinator
    "Coordinator",
    "OfflineCoordinator",
    "ConflictDetector",
    "ScenarioGenerator",
    "COORDINATOR_SYSTEM_PROMPT",
    # Drift Agent
    "DriftAgent",
    "OfflineDriftAnalyzer",
    "DRIFT_AGENT_SYSTEM_PROMPT",
    # Tax Agent
    "TaxAgent",
    "OfflineTaxAnalyzer",
    "TAX_AGENT_SYSTEM_PROMPT",
]

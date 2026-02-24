"""
SENTINEL STATE MODULE

State machine and utility function for system orchestration.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Steps 2.5-2.6
"""

from src.state.machine import (
    SentinelStateMachine,
    StateTransition,
    StateMachineFactory,
    InvalidTransitionError,
)
from src.state.utility import (
    UtilityFunction,
    UtilityFunctionFactory,
    ScoringConfig,
    score_and_rank,
)

__all__ = [
    # State Machine
    "SentinelStateMachine",
    "StateTransition",
    "StateMachineFactory",
    "InvalidTransitionError",
    # Utility Function
    "UtilityFunction",
    "UtilityFunctionFactory",
    "ScoringConfig",
    "score_and_rank",
]

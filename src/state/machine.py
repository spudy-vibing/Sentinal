"""
SENTINEL STATE MACHINE

Manages system state transitions with full audit logging.

States: MONITOR → DETECT → ANALYZE → CONFLICT_RESOLUTION → RECOMMEND → APPROVED → EXECUTE → MONITOR

All transitions are logged to the Merkle chain for compliance.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.5
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

from transitions import Machine
from transitions.core import EventData

from src.contracts.interfaces import IStateMachine, IMerkleChain
from src.contracts.schemas import SystemState
from src.contracts.security import AuditEventType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# STATE TRANSITION RECORD
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: str
    to_state: str
    trigger: str
    timestamp: datetime
    session_id: str
    metadata: dict = field(default_factory=dict)
    merkle_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for Merkle chain."""
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "trigger": self.trigger,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "metadata": self.metadata,
        }


# ═══════════════════════════════════════════════════════════════════════════
# STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════

class SentinelStateMachine(IStateMachine):
    """
    State machine for Sentinel system flow.

    Implements the core analysis pipeline:

    MONITOR → DETECT → ANALYZE → CONFLICT_RESOLUTION → RECOMMEND → APPROVED → EXECUTE
       ↑                                                                          │
       └──────────────────────────────────────────────────────────────────────────┘

    All transitions are logged to the Merkle chain for audit compliance.
    """

    # Define valid states
    STATES = [
        SystemState.MONITOR.value,
        SystemState.DETECT.value,
        SystemState.ANALYZE.value,
        SystemState.CONFLICT_RESOLUTION.value,
        SystemState.RECOMMEND.value,
        SystemState.APPROVED.value,
        SystemState.EXECUTE.value,
    ]

    # Define valid transitions
    TRANSITIONS = [
        # Normal flow
        {"trigger": "detect_event", "source": SystemState.MONITOR.value, "dest": SystemState.DETECT.value},
        {"trigger": "start_analysis", "source": SystemState.DETECT.value, "dest": SystemState.ANALYZE.value},
        {"trigger": "detect_conflict", "source": SystemState.ANALYZE.value, "dest": SystemState.CONFLICT_RESOLUTION.value},
        {"trigger": "no_conflict", "source": SystemState.ANALYZE.value, "dest": SystemState.RECOMMEND.value},
        {"trigger": "resolve_conflict", "source": SystemState.CONFLICT_RESOLUTION.value, "dest": SystemState.RECOMMEND.value},
        {"trigger": "approve", "source": SystemState.RECOMMEND.value, "dest": SystemState.APPROVED.value},
        {"trigger": "execute", "source": SystemState.APPROVED.value, "dest": SystemState.EXECUTE.value},
        {"trigger": "complete", "source": SystemState.EXECUTE.value, "dest": SystemState.MONITOR.value},

        # Reset/abort paths
        {"trigger": "reset", "source": SystemState.DETECT.value, "dest": SystemState.MONITOR.value},
        {"trigger": "reset", "source": SystemState.ANALYZE.value, "dest": SystemState.MONITOR.value},
        {"trigger": "reset", "source": SystemState.CONFLICT_RESOLUTION.value, "dest": SystemState.MONITOR.value},
        {"trigger": "reject", "source": SystemState.RECOMMEND.value, "dest": SystemState.MONITOR.value},
        {"trigger": "abort", "source": SystemState.APPROVED.value, "dest": SystemState.MONITOR.value},
        {"trigger": "abort", "source": SystemState.EXECUTE.value, "dest": SystemState.MONITOR.value},
    ]

    def __init__(
        self,
        session_id: str,
        merkle_chain: Optional[IMerkleChain] = None,
        initial_state: str = SystemState.MONITOR.value,
    ):
        """
        Initialize state machine.

        Args:
            session_id: Session identifier for audit logging
            merkle_chain: Optional Merkle chain for audit trail
            initial_state: Starting state (default: MONITOR)
        """
        self.session_id = session_id
        self._merkle_chain = merkle_chain
        self._history: list[StateTransition] = []
        self._callbacks: dict[str, list[Callable]] = {}

        # Initialize the transitions Machine
        self._machine = Machine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial=initial_state,
            auto_transitions=False,
            send_event=True,  # Pass EventData to callbacks
            before_state_change=self._before_transition,
            after_state_change=self._after_transition,
        )

        # Log initial state
        self._log_initial_state(initial_state)

    # ─────────────────────────────────────────────────────────────────────
    # IStateMachine Implementation
    # ─────────────────────────────────────────────────────────────────────

    def get_state(self) -> str:
        """Get current state."""
        return self.state

    def can_transition(self, to_state: str) -> bool:
        """Check if transition to target state is valid."""
        # Find a trigger that would get us to the target state
        for transition in self.TRANSITIONS:
            if transition["source"] == self.state and transition["dest"] == to_state:
                return True
        return False

    def transition(self, to_state: str, metadata: dict = None) -> bool:
        """
        Attempt state transition.

        Args:
            to_state: Target state
            metadata: Additional data for audit log

        Returns:
            True if transition succeeded

        Raises:
            InvalidTransitionError: If transition not allowed
        """
        # Find the trigger for this transition
        trigger = self._find_trigger(self.state, to_state)
        if trigger is None:
            raise InvalidTransitionError(
                f"No valid transition from {self.state} to {to_state}"
            )

        # Store metadata for the transition
        self._pending_metadata = metadata or {}

        # Execute the transition
        trigger_method = getattr(self, trigger)
        return trigger_method()

    def get_transition_history(self) -> list[dict]:
        """Get history of state transitions."""
        return [t.to_dict() for t in self._history]

    # ─────────────────────────────────────────────────────────────────────
    # Transition Callbacks
    # ─────────────────────────────────────────────────────────────────────

    def _before_transition(self, event: EventData) -> None:
        """Called before any state transition."""
        logger.debug(
            f"Transition starting: {event.transition.source} → {event.transition.dest} "
            f"(trigger: {event.event.name})"
        )

    def _after_transition(self, event: EventData) -> None:
        """Called after any state transition."""
        # Get metadata if available
        metadata = getattr(self, "_pending_metadata", {})
        self._pending_metadata = {}

        # Create transition record
        transition = StateTransition(
            from_state=event.transition.source,
            to_state=event.transition.dest,
            trigger=event.event.name,
            timestamp=datetime.now(timezone.utc),
            session_id=self.session_id,
            metadata=metadata,
        )

        # Log to Merkle chain
        if self._merkle_chain:
            merkle_hash = self._merkle_chain.add_block({
                "event_type": AuditEventType.STATE_TRANSITION.value,
                **transition.to_dict(),
            })
            transition.merkle_hash = merkle_hash

        # Add to history
        self._history.append(transition)

        # Call registered callbacks
        self._invoke_callbacks(event.transition.dest, transition)

        logger.info(
            f"State transition: {transition.from_state} → {transition.to_state} "
            f"(trigger: {transition.trigger})"
        )

    def _log_initial_state(self, state: str) -> None:
        """Log the initial state to Merkle chain."""
        if self._merkle_chain:
            self._merkle_chain.add_block({
                "event_type": AuditEventType.STATE_TRANSITION.value,
                "from_state": None,
                "to_state": state,
                "trigger": "initialize",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": self.session_id,
                "metadata": {"initial": True},
            })

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────

    def _find_trigger(self, from_state: str, to_state: str) -> Optional[str]:
        """Find the trigger name for a state transition."""
        for transition in self.TRANSITIONS:
            if transition["source"] == from_state and transition["dest"] == to_state:
                return transition["trigger"]
        return None

    def _invoke_callbacks(self, state: str, transition: StateTransition) -> None:
        """Invoke registered callbacks for a state."""
        callbacks = self._callbacks.get(state, [])
        for callback in callbacks:
            try:
                callback(transition)
            except Exception as e:
                logger.error(f"Callback error for state {state}: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # Callback Registration
    # ─────────────────────────────────────────────────────────────────────

    def on_enter(self, state: str, callback: Callable[[StateTransition], None]) -> None:
        """
        Register a callback for entering a state.

        Args:
            state: State to trigger callback
            callback: Function to call with StateTransition
        """
        if state not in self._callbacks:
            self._callbacks[state] = []
        self._callbacks[state].append(callback)

    def remove_callback(self, state: str, callback: Callable) -> bool:
        """
        Remove a registered callback.

        Args:
            state: State the callback is registered for
            callback: Callback to remove

        Returns:
            True if callback was found and removed
        """
        if state not in self._callbacks:
            return False
        try:
            self._callbacks[state].remove(callback)
            return True
        except ValueError:
            return False

    # ─────────────────────────────────────────────────────────────────────
    # Convenience Methods
    # ─────────────────────────────────────────────────────────────────────

    def is_idle(self) -> bool:
        """Check if system is in MONITOR state (idle)."""
        return self.state == SystemState.MONITOR.value

    def is_analyzing(self) -> bool:
        """Check if system is in an analysis state."""
        return self.state in [
            SystemState.DETECT.value,
            SystemState.ANALYZE.value,
            SystemState.CONFLICT_RESOLUTION.value,
        ]

    def is_pending_approval(self) -> bool:
        """Check if system is waiting for human approval."""
        return self.state == SystemState.RECOMMEND.value

    def is_executing(self) -> bool:
        """Check if system is executing trades."""
        return self.state in [
            SystemState.APPROVED.value,
            SystemState.EXECUTE.value,
        ]

    def get_available_triggers(self) -> list[str]:
        """Get list of valid triggers for current state."""
        triggers = []
        for transition in self.TRANSITIONS:
            if transition["source"] == self.state:
                triggers.append(transition["trigger"])
        return triggers

    def get_last_transition(self) -> Optional[StateTransition]:
        """Get the most recent transition."""
        if not self._history:
            return None
        return self._history[-1]

    def time_in_state(self) -> float:
        """Get seconds spent in current state."""
        if not self._history:
            return 0.0
        last = self._history[-1]
        return (datetime.now(timezone.utc) - last.timestamp).total_seconds()

    def reset_to_monitor(self, reason: str = "manual_reset") -> bool:
        """
        Force reset to MONITOR state.

        Args:
            reason: Reason for reset (logged to audit)

        Returns:
            True if reset succeeded
        """
        if self.state == SystemState.MONITOR.value:
            return True

        # Try reset trigger first
        if self.state in [
            SystemState.DETECT.value,
            SystemState.ANALYZE.value,
            SystemState.CONFLICT_RESOLUTION.value,
        ]:
            self._pending_metadata = {"reason": reason}
            return self.reset()

        # Try reject for RECOMMEND
        if self.state == SystemState.RECOMMEND.value:
            self._pending_metadata = {"reason": reason}
            return self.reject()

        # Try abort for APPROVED/EXECUTE
        if self.state in [SystemState.APPROVED.value, SystemState.EXECUTE.value]:
            self._pending_metadata = {"reason": reason}
            return self.abort()

        return False


# ═══════════════════════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════

class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class StateMachineFactory:
    """Factory for creating state machines with common configurations."""

    def __init__(self, merkle_chain: Optional[IMerkleChain] = None):
        """
        Initialize factory.

        Args:
            merkle_chain: Merkle chain to use for all state machines
        """
        self._merkle_chain = merkle_chain
        self._machines: dict[str, SentinelStateMachine] = {}

    def create(
        self,
        session_id: str,
        initial_state: str = SystemState.MONITOR.value,
    ) -> SentinelStateMachine:
        """
        Create a new state machine.

        Args:
            session_id: Session identifier
            initial_state: Starting state

        Returns:
            New SentinelStateMachine instance
        """
        machine = SentinelStateMachine(
            session_id=session_id,
            merkle_chain=self._merkle_chain,
            initial_state=initial_state,
        )
        self._machines[session_id] = machine
        return machine

    def get(self, session_id: str) -> Optional[SentinelStateMachine]:
        """Get existing state machine by session ID."""
        return self._machines.get(session_id)

    def remove(self, session_id: str) -> bool:
        """Remove a state machine."""
        if session_id in self._machines:
            del self._machines[session_id]
            return True
        return False

    def get_all_states(self) -> dict[str, str]:
        """Get current state of all machines."""
        return {
            session_id: machine.get_state()
            for session_id, machine in self._machines.items()
        }

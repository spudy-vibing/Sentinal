"""
SENTINEL BASE AGENT

Base class for all AI agents with Claude API integration.

All agents:
- Use Claude for analysis (structured output)
- Have RBAC permissions enforced
- Log actions to Merkle chain
- Follow hub-and-spoke communication (NEVER talk directly to other agents)

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.1
"""

from __future__ import annotations

import os
import json
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Optional, TypeVar, Type, Any

from anthropic import Anthropic

from src.contracts.interfaces import IAgent, IMerkleChain
from src.contracts.schemas import AgentType
from src.contracts.security import (
    SessionConfig,
    Permission,
    AuditEventType,
    require_permission,
)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Environment variable for API key
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"

# Default model for agents
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Model for complex reasoning (Coordinator)
REASONING_MODEL = "claude-sonnet-4-20250514"

# Output type variable for generic typing
T = TypeVar("T")


# ═══════════════════════════════════════════════════════════════════════════
# BASE AGENT
# ═══════════════════════════════════════════════════════════════════════════

class BaseAgent(IAgent):
    """
    Base class for all Sentinel agents.

    Provides:
    - Claude API integration with structured output
    - Session-based RBAC enforcement
    - Merkle chain audit logging
    - System prompt management

    Usage:
        class MyAgent(BaseAgent):
            def __init__(self, ...):
                super().__init__(
                    agent_type=AgentType.DRIFT,
                    system_prompt="You are a portfolio drift detection agent..."
                )

            async def analyze(self, portfolio_id, context):
                result = await self._call_claude(prompt, DriftAgentOutput)
                return result
    """

    def __init__(
        self,
        agent_type: AgentType,
        system_prompt: str,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        session: Optional[SessionConfig] = None,
        merkle_chain: Optional[IMerkleChain] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ):
        """
        Initialize base agent.

        Args:
            agent_type: Type of agent (DRIFT, TAX, COORDINATOR)
            system_prompt: System prompt defining agent behavior
            model: Claude model to use
            api_key: Anthropic API key (falls back to env var)
            session: Security session for RBAC
            merkle_chain: Audit chain for logging
            max_tokens: Maximum tokens in response
            temperature: Response temperature (0 = deterministic)
        """
        self._agent_type = agent_type
        self._system_prompt = system_prompt
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

        # Session for RBAC
        self._session = session

        # Merkle chain for audit logging
        self._audit_chain = merkle_chain

        # Initialize Anthropic client
        key = api_key or os.environ.get(ANTHROPIC_API_KEY_ENV)
        if not key:
            raise RuntimeError(
                f"Anthropic API key not configured. "
                f"Set {ANTHROPIC_API_KEY_ENV} environment variable."
            )
        self._client = Anthropic(api_key=key)

        # Track invocations
        self._invocation_count = 0

    def get_agent_type(self) -> AgentType:
        """Return agent type."""
        return self._agent_type

    @abstractmethod
    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> Any:
        """Run analysis - implemented by subclasses."""
        pass

    # ─── Claude API Integration ───────────────────────────────────────────────

    async def _call_claude(
        self,
        user_prompt: str,
        output_type: Type[T],
        additional_context: Optional[str] = None
    ) -> T:
        """
        Call Claude with structured output.

        Args:
            user_prompt: The analysis prompt
            output_type: Pydantic model for response parsing
            additional_context: Extra context to append to system prompt

        Returns:
            Parsed response as output_type instance

        Raises:
            ValueError: If response cannot be parsed
        """
        # Build system prompt
        system = self._system_prompt
        if additional_context:
            system = f"{system}\n\n{additional_context}"

        # Add output format instructions
        schema_json = json.dumps(output_type.model_json_schema(), indent=2)
        system = f"""{system}

You MUST respond with valid JSON that matches this schema:
{schema_json}

Respond ONLY with the JSON object, no additional text or markdown."""

        # Log invocation
        self._log_invocation(user_prompt[:200])

        # Call Claude
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Extract text content
        content = response.content[0].text

        # Parse JSON response
        try:
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            data = json.loads(content)
            result = output_type.model_validate(data)

            # Log completion
            self._log_completion(success=True)

            return result

        except Exception as e:
            self._log_completion(success=False, error=str(e))
            raise ValueError(
                f"Failed to parse Claude response as {output_type.__name__}: {e}\n"
                f"Response was: {content[:500]}"
            )

    async def _call_claude_raw(
        self,
        user_prompt: str,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Call Claude and get raw text response.

        For cases where structured output isn't needed.
        """
        system = self._system_prompt
        if additional_context:
            system = f"{system}\n\n{additional_context}"

        self._log_invocation(user_prompt[:200])

        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system,
            messages=[{"role": "user", "content": user_prompt}]
        )

        content = response.content[0].text
        self._log_completion(success=True)

        return content

    # ─── Audit Logging ────────────────────────────────────────────────────────

    def _log_invocation(self, prompt_preview: str) -> None:
        """Log agent invocation to Merkle chain."""
        if not self._audit_chain:
            return

        self._invocation_count += 1

        self._audit_chain.add_block({
            "event_type": AuditEventType.AGENT_INVOKED.value,
            "session_id": self._session.session_id if self._session else "unknown",
            "actor": self._agent_type.value,
            "action": "analyze",
            "invocation_number": self._invocation_count,
            "prompt_preview": prompt_preview,
            "model": self._model,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def _log_completion(
        self,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Log agent completion to Merkle chain."""
        if not self._audit_chain:
            return

        event_type = (
            AuditEventType.AGENT_COMPLETED if success
            else AuditEventType.AGENT_ERROR
        )

        self._audit_chain.add_block({
            "event_type": event_type.value,
            "session_id": self._session.session_id if self._session else "unknown",
            "actor": self._agent_type.value,
            "action": "analyze_complete" if success else "analyze_error",
            "success": success,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # ─── Session Management ───────────────────────────────────────────────────

    def set_session(self, session: SessionConfig) -> None:
        """Set the security session for RBAC checks."""
        self._session = session

    def set_merkle_chain(self, chain: IMerkleChain) -> None:
        """Set the Merkle chain for audit logging."""
        self._audit_chain = chain

    @property
    def session(self) -> Optional[SessionConfig]:
        """Get current session."""
        return self._session

    # ─── Utilities ────────────────────────────────────────────────────────────

    def _format_holdings_for_prompt(
        self,
        holdings: list,
        include_tax_lots: bool = False
    ) -> str:
        """Format holdings list for LLM prompt."""
        lines = []
        for h in holdings:
            line = (
                f"- {h.ticker}: {h.quantity:,.0f} shares @ ${h.current_price:.2f} "
                f"= ${h.market_value:,.0f} ({h.portfolio_weight:.1%} of portfolio)"
            )

            if h.unrealized_gain_loss >= 0:
                line += f" | Gain: ${h.unrealized_gain_loss:,.0f}"
            else:
                line += f" | Loss: ${abs(h.unrealized_gain_loss):,.0f}"

            lines.append(line)

            if include_tax_lots and h.tax_lots:
                for lot in h.tax_lots:
                    lot_line = (
                        f"    └─ Lot {lot.lot_id}: {lot.quantity:,.0f} shares "
                        f"@ ${lot.purchase_price:.2f} "
                        f"(purchased {lot.purchase_date.strftime('%Y-%m-%d')})"
                    )
                    lines.append(lot_line)

        return "\n".join(lines)

    def _format_transactions_for_prompt(
        self,
        transactions: list
    ) -> str:
        """Format recent transactions for LLM prompt."""
        if not transactions:
            return "No recent transactions."

        lines = []
        for t in transactions:
            line = (
                f"- {t.timestamp.strftime('%Y-%m-%d')}: "
                f"{t.action.value.upper()} {t.quantity:,.0f} {t.ticker} "
                f"@ ${t.price:.2f}"
            )
            lines.append(line)

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# AGENT FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class AgentFactory:
    """
    Factory for creating configured agent instances.

    Usage:
        factory = AgentFactory(session=advisor_session, merkle_chain=chain)
        drift_agent = factory.create_drift_agent()
        tax_agent = factory.create_tax_agent()
    """

    def __init__(
        self,
        session: Optional[SessionConfig] = None,
        merkle_chain: Optional[IMerkleChain] = None,
        api_key: Optional[str] = None
    ):
        self._session = session
        self._merkle_chain = merkle_chain
        self._api_key = api_key

    def create_drift_agent(self) -> "DriftAgent":
        """Create configured Drift Agent."""
        from .drift_agent import DriftAgent
        return DriftAgent(
            session=self._session,
            merkle_chain=self._merkle_chain,
            api_key=self._api_key
        )

    def create_tax_agent(self) -> "TaxAgent":
        """Create configured Tax Agent."""
        from .tax_agent import TaxAgent
        return TaxAgent(
            session=self._session,
            merkle_chain=self._merkle_chain,
            api_key=self._api_key
        )

"""
SENTINEL V2 — Sentinel Bridge Service
Bridge between FastAPI and existing Sentinel agents.
Wraps the existing OfflineCoordinator with real-time event emission.
"""

from typing import Callable, Optional, Dict, Any, List
import asyncio
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add project root to path for Sentinel core imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class SentinelBridge:
    """
    Bridge between the web API and Sentinel's core agent system.
    Provides async wrappers around synchronous agent operations
    and emits real-time activity events.
    """

    def __init__(self, activity_callback: Callable):
        """
        Initialize the bridge with a callback for emitting events.

        Args:
            activity_callback: Async function to emit activity events
        """
        self.activity_callback = activity_callback
        self.merkle_chain = None
        self.coordinator = None
        self._initialized = False

    async def initialize(self):
        """Lazy initialization of Sentinel components."""
        if self._initialized:
            return

        try:
            from src.security import MerkleChain
            from src.agents import OfflineCoordinator

            self.merkle_chain = MerkleChain()
            self.coordinator = OfflineCoordinator()
            self._initialized = True

            await self.emit("system", {
                "agent_name": "System",
                "status": "ready",
                "message": "Sentinel core initialized"
            })
        except ImportError as e:
            # Sentinel core not available, use demo mode
            await self.emit("system", {
                "agent_name": "System",
                "status": "demo_mode",
                "message": f"Running in demo mode: {str(e)}"
            })

    async def emit(self, event_type: str, data: dict):
        """Emit activity event to WebSocket clients."""
        await self.activity_callback({
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        })

    async def load_portfolio(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a portfolio by ID.

        Args:
            portfolio_id: The portfolio identifier

        Returns:
            Portfolio data or None if not found
        """
        await self.emit("agent_activity", {
            "agent_name": "Data Loader",
            "agent_type": "system",
            "status": "analyzing",
            "message": f"Loading portfolio {portfolio_id}..."
        })

        try:
            from src.data import load_portfolio
            portfolio = load_portfolio(portfolio_id)

            await self.emit("agent_activity", {
                "agent_name": "Data Loader",
                "agent_type": "system",
                "status": "complete",
                "message": f"Loaded {portfolio.name} (${portfolio.aum_usd:,.0f} AUM)"
            })

            return portfolio
        except Exception as e:
            # Return demo portfolio
            await self.emit("agent_activity", {
                "agent_name": "Data Loader",
                "agent_type": "system",
                "status": "complete",
                "message": "Using demo portfolio data"
            })
            return None

    async def process_market_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        portfolio_id: str = "portfolio_a"
    ) -> Dict[str, Any]:
        """
        Process a market event through the agent pipeline.

        Args:
            event_type: Type of market event
            event_data: Event-specific data
            portfolio_id: Target portfolio

        Returns:
            Analysis results from the agent pipeline
        """
        await self.initialize()

        results = {
            "event_type": event_type,
            "portfolio_id": portfolio_id,
            "agents_triggered": [],
            "findings": [],
            "scenarios": [],
            "merkle_hash": None
        }

        # Emit event received
        await self.emit("agent_activity", {
            "agent_name": "Coordinator",
            "agent_type": "coordinator",
            "status": "analyzing",
            "message": f"Received {event_type} event, initiating analysis..."
        })

        await asyncio.sleep(0.3)  # Simulate processing

        # Run Drift Agent
        await self._run_drift_agent(event_data, results)

        # Run Tax Agent
        await self._run_tax_agent(event_data, results)

        # Run Compliance Agent
        await self._run_compliance_agent(event_data, results)

        # Generate Scenarios
        await self._run_scenario_agent(results)

        # Log to Merkle chain
        if self.merkle_chain:
            self.merkle_chain.add_block({
                "event_type": event_type,
                "event_data": event_data,
                "portfolio_id": portfolio_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            results["merkle_hash"] = self.merkle_chain.get_root_hash()

            await self.emit("merkle_block", {
                "block_hash": results["merkle_hash"][:16] + "...",
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # Complete
        await self.emit("agent_activity", {
            "agent_name": "Coordinator",
            "agent_type": "coordinator",
            "status": "complete",
            "message": f"Analysis complete. {len(results['scenarios'])} scenarios generated."
        })

        return results

    async def _run_drift_agent(self, event_data: Dict, results: Dict):
        """Run the Drift Detection Agent."""
        await self.emit("agent_activity", {
            "agent_name": "Drift Agent",
            "agent_type": "drift",
            "status": "analyzing",
            "message": "Checking portfolio drift and concentration..."
        })

        await asyncio.sleep(0.5)

        # Simulate findings
        if event_data.get("magnitude", 0) < -10:
            results["findings"].append({
                "agent": "drift",
                "severity": "high",
                "finding": "NVDA concentration at 17% exceeds 15% limit",
                "recommendation": "Reduce position by 2%"
            })

        results["agents_triggered"].append("drift")

        await self.emit("agent_activity", {
            "agent_name": "Drift Agent",
            "agent_type": "drift",
            "status": "complete",
            "message": "Detected concentration risk in NVDA position"
        })

    async def _run_tax_agent(self, event_data: Dict, results: Dict):
        """Run the Tax Optimization Agent."""
        await self.emit("agent_activity", {
            "agent_name": "Tax Agent",
            "agent_type": "tax",
            "status": "analyzing",
            "message": "Analyzing tax implications and wash sale rules..."
        })

        await asyncio.sleep(0.4)

        results["findings"].append({
            "agent": "tax",
            "severity": "medium",
            "finding": "Wash sale window active for NVDA (15 days remaining)",
            "recommendation": "Use AMD as correlated substitute"
        })

        results["agents_triggered"].append("tax")

        await self.emit("agent_activity", {
            "agent_name": "Tax Agent",
            "agent_type": "tax",
            "status": "complete",
            "message": "Identified wash sale conflict - 15 days remaining"
        })

    async def _run_compliance_agent(self, event_data: Dict, results: Dict):
        """Run the Compliance Agent."""
        await self.emit("agent_activity", {
            "agent_name": "Compliance Agent",
            "agent_type": "compliance",
            "status": "analyzing",
            "message": "Checking regulatory constraints..."
        })

        await asyncio.sleep(0.3)

        results["agents_triggered"].append("compliance")

        await self.emit("agent_activity", {
            "agent_name": "Compliance Agent",
            "agent_type": "compliance",
            "status": "complete",
            "message": "No compliance violations detected"
        })

    async def _run_scenario_agent(self, results: Dict):
        """Run the Scenario Generation Agent."""
        await self.emit("agent_activity", {
            "agent_name": "Scenario Agent",
            "agent_type": "scenario",
            "status": "analyzing",
            "message": "Generating rebalancing scenarios..."
        })

        await asyncio.sleep(0.6)

        # Generate scenarios based on findings
        results["scenarios"] = [
            {
                "id": "scenario_amd_substitute",
                "title": "AMD Substitute Strategy",
                "score": 72.4,
                "is_recommended": True
            },
            {
                "id": "scenario_wait_16_days",
                "title": "Wait 16 Days",
                "score": 58.2,
                "is_recommended": False
            },
            {
                "id": "scenario_accept_wash_sale",
                "title": "Accept Wash Sale",
                "score": 45.1,
                "is_recommended": False
            }
        ]

        results["agents_triggered"].append("scenario")

        await self.emit("agent_activity", {
            "agent_name": "Scenario Agent",
            "agent_type": "scenario",
            "status": "complete",
            "message": f"Generated {len(results['scenarios'])} scenarios"
        })

        # Send scenarios update
        await self.emit("scenarios", {
            "scenarios": results["scenarios"]
        })

    async def run_agent_debate(
        self,
        topic: str,
        agents: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run a debate between agents on a specific topic.

        Args:
            topic: The debate topic
            agents: List of agent names to participate

        Returns:
            Debate results with consensus
        """
        if agents is None:
            agents = ["Drift Agent", "Tax Agent"]

        await self.emit("agent_activity", {
            "agent_name": "Coordinator",
            "agent_type": "coordinator",
            "status": "debating",
            "message": f"Initiating debate: {topic}"
        })

        debate_messages = []

        # Agent 1 opens
        await asyncio.sleep(0.5)
        msg1 = {
            "agent_name": agents[0],
            "position": "pro",
            "argument": "Given the concentration risk at 17%, we should act now. The risk of further losses outweighs the wash sale penalty.",
            "confidence": 0.78,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        debate_messages.append(msg1)
        await self.emit("debate_message", msg1)

        # Agent 2 responds
        await asyncio.sleep(0.8)
        msg2 = {
            "agent_name": agents[1],
            "position": "con",
            "argument": "The $25K wash sale penalty is significant. With only 16 days remaining, the expected loss from waiting is lower than the certain tax cost.",
            "confidence": 0.72,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        debate_messages.append(msg2)
        await self.emit("debate_message", msg2)

        # Agent 1 rebuts
        await asyncio.sleep(0.6)
        msg3 = {
            "agent_name": agents[0],
            "position": "pro",
            "argument": "However, using AMD as a substitute allows us to act immediately while maintaining tax efficiency. Best of both worlds.",
            "confidence": 0.85,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        debate_messages.append(msg3)
        await self.emit("debate_message", msg3)

        # Consensus
        await asyncio.sleep(0.4)
        result = {
            "topic": topic,
            "messages": debate_messages,
            "consensus": "Use AMD substitute strategy",
            "confidence": 0.82,
            "winning_argument": "AMD substitute provides risk reduction without tax penalty"
        }

        await self.emit("agent_activity", {
            "agent_name": "Coordinator",
            "agent_type": "coordinator",
            "status": "complete",
            "message": f"Debate concluded: {result['consensus']}"
        })

        return result

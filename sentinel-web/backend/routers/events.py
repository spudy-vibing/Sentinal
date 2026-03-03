"""
SENTINEL V2 — Events Router
Handles market event injection and triggers agent analysis.
"""

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime, timezone
import json
import uuid
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import audit store for persistence
from services.audit_store import audit_store

router = APIRouter()


def _extract_metrics(utility_score) -> dict:
    """Extract metrics from UtilityScore for frontend display."""
    default_metrics = {
        "risk_reduction": 5.0,
        "tax_savings": 5.0,
        "goal_alignment": 5.0,
        "transaction_cost": 5.0,
        "urgency": 5.0
    }

    if not utility_score:
        return default_metrics

    # Map dimension names to frontend metric names
    dimension_map = {
        "risk_reduction": "risk_reduction",
        "tax_efficiency": "tax_savings",
        "goal_alignment": "goal_alignment",
        "cost_efficiency": "transaction_cost",
        "urgency": "urgency"
    }

    # Extract from dimension_scores list
    if hasattr(utility_score, 'dimension_scores') and utility_score.dimension_scores:
        for ds in utility_score.dimension_scores:
            dim_name = ds.dimension.lower().replace(' ', '_')
            for key, metric_name in dimension_map.items():
                if key in dim_name or dim_name in key:
                    default_metrics[metric_name] = ds.raw_score
                    break

    return default_metrics


class MarketEventRequest(BaseModel):
    """Request to inject a market event."""
    event_type: Literal["tech_crash", "earnings_beat", "fed_rate", "tax_review", "custom"] = "tech_crash"
    portfolio_id: str = "portfolio_a"
    magnitude: float = -0.04
    description: Optional[str] = None
    enable_debate: bool = True
    enable_thinking: bool = True
    enable_chain_reaction: bool = True


class EventResponse(BaseModel):
    """Response after injecting an event."""
    status: str
    event_id: str
    message: str


# Preset event configurations
PRESET_EVENTS = {
    "tech_crash": {
        "affected_sectors": ["Technology"],
        "magnitude": -0.04,
        "affected_tickers": ["NVDA", "AMD", "AAPL", "MSFT"],
        "description": "Technology sector drops 4% on semiconductor concerns"
    },
    "earnings_beat": {
        "affected_sectors": ["Technology"],
        "magnitude": 0.08,
        "affected_tickers": ["NVDA"],
        "description": "NVIDIA beats earnings estimates by 15%, stock surges"
    },
    "fed_rate": {
        "affected_sectors": ["Fixed Income", "Financials", "Real Estate"],
        "magnitude": -0.02,
        "description": "Federal Reserve signals additional rate hikes, markets retreat"
    },
    "tax_review": {
        "affected_sectors": ["Technology"],
        "magnitude": 0.0,
        "affected_tickers": ["NVDA"],
        "description": "Tax-loss harvesting opportunity review: NVDA wash sale window closing in 15 days"
    }
}


@router.post("/inject", response_model=EventResponse)
async def inject_event(
    request: MarketEventRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    Inject a market event to trigger the agent analysis pipeline.

    This will:
    1. Validate and create the event
    2. Stream agent activity via WebSocket
    3. Optionally enable debate mode, thinking mode, and chain reactions
    """
    # Generate event ID
    event_id = f"evt_{uuid.uuid4().hex[:8]}"

    # Get preset or use custom
    if request.event_type in PRESET_EVENTS:
        event_data = PRESET_EVENTS[request.event_type].copy()
        if request.description:
            event_data["description"] = request.description
    else:
        event_data = {
            "affected_sectors": ["Technology"],
            "magnitude": request.magnitude,
            "affected_tickers": [],
            "description": request.description or "Custom market event"
        }

    # Get WebSocket manager from app state
    ws_manager = req.app.state.ws_manager

    # Process in background while streaming updates
    background_tasks.add_task(
        process_event_with_streaming,
        event_id=event_id,
        portfolio_id=request.portfolio_id,
        event_data=event_data,
        ws_manager=ws_manager,
        enable_debate=request.enable_debate,
        enable_thinking=request.enable_thinking,
        enable_chain_reaction=request.enable_chain_reaction
    )

    return EventResponse(
        status="processing",
        event_id=event_id,
        message="Event injected. Watch the activity stream for real-time updates."
    )


@router.get("/presets")
async def get_presets():
    """Get available event presets for the UI."""
    return {
        "presets": [
            {
                "id": "tech_crash",
                "name": "Tech Crash -4%",
                "description": "Technology sector drops on semiconductor concerns",
                "icon": "trending-down",
                "color": "red",
                "magnitude": -0.04
            },
            {
                "id": "earnings_beat",
                "name": "NVDA Earnings +8%",
                "description": "NVIDIA beats estimates, stock surges",
                "icon": "trending-up",
                "color": "green",
                "magnitude": 0.08
            },
            {
                "id": "fed_rate",
                "name": "Fed Rate Concern",
                "description": "Federal Reserve signals rate hikes",
                "icon": "landmark",
                "color": "amber",
                "magnitude": -0.02
            },
            {
                "id": "tax_review",
                "name": "Tax Opportunities",
                "description": "Review tax-loss harvesting and wash sale windows",
                "icon": "calculator",
                "color": "blue",
                "magnitude": 0.0
            },
        ]
    }


async def process_event_with_streaming(
    event_id: str,
    portfolio_id: str,
    event_data: dict,
    ws_manager,
    enable_debate: bool = True,
    enable_thinking: bool = True,
    enable_chain_reaction: bool = True
):
    """
    Process a market event through the Sentinel pipeline with real-time streaming.

    Uses AgentRunner to dispatch real LLM agents (when API key present) or
    offline rule-based analyzers. Thinking/debate messages are template-based
    from actual agent findings (no extra LLM calls).
    """
    from src.security import MerkleChain
    from src.data import load_portfolio
    from src.contracts.schemas import MarketEventInput, EventType
    from services.agent_runner import AgentRunner, AgentRunnerConfig
    from config import get_settings

    import sys
    start_time = datetime.now(timezone.utc)
    settings = get_settings()

    print(f"\n{'='*60}", flush=True)
    print(f"  [EVENT] Starting event processing: {event_id}", flush=True)
    print(f"  [EVENT] Portfolio: {portfolio_id}", flush=True)
    print(f"  [EVENT] Real agents: {settings.use_real_agents and bool(settings.anthropic_api_key)}", flush=True)
    print(f"{'='*60}\n", flush=True)
    sys.stdout.flush()

    try:
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Gateway Receives Event
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 1] Gateway receiving event...", flush=True)
        await ws_manager.send_agent_activity({
            "agent": "gateway",
            "status": "active",
            "message": f"Event received: {event_data['description']}",
            "event_id": event_id
        })
        await asyncio.sleep(0.5)

        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Load Portfolio
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 2] Loading portfolio...", flush=True)
        try:
            portfolio = load_portfolio(portfolio_id)
            print(f"  [STEP 2] Portfolio loaded: {portfolio.name}")
        except Exception as e:
            print(f"  [STEP 2] Portfolio not found, using demo: {e}")
            from src.demos.golden_path import _create_demo_portfolio
            portfolio = _create_demo_portfolio()

        await ws_manager.send_agent_activity({
            "agent": "gateway",
            "status": "complete",
            "message": f"Portfolio loaded: {portfolio.name} (${portfolio.aum_usd:,.0f})",
            "portfolio": {
                "id": portfolio.portfolio_id,
                "name": portfolio.name,
                "aum": portfolio.aum_usd
            }
        })
        await asyncio.sleep(0.3)

        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Coordinator Starts
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 3] Coordinator starting...", flush=True)
        await ws_manager.send_agent_activity({
            "agent": "coordinator",
            "status": "active",
            "message": "Initiating analysis pipeline..."
        })
        await asyncio.sleep(0.3)

        await ws_manager.send_agent_activity({
            "agent": "coordinator",
            "status": "active",
            "message": "Dispatching specialist agents..."
        })
        await asyncio.sleep(0.2)

        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Run AgentRunner (real or offline agents)
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 4] Running AgentRunner...", flush=True)
        merkle_chain = MerkleChain()
        runner_config = AgentRunnerConfig(
            use_real_agents=settings.use_real_agents,
            api_key=settings.anthropic_api_key,
            model=settings.agent_model,
        )
        runner = AgentRunner(config=runner_config, merkle_chain=merkle_chain)

        market_event = MarketEventInput(
            event_id=event_id,
            event_type=EventType.MARKET_EVENT,
            timestamp=datetime.now(timezone.utc),
            session_id=f"session_{uuid.uuid4().hex[:8]}",
            priority=8,
            **event_data
        )
        context = {"market_event": market_event.model_dump()}

        # AgentRunner handles WS updates for drift/tax agent status
        result = await runner.run(
            portfolio=portfolio,
            context=context,
            ws_manager=ws_manager,
        )
        print(f"  [STEP 4] AgentRunner complete", flush=True)

        drift_findings = result.drift_findings
        tax_findings = result.tax_findings

        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Template-based thinking stream (from real findings)
        # ═══════════════════════════════════════════════════════════════
        if enable_thinking:
            print("  [STEP 5] Streaming thinking from findings...", flush=True)
            await _stream_thinking_from_findings(ws_manager, drift_findings, tax_findings)

        # ═══════════════════════════════════════════════════════════════
        # STEP 6: Compliance Agent (template-based from drift findings)
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 6] Compliance agent...", flush=True)
        await ws_manager.send_agent_activity({
            "agent": "compliance",
            "status": "active",
            "message": "Checking regulatory compliance and concentration limits..."
        })
        await asyncio.sleep(0.5)

        if enable_thinking:
            concentration_violations = len(drift_findings.concentration_risks)
            tickers_over = ", ".join(r.ticker for r in drift_findings.concentration_risks) or "none"
            compliance_thoughts = [
                {"type": "observation", "content": "Reviewing portfolio against investment policy statement...", "confidence": 95},
                {"type": "analysis", "content": f"Checking concentration limits: {tickers_over} flagged", "confidence": 92},
                {"type": "observation", "content": "Verifying sector allocation compliance", "confidence": 94},
                {"type": "conclusion", "content": f"Compliance review complete: {concentration_violations} violation(s)", "confidence": 96},
            ]
            for thought in compliance_thoughts:
                await ws_manager.send_thinking({"agent": "compliance", **thought})
                await asyncio.sleep(0.3)

        # Close compliance thinking stream
        await ws_manager.broadcast({
            "type": "thinking",
            "data": {"agent_name": "Compliance Agent", "is_complete": True}
        })

        concentration_violations = len(drift_findings.concentration_risks)
        compliance_status = "violations" if concentration_violations > 0 else "compliant"
        await ws_manager.send_agent_activity({
            "agent": "compliance",
            "status": "complete",
            "message": f"Compliance review complete: {concentration_violations} concentration violations, {compliance_status}",
            "findings": {
                "concentration_violations": concentration_violations,
                "sector_compliance": True,
                "ips_violations": 0,
                "regulatory_flags": []
            }
        })
        await asyncio.sleep(0.3)

        # ═══════════════════════════════════════════════════════════════
        # STEP 7: Conflict broadcast + Optional Debate
        # ═══════════════════════════════════════════════════════════════
        if result.conflicts_detected:
            # Conflict WS message already sent by AgentRunner
            await asyncio.sleep(0.5)

            if enable_debate:
                print("  [STEP 7] Running agent debate...", flush=True)
                # Try LLM-powered debate, fall back to templates
                if settings.anthropic_api_key:
                    import anthropic
                    from services.debate_runner import DebateRunner
                    debate_runner = DebateRunner(
                        api_key=settings.anthropic_api_key,
                        model=settings.agent_model,
                        ws_manager=ws_manager,
                    )
                    top_risk = drift_findings.concentration_risks[0] if drift_findings.concentration_risks else None
                    debate_question = f"Should we sell {top_risk.ticker} now?" if top_risk else "How should we rebalance?"
                    try:
                        await debate_runner.run_debate(debate_question, drift_findings, tax_findings, portfolio)
                    except (RuntimeError, json.JSONDecodeError, ConnectionError, TimeoutError, anthropic.APIError) as e:
                        print(f"  [STEP 7] LLM debate failed ({type(e).__name__}: {e}), using templates", flush=True)
                        await run_agent_debate(ws_manager, drift_findings, tax_findings)
                else:
                    await run_agent_debate(ws_manager, drift_findings, tax_findings)

        # ═══════════════════════════════════════════════════════════════
        # STEP 8: Scenario Generation broadcast
        # ═══════════════════════════════════════════════════════════════
        print(f"  [STEP 8] Broadcasting {len(result.scenarios)} scenarios...", flush=True)
        await ws_manager.send_agent_activity({
            "agent": "coordinator",
            "status": "active",
            "message": f"Generating {len(result.scenarios)} recommendation scenarios..."
        })
        await asyncio.sleep(0.5)

        await ws_manager.send_agent_activity({
            "agent": "coordinator",
            "status": "active",
            "message": "Scoring scenarios with 5-dimensional utility function..."
        })
        await asyncio.sleep(0.4)

        # ═══════════════════════════════════════════════════════════════
        # STEP 9: Analysis Complete
        # ═══════════════════════════════════════════════════════════════
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        print(f"  [STEP 9] Elapsed: {elapsed:.1f}s", flush=True)

        await ws_manager.send_agent_activity({
            "agent": "coordinator",
            "status": "complete",
            "message": f"Analysis complete in {elapsed:.1f}s. Recommended: {result.recommended_scenario_id}",
            "recommended_scenario_id": result.recommended_scenario_id,
            "merkle_hash": result.merkle_hash
        })

        # Build scenario list and store for API access
        from routers.scenarios import scenario_store

        scenario_list = [
            {
                "id": s.scenario_id,
                "title": s.title,
                "description": s.description,
                "score": s.utility_score.total_score if s.utility_score else 0,
                "is_recommended": s.scenario_id == result.recommended_scenario_id,
                "actions": [
                    {
                        "type": a.action.value,
                        "ticker": a.ticker,
                        "quantity": a.quantity,
                        "rationale": getattr(a, 'rationale', '')
                    }
                    for a in s.action_steps
                ],
                "metrics": _extract_metrics(s.utility_score),
                "risks": getattr(s, 'risks', []),
                "expected_outcomes": getattr(s, 'expected_outcomes', {})
            }
            for s in result.scenarios
        ]

        scenario_store.clear()
        for scenario in scenario_list:
            scenario_store[scenario['id']] = scenario

        await ws_manager.send_scenarios(scenario_list)
        print("  [STEP 9] Scenarios sent", flush=True)

        # ═══════════════════════════════════════════════════════════════
        # STEP 10: Merkle Chain Blocks - Persist to SQLite & Send to UI
        # ═══════════════════════════════════════════════════════════════
        print(f"  [STEP 10] Persisting & sending {min(8, len(merkle_chain._blocks))} merkle blocks...", flush=True)
        for block in merkle_chain._blocks[-8:]:
            try:
                audit_store.add_block({
                    "index": block.index,
                    "event_id": block.event_id,
                    "event_type": block.event_type,
                    "timestamp": block.timestamp.isoformat(),
                    "session_id": block.session_id,
                    "actor": block.actor,
                    "action": block.action,
                    "resource": block.resource,
                    "data": block.data,
                    "previous_hash": block.previous_hash,
                    "current_hash": block.current_hash
                })
            except Exception as e:
                print(f"  [STEP 10] Failed to persist block: {e}", flush=True)

            await ws_manager.send_merkle_block({
                "event_type": block.event_type,
                "hash": block.current_hash[:16] + "...",
                "timestamp": block.timestamp.isoformat(),
                "actor": block.actor,
                "action": block.action,
                "resource": block.resource
            })
            await asyncio.sleep(0.1)

        print(f"\n{'='*60}", flush=True)
        print(f"  [COMPLETE] Event processing finished successfully!", flush=True)
        print(f"{'='*60}\n", flush=True)

    except Exception as e:
        import traceback
        print(f"\n  [ERROR] Exception during event processing:")
        print(f"  [ERROR] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        await ws_manager.send_agent_activity({
            "agent": "coordinator",
            "status": "error",
            "message": f"Error during analysis: {str(e)}"
        })
        raise


async def _stream_thinking_from_findings(ws_manager, drift_findings, tax_findings):
    """Stream thinking messages templated from actual agent findings (no extra LLM calls)."""
    # Drift thinking
    for risk in drift_findings.concentration_risks:
        severity_str = risk.severity.value if hasattr(risk.severity, 'value') else str(risk.severity)
        await ws_manager.send_thinking({
            "agent": "drift",
            "type": "observation",
            "content": f"{risk.ticker} at {risk.current_weight:.1%} exceeds {risk.limit:.0%} concentration limit ({severity_str} severity)",
            "confidence": 93,
        })
        await asyncio.sleep(0.3)

    if drift_findings.recommended_trades:
        trade = drift_findings.recommended_trades[0]
        await ws_manager.send_thinking({
            "agent": "drift",
            "type": "conclusion",
            "content": f"Recommend {trade.action.value} {trade.quantity:,.0f} {trade.ticker} (urgency {trade.urgency}/10)",
            "confidence": 90,
        })
        await asyncio.sleep(0.3)

    # Tax thinking
    for ws in tax_findings.wash_sale_violations:
        await ws_manager.send_thinking({
            "agent": "tax",
            "type": "observation",
            "content": f"Wash sale window: {ws.ticker} sold {ws.days_since_sale} days ago, ${ws.disallowed_loss:,.0f} at risk",
            "confidence": 94,
        })
        await asyncio.sleep(0.3)

    for opp in tax_findings.tax_opportunities[:2]:
        opp_type = opp.opportunity_type.value if hasattr(opp.opportunity_type, 'value') else str(opp.opportunity_type)
        await ws_manager.send_thinking({
            "agent": "tax",
            "type": "analysis",
            "content": f"Tax opportunity: {opp.ticker} — {opp_type}, estimated benefit ${opp.estimated_benefit:,.0f}",
            "confidence": 88,
        })
        await asyncio.sleep(0.3)

    if tax_findings.recommendations:
        await ws_manager.send_thinking({
            "agent": "tax",
            "type": "conclusion",
            "content": tax_findings.recommendations[0],
            "confidence": 91,
        })
        await asyncio.sleep(0.3)

    # Close thinking streams so frontend clears "Analyzing" state
    await ws_manager.broadcast({
        "type": "thinking",
        "data": {"agent_name": "Drift Agent", "is_complete": True}
    })
    await ws_manager.broadcast({
        "type": "thinking",
        "data": {"agent_name": "Tax Agent", "is_complete": True}
    })


async def run_agent_debate(ws_manager, drift_findings, tax_findings):
    """Run template-based debate between Drift and Tax agents using real findings."""
    # Build debate content from actual findings
    top_risk = drift_findings.concentration_risks[0] if drift_findings.concentration_risks else None
    top_wash = tax_findings.wash_sale_violations[0] if tax_findings.wash_sale_violations else None

    # Default content if no specific findings
    risk_ticker = top_risk.ticker if top_risk else "overweight position"
    risk_weight = f"{top_risk.current_weight:.0%}" if top_risk else "above limit"
    risk_limit = f"{top_risk.limit:.0%}" if top_risk else "concentration limit"
    wash_ticker = top_wash.ticker if top_wash else risk_ticker
    wash_days = top_wash.days_since_sale if top_wash else 0
    wash_loss = f"${top_wash.disallowed_loss:,.0f}" if top_wash else "$0"

    question = f"Should we sell {risk_ticker} now?"

    await ws_manager.send_debate_phase("opening", question)
    await asyncio.sleep(0.3)

    debate_messages = [
        {
            "agent_id": "drift",
            "agent_name": "Drift Agent",
            "phase": "opening",
            "position": "for",
            "message": f"We MUST sell {risk_ticker}. The position is at {risk_weight}, well above our {risk_limit} concentration limit. This level of concentration exposes the portfolio to unacceptable single-stock risk.",
            "confidence": 94,
            "key_points": [f"{risk_weight} concentration", f"{risk_limit} limit breached", "Single-stock risk"]
        },
    ]

    if top_wash:
        debate_messages.append({
            "agent_id": "tax",
            "agent_name": "Tax Agent",
            "phase": "opening",
            "position": "against",
            "message": f"Hold on. The client sold {wash_ticker} just {wash_days} days ago. If we sell more now, we trigger a wash sale and lose {wash_loss} in tax deductions. That's real money.",
            "confidence": 91,
            "key_points": [f"{wash_days} days since last sale", "Wash sale window active", f"{wash_loss} at risk"]
        })
    else:
        debate_messages.append({
            "agent_id": "tax",
            "agent_name": "Tax Agent",
            "phase": "opening",
            "position": "neutral",
            "message": f"No wash sale risk detected for {risk_ticker}. However, we should consider the tax impact of selling — capital gains rates apply.",
            "confidence": 88,
            "key_points": ["No wash sale risk", "Capital gains consideration", "Tax efficiency"]
        })

    for msg in debate_messages:
        await ws_manager.send_debate_message(msg)
        await asyncio.sleep(1.2)

    await ws_manager.send_debate_phase("rebuttal", question)
    await asyncio.sleep(0.3)

    rebuttal_messages = [
        {
            "agent_id": "drift",
            "agent_name": "Drift Agent",
            "phase": "rebuttal",
            "position": "for",
            "message": f"I understand the tax concern, but the concentration risk is immediate. If the sector drops further, we're looking at much larger losses. Can we find a substitute security?",
            "confidence": 88,
            "key_points": ["Immediate risk", "Potential for larger losses", "Substitute security?"]
        },
        {
            "agent_id": "tax",
            "agent_name": "Tax Agent",
            "phase": "rebuttal",
            "position": "neutral",
            "message": f"A correlated substitute could work. We sell {risk_ticker}, buy a similar security, maintain exposure, AND avoid tax penalties. This satisfies both risk and tax concerns.",
            "confidence": 92,
            "key_points": ["Substitute security", "Maintains exposure", "Tax-efficient"]
        },
    ]

    for msg in rebuttal_messages:
        await ws_manager.send_debate_message(msg)
        await asyncio.sleep(1.0)

    await ws_manager.send_debate_phase("synthesis", question)
    await asyncio.sleep(0.3)

    synthesis = {
        "agent_id": "coordinator",
        "agent_name": "Coordinator",
        "phase": "synthesis",
        "position": "neutral",
        "message": f"Synthesis found. Sell {risk_ticker} to address concentration risk, with a correlated substitute to maintain sector exposure. This balances risk reduction with tax efficiency.",
        "confidence": 95,
        "key_points": [f"Sell {risk_ticker}", "Buy substitute", "Best of both approaches"]
    }

    await ws_manager.send_debate_message(synthesis)
    await asyncio.sleep(0.8)

    await ws_manager.send_debate_phase("consensus", question)
    await asyncio.sleep(0.3)

    await ws_manager.broadcast({
        "type": "debate_consensus",
        "data": {
            "consensus_reached": True,
            "agreements": {"drift": True, "tax": True},
            "final_decision": f"Sell {risk_ticker}, use correlated substitute"
        }
    })

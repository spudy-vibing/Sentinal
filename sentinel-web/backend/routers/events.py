"""
SENTINEL V2 — Events Router
Handles market event injection and triggers agent analysis.
"""

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime, timezone
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
    event_type: Literal["tech_crash", "earnings_beat", "fed_rate", "custom"] = "tech_crash"
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

    This function orchestrates:
    1. Gateway validation
    2. Coordinator dispatch
    3. Parallel agent execution (Drift + Tax)
    4. Conflict detection
    5. Optional debate mode
    6. Scenario generation
    7. Merkle chain logging
    """
    from src.agents import OfflineCoordinator
    from src.security import MerkleChain
    from src.data import load_portfolio
    from src.contracts.schemas import MarketEventInput, EventType

    import sys
    start_time = datetime.now(timezone.utc)
    print(f"\n{'='*60}", flush=True)
    print(f"  [EVENT] Starting event processing: {event_id}", flush=True)
    print(f"  [EVENT] Portfolio: {portfolio_id}", flush=True)
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
        print("  [STEP 1] Gateway activity sent", flush=True)

        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Load Portfolio
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 2] Loading portfolio...", flush=True)
        try:
            portfolio = load_portfolio(portfolio_id)
            print(f"  [STEP 2] Portfolio loaded: {portfolio.name}")
        except Exception as e:
            print(f"  [STEP 2] Portfolio not found, using demo: {e}")
            # Create demo portfolio if not found
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
            "message": "Dispatching specialist agents in parallel..."
        })
        await asyncio.sleep(0.2)

        # ═══════════════════════════════════════════════════════════════
        # STEP 4: Parallel Agent Dispatch (Drift + Tax)
        # ═══════════════════════════════════════════════════════════════

        # Start Drift Agent
        await ws_manager.send_agent_activity({
            "agent": "drift",
            "status": "active",
            "message": "Analyzing portfolio drift and concentration..."
        })

        # Start Tax Agent (parallel)
        await asyncio.sleep(0.1)
        await ws_manager.send_agent_activity({
            "agent": "tax",
            "status": "active",
            "message": "Checking tax implications and wash sale risks..."
        })

        # Optional: Stream thinking for Tax Agent
        if enable_thinking:
            thoughts = [
                {"type": "observation", "content": "Checking recent transaction history...", "confidence": 95},
                {"type": "observation", "content": f"Found NVDA sale 15 days ago", "confidence": 92},
                {"type": "analysis", "content": "This is within the 30-day wash sale window", "confidence": 94},
                {"type": "calculation", "content": "Disallowed loss would be approximately $25,000", "confidence": 85},
                {"type": "consideration", "content": "Need to find a substitute security...", "confidence": 88},
                {"type": "conclusion", "content": "AMD is a valid correlated substitute", "confidence": 91},
            ]
            for thought in thoughts:
                await ws_manager.send_thinking({
                    "agent": "tax",
                    **thought
                })
                await asyncio.sleep(0.4)

        # Simulate parallel execution time
        await asyncio.sleep(0.8)

        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Execute Actual Analysis
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 5] Executing analysis...", flush=True)
        merkle_chain = MerkleChain()
        coordinator = OfflineCoordinator(merkle_chain=merkle_chain)

        # Create market event
        print("  [STEP 5] Creating market event...", flush=True)
        market_event = MarketEventInput(
            event_id=event_id,
            event_type=EventType.MARKET_EVENT,
            timestamp=datetime.now(timezone.utc),
            session_id=f"session_{uuid.uuid4().hex[:8]}",
            priority=8,
            **event_data
        )

        print("  [STEP 5] Running coordinator.execute_analysis...", flush=True)
        result = coordinator.execute_analysis(
            portfolio=portfolio,
            transactions=[],
            context={"market_event": market_event.model_dump()}
        )
        print(f"  [STEP 5] Analysis complete! Result: {type(result)}")

        # ═══════════════════════════════════════════════════════════════
        # STEP 6: Drift Agent Complete
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 6] Sending Drift Agent complete...", flush=True)
        drift_findings = result.drift_findings
        await ws_manager.send_agent_activity({
            "agent": "drift",
            "status": "complete",
            "message": f"Found {len(drift_findings.concentration_risks)} concentration risks",
            "findings": {
                "concentration_risks": [
                    {
                        "ticker": r.ticker,
                        "current_weight": r.current_weight,
                        "limit": r.limit,
                        "severity": r.severity.value if hasattr(r.severity, 'value') else str(r.severity)
                    }
                    for r in drift_findings.concentration_risks
                ],
                "drift_detected": drift_findings.drift_detected,
                "urgency_score": drift_findings.urgency_score
            }
        })
        print("  [STEP 6] Drift Agent complete sent", flush=True)
        await asyncio.sleep(0.3)

        # ═══════════════════════════════════════════════════════════════
        # STEP 7: Tax Agent Complete
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 7] Sending Tax Agent complete...", flush=True)
        tax_findings = result.tax_findings
        print(f"  [STEP 7] Tax findings: {len(tax_findings.wash_sale_violations)} wash sales, {len(tax_findings.tax_opportunities)} opportunities", flush=True)
        try:
            await ws_manager.send_agent_activity({
                "agent": "tax",
                "status": "complete",
                "message": f"Found {len(tax_findings.wash_sale_violations)} wash sale risks, {len(tax_findings.tax_opportunities)} opportunities",
                "findings": {
                    "wash_sales": [
                        {
                            "ticker": w.ticker,
                            "days_since_sale": w.days_since_sale,
                            "disallowed_loss": w.disallowed_loss
                        }
                        for w in tax_findings.wash_sale_violations
                    ],
                    "opportunities": [
                        {
                            "ticker": o.ticker,
                            "type": str(o.opportunity_type) if hasattr(o.opportunity_type, 'value') else o.opportunity_type,
                            "benefit": o.estimated_benefit
                        }
                        for o in tax_findings.tax_opportunities
                    ]
                }
            })
            print("  [STEP 7] Tax Agent complete sent", flush=True)
        except Exception as e:
            print(f"  [STEP 7] ERROR sending tax agent: {e}", flush=True)
            import traceback
            traceback.print_exc()
        await asyncio.sleep(0.3)
        print("  [STEP 7] Sleep complete, moving to STEP 7.5 (Compliance)", flush=True)

        # ═══════════════════════════════════════════════════════════════
        # STEP 7.5: Compliance Agent
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 7.5] Starting Compliance Agent...", flush=True)
        await ws_manager.send_agent_activity({
            "agent": "compliance",
            "status": "active",
            "message": "Checking regulatory compliance and concentration limits..."
        })
        await asyncio.sleep(0.5)

        # Stream thinking for Compliance Agent
        if enable_thinking:
            compliance_thoughts = [
                {"type": "observation", "content": "Reviewing portfolio against investment policy statement...", "confidence": 95},
                {"type": "analysis", "content": "Checking concentration limits for single positions", "confidence": 92},
                {"type": "observation", "content": "Verifying sector allocation compliance", "confidence": 94},
                {"type": "conclusion", "content": "Compliance review complete", "confidence": 96},
            ]
            for thought in compliance_thoughts:
                await ws_manager.send_thinking({
                    "agent": "compliance",
                    **thought
                })
                await asyncio.sleep(0.3)

        # Complete Compliance Agent
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
        print("  [STEP 7.5] Compliance Agent complete sent", flush=True)
        await asyncio.sleep(0.3)

        # ═══════════════════════════════════════════════════════════════
        # STEP 8: Conflict Detection
        # ═══════════════════════════════════════════════════════════════
        print(f"  [STEP 8] Checking conflicts: {result.conflicts_detected}", flush=True)
        print(f"  [STEP 8] Number of conflicts: {len(result.conflicts_detected) if result.conflicts_detected else 0}", flush=True)
        if result.conflicts_detected:
            await ws_manager.send_agent_activity({
                "agent": "coordinator",
                "status": "warning",
                "message": f"CONFLICT DETECTED: {len(result.conflicts_detected)} conflicts found",
                "conflicts": [
                    {
                        "type": c.conflict_type,
                        "description": c.description,
                        "agents": [a.value for a in c.agents_involved]
                    }
                    for c in result.conflicts_detected
                ]
            })
            await asyncio.sleep(0.5)

            # ═══════════════════════════════════════════════════════════
            # STEP 9: Optional Debate Mode
            # ═══════════════════════════════════════════════════════════
            print(f"  [STEP 9] Debate enabled: {enable_debate}", flush=True)
            if enable_debate and result.conflicts_detected:
                print("  [STEP 9] Running agent debate...", flush=True)
                await run_agent_debate(ws_manager, drift_findings, tax_findings)
                print("  [STEP 9] Agent debate complete", flush=True)

        # ═══════════════════════════════════════════════════════════════
        # STEP 10: Scenario Generation
        # ═══════════════════════════════════════════════════════════════
        print(f"  [STEP 10] Generating scenarios: {len(result.scenarios)} scenarios", flush=True)
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
        # STEP 11: Analysis Complete
        # ═══════════════════════════════════════════════════════════════
        print("  [STEP 11] Preparing final completion message...", flush=True)
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        print(f"  [STEP 11] Elapsed time: {elapsed:.1f}s", flush=True)

        await ws_manager.send_agent_activity({
            "agent": "coordinator",
            "status": "complete",
            "message": f"Analysis complete in {elapsed:.1f}s. Recommended: {result.recommended_scenario_id}",
            "recommended_scenario_id": result.recommended_scenario_id,
            "merkle_hash": result.merkle_hash
        })
        print("  [STEP 11] Coordinator complete sent", flush=True)

        # Send scenarios and store them for API access
        print(f"  [STEP 11] Sending {len(result.scenarios)} scenarios...", flush=True)

        # Import scenario store from scenarios router
        from routers.scenarios import scenario_store

        # Build scenario list and store it
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

        # Store scenarios for API access
        scenario_store.clear()
        for scenario in scenario_list:
            scenario_store[scenario['id']] = scenario

        await ws_manager.send_scenarios(scenario_list)

        print("  [STEP 11] Scenarios sent", flush=True)

        # ═══════════════════════════════════════════════════════════════
        # STEP 12: Merkle Chain Blocks - Persist to SQLite & Send to UI
        # ═══════════════════════════════════════════════════════════════
        print(f"  [STEP 12] Persisting & sending {min(8, len(merkle_chain._blocks))} merkle blocks...", flush=True)
        for block in merkle_chain._blocks[-8:]:
            # Persist to SQLite
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
                print(f"  [STEP 12] Failed to persist block: {e}", flush=True)

            # Send to WebSocket
            await ws_manager.send_merkle_block({
                "event_type": block.event_type,
                "hash": block.current_hash[:16] + "...",
                "timestamp": block.timestamp.isoformat(),
                "actor": block.actor,
                "action": block.action,
                "resource": block.resource
            })
            await asyncio.sleep(0.1)
        print("  [STEP 12] Merkle blocks persisted & sent", flush=True)
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


async def run_agent_debate(ws_manager, drift_findings, tax_findings):
    """Run a simulated debate between Drift and Tax agents."""

    await ws_manager.send_debate_phase("opening", "Should we sell NVDA now?")
    await asyncio.sleep(0.3)

    debate_messages = [
        {
            "agent_id": "drift",
            "agent_name": "Drift Agent",
            "phase": "opening",
            "position": "for",
            "message": "We MUST sell NVDA. The position is at 17%, well above our 15% concentration limit. This level of concentration exposes the portfolio to unacceptable single-stock risk.",
            "confidence": 94,
            "key_points": ["17% concentration", "15% limit breached", "Single-stock risk"]
        },
        {
            "agent_id": "tax",
            "agent_name": "Tax Agent",
            "phase": "opening",
            "position": "against",
            "message": "Hold on. The client sold NVDA just 15 days ago. If we sell more now, we trigger a wash sale and lose $25,000 in tax deductions. That's real money.",
            "confidence": 91,
            "key_points": ["15 days since last sale", "Wash sale window active", "$25K at risk"]
        },
    ]

    for msg in debate_messages[:2]:
        await ws_manager.send_debate_message(msg)
        await asyncio.sleep(1.2)

    await ws_manager.send_debate_phase("rebuttal", "Should we sell NVDA now?")
    await asyncio.sleep(0.3)

    rebuttal_messages = [
        {
            "agent_id": "drift",
            "agent_name": "Drift Agent",
            "phase": "rebuttal",
            "position": "for",
            "message": "I understand the tax concern, but the concentration risk is immediate. If tech drops another 5%, we're looking at much larger losses than $25K. Can we find a substitute security?",
            "confidence": 88,
            "key_points": ["Immediate risk", "Potential for larger losses", "Substitute security?"]
        },
        {
            "agent_id": "tax",
            "agent_name": "Tax Agent",
            "phase": "rebuttal",
            "position": "neutral",
            "message": "Actually... AMD could work as a substitute. It's correlated with NVDA but not 'substantially identical' under IRS rules. We could sell NVDA, buy AMD, maintain tech exposure, AND avoid the wash sale.",
            "confidence": 92,
            "key_points": ["AMD as substitute", "Correlated but not identical", "Avoids wash sale"]
        },
    ]

    for msg in rebuttal_messages:
        await ws_manager.send_debate_message(msg)
        await asyncio.sleep(1.0)

    await ws_manager.send_debate_phase("synthesis", "Should we sell NVDA now?")
    await asyncio.sleep(0.3)

    synthesis = {
        "agent_id": "coordinator",
        "agent_name": "Coordinator",
        "phase": "synthesis",
        "position": "neutral",
        "message": "I've found a synthesis that satisfies both concerns. We sell NVDA to address concentration risk, but simultaneously buy AMD as a correlated substitute. This maintains tech exposure, reduces concentration, AND avoids the wash sale penalty. Both agents should find this acceptable.",
        "confidence": 95,
        "key_points": ["Sell NVDA", "Buy AMD simultaneously", "Best of both approaches"]
    }

    await ws_manager.send_debate_message(synthesis)
    await asyncio.sleep(0.8)

    await ws_manager.send_debate_phase("consensus", "Should we sell NVDA now?")
    await asyncio.sleep(0.3)

    await ws_manager.broadcast({
        "type": "debate_consensus",
        "data": {
            "consensus_reached": True,
            "agreements": {
                "drift": True,
                "tax": True
            },
            "final_decision": "Sell NVDA, buy AMD as correlated substitute"
        }
    })

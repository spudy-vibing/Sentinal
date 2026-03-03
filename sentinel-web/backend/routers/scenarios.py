"""
SENTINEL V2 — Scenarios Router
Handles scenario management and approval workflow.
Now with Claude-powered dynamic scenario generation.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import uuid
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import audit store for persistence
from services.audit_store import audit_store
from config import get_settings

router = APIRouter()
settings = get_settings()

# In-memory scenario storage (would be database in production)
scenario_store: Dict[str, Any] = {}

# Track approved scenarios
approved_scenarios: Dict[str, Dict[str, Any]] = {}


class ActionStep(BaseModel):
    """Single action in a scenario."""
    type: str  # "buy", "sell", "hold"
    ticker: str
    quantity: float
    rationale: Optional[str] = None


class ScenarioMetrics(BaseModel):
    """Utility score breakdown."""
    risk_reduction: float
    tax_savings: float
    goal_alignment: float
    transaction_cost: float
    urgency: float


class Scenario(BaseModel):
    """Full scenario data."""
    id: str
    title: str
    description: str
    score: float
    is_recommended: bool
    actions: List[ActionStep]
    metrics: ScenarioMetrics
    risks: List[str] = []
    expected_outcomes: Dict[str, Any] = {}


class ApprovalRequest(BaseModel):
    """Request to approve a scenario."""
    scenario_id: str
    approver_id: str = "advisor_001"
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response after approving a scenario."""
    status: str
    scenario_id: str
    merkle_hash: str
    timestamp: str
    message: str


class WhatIfRequest(BaseModel):
    """What-if analysis request."""
    scenario_id: str
    adjustments: Dict[str, float]  # e.g., {"tax_sensitivity": 0.9}


@router.get("/")
async def list_scenarios():
    """Get all generated scenarios with approval status."""
    # Get scenarios from store or use demo scenarios
    scenarios = list(scenario_store.values()) if scenario_store else get_demo_scenarios()

    # Add approval status to each scenario
    result = []
    for scenario in scenarios:
        scenario_dict = scenario.model_dump() if hasattr(scenario, 'model_dump') else dict(scenario)
        scenario_id = scenario_dict.get('id')
        if scenario_id in approved_scenarios:
            scenario_dict['status'] = 'approved'
            scenario_dict['approval_info'] = approved_scenarios[scenario_id]
        else:
            scenario_dict['status'] = 'proposed'
        result.append(scenario_dict)

    return result


@router.get("/{scenario_id}", response_model=Scenario)
async def get_scenario(scenario_id: str):
    """Get a specific scenario by ID."""
    if scenario_id in scenario_store:
        return scenario_store[scenario_id]

    # Check demo scenarios
    demos = get_demo_scenarios()
    for s in demos:
        if s.id == scenario_id:
            return s

    raise HTTPException(status_code=404, detail="Scenario not found")


@router.post("/approve", response_model=ApprovalResponse)
async def approve_scenario(request: ApprovalRequest, req: Request):
    """
    Approve a scenario for execution.
    This logs the decision to the Merkle chain.
    """
    # Check if already approved
    if request.scenario_id in approved_scenarios:
        return ApprovalResponse(
            status="already_approved",
            scenario_id=request.scenario_id,
            merkle_hash=approved_scenarios[request.scenario_id]["merkle_hash"],
            timestamp=approved_scenarios[request.scenario_id]["timestamp"],
            message="Scenario was already approved"
        )

    try:
        from src.security import MerkleChain

        timestamp = datetime.now(timezone.utc).isoformat()

        # Create Merkle entry
        merkle = MerkleChain()
        merkle.add_block({
            "event_type": "scenario_approved",
            "scenario_id": request.scenario_id,
            "approver_id": request.approver_id,
            "notes": request.notes,
            "timestamp": timestamp
        })

        merkle_hash = merkle.get_root_hash()

        # Store approval status
        approved_scenarios[request.scenario_id] = {
            "merkle_hash": merkle_hash,
            "approver_id": request.approver_id,
            "notes": request.notes,
            "timestamp": timestamp
        }

        # Update scenario in store if it exists
        if request.scenario_id in scenario_store:
            scenario_store[request.scenario_id]['status'] = 'approved'
            scenario_store[request.scenario_id]['approval_info'] = approved_scenarios[request.scenario_id]

        # Persist to SQLite audit store
        try:
            audit_store.add_block({
                "index": 0,
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "event_type": "scenario_approved",
                "timestamp": timestamp,
                "session_id": "ui_session",
                "actor": request.approver_id,
                "action": "approve",
                "resource": request.scenario_id,
                "data": {"notes": request.notes},
                "previous_hash": None,
                "current_hash": merkle_hash
            })
        except Exception as e:
            print(f"Failed to persist approval to audit store: {e}")

        # Broadcast approval via WebSocket
        ws_manager = req.app.state.ws_manager
        await ws_manager.broadcast({
            "type": "scenario_approved",
            "data": {
                "scenario_id": request.scenario_id,
                "approver_id": request.approver_id,
                "merkle_hash": merkle_hash[:24] + "...",
                "timestamp": timestamp
            }
        })

        # Send Merkle block
        await ws_manager.send_merkle_block({
            "event_type": "scenario_approved",
            "hash": merkle_hash[:16] + "...",
            "timestamp": timestamp
        })

        return ApprovalResponse(
            status="approved",
            scenario_id=request.scenario_id,
            merkle_hash=merkle_hash,
            timestamp=timestamp,
            message="Scenario approved and logged to audit trail"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/what-if")
async def what_if_analysis(request: WhatIfRequest, req: Request):
    """
    Run what-if analysis with adjusted parameters.
    Returns recalculated scores based on new weights.
    """
    try:
        from src.state import UtilityFunction
        from src.contracts.schemas import UtilityWeights

        # Get base weights
        weights = UtilityWeights(
            risk_reduction=request.adjustments.get("risk_reduction", 0.25),
            tax_savings=request.adjustments.get("tax_savings", 0.25),
            goal_alignment=request.adjustments.get("goal_alignment", 0.20),
            transaction_cost=request.adjustments.get("transaction_cost", 0.15),
            urgency=request.adjustments.get("urgency", 0.15)
        )

        # Get scenarios from store or use demo scenarios
        if scenario_store:
            scenarios = [
                Scenario(**s) if isinstance(s, dict) else s
                for s in scenario_store.values()
            ]
        else:
            scenarios = get_demo_scenarios()

        # Recalculate scores
        utility = UtilityFunction()
        results = []

        for scenario in scenarios:
            # Recalculate with new weights
            new_score = (
                scenario.metrics.risk_reduction * weights.risk_reduction * 10 +
                scenario.metrics.tax_savings * weights.tax_savings * 10 +
                scenario.metrics.goal_alignment * weights.goal_alignment * 10 +
                (10 - scenario.metrics.transaction_cost) * weights.transaction_cost * 10 +
                scenario.metrics.urgency * weights.urgency * 10
            )

            results.append({
                "id": scenario.id,
                "title": scenario.title,
                "original_score": scenario.score,
                "new_score": round(new_score, 1),
                "change": round(new_score - scenario.score, 1)
            })

        # Sort by new score
        results.sort(key=lambda x: x["new_score"], reverse=True)

        # Mark new recommendation
        for r in results:
            r["is_recommended"] = r == results[0]

        # Broadcast update
        ws_manager = req.app.state.ws_manager
        await ws_manager.broadcast({
            "type": "what_if_result",
            "data": {
                "adjustments": request.adjustments,
                "results": results
            }
        })

        return {
            "adjustments": request.adjustments,
            "results": results,
            "new_recommendation": results[0]["id"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{scenario_a}/{scenario_b}")
async def compare_scenarios(scenario_a: str, scenario_b: str):
    """Compare two scenarios side-by-side."""
    scenarios = get_demo_scenarios()
    a = next((s for s in scenarios if s.id == scenario_a), None)
    b = next((s for s in scenarios if s.id == scenario_b), None)

    if not a or not b:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return {
        "comparison": {
            "scenario_a": {
                "id": a.id,
                "title": a.title,
                "score": a.score,
                "metrics": a.metrics.model_dump(),
                "actions_count": len(a.actions)
            },
            "scenario_b": {
                "id": b.id,
                "title": b.title,
                "score": b.score,
                "metrics": b.metrics.model_dump(),
                "actions_count": len(b.actions)
            },
            "differences": {
                "score_delta": round(a.score - b.score, 1),
                "risk_delta": round(a.metrics.risk_reduction - b.metrics.risk_reduction, 1),
                "tax_delta": round(a.metrics.tax_savings - b.metrics.tax_savings, 1),
            },
            "recommendation": a.id if a.score > b.score else b.id
        }
    }


class GenerateRequest(BaseModel):
    """Request to generate scenarios dynamically."""
    portfolio_id: str = "portfolio_a"
    market_event: Optional[str] = "Tech sector down 4%"
    drift_analysis: Optional[str] = None
    tax_analysis: Optional[str] = None
    risk_profile: str = "moderate"  # conservative, moderate, aggressive


SCENARIO_GENERATION_PROMPT = """You are a UHNW portfolio advisor generating rebalancing scenarios.

PORTFOLIO CONTEXT:
{portfolio_context}

MARKET EVENT:
{market_event}

DRIFT ANALYSIS:
{drift_analysis}

TAX ANALYSIS:
{tax_analysis}

RISK PROFILE: {risk_profile}

Generate exactly 3 distinct scenarios to address this situation. Each scenario should offer a different risk/reward trade-off.

Output as JSON array with this exact structure:
[
  {{
    "title": "Short descriptive title",
    "description": "2-3 sentence explanation of the approach",
    "actions": [
      {{"type": "sell|buy|hold", "ticker": "SYMBOL", "quantity": 1000, "rationale": "Why this action"}}
    ],
    "metrics": {{
      "risk_reduction": 7.5,
      "tax_savings": 8.0,
      "goal_alignment": 7.0,
      "transaction_cost": 3.0,
      "urgency": 6.5
    }},
    "risks": ["Risk 1", "Risk 2"],
    "expected_outcomes": {{"concentration_after": 0.13, "tax_impact": -5000}}
  }}
]

Each metric is scored 1-10. Higher is better for all except transaction_cost (lower is better).
The first scenario should be the most balanced/recommended approach.
"""


@router.post("/generate")
async def generate_scenarios(request: GenerateRequest, req: Request):
    """
    Generate scenarios dynamically using Claude.
    Streams progress updates via WebSocket.
    """
    ws_manager = req.app.state.ws_manager

    # Build portfolio context
    portfolio_context = f"Portfolio: {request.portfolio_id}"
    try:
        from src.data import load_portfolio
        portfolio = load_portfolio(request.portfolio_id)
        holdings_str = "\n".join([
            f"- {h.ticker}: {h.portfolio_weight:.1%} (${h.market_value:,.0f})"
            for h in portfolio.holdings[:10]
        ])
        portfolio_context = f"""
Portfolio: {portfolio.name}
AUM: ${portfolio.aum_usd:,.0f}
Concentration Limit: {portfolio.client_profile.concentration_limit:.0%}

Holdings:
{holdings_str}
"""
    except Exception as e:
        portfolio_context = f"Portfolio: {request.portfolio_id} (details unavailable: {e})"

    # Broadcast that we're generating
    await ws_manager.broadcast({
        "type": "scenario_generating",
        "data": {"status": "starting", "message": "Analyzing portfolio..."}
    })

    try:
        import anthropic

        if not settings.anthropic_api_key:
            # Return demo scenarios if no API key
            await ws_manager.broadcast({
                "type": "scenario_generating",
                "data": {"status": "complete", "message": "Using demo scenarios (no API key)"}
            })
            scenarios = get_demo_scenarios()
            for s in scenarios:
                scenario_store[s.id] = s
            return {"scenarios": [s.model_dump() for s in scenarios], "source": "demo"}

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Build prompt
        prompt = SCENARIO_GENERATION_PROMPT.format(
            portfolio_context=portfolio_context,
            market_event=request.market_event or "General portfolio review",
            drift_analysis=request.drift_analysis or "NVDA at 17% exceeds 15% concentration limit",
            tax_analysis=request.tax_analysis or "NVDA sold 15 days ago, wash sale window active",
            risk_profile=request.risk_profile
        )

        await ws_manager.broadcast({
            "type": "scenario_generating",
            "data": {"status": "thinking", "message": "Claude analyzing scenarios..."}
        })

        # Call Claude
        response = client.messages.create(
            model=settings.default_model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        json_text = response_text
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0]

        scenarios_data = json.loads(json_text.strip())

        # Convert to Scenario objects and store
        scenarios = []
        for i, s in enumerate(scenarios_data):
            scenario = Scenario(
                id=f"scenario_{uuid.uuid4().hex[:8]}",
                title=s.get("title", f"Scenario {i+1}"),
                description=s.get("description", ""),
                score=calculate_score(s.get("metrics", {}), request.risk_profile),
                is_recommended=(i == 0),
                actions=[ActionStep(**a) for a in s.get("actions", [])],
                metrics=ScenarioMetrics(**s.get("metrics", {
                    "risk_reduction": 5, "tax_savings": 5, "goal_alignment": 5,
                    "transaction_cost": 5, "urgency": 5
                })),
                risks=s.get("risks", []),
                expected_outcomes=s.get("expected_outcomes", {})
            )
            scenarios.append(scenario)
            scenario_store[scenario.id] = scenario

        # Sort by score and mark recommended
        scenarios.sort(key=lambda x: x.score, reverse=True)
        for i, s in enumerate(scenarios):
            s.is_recommended = (i == 0)
            scenario_store[s.id] = s

        await ws_manager.broadcast({
            "type": "scenario_generating",
            "data": {"status": "complete", "message": f"Generated {len(scenarios)} scenarios"}
        })

        # Also broadcast scenarios for UI update
        await ws_manager.broadcast({
            "type": "scenarios_ready",
            "data": {"scenarios": [s.model_dump() for s in scenarios]}
        })

        return {"scenarios": [s.model_dump() for s in scenarios], "source": "claude"}

    except json.JSONDecodeError as e:
        logging.warning(f"Failed to parse Claude scenario response: {e}")
        await ws_manager.broadcast({
            "type": "scenario_generating",
            "data": {"status": "fallback", "message": "Failed to parse Claude response, using demo scenarios"}
        })
        scenarios = get_demo_scenarios()
        return {"scenarios": [s.model_dump() for s in scenarios], "source": "demo_fallback"}

    except Exception as e:
        logging.warning(f"Scenario generation failed, returning error: {e}")
        await ws_manager.broadcast({
            "type": "scenario_generating",
            "data": {"status": "error", "message": str(e)}
        })
        raise HTTPException(status_code=500, detail=str(e))


def calculate_score(metrics: Dict[str, float], risk_profile: str) -> float:
    """Calculate utility score based on risk profile weights."""
    weights = {
        "conservative": {"risk": 0.40, "tax": 0.20, "goal": 0.20, "cost": 0.15, "urgency": 0.05},
        "moderate": {"risk": 0.25, "tax": 0.30, "goal": 0.25, "cost": 0.10, "urgency": 0.10},
        "aggressive": {"risk": 0.15, "tax": 0.20, "goal": 0.30, "cost": 0.10, "urgency": 0.25}
    }.get(risk_profile, {"risk": 0.25, "tax": 0.25, "goal": 0.20, "cost": 0.15, "urgency": 0.15})

    score = (
        metrics.get("risk_reduction", 5) * weights["risk"] +
        metrics.get("tax_savings", 5) * weights["tax"] +
        metrics.get("goal_alignment", 5) * weights["goal"] +
        (10 - metrics.get("transaction_cost", 5)) * weights["cost"] +
        metrics.get("urgency", 5) * weights["urgency"]
    ) * 10

    return round(score, 1)


def get_demo_scenarios() -> List[Scenario]:
    """Return demo scenarios for UI development."""
    return [
        Scenario(
            id="scenario_amd_substitute",
            title="AMD Substitute Strategy",
            description="Sell NVDA to reduce concentration, buy AMD as correlated substitute to maintain tech exposure while avoiding wash sale.",
            score=72.4,
            is_recommended=True,
            actions=[
                ActionStep(type="sell", ticker="NVDA", quantity=2000, rationale="Reduce concentration"),
                ActionStep(type="buy", ticker="AMD", quantity=5600, rationale="Correlated substitute"),
            ],
            metrics=ScenarioMetrics(
                risk_reduction=8.5,
                tax_savings=8.2,
                goal_alignment=7.0,
                transaction_cost=3.0,
                urgency=7.5
            ),
            risks=["AMD correlation may diverge", "Execution timing risk"],
            expected_outcomes={"concentration_after": 0.13, "tax_impact": 0}
        ),
        Scenario(
            id="scenario_wait_16_days",
            title="Wait 16 Days",
            description="Hold current positions until wash sale window closes, then rebalance freely.",
            score=58.2,
            is_recommended=False,
            actions=[
                ActionStep(type="hold", ticker="NVDA", quantity=0, rationale="Wait for window"),
            ],
            metrics=ScenarioMetrics(
                risk_reduction=4.0,
                tax_savings=9.0,
                goal_alignment=6.0,
                transaction_cost=1.0,
                urgency=3.0
            ),
            risks=["Concentration risk persists", "Market may move against us"],
            expected_outcomes={"concentration_after": 0.17, "tax_impact": 0}
        ),
        Scenario(
            id="scenario_accept_wash_sale",
            title="Accept Wash Sale",
            description="Sell NVDA immediately accepting the $25K wash sale penalty to eliminate concentration risk.",
            score=45.1,
            is_recommended=False,
            actions=[
                ActionStep(type="sell", ticker="NVDA", quantity=2000, rationale="Immediate risk reduction"),
            ],
            metrics=ScenarioMetrics(
                risk_reduction=9.0,
                tax_savings=2.0,
                goal_alignment=5.0,
                transaction_cost=4.0,
                urgency=9.0
            ),
            risks=["$25K tax penalty", "Reduced tech exposure"],
            expected_outcomes={"concentration_after": 0.13, "tax_impact": -25000}
        ),
        Scenario(
            id="scenario_partial_trim",
            title="Partial Trim + Rebalance",
            description="Sell half the excess NVDA now, remainder after wash sale window. Balanced approach.",
            score=61.8,
            is_recommended=False,
            actions=[
                ActionStep(type="sell", ticker="NVDA", quantity=1000, rationale="Partial reduction"),
                ActionStep(type="buy", ticker="BND", quantity=15000, rationale="Increase fixed income"),
            ],
            metrics=ScenarioMetrics(
                risk_reduction=6.5,
                tax_savings=6.0,
                goal_alignment=7.5,
                transaction_cost=4.5,
                urgency=6.0
            ),
            risks=["Partial wash sale exposure", "Still somewhat concentrated"],
            expected_outcomes={"concentration_after": 0.15, "tax_impact": -12500}
        ),
    ]

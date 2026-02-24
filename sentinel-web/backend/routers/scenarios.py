"""
SENTINEL V2 — Scenarios Router
Handles scenario management and approval workflow.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import audit store for persistence
from services.audit_store import audit_store

router = APIRouter()

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

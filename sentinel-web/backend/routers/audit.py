"""
SENTINEL V2 - Audit Trail API

Endpoints for querying and managing the audit trail.
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import tempfile
import os

from services.audit_store import audit_store

router = APIRouter()


@router.get("/blocks")
async def get_audit_blocks(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    search: Optional[str] = Query(None, description="Search in data/action/resource"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
) -> Dict[str, Any]:
    """
    Get audit trail blocks with optional filtering.

    Returns paginated list of blocks matching the filters.
    """
    blocks = audit_store.get_blocks(
        event_type=event_type,
        actor=actor,
        session_id=session_id,
        from_date=from_date,
        to_date=to_date,
        search=search,
        limit=limit,
        offset=offset
    )

    return {
        "blocks": blocks,
        "count": len(blocks),
        "limit": limit,
        "offset": offset,
        "has_more": len(blocks) == limit
    }


@router.get("/blocks/{block_hash}")
async def get_block_by_hash(block_hash: str) -> Dict[str, Any]:
    """Get a specific block by its hash."""
    block = audit_store.get_block_by_hash(block_hash)

    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    return block


@router.get("/stats")
async def get_audit_stats() -> Dict[str, Any]:
    """
    Get audit trail statistics.

    Returns counts by event type, actor, and other metrics.
    """
    return audit_store.get_stats()


@router.get("/event-types")
async def get_event_types() -> List[str]:
    """Get all distinct event types in the audit trail."""
    return audit_store.get_event_types()


@router.get("/actors")
async def get_actors() -> List[str]:
    """Get all distinct actors in the audit trail."""
    return audit_store.get_actors()


@router.get("/verify")
async def verify_chain() -> Dict[str, Any]:
    """
    Verify the integrity of the audit chain.

    Checks that all blocks are properly linked via previous_hash.
    """
    result = audit_store.verify_chain()

    return {
        **result,
        "verified_at": datetime.utcnow().isoformat(),
        "message": "Chain integrity verified" if result["valid"] else "Chain integrity issues detected"
    }


@router.get("/export")
async def export_audit_trail(
    format: str = Query("csv", enum=["csv", "json"]),
    event_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """
    Export audit trail to file.

    Returns downloadable CSV or JSON file.
    """
    # Get filtered blocks
    blocks = audit_store.get_blocks(
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        limit=10000
    )

    if not blocks:
        raise HTTPException(status_code=404, detail="No blocks match the criteria")

    # Create temp file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_trail_{timestamp}.{format}"

    if format == "csv":
        import csv
        filepath = os.path.join(tempfile.gettempdir(), filename)

        with open(filepath, 'w', newline='') as f:
            # Flatten data for CSV
            flat_blocks = []
            for b in blocks:
                flat = {k: v for k, v in b.items() if k != 'data'}
                if b.get('data'):
                    flat['data'] = str(b['data'])
                flat_blocks.append(flat)

            if flat_blocks:
                writer = csv.DictWriter(f, fieldnames=flat_blocks[0].keys())
                writer.writeheader()
                writer.writerows(flat_blocks)

        return FileResponse(
            filepath,
            media_type="text/csv",
            filename=filename
        )

    else:  # JSON
        import json
        filepath = os.path.join(tempfile.gettempdir(), filename)

        with open(filepath, 'w') as f:
            json.dump({"blocks": blocks, "exported_at": datetime.utcnow().isoformat()}, f, indent=2)

        return FileResponse(
            filepath,
            media_type="application/json",
            filename=filename
        )


@router.post("/seed-demo")
async def seed_demo_data() -> Dict[str, Any]:
    """
    Seed the audit trail with demo data for testing.
    Only for development/demo purposes.
    """
    from datetime import timedelta
    import uuid

    demo_events = [
        {
            "event_type": "system_initialized",
            "actor": "system",
            "action": "chain_initialized",
            "resource": None,
            "data": {"version": "2.0"}
        },
        {
            "event_type": "session_created",
            "actor": "advisor_001",
            "action": "login",
            "session_id": "sess_demo_001",
            "resource": "auth",
            "data": {"role": "human_advisor"}
        },
        {
            "event_type": "market_event_detected",
            "actor": "system",
            "action": "detect",
            "resource": "NVDA",
            "data": {"event": "tech_crash", "magnitude": -0.04}
        },
        {
            "event_type": "agent_invoked",
            "actor": "drift_agent",
            "action": "analyze",
            "session_id": "sess_demo_001",
            "resource": "portfolio_a",
            "data": {"drift_pct": 0.18}
        },
        {
            "event_type": "agent_completed",
            "actor": "drift_agent",
            "action": "complete",
            "session_id": "sess_demo_001",
            "resource": "portfolio_a",
            "data": {"findings": "NVDA over-concentrated"}
        },
        {
            "event_type": "agent_invoked",
            "actor": "tax_agent",
            "action": "analyze",
            "session_id": "sess_demo_001",
            "resource": "portfolio_a",
            "data": {}
        },
        {
            "event_type": "agent_completed",
            "actor": "tax_agent",
            "action": "complete",
            "session_id": "sess_demo_001",
            "resource": "portfolio_a",
            "data": {"wash_sale_risk": True}
        },
        {
            "event_type": "conflict_detected",
            "actor": "coordinator",
            "action": "detect_conflict",
            "session_id": "sess_demo_001",
            "resource": "NVDA",
            "data": {"agents": ["drift", "tax"], "topic": "sell_timing"}
        },
        {
            "event_type": "scenario_generated",
            "actor": "coordinator",
            "action": "generate",
            "session_id": "sess_demo_001",
            "resource": "scenario_amd_substitute",
            "data": {"score": 72.4, "is_recommended": True}
        },
        {
            "event_type": "scenario_approved",
            "actor": "advisor_001",
            "action": "approve",
            "session_id": "sess_demo_001",
            "resource": "scenario_amd_substitute",
            "data": {"notes": "Approved via Sentinel V2 UI"}
        },
    ]

    now = datetime.utcnow()
    count = 0

    for i, event in enumerate(demo_events):
        # Spread events over last 2 hours
        event_time = now - timedelta(minutes=(len(demo_events) - i) * 12)

        block = {
            "index": i,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "timestamp": event_time.isoformat(),
            "current_hash": f"{uuid.uuid4().hex[:32]}",
            "previous_hash": f"{uuid.uuid4().hex[:32]}" if i > 0 else "0" * 64,
            **event
        }

        try:
            audit_store.add_block(block)
            count += 1
        except Exception as e:
            print(f"Failed to add demo block: {e}")

    return {
        "message": f"Seeded {count} demo audit blocks",
        "count": count
    }

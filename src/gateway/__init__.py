"""
SENTINEL GATEWAY PACKAGE

Central event ingestion, validation, and routing for the Sentinel system.

Usage:
    from src.gateway import Gateway, EventFactory

    gateway = Gateway(merkle_chain=audit_chain)
    await gateway.start()

    # Submit a market event
    event = EventFactory.create_market_event(
        session_id="advisor:main",
        affected_sectors=["Technology"],
        magnitude=-0.04,
        description="Tech selloff 4%"
    )
    event_id = await gateway.submit(event)

    # Register handler
    gateway.register_handler(EventType.MARKET_EVENT, my_handler)

    # Process events
    await gateway.process_session("advisor:main")
"""

from .gateway import (
    Gateway,
    SessionQueue,
    PriorityItem,
    EventFactory,
)

__all__ = [
    "Gateway",
    "SessionQueue",
    "PriorityItem",
    "EventFactory",
]

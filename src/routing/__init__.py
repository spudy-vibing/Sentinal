"""
SENTINEL ROUTING MODULE

Event routing and persona-based agent selection.
"""

from .persona_router import (
    PersonaRouter,
    RoutingDecision,
    RoutingPriority,
    get_router,
    route_event,
)

__all__ = [
    "PersonaRouter",
    "RoutingDecision",
    "RoutingPriority",
    "get_router",
    "route_event",
]

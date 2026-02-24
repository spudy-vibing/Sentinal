"""
SENTINEL UI MODULE

Canvas generation and UI components for advisor interface.

Components follow the Private Banking Precision design framework.
"""

from .canvas import (
    CanvasGenerator,
    generate_canvas,
    save_canvas,
)

from .components import (
    # Component classes
    Badge,
    Button,
    ScoreBar,
    MetricCard,
    Slider,
    TradeRow,
    AlertBanner,
    # Enums
    BadgeVariant,
    ButtonVariant,
    CardVariant,
    # Factory
    ComponentFactory,
    components,
)

__all__ = [
    # Canvas
    "CanvasGenerator",
    "generate_canvas",
    "save_canvas",
    # Components
    "Badge",
    "Button",
    "ScoreBar",
    "MetricCard",
    "Slider",
    "TradeRow",
    "AlertBanner",
    # Enums
    "BadgeVariant",
    "ButtonVariant",
    "CardVariant",
    # Factory
    "ComponentFactory",
    "components",
]

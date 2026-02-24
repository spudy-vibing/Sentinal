"""
SENTINEL UI COMPONENTS

Reusable UI components for Canvas generation.

Components follow the Sentinel Design Framework:
- Private Banking Precision aesthetic
- Obsidian color palette
- Champagne gold accents

Reference: docs/DESIGN_FRAMEWORK.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
# COMPONENT TYPES
# ═══════════════════════════════════════════════════════════════════════════

class BadgeVariant(str, Enum):
    """Badge color variants."""
    DEFAULT = "default"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    INFO = "info"
    ACCENT = "accent"


class ButtonVariant(str, Enum):
    """Button style variants."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    GHOST = "ghost"
    DANGER = "danger"


class CardVariant(str, Enum):
    """Card style variants."""
    DEFAULT = "default"
    ELEVATED = "elevated"
    HIGHLIGHTED = "highlighted"


# ═══════════════════════════════════════════════════════════════════════════
# COMPONENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Badge:
    """Small label for status or categories."""
    text: str
    variant: BadgeVariant = BadgeVariant.DEFAULT

    def render(self) -> str:
        variant_styles = {
            BadgeVariant.DEFAULT: "background: var(--s-obsidian-700); color: var(--s-obsidian-200);",
            BadgeVariant.SUCCESS: "background: var(--s-positive-500); color: var(--s-obsidian-900);",
            BadgeVariant.WARNING: "background: var(--s-warning-500); color: var(--s-obsidian-900);",
            BadgeVariant.DANGER: "background: var(--s-negative-500); color: white;",
            BadgeVariant.INFO: "background: var(--s-info-500); color: white;",
            BadgeVariant.ACCENT: "background: var(--s-champagne-500); color: var(--s-obsidian-900);",
        }

        style = variant_styles.get(self.variant, variant_styles[BadgeVariant.DEFAULT])

        return f"""
<span class="sentinel-badge" style="{style}
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
">{self.text}</span>
"""


@dataclass
class Button:
    """Interactive button component."""
    text: str
    variant: ButtonVariant = ButtonVariant.PRIMARY
    onclick: str = ""
    disabled: bool = False

    def render(self) -> str:
        variant_styles = {
            ButtonVariant.PRIMARY: """
                background: var(--s-champagne-500);
                color: var(--s-obsidian-900);
            """,
            ButtonVariant.SECONDARY: """
                background: var(--s-obsidian-700);
                color: var(--s-obsidian-200);
            """,
            ButtonVariant.GHOST: """
                background: transparent;
                color: var(--s-obsidian-200);
                border: 1px solid var(--s-border-default);
            """,
            ButtonVariant.DANGER: """
                background: var(--s-negative-500);
                color: white;
            """,
        }

        style = variant_styles.get(self.variant, variant_styles[ButtonVariant.PRIMARY])
        disabled_attr = "disabled" if self.disabled else ""
        onclick_attr = f'onclick="{self.onclick}"' if self.onclick else ""

        return f"""
<button class="sentinel-btn" {onclick_attr} {disabled_attr} style="{style}
  font-family: var(--s-font-body);
  font-size: 0.875rem;
  font-weight: 500;
  padding: 12px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 150ms cubic-bezier(0.16, 1, 0.3, 1);
">{self.text}</button>
"""


@dataclass
class ScoreBar:
    """Visual score bar with fill."""
    value: float  # 0-100
    label: str = ""
    show_value: bool = True

    def render(self) -> str:
        value_html = f'<span style="font-family: var(--s-font-mono); font-size: 1rem; color: var(--s-champagne-500);">{self.value:.0f}</span>' if self.show_value else ""
        label_html = f'<span style="font-size: 0.75rem; color: var(--s-obsidian-400); text-transform: uppercase; letter-spacing: 0.05em;">{self.label}</span>' if self.label else ""

        return f"""
<div class="sentinel-score-bar">
  <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
    {label_html}
    {value_html}
  </div>
  <div style="height: 4px; background: var(--s-obsidian-700); border-radius: 2px; overflow: hidden;">
    <div style="height: 100%; width: {min(100, max(0, self.value))}%; background: linear-gradient(90deg, var(--s-champagne-500), var(--s-champagne-300)); border-radius: 2px;"></div>
  </div>
</div>
"""


@dataclass
class MetricCard:
    """Card displaying a single metric."""
    label: str
    value: str
    change: Optional[float] = None  # Percentage change
    change_label: str = ""

    def render(self) -> str:
        change_html = ""
        if self.change is not None:
            if self.change >= 0:
                change_color = "var(--s-positive-500)"
                change_icon = "↑"
            else:
                change_color = "var(--s-negative-500)"
                change_icon = "↓"

            change_html = f"""
<div style="font-size: 0.75rem; color: {change_color}; margin-top: 4px;">
  {change_icon} {abs(self.change):.1f}% {self.change_label}
</div>
"""

        return f"""
<div class="sentinel-metric-card" style="
  background: var(--s-obsidian-800);
  border: 1px solid var(--s-border-subtle);
  border-radius: 8px;
  padding: 20px;
">
  <div style="font-size: 0.75rem; color: var(--s-obsidian-400); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">
    {self.label}
  </div>
  <div style="font-family: var(--s-font-display); font-size: 1.75rem; font-weight: 500; color: var(--s-obsidian-50);">
    {self.value}
  </div>
  {change_html}
</div>
"""


@dataclass
class Slider:
    """Interactive slider for what-if analysis."""
    id: str
    label: str
    min_value: float
    max_value: float
    current_value: float
    step: float = 1
    unit: str = ""

    def render(self) -> str:
        return f"""
<div class="sentinel-slider" style="margin-bottom: 20px;">
  <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
    <label style="font-size: 0.875rem; color: var(--s-obsidian-200);" for="{self.id}">{self.label}</label>
    <span id="{self.id}_value" style="font-family: var(--s-font-mono); font-size: 0.875rem; color: var(--s-champagne-500);">
      {self.current_value}{self.unit}
    </span>
  </div>
  <input type="range"
    id="{self.id}"
    min="{self.min_value}"
    max="{self.max_value}"
    value="{self.current_value}"
    step="{self.step}"
    style="
      width: 100%;
      height: 4px;
      background: var(--s-obsidian-700);
      border-radius: 2px;
      appearance: none;
      outline: none;
    "
    oninput="document.getElementById('{self.id}_value').textContent = this.value + '{self.unit}'"
  >
  <style>
    #{self.id}::-webkit-slider-thumb {{
      appearance: none;
      width: 16px;
      height: 16px;
      background: var(--s-champagne-500);
      border-radius: 50%;
      cursor: pointer;
    }}
  </style>
</div>
"""


@dataclass
class TradeRow:
    """Single trade display row."""
    ticker: str
    action: Literal["BUY", "SELL"]
    quantity: float
    price: float
    timing: str = "Immediate"

    def render(self) -> str:
        action_color = "var(--s-positive-500)" if self.action == "BUY" else "var(--s-negative-500)"
        total = self.quantity * self.price

        return f"""
<div class="sentinel-trade-row" style="
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--s-obsidian-850);
  border-radius: 4px;
  margin-bottom: 8px;
">
  <div style="flex: 0 0 80px;">
    <span style="font-weight: 500; color: {action_color};">{self.action}</span>
  </div>
  <div style="flex: 1;">
    <span style="font-family: var(--s-font-mono); color: var(--s-obsidian-100);">{self.ticker}</span>
  </div>
  <div style="flex: 0 0 100px; text-align: right;">
    <span style="font-family: var(--s-font-mono); color: var(--s-obsidian-200);">{self.quantity:,.0f}</span>
  </div>
  <div style="flex: 0 0 100px; text-align: right;">
    <span style="font-family: var(--s-font-mono); color: var(--s-obsidian-300);">${self.price:,.2f}</span>
  </div>
  <div style="flex: 0 0 120px; text-align: right;">
    <span style="font-family: var(--s-font-mono); color: var(--s-champagne-500);">${total:,.0f}</span>
  </div>
  <div style="flex: 0 0 100px; text-align: right;">
    <span style="font-size: 0.75rem; color: var(--s-obsidian-400);">{self.timing}</span>
  </div>
</div>
"""


@dataclass
class AlertBanner:
    """Alert banner for important messages."""
    message: str
    variant: Literal["info", "warning", "danger", "success"] = "info"
    dismissible: bool = True

    def render(self) -> str:
        variant_styles = {
            "info": ("var(--s-info-500)", "var(--s-info-500)"),
            "warning": ("var(--s-warning-500)", "var(--s-warning-500)"),
            "danger": ("var(--s-negative-500)", "var(--s-negative-500)"),
            "success": ("var(--s-positive-500)", "var(--s-positive-500)"),
        }

        border_color, icon_color = variant_styles.get(self.variant, variant_styles["info"])

        icons = {
            "info": "ℹ",
            "warning": "⚠",
            "danger": "✕",
            "success": "✓",
        }
        icon = icons.get(self.variant, "ℹ")

        dismiss_html = """
<button onclick="this.parentElement.style.display='none'" style="
  background: none;
  border: none;
  color: var(--s-obsidian-400);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 4px;
">×</button>
""" if self.dismissible else ""

        return f"""
<div class="sentinel-alert" style="
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--s-obsidian-800);
  border: 1px solid {border_color};
  border-radius: 8px;
  margin-bottom: 16px;
">
  <span style="font-size: 1.25rem; color: {icon_color};">{icon}</span>
  <span style="flex: 1; color: var(--s-obsidian-200);">{self.message}</span>
  {dismiss_html}
</div>
"""


# ═══════════════════════════════════════════════════════════════════════════
# COMPONENT FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class ComponentFactory:
    """Factory for creating UI components."""

    @staticmethod
    def badge(text: str, variant: str = "default") -> Badge:
        """Create a badge component."""
        return Badge(text=text, variant=BadgeVariant(variant))

    @staticmethod
    def button(
        text: str,
        variant: str = "primary",
        onclick: str = "",
        disabled: bool = False
    ) -> Button:
        """Create a button component."""
        return Button(
            text=text,
            variant=ButtonVariant(variant),
            onclick=onclick,
            disabled=disabled
        )

    @staticmethod
    def score_bar(value: float, label: str = "") -> ScoreBar:
        """Create a score bar component."""
        return ScoreBar(value=value, label=label)

    @staticmethod
    def metric(
        label: str,
        value: str,
        change: Optional[float] = None
    ) -> MetricCard:
        """Create a metric card component."""
        return MetricCard(label=label, value=value, change=change)

    @staticmethod
    def slider(
        id: str,
        label: str,
        min_val: float,
        max_val: float,
        current: float,
        unit: str = ""
    ) -> Slider:
        """Create a slider component."""
        return Slider(
            id=id,
            label=label,
            min_value=min_val,
            max_value=max_val,
            current_value=current,
            unit=unit
        )

    @staticmethod
    def trade(
        ticker: str,
        action: str,
        quantity: float,
        price: float
    ) -> TradeRow:
        """Create a trade row component."""
        return TradeRow(
            ticker=ticker,
            action=action.upper(),
            quantity=quantity,
            price=price
        )

    @staticmethod
    def alert(message: str, variant: str = "info") -> AlertBanner:
        """Create an alert banner component."""
        return AlertBanner(message=message, variant=variant)


# Convenience instance
components = ComponentFactory()

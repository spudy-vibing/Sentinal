"""
SENTINEL DEMOS MODULE

Interactive demonstrations of the Sentinel system.

Demos:
- golden_path: Full pipeline from market event to Canvas UI
- proactive_heartbeat: Scheduled monitoring and proactive alerts
- webhook_trigger: External event handling (SEC filings, news)

Usage:
    python -m src.demos.golden_path
    python -m src.demos.proactive_heartbeat
    python -m src.demos.webhook_trigger

Or via main:
    python -m src.main --demo golden_path
"""

from .golden_path import run_demo as run_golden_path
from .proactive_heartbeat import run_demo as run_heartbeat
from .webhook_trigger import run_demo as run_webhook

__all__ = [
    "run_golden_path",
    "run_heartbeat",
    "run_webhook",
]

"""
SENTINEL CANVAS (A2UI)

Agent-to-UI system for generating interactive recommendation interfaces.

The Canvas generates HTML/CSS/JS that advisors can interact with:
- View scenarios with utility scores
- Compare recommendations side-by-side
- Use sliders for what-if analysis
- Approve or reject recommendations

Design Reference: docs/DESIGN_FRAMEWORK.md
Implementation Reference: docs/IMPLEMENTATION_PLAN.md Phase 3, Step 3.5
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

from src.contracts.schemas import (
    CoordinatorOutput,
    Scenario,
    UtilityScore,
    CanvasState,
    UIAction,
    UIActionType,
)


# ═══════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS (from DESIGN_FRAMEWORK.md)
# ═══════════════════════════════════════════════════════════════════════════

DESIGN_TOKENS = """
:root {
  /* ═══════════════════════════════════════════════════════════
     SENTINEL COLOR SYSTEM - Private Banking Precision
     ═══════════════════════════════════════════════════════════ */

  /* Foundation: Obsidian Scale */
  --s-obsidian-950: #050506;
  --s-obsidian-900: #0A0A0B;
  --s-obsidian-850: #0F0F11;
  --s-obsidian-800: #141416;
  --s-obsidian-700: #1C1C1F;
  --s-obsidian-600: #252528;
  --s-obsidian-500: #3A3A3F;
  --s-obsidian-400: #5C5C63;
  --s-obsidian-300: #8E8E96;
  --s-obsidian-200: #B8B8BF;
  --s-obsidian-100: #E8E8EB;
  --s-obsidian-50:  #F5F5F7;

  /* Accent: Champagne Gold */
  --s-champagne-500: #C9A962;
  --s-champagne-400: #D4BA7D;
  --s-champagne-300: #E0CB99;

  /* Semantic Colors */
  --s-positive-500: #22A55D;
  --s-positive-300: #7DD4A3;
  --s-negative-500: #D44545;
  --s-negative-300: #EF9A9A;
  --s-warning-500: #D4A745;
  --s-info-500: #4589D4;

  /* Transparency Layers */
  --s-glass-thick: rgba(10, 10, 11, 0.95);
  --s-glass-medium: rgba(10, 10, 11, 0.80);
  --s-border-subtle: rgba(255, 255, 255, 0.06);
  --s-border-default: rgba(255, 255, 255, 0.10);
  --s-border-accent: rgba(201, 169, 98, 0.40);
  --s-glow-champagne: rgba(201, 169, 98, 0.15);

  /* Typography */
  --s-font-display: 'Cormorant Garamond', Georgia, serif;
  --s-font-body: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --s-font-mono: 'JetBrains Mono', 'SF Mono', monospace;

  /* Spacing */
  --s-space-1: 4px;
  --s-space-2: 8px;
  --s-space-3: 12px;
  --s-space-4: 16px;
  --s-space-5: 20px;
  --s-space-6: 24px;
  --s-space-8: 32px;
  --s-space-10: 40px;
  --s-space-12: 48px;

  /* Motion */
  --s-ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --s-duration-fast: 150ms;
  --s-duration-normal: 250ms;
  --s-duration-slow: 400ms;
}
"""


# ═══════════════════════════════════════════════════════════════════════════
# BASE STYLES
# ═══════════════════════════════════════════════════════════════════════════

BASE_STYLES = """
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--s-font-body);
  background: var(--s-obsidian-900);
  color: var(--s-obsidian-100);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.sentinel-canvas {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--s-space-8);
}

/* Header */
.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--s-space-8);
  padding-bottom: var(--s-space-6);
  border-bottom: 1px solid var(--s-border-subtle);
}

.canvas-title {
  font-family: var(--s-font-display);
  font-size: 2rem;
  font-weight: 500;
  color: var(--s-obsidian-50);
  letter-spacing: -0.02em;
}

.canvas-subtitle {
  font-size: 0.875rem;
  color: var(--s-obsidian-400);
  margin-top: var(--s-space-2);
}

.canvas-meta {
  text-align: right;
}

.meta-label {
  font-size: 0.75rem;
  color: var(--s-obsidian-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-value {
  font-family: var(--s-font-mono);
  font-size: 0.875rem;
  color: var(--s-obsidian-200);
}

/* Scenario Grid */
.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--s-space-6);
  margin-bottom: var(--s-space-8);
}

/* Scenario Card */
.scenario-card {
  background: var(--s-obsidian-800);
  border: 1px solid var(--s-border-subtle);
  border-radius: 8px;
  padding: var(--s-space-6);
  transition: all var(--s-duration-normal) var(--s-ease-out);
  position: relative;
  overflow: hidden;
}

.scenario-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--s-champagne-500), transparent);
  opacity: 0;
  transition: opacity var(--s-duration-normal);
}

.scenario-card:hover {
  border-color: var(--s-border-default);
  transform: translateY(-2px);
}

.scenario-card:hover::before {
  opacity: 1;
}

.scenario-card.recommended {
  border-color: var(--s-border-accent);
  box-shadow: 0 0 40px var(--s-glow-champagne);
}

.scenario-card.recommended::before {
  opacity: 1;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--s-space-4);
}

.scenario-title {
  font-family: var(--s-font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--s-obsidian-50);
}

.scenario-badge {
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: var(--s-space-1) var(--s-space-2);
  border-radius: 4px;
  background: var(--s-champagne-500);
  color: var(--s-obsidian-900);
}

.scenario-description {
  font-size: 0.875rem;
  color: var(--s-obsidian-300);
  margin-bottom: var(--s-space-5);
  line-height: 1.5;
}

/* Utility Score */
.utility-score {
  margin-bottom: var(--s-space-5);
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--s-space-2);
}

.score-label {
  font-size: 0.75rem;
  color: var(--s-obsidian-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.score-value {
  font-family: var(--s-font-mono);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--s-champagne-500);
}

.score-bar {
  height: 4px;
  background: var(--s-obsidian-700);
  border-radius: 2px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--s-champagne-500), var(--s-champagne-300));
  border-radius: 2px;
  transition: width var(--s-duration-slow) var(--s-ease-out);
}

/* Dimension Scores */
.dimension-scores {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--s-space-2);
  margin-bottom: var(--s-space-5);
}

.dimension {
  text-align: center;
}

.dimension-label {
  font-size: 0.625rem;
  color: var(--s-obsidian-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--s-space-1);
}

.dimension-value {
  font-family: var(--s-font-mono);
  font-size: 0.875rem;
  color: var(--s-obsidian-200);
}

/* Action Steps */
.action-steps {
  margin-bottom: var(--s-space-5);
}

.steps-title {
  font-size: 0.75rem;
  color: var(--s-obsidian-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--s-space-3);
}

.step {
  display: flex;
  align-items: flex-start;
  gap: var(--s-space-3);
  padding: var(--s-space-3);
  background: var(--s-obsidian-850);
  border-radius: 4px;
  margin-bottom: var(--s-space-2);
}

.step-number {
  font-family: var(--s-font-mono);
  font-size: 0.75rem;
  color: var(--s-champagne-500);
  background: var(--s-obsidian-700);
  padding: var(--s-space-1) var(--s-space-2);
  border-radius: 4px;
}

.step-content {
  flex: 1;
}

.step-action {
  font-weight: 500;
  color: var(--s-obsidian-100);
}

.step-action.sell { color: var(--s-negative-500); }
.step-action.buy { color: var(--s-positive-500); }

.step-details {
  font-size: 0.75rem;
  color: var(--s-obsidian-400);
  margin-top: var(--s-space-1);
}

/* Risks */
.risks {
  margin-bottom: var(--s-space-5);
}

.risk-item {
  font-size: 0.75rem;
  color: var(--s-warning-500);
  padding: var(--s-space-1) 0;
  padding-left: var(--s-space-4);
  position: relative;
}

.risk-item::before {
  content: '!';
  position: absolute;
  left: 0;
  font-weight: 600;
}

/* Actions */
.card-actions {
  display: flex;
  gap: var(--s-space-3);
  padding-top: var(--s-space-4);
  border-top: 1px solid var(--s-border-subtle);
}

.btn {
  flex: 1;
  padding: var(--s-space-3) var(--s-space-4);
  font-family: var(--s-font-body);
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--s-duration-fast) var(--s-ease-out);
}

.btn-primary {
  background: var(--s-champagne-500);
  color: var(--s-obsidian-900);
}

.btn-primary:hover {
  background: var(--s-champagne-400);
}

.btn-secondary {
  background: var(--s-obsidian-700);
  color: var(--s-obsidian-200);
}

.btn-secondary:hover {
  background: var(--s-obsidian-600);
}

/* Conflicts Panel */
.conflicts-panel {
  background: var(--s-obsidian-800);
  border: 1px solid var(--s-negative-500);
  border-radius: 8px;
  padding: var(--s-space-6);
  margin-bottom: var(--s-space-8);
}

.conflicts-title {
  font-family: var(--s-font-display);
  font-size: 1.25rem;
  color: var(--s-negative-500);
  margin-bottom: var(--s-space-4);
}

.conflict-item {
  padding: var(--s-space-4);
  background: var(--s-obsidian-850);
  border-radius: 4px;
  margin-bottom: var(--s-space-3);
}

.conflict-type {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--s-warning-500);
  margin-bottom: var(--s-space-2);
}

.conflict-description {
  font-size: 0.875rem;
  color: var(--s-obsidian-200);
  margin-bottom: var(--s-space-3);
}

.conflict-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-space-2);
}

.option-chip {
  font-size: 0.75rem;
  padding: var(--s-space-2) var(--s-space-3);
  background: var(--s-obsidian-700);
  border-radius: 4px;
  color: var(--s-obsidian-300);
  cursor: pointer;
  transition: all var(--s-duration-fast);
}

.option-chip:hover {
  background: var(--s-obsidian-600);
  color: var(--s-obsidian-100);
}

/* Footer */
.canvas-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--s-space-6);
  border-top: 1px solid var(--s-border-subtle);
}

.merkle-hash {
  font-family: var(--s-font-mono);
  font-size: 0.75rem;
  color: var(--s-obsidian-400);
}
"""


# ═══════════════════════════════════════════════════════════════════════════
# CANVAS GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class CanvasGenerator:
    """
    Generates interactive HTML Canvas from CoordinatorOutput.

    The Canvas provides:
    - Scenario cards with utility scores
    - Action step details
    - Conflict warnings
    - Approve/Reject buttons
    - What-if sliders

    Usage:
        generator = CanvasGenerator()
        html = generator.generate(coordinator_output)
    """

    def __init__(self, include_scripts: bool = True):
        """
        Initialize generator.

        Args:
            include_scripts: Include JavaScript for interactivity
        """
        self.include_scripts = include_scripts

    def generate(self, output: CoordinatorOutput) -> str:
        """
        Generate complete HTML Canvas.

        Args:
            output: CoordinatorOutput from Coordinator

        Returns:
            Complete HTML document as string
        """
        html_parts = [
            self._generate_doctype(),
            self._generate_head(output),
            '<body>',
            '<div class="sentinel-canvas">',
            self._generate_header(output),
            self._generate_conflicts(output),
            self._generate_scenarios(output),
            self._generate_footer(output),
            '</div>',
            self._generate_scripts(output) if self.include_scripts else '',
            '</body>',
            '</html>'
        ]

        return '\n'.join(html_parts)

    def _generate_doctype(self) -> str:
        return '<!DOCTYPE html>'

    def _generate_head(self, output: CoordinatorOutput) -> str:
        return f"""
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sentinel Analysis — {output.portfolio_id}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    {DESIGN_TOKENS}
    {BASE_STYLES}
  </style>
</head>
"""

    def _generate_header(self, output: CoordinatorOutput) -> str:
        timestamp = output.analysis_timestamp.strftime('%Y-%m-%d %H:%M UTC')
        return f"""
<header class="canvas-header">
  <div>
    <h1 class="canvas-title">Portfolio Analysis</h1>
    <p class="canvas-subtitle">{output.portfolio_id} • Triggered by {output.trigger_event}</p>
  </div>
  <div class="canvas-meta">
    <div class="meta-label">Analysis Time</div>
    <div class="meta-value">{timestamp}</div>
  </div>
</header>
"""

    def _generate_conflicts(self, output: CoordinatorOutput) -> str:
        if not output.conflicts_detected:
            return ''

        conflict_items = []
        for conflict in output.conflicts_detected:
            options_html = ''.join([
                f'<span class="option-chip" data-option="{i}">{opt}</span>'
                for i, opt in enumerate(conflict.resolution_options)
            ])

            conflict_items.append(f"""
<div class="conflict-item" data-conflict-id="{conflict.conflict_id}">
  <div class="conflict-type">{conflict.conflict_type.replace('_', ' ')}</div>
  <div class="conflict-description">{conflict.description}</div>
  <div class="conflict-options">{options_html}</div>
</div>
""")

        return f"""
<div class="conflicts-panel">
  <h2 class="conflicts-title">⚠ Conflicts Detected ({len(output.conflicts_detected)})</h2>
  {''.join(conflict_items)}
</div>
"""

    def _generate_scenarios(self, output: CoordinatorOutput) -> str:
        scenario_cards = []

        for scenario in output.scenarios:
            is_recommended = scenario.scenario_id == output.recommended_scenario_id
            card_class = 'scenario-card recommended' if is_recommended else 'scenario-card'

            # Utility score
            score_html = ''
            if scenario.utility_score:
                score = scenario.utility_score
                score_html = f"""
<div class="utility-score">
  <div class="score-header">
    <span class="score-label">Utility Score</span>
    <span class="score-value">{score.total_score:.0f}</span>
  </div>
  <div class="score-bar">
    <div class="score-fill" style="width: {score.total_score}%"></div>
  </div>
</div>
<div class="dimension-scores">
  {self._generate_dimension_scores(score)}
</div>
"""

            # Action steps
            steps_html = ''
            if scenario.action_steps:
                steps_items = []
                for step in scenario.action_steps[:4]:  # Limit to 4 steps
                    action_class = step.action.value.lower()
                    steps_items.append(f"""
<div class="step">
  <span class="step-number">{step.step_number}</span>
  <div class="step-content">
    <div class="step-action {action_class}">
      {step.action.value.upper()} {step.quantity:,.0f} {step.ticker}
    </div>
    <div class="step-details">{step.timing} • {step.rationale[:50]}...</div>
  </div>
</div>
""")
                steps_html = f"""
<div class="action-steps">
  <div class="steps-title">Action Steps</div>
  {''.join(steps_items)}
</div>
"""

            # Risks
            risks_html = ''
            if scenario.risks:
                risk_items = ''.join([
                    f'<div class="risk-item">{risk}</div>'
                    for risk in scenario.risks if risk
                ])
                if risk_items:
                    risks_html = f'<div class="risks">{risk_items}</div>'

            # Badge
            badge_html = '<span class="scenario-badge">Recommended</span>' if is_recommended else ''

            scenario_cards.append(f"""
<div class="{card_class}" data-scenario-id="{scenario.scenario_id}">
  <div class="scenario-header">
    <h3 class="scenario-title">{scenario.title}</h3>
    {badge_html}
  </div>
  <p class="scenario-description">{scenario.description}</p>
  {score_html}
  {steps_html}
  {risks_html}
  <div class="card-actions">
    <button class="btn btn-primary" onclick="approveScenario('{scenario.scenario_id}')">
      Approve
    </button>
    <button class="btn btn-secondary" onclick="whatIfScenario('{scenario.scenario_id}')">
      What If...
    </button>
  </div>
</div>
""")

        return f"""
<div class="scenarios-grid">
  {''.join(scenario_cards)}
</div>
"""

    def _generate_dimension_scores(self, score: UtilityScore) -> str:
        dimensions = [
            ('Risk', 'risk_reduction'),
            ('Tax', 'tax_savings'),
            ('Goal', 'goal_alignment'),
            ('Cost', 'transaction_cost'),
            ('Urgency', 'urgency'),
        ]

        html_parts = []
        for label, key in dimensions:
            dim_score = next(
                (d for d in score.dimension_scores if d.dimension == key),
                None
            )
            value = dim_score.raw_score if dim_score else 0

            html_parts.append(f"""
<div class="dimension">
  <div class="dimension-label">{label}</div>
  <div class="dimension-value">{value:.1f}</div>
</div>
""")

        return ''.join(html_parts)

    def _generate_footer(self, output: CoordinatorOutput) -> str:
        hash_display = output.merkle_hash[:16] + '...' if len(output.merkle_hash) > 16 else output.merkle_hash

        return f"""
<footer class="canvas-footer">
  <div class="merkle-hash">Audit Hash: {hash_display}</div>
  <div class="canvas-actions">
    <button class="btn btn-secondary" onclick="exportAnalysis()">Export</button>
  </div>
</footer>
"""

    def _generate_scripts(self, output: CoordinatorOutput) -> str:
        # JSON-safe output data
        scenarios_json = json.dumps([
            {
                'id': s.scenario_id,
                'title': s.title,
            }
            for s in output.scenarios
        ])

        return f"""
<script>
  const portfolioId = '{output.portfolio_id}';
  const scenarios = {scenarios_json};

  function approveScenario(scenarioId) {{
    console.log('Approving scenario:', scenarioId);
    // In production, this would POST to the API
    const action = {{
      action_type: 'approve',
      scenario_id: scenarioId,
      parameters: {{}},
      session_id: 'canvas_session',
      timestamp: new Date().toISOString()
    }};

    // Visual feedback
    const card = document.querySelector(`[data-scenario-id="${{scenarioId}}"]`);
    if (card) {{
      card.style.borderColor = 'var(--s-positive-500)';
      card.querySelector('.btn-primary').textContent = 'Approved ✓';
      card.querySelector('.btn-primary').disabled = true;
    }}

    alert(`Scenario "${{scenarios.find(s => s.id === scenarioId)?.title}}" approved.\\n\\nIn production, this would execute the trades.`);
  }}

  function whatIfScenario(scenarioId) {{
    console.log('What-if for scenario:', scenarioId);
    // In production, this would open a modal with sliders
    alert(`What-If analysis for scenario "${{scenarios.find(s => s.id === scenarioId)?.title}}"\\n\\nThis would show sliders to adjust quantities, timing, etc.`);
  }}

  function exportAnalysis() {{
    console.log('Exporting analysis');
    alert('Export functionality would generate PDF/Excel report.');
  }}

  // Add click handlers for conflict options
  document.querySelectorAll('.option-chip').forEach(chip => {{
    chip.addEventListener('click', () => {{
      const conflictId = chip.closest('.conflict-item').dataset.conflictId;
      const optionIndex = chip.dataset.option;
      console.log('Selected option', optionIndex, 'for conflict', conflictId);

      // Visual feedback
      chip.closest('.conflict-options').querySelectorAll('.option-chip').forEach(c => {{
        c.style.background = 'var(--s-obsidian-700)';
        c.style.color = 'var(--s-obsidian-300)';
      }});
      chip.style.background = 'var(--s-champagne-500)';
      chip.style.color = 'var(--s-obsidian-900)';
    }});
  }});
</script>
"""


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def generate_canvas(output: CoordinatorOutput) -> str:
    """
    Generate Canvas HTML from CoordinatorOutput.

    Args:
        output: CoordinatorOutput from Coordinator

    Returns:
        Complete HTML document
    """
    generator = CanvasGenerator()
    return generator.generate(output)


def save_canvas(output: CoordinatorOutput, filepath: str) -> None:
    """
    Generate and save Canvas HTML to file.

    Args:
        output: CoordinatorOutput from Coordinator
        filepath: Path to save HTML file
    """
    html = generate_canvas(output)
    with open(filepath, 'w') as f:
        f.write(html)

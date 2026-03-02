"""
SENTINEL V2 — LLM-Powered Debate Runner

Orchestrates multi-round debate between agents using Claude API calls.
Each agent gets a prompt with the question, findings, and prior arguments,
then Claude generates a contextual argument. Falls back to template debate on failure.
"""

import asyncio
import json
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Debate turn configurations
DEBATE_TURNS = [
    {"agent_id": "drift", "agent_name": "Drift Agent", "phase": "opening", "role": "drift analysis specialist"},
    {"agent_id": "tax", "agent_name": "Tax Agent", "phase": "opening", "role": "tax optimization specialist"},
    {"agent_id": "drift", "agent_name": "Drift Agent", "phase": "rebuttal", "role": "drift analysis specialist"},
    {"agent_id": "tax", "agent_name": "Tax Agent", "phase": "rebuttal", "role": "tax optimization specialist"},
    {"agent_id": "coordinator", "agent_name": "Coordinator", "phase": "synthesis", "role": "portfolio coordinator synthesizing both perspectives"},
]


def _build_findings_summary(drift_findings, tax_findings) -> dict:
    """Extract concise summaries from agent findings for debate prompts."""
    drift_summary_parts = []
    for r in drift_findings.concentration_risks:
        severity = r.severity.value if hasattr(r.severity, 'value') else str(r.severity)
        drift_summary_parts.append(
            f"{r.ticker} at {r.current_weight:.1%} (limit {r.limit:.0%}, {severity})"
        )
    if drift_findings.recommended_trades:
        t = drift_findings.recommended_trades[0]
        drift_summary_parts.append(
            f"Recommends {t.action.value} {t.quantity:,.0f} shares of {t.ticker}"
        )

    tax_summary_parts = []
    for w in tax_findings.wash_sale_violations:
        tax_summary_parts.append(
            f"Wash sale risk: {w.ticker} sold {w.days_since_sale} days ago, "
            f"${w.disallowed_loss:,.0f} deduction at risk"
        )
    for o in tax_findings.tax_opportunities[:2]:
        opp_type = o.opportunity_type.value if hasattr(o.opportunity_type, 'value') else str(o.opportunity_type)
        tax_summary_parts.append(
            f"Tax opportunity: {o.ticker} — {opp_type}, ~${o.estimated_benefit:,.0f} benefit"
        )

    return {
        "drift": "; ".join(drift_summary_parts) or "No significant drift detected",
        "tax": "; ".join(tax_summary_parts) or "No tax concerns identified",
    }


def _build_prompt(turn: dict, question: str, findings: dict, history: list[dict]) -> str:
    """Build the debate prompt for a single turn."""
    agent_id = turn["agent_id"]
    role = turn["role"]
    phase = turn["phase"]

    # Select which findings this agent owns
    if agent_id == "drift":
        own_findings = findings["drift"]
        other_findings = findings["tax"]
    elif agent_id == "tax":
        own_findings = findings["tax"]
        other_findings = findings["drift"]
    else:
        own_findings = f"Drift: {findings['drift']}\nTax: {findings['tax']}"
        other_findings = ""

    history_text = ""
    if history:
        history_text = "\n".join(
            f"- {h['agent_name']} ({h['phase']}): {h['message']}"
            for h in history
        )

    phase_instruction = {
        "opening": "Present your initial position clearly. State your key concern and recommendation.",
        "rebuttal": "Respond to the other agent's arguments. Acknowledge valid points but defend your position or propose a compromise.",
        "synthesis": "Synthesize both perspectives into a unified recommendation. Identify the best path forward that balances risk and tax concerns.",
    }[phase]

    return f"""You are the {role} in a UHNW portfolio management debate.

Question: {question}

Your analysis found: {own_findings}
{"Other agent's findings: " + other_findings if other_findings else ""}

{"Previous arguments:" if history_text else ""}
{history_text}

Phase: {phase}
Instruction: {phase_instruction}

Respond with ONLY a JSON object (no markdown, no backticks):
{{"message": "your argument (2-3 sentences, direct and specific)", "confidence": <int 70-98>, "key_points": ["point1", "point2", "point3"], "position": "for"|"against"|"neutral"}}"""


class DebateRunner:
    """Orchestrates LLM-powered multi-round debate between agents."""

    def __init__(self, api_key: str, model: str, ws_manager):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.ws_manager = ws_manager

    async def run_debate(self, question: str, drift_findings, tax_findings, portfolio):
        """Run multi-round LLM debate, streaming messages via WebSocket."""
        findings = _build_findings_summary(drift_findings, tax_findings)
        history: list[dict] = []
        current_phase = None

        for turn in DEBATE_TURNS:
            phase = turn["phase"]

            # Send phase change if new phase
            if phase != current_phase:
                current_phase = phase
                await self.ws_manager.send_debate_phase(phase, question)
                await asyncio.sleep(0.3)

            # Build prompt and call Claude
            prompt = _build_prompt(turn, question, findings, history)
            response = await self._call_llm(prompt)

            if response is None:
                raise RuntimeError(f"LLM call failed for {turn['agent_name']} {phase}")

            # Build debate message
            message = {
                "agent_id": turn["agent_id"],
                "agent_name": turn["agent_name"],
                "phase": phase,
                "position": response.get("position", "neutral"),
                "message": response.get("message", ""),
                "confidence": response.get("confidence", 85),
                "key_points": response.get("key_points", []),
            }

            # Track history for subsequent turns
            history.append(message)

            # Send to frontend
            await self.ws_manager.send_debate_message(message)
            await asyncio.sleep(1.0)

        # Send consensus phase
        await self.ws_manager.send_debate_phase("consensus", question)
        await asyncio.sleep(0.3)

        # Build consensus from the synthesis message
        synthesis = history[-1] if history else {}
        await self.ws_manager.broadcast({
            "type": "debate_consensus",
            "data": {
                "consensus_reached": True,
                "agreements": {"drift": True, "tax": True},
                "final_decision": synthesis.get("message", "Agents reached consensus"),
                "key_points": synthesis.get("key_points", []),
            }
        })

    async def _call_llm(self, prompt: str) -> dict | None:
        """Make a single Claude API call and parse JSON response."""
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=300,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()

            # Handle potential markdown wrapping
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            return json.loads(text)

        except Exception as e:
            logger.error(f"Debate LLM call failed: {e}")
            return None

"""
SENTINEL SKILL REGISTRY

Dynamic skill injection for context-aware agent prompts.

Skills are loaded lazily based on context to save tokens.
Only relevant skills are injected into agent prompts.

Reference: docs/Sentinel Architecture Specification §5
Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.4
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable
from enum import Enum


from src.contracts.interfaces import ISkillRegistry


# ═══════════════════════════════════════════════════════════════════════════
# SKILL TRIGGERS
# ═══════════════════════════════════════════════════════════════════════════

class SkillTrigger(str, Enum):
    """Conditions that trigger skill loading."""
    CONCENTRATION_RISK = "concentration_risk"
    WASH_SALE = "wash_sale"
    TAX_LOSS_HARVEST = "tax_loss_harvest"
    REBALANCE = "rebalance"
    MARKET_EVENT = "market_event"
    SECTOR_ANALYSIS = "sector_analysis"
    LOT_SELECTION = "lot_selection"


# ═══════════════════════════════════════════════════════════════════════════
# SKILL METADATA
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    name: str
    description: str
    triggers: list[SkillTrigger]
    token_cost: int
    priority: int = 5  # Higher priority = loaded first
    content: str = ""  # Inline content or loaded from file


# ═══════════════════════════════════════════════════════════════════════════
# BUILT-IN SKILLS
# ═══════════════════════════════════════════════════════════════════════════

CONCENTRATION_RISK_SKILL = """## Concentration Risk Analysis

When a position exceeds the client's concentration limit:

1. **Identify the Risk**
   - Calculate exact percentage over limit
   - Assess historical volatility of the position
   - Consider correlation with other holdings

2. **Severity Assessment**
   - Low: 0-2% over limit
   - Medium: 2-5% over limit
   - High: 5-10% over limit
   - Critical: >10% over limit

3. **Recommendation Framework**
   - For Low severity: Monitor, consider gradual reduction
   - For Medium severity: Plan reduction over 2-4 weeks
   - For High severity: Recommend immediate partial reduction
   - For Critical severity: Urgent action required

4. **Execution Considerations**
   - Check for tax lot optimization opportunities
   - Consider market impact for large positions
   - Identify substitute securities for sector exposure
   - Factor in client's tax sensitivity

5. **Substitute Identification**
   - Same sector, similar market cap
   - Avoid substantially identical securities (wash sale risk)
   - Consider ETFs for broader exposure
   - Check correlation to maintain portfolio characteristics
"""

WASH_SALE_SKILL = """## Wash Sale Rules (IRS Section 1091)

A wash sale occurs when you:
1. Sell a security at a loss
2. Buy the same or "substantially identical" security
3. Within 31 days BEFORE or AFTER the sale

### Key Rules

**31-Day Window**
- 31 days before the sale
- The day of the sale
- 31 days after the sale
- Total window: 61 days

**Substantially Identical**
- Same stock or bond
- Options or contracts for same security
- Mutual funds tracking same index (grey area)
- ETFs with same holdings (depends on similarity)

**Consequences**
- Loss is disallowed (cannot deduct)
- Disallowed loss added to cost basis of new shares
- Holding period of old shares carries over

### Safe Alternatives

To maintain market exposure while avoiding wash sale:
1. Buy different company in same sector
2. Buy sector ETF instead of individual stock
3. Wait 31 days before repurchasing
4. Buy before selling and wait 31 days

### Calculation

```
Disallowed Loss = Sale Loss × (Replacement Shares / Sold Shares)
New Cost Basis = Purchase Price + Disallowed Loss per Share
```
"""

TAX_LOSS_HARVEST_SKILL = """## Tax-Loss Harvesting Strategy

### Opportunity Identification

1. **Screen Holdings for Losses**
   - Current market value < cost basis
   - Sufficient loss to warrant transaction costs
   - Not in wash sale window from prior transaction

2. **Prioritize by Value**
   - Larger losses first
   - Short-term losses (offset ordinary income first)
   - Long-term losses (offset long-term gains at lower rate)

### Tax Benefit Calculation

**For UHNW Clients (assume highest brackets)**
- Short-term gains/losses: 40.8% (37% + 3.8% NIIT)
- Long-term gains/losses: 23.8% (20% + 3.8% NIIT)

**Annual Limits**
- Unlimited losses can offset capital gains
- Up to $3,000 net loss against ordinary income
- Excess losses carry forward indefinitely

### Execution Strategy

1. **Identify Position to Harvest**
   - Calculate unrealized loss
   - Check holding period (short vs long term)
   - Verify no recent purchases (wash sale window)

2. **Select Replacement Security**
   - Different ticker, similar exposure
   - Not substantially identical
   - Maintains portfolio allocation targets

3. **Execute and Document**
   - Sell loss position
   - Immediately buy replacement
   - Document for tax records

### Year-End Considerations

- Harvest before December 31 for current year benefit
- Consider future capital gain expectations
- Balance tax efficiency with investment goals
"""

LOT_SELECTION_SKILL = """## Tax Lot Selection Strategies

### Available Methods

**FIFO (First In, First Out)**
- Default method if none specified
- Sells oldest shares first
- May result in higher gains (older = lower cost basis typically)

**LIFO (Last In, First Out)**
- Sells newest shares first
- May help with short-term vs long-term classification
- Generally less common

**HIFO (Highest In, First Out)**
- Sells highest cost basis first
- Minimizes capital gains
- Often optimal for tax efficiency

**Specific Identification**
- Choose exact lots to sell
- Maximum control over tax outcome
- Requires proper documentation

### Decision Framework

| Goal | Best Method |
|------|-------------|
| Minimize current taxes | HIFO |
| Preserve long-term lots | Specific ID |
| Simple accounting | FIFO |
| Harvest specific losses | Specific ID |

### Implementation Notes

1. Must elect specific ID before sale
2. Broker must confirm lot in writing
3. Cannot change method after trade settles
4. Keep records of all lot selections
"""

REBALANCE_SKILL = """## Portfolio Rebalancing Guidelines

### Trigger Thresholds

- **Percentage-based**: Rebalance when any asset class drifts >5% from target
- **Calendar-based**: Review quarterly regardless of drift
- **Tactical**: Respond to significant market events

### Execution Sequence

1. **Calculate Drift**
   - Current weight vs target for each asset class
   - Absolute drift (percentage points)
   - Relative drift (% of target)

2. **Prioritize Actions**
   - Address largest drifts first
   - Consider tax implications
   - Factor in transaction costs

3. **Minimize Transactions**
   - Use new contributions when possible
   - Harvest losses opportunistically
   - Batch trades for efficiency

### Tax-Aware Rebalancing

- Sell overweight positions with losses first
- Use specific lot identification
- Consider wash sale implications
- Avoid short-term gains when possible

### Cash Flow Integration

- Direct dividends to underweight assets
- Use new deposits for rebalancing
- Avoid selling just to rebalance
"""

SECTOR_ANALYSIS_SKILL = """## Sector Exposure Analysis

### Sector Classification (GICS)

1. Information Technology
2. Health Care
3. Financials
4. Consumer Discretionary
5. Communication Services
6. Industrials
7. Consumer Staples
8. Energy
9. Utilities
10. Real Estate
11. Materials

### Analysis Framework

**Concentration Check**
- Any single sector >25% = high concentration
- Compare to benchmark (S&P 500 weights)
- Consider correlation between sectors

**Risk Assessment**
- Cyclical vs defensive mix
- Interest rate sensitivity
- Economic cycle positioning

### Sector Substitutes

When reducing concentration, consider:
- Same sector ETF for broad exposure
- Competitor in same industry
- Adjacent sector with correlation
- Factor-based alternatives

### Event-Driven Considerations

- Regulatory changes (Healthcare, Financials)
- Commodity prices (Energy, Materials)
- Interest rates (Financials, Real Estate, Utilities)
- Consumer sentiment (Discretionary, Staples)
"""


# ═══════════════════════════════════════════════════════════════════════════
# SKILL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

class SkillRegistry(ISkillRegistry):
    """
    Dynamic skill registry with context-aware loading.

    Loads only relevant skills into agent context to save tokens.
    Skills can be built-in or loaded from external files.

    Usage:
        registry = SkillRegistry()

        # Discover relevant skills for context
        context = {"holdings": portfolio.holdings}
        skills = registry.discover_relevant_skills(context, token_budget=5000)

        # Load and inject into prompt
        skill_content = registry.get_skill_content(skills)
        prompt = base_prompt + "\\n\\nRELEVANT SKILLS:\\n" + skill_content
    """

    def __init__(
        self,
        skills_path: Optional[Path] = None,
        load_builtins: bool = True
    ):
        """
        Initialize skill registry.

        Args:
            skills_path: Path to external skills directory (optional)
            load_builtins: Whether to load built-in skills
        """
        self._skills: dict[str, SkillMetadata] = {}
        self._skills_path = skills_path

        if load_builtins:
            self._load_builtin_skills()

        if skills_path and skills_path.exists():
            self._load_external_skills()

    def _load_builtin_skills(self) -> None:
        """Load built-in skills for Sentinel."""
        builtins = [
            SkillMetadata(
                name="concentration_risk",
                description="Analyze and manage position concentration risks",
                triggers=[SkillTrigger.CONCENTRATION_RISK],
                token_cost=800,
                priority=10,
                content=CONCENTRATION_RISK_SKILL
            ),
            SkillMetadata(
                name="wash_sale",
                description="IRS wash sale rules and compliance",
                triggers=[SkillTrigger.WASH_SALE],
                token_cost=700,
                priority=9,
                content=WASH_SALE_SKILL
            ),
            SkillMetadata(
                name="tax_loss_harvest",
                description="Tax-loss harvesting strategy and execution",
                triggers=[SkillTrigger.TAX_LOSS_HARVEST],
                token_cost=750,
                priority=8,
                content=TAX_LOSS_HARVEST_SKILL
            ),
            SkillMetadata(
                name="lot_selection",
                description="Tax lot selection strategies (FIFO, LIFO, HIFO)",
                triggers=[SkillTrigger.LOT_SELECTION],
                token_cost=500,
                priority=7,
                content=LOT_SELECTION_SKILL
            ),
            SkillMetadata(
                name="rebalance",
                description="Portfolio rebalancing guidelines",
                triggers=[SkillTrigger.REBALANCE],
                token_cost=600,
                priority=6,
                content=REBALANCE_SKILL
            ),
            SkillMetadata(
                name="sector_analysis",
                description="Sector exposure and substitution analysis",
                triggers=[SkillTrigger.SECTOR_ANALYSIS, SkillTrigger.MARKET_EVENT],
                token_cost=650,
                priority=5,
                content=SECTOR_ANALYSIS_SKILL
            ),
        ]

        for skill in builtins:
            self._skills[skill.name] = skill

    def _load_external_skills(self) -> None:
        """Load skills from external directory."""
        if not self._skills_path:
            return

        for skill_dir in self._skills_path.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        metadata = self._parse_skill_file(skill_file)
                        self._skills[metadata.name] = metadata
                    except Exception:
                        pass  # Skip invalid skills

    def _parse_skill_file(self, skill_file: Path) -> SkillMetadata:
        """Parse a SKILL.md file into SkillMetadata."""
        content = skill_file.read_text()
        lines = content.split("\n")

        # Parse YAML-like header
        name = skill_file.parent.name
        description = ""
        triggers = []
        token_cost = 1000
        priority = 5

        in_header = False
        header_end = 0

        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_header:
                    in_header = True
                else:
                    header_end = i + 1
                    break
            elif in_header:
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
                elif line.startswith("triggers:"):
                    trigger_str = line.split(":", 1)[1].strip()
                    triggers = [
                        SkillTrigger(t.strip())
                        for t in trigger_str.split(",")
                        if t.strip() in [e.value for e in SkillTrigger]
                    ]
                elif line.startswith("token_cost:"):
                    token_cost = int(line.split(":", 1)[1].strip())
                elif line.startswith("priority:"):
                    priority = int(line.split(":", 1)[1].strip())

        skill_content = "\n".join(lines[header_end:])

        return SkillMetadata(
            name=name,
            description=description,
            triggers=triggers,
            token_cost=token_cost,
            priority=priority,
            content=skill_content
        )

    def discover_relevant_skills(
        self,
        context: dict,
        token_budget: int = 10_000
    ) -> list[str]:
        """
        Discover skills relevant to current context.

        Args:
            context: Current analysis context including:
                - holdings: List of Holding objects
                - recent_transactions: List of Transaction objects
                - market_event: Market event dict (optional)
                - concentration_limit: Client's limit (optional)

        Returns:
            List of skill names to inject (sorted by priority)
        """
        relevant = []
        holdings = context.get("holdings", [])
        transactions = context.get("recent_transactions", [])
        market_event = context.get("market_event")
        concentration_limit = context.get("concentration_limit", 0.15)

        for skill_name, skill in self._skills.items():
            is_relevant = False

            for trigger in skill.triggers:
                if trigger == SkillTrigger.CONCENTRATION_RISK:
                    # Check if any position exceeds concentration limit
                    if holdings:
                        max_weight = max(
                            (getattr(h, "portfolio_weight", 0) for h in holdings),
                            default=0
                        )
                        if max_weight > concentration_limit:
                            is_relevant = True

                elif trigger == SkillTrigger.WASH_SALE:
                    # Check if there are recent sales
                    if transactions:
                        from src.contracts.schemas import TradeAction
                        recent_sales = [
                            t for t in transactions
                            if getattr(t, "action", None) == TradeAction.SELL
                        ]
                        if recent_sales:
                            is_relevant = True

                elif trigger == SkillTrigger.TAX_LOSS_HARVEST:
                    # Check for unrealized losses
                    if holdings:
                        has_losses = any(
                            getattr(h, "unrealized_gain_loss", 0) < 0
                            for h in holdings
                        )
                        if has_losses:
                            is_relevant = True

                elif trigger == SkillTrigger.LOT_SELECTION:
                    # Relevant when selling positions with multiple lots
                    if holdings:
                        has_multiple_lots = any(
                            len(getattr(h, "tax_lots", [])) > 1
                            for h in holdings
                        )
                        if has_multiple_lots:
                            is_relevant = True

                elif trigger == SkillTrigger.REBALANCE:
                    # Always relevant for drift analysis
                    is_relevant = True

                elif trigger == SkillTrigger.MARKET_EVENT:
                    if market_event:
                        is_relevant = True

                elif trigger == SkillTrigger.SECTOR_ANALYSIS:
                    # Relevant when market event affects sectors
                    if market_event and market_event.get("affected_sectors"):
                        is_relevant = True

            if is_relevant:
                relevant.append((skill.priority, skill.token_cost, skill_name))

        # Sort by priority (descending) and filter by token budget
        relevant.sort(key=lambda x: -x[0])

        selected = []
        total_tokens = 0

        for priority, cost, name in relevant:
            if total_tokens + cost <= token_budget:
                selected.append(name)
                total_tokens += cost

        return selected

    def load_skill(self, skill_name: str) -> str:
        """
        Load skill content by name.

        Args:
            skill_name: Name of skill to load

        Returns:
            Skill content as string

        Raises:
            KeyError: If skill not found
        """
        if skill_name not in self._skills:
            raise KeyError(f"Skill '{skill_name}' not found")

        return self._skills[skill_name].content

    def list_skills(self) -> list[dict]:
        """
        List all available skills with metadata.

        Returns:
            List of skill metadata dicts
        """
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "triggers": [t.value for t in skill.triggers],
                "token_cost": skill.token_cost,
                "priority": skill.priority
            }
            for skill in self._skills.values()
        ]

    def get_skill_content(self, skill_names: list[str]) -> str:
        """
        Get combined content for multiple skills.

        Args:
            skill_names: List of skill names to load

        Returns:
            Combined skill content formatted for prompt injection
        """
        contents = []
        for name in skill_names:
            try:
                content = self.load_skill(name)
                contents.append(content)
            except KeyError:
                pass

        return "\n\n".join(contents)

    def register_skill(self, skill: SkillMetadata) -> None:
        """
        Register a new skill dynamically.

        Args:
            skill: SkillMetadata to register
        """
        self._skills[skill.name] = skill

    def unregister_skill(self, skill_name: str) -> None:
        """
        Unregister a skill.

        Args:
            skill_name: Name of skill to remove
        """
        if skill_name in self._skills:
            del self._skills[skill_name]

    def get_total_token_cost(self, skill_names: list[str]) -> int:
        """
        Get total token cost for a list of skills.

        Args:
            skill_names: List of skill names

        Returns:
            Total token cost
        """
        return sum(
            self._skills[name].token_cost
            for name in skill_names
            if name in self._skills
        )


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get or create default skill registry."""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry


def inject_skills_into_prompt(
    base_prompt: str,
    context: dict,
    token_budget: int = 5000
) -> str:
    """
    Inject relevant skills into a prompt.

    Args:
        base_prompt: The base agent prompt
        context: Current analysis context
        token_budget: Maximum tokens for skills

    Returns:
        Enhanced prompt with relevant skills
    """
    registry = get_skill_registry()
    skill_names = registry.discover_relevant_skills(context, token_budget)

    if not skill_names:
        return base_prompt

    skill_content = registry.get_skill_content(skill_names)

    return f"""{base_prompt}

═══════════════════════════════════════════════════════════════════════════
RELEVANT SKILLS (Context-Injected)
═══════════════════════════════════════════════════════════════════════════

{skill_content}"""

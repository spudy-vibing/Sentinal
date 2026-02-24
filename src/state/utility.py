"""
SENTINEL UTILITY FUNCTION

5-dimensional scoring system for recommendation ranking.

Dimensions:
- Risk Reduction: How well does this reduce portfolio risk?
- Tax Savings: Net tax impact (positive = savings)
- Goal Alignment: Alignment with client's investment goals
- Transaction Cost: Cost efficiency (higher = lower cost)
- Urgency: Time-sensitivity of action

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.6
"""

from __future__ import annotations

import logging
from typing import Optional
from dataclasses import dataclass

from src.contracts.interfaces import IUtilityFunction
from src.contracts.schemas import (
    Scenario,
    Portfolio,
    UtilityWeights,
    UtilityScore,
    DimensionScore,
    RiskProfile,
    TradeAction,
    UTILITY_WEIGHTS_BY_PROFILE,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SCORING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ScoringConfig:
    """Configuration for utility scoring."""
    # Risk thresholds
    concentration_limit: float = 0.15
    max_sector_weight: float = 0.30

    # Tax parameters
    wash_sale_penalty: float = 2.0  # Points deducted per wash sale
    harvest_bonus: float = 1.5  # Points added per harvest opportunity

    # Cost parameters
    estimated_commission_rate: float = 0.001  # 0.1% per trade
    min_cost_threshold: float = 100  # Below this, cost score is 10

    # Urgency parameters
    critical_urgency_threshold: int = 8
    high_urgency_threshold: int = 6


# ═══════════════════════════════════════════════════════════════════════════
# DIMENSION SCORERS
# ═══════════════════════════════════════════════════════════════════════════

class RiskScorer:
    """Score risk reduction dimension."""

    @staticmethod
    def score(
        scenario: Scenario,
        portfolio: Portfolio,
        config: ScoringConfig
    ) -> float:
        """
        Score risk reduction (0-10).

        Higher score = better risk reduction.
        """
        score = 5.0  # Baseline
        expected = scenario.expected_outcomes

        # Check concentration reduction
        concentration_before = expected.get("concentration_before", 0)
        concentration_after = expected.get("concentration_after", 0)

        if concentration_before > config.concentration_limit:
            # Reward for reducing concentration
            reduction = concentration_before - concentration_after
            if concentration_after <= config.concentration_limit:
                score += 3.0  # Full compliance achieved
            else:
                score += min(2.0, reduction * 20)  # Partial credit

        # Check diversification improvement
        diversification_delta = expected.get("diversification_delta", 0)
        score += min(1.0, diversification_delta * 10)

        # Penalize for introducing new risks
        new_risks = len(scenario.risks)
        if new_risks > 0:
            score -= min(2.0, new_risks * 0.5)

        # Check sector exposure normalization
        sector_improvement = expected.get("sector_improvement", 0)
        score += min(1.0, sector_improvement * 5)

        return max(0.0, min(10.0, score))


class TaxScorer:
    """Score tax savings dimension."""

    @staticmethod
    def score(
        scenario: Scenario,
        portfolio: Portfolio,
        config: ScoringConfig
    ) -> float:
        """
        Score tax savings (0-10).

        Higher score = better tax outcome.
        """
        score = 5.0  # Baseline
        expected = scenario.expected_outcomes

        # Direct tax impact
        tax_impact = expected.get("tax_impact", 0)
        if tax_impact < 0:
            # Tax savings (negative impact = good)
            score += min(3.0, abs(tax_impact) / 5000)
        else:
            # Tax cost
            score -= min(3.0, tax_impact / 5000)

        # Wash sale violations
        wash_sale_count = expected.get("wash_sale_violations", 0)
        score -= wash_sale_count * config.wash_sale_penalty

        # Tax loss harvesting opportunities captured
        harvest_count = expected.get("harvest_opportunities_captured", 0)
        score += harvest_count * config.harvest_bonus

        # Long-term vs short-term gains
        lt_gains = expected.get("long_term_gains", 0)
        st_gains = expected.get("short_term_gains", 0)
        if lt_gains > 0 and st_gains > 0:
            # Prefer long-term gains (lower tax rate)
            lt_ratio = lt_gains / (lt_gains + st_gains)
            score += (lt_ratio - 0.5) * 2  # Bonus/penalty based on ratio

        return max(0.0, min(10.0, score))


class GoalScorer:
    """Score goal alignment dimension."""

    @staticmethod
    def score(
        scenario: Scenario,
        portfolio: Portfolio,
        config: ScoringConfig
    ) -> float:
        """
        Score goal alignment (0-10).

        Higher score = better alignment with client goals.
        """
        score = 5.0  # Baseline
        expected = scenario.expected_outcomes
        client = portfolio.client_profile

        # Allocation drift correction
        drift_before = expected.get("drift_before", 0)
        drift_after = expected.get("drift_after", 0)

        if drift_before > 0:
            drift_reduction = drift_before - drift_after
            score += min(2.5, drift_reduction / drift_before * 2.5)

        # Target allocation alignment
        target_alignment = expected.get("target_alignment", 0.5)
        score += (target_alignment - 0.5) * 4  # -2 to +2

        # Risk profile alignment
        risk_alignment = expected.get("risk_profile_alignment", 0.5)
        if client.risk_tolerance == RiskProfile.CONSERVATIVE:
            # Conservative clients care more about risk alignment
            score += (risk_alignment - 0.5) * 3
        else:
            score += (risk_alignment - 0.5) * 2

        # Income/growth preference alignment
        income_preference = expected.get("income_alignment", 0)
        growth_preference = expected.get("growth_alignment", 0)

        if client.risk_tolerance == RiskProfile.CONSERVATIVE:
            score += income_preference * 0.5
        elif client.risk_tolerance == RiskProfile.AGGRESSIVE:
            score += growth_preference * 0.5

        return max(0.0, min(10.0, score))


class CostScorer:
    """Score transaction cost dimension."""

    @staticmethod
    def score(
        scenario: Scenario,
        portfolio: Portfolio,
        config: ScoringConfig
    ) -> float:
        """
        Score transaction cost efficiency (0-10).

        Higher score = lower transaction cost.
        """
        # Calculate total trade value
        total_value = 0
        for step in scenario.action_steps:
            if step.action in [TradeAction.BUY, TradeAction.SELL]:
                holding = portfolio.get_holding(step.ticker)
                price = holding.current_price if holding else 0
                total_value += step.quantity * price

        # Estimate total costs
        commission_cost = total_value * config.estimated_commission_rate
        spread_cost = total_value * 0.0005  # Estimated 5bp spread
        total_cost = commission_cost + spread_cost

        # Add any explicit costs from expected outcomes
        explicit_costs = scenario.expected_outcomes.get("transaction_costs", 0)
        total_cost += explicit_costs

        # Score inversely proportional to cost
        if total_cost <= config.min_cost_threshold:
            return 10.0

        # Scale: $100 = 10, $1000 = 8, $10000 = 5, $50000 = 2
        import math
        score = 10 - math.log10(max(1, total_cost / config.min_cost_threshold)) * 2.5

        return max(0.0, min(10.0, score))


class UrgencyScorer:
    """Score urgency dimension."""

    @staticmethod
    def score(
        scenario: Scenario,
        portfolio: Portfolio,
        config: ScoringConfig
    ) -> float:
        """
        Score urgency alignment (0-10).

        Higher score = better urgency match.

        Scenarios that address urgent issues score higher.
        Non-urgent actions on urgent issues score lower.
        """
        expected = scenario.expected_outcomes

        # Base urgency from scenario
        scenario_urgency = expected.get("urgency_level", 5)

        # Check if scenario addresses urgent issues
        addresses_urgent = expected.get("addresses_urgent_issues", False)
        issue_urgency = expected.get("issue_urgency", 5)

        if addresses_urgent and issue_urgency >= config.critical_urgency_threshold:
            # Scenario addresses critical issues - reward proportionally
            return min(10.0, 6.0 + issue_urgency * 0.4)

        if addresses_urgent and issue_urgency >= config.high_urgency_threshold:
            # Addresses high urgency issues
            return min(10.0, 5.0 + issue_urgency * 0.3)

        # Moderate urgency handling
        if scenario_urgency >= config.high_urgency_threshold:
            return 7.0 + (scenario_urgency - config.high_urgency_threshold) * 0.5

        # Low urgency - baseline scoring
        return 5.0 + (scenario_urgency - 5) * 0.2


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

class UtilityFunction(IUtilityFunction):
    """
    5-dimensional utility scoring for recommendation ranking.

    Implements weighted scoring across:
    - Risk Reduction
    - Tax Savings
    - Goal Alignment
    - Transaction Cost
    - Urgency

    Weights vary by client risk profile (see UTILITY_WEIGHTS_BY_PROFILE).
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        """
        Initialize utility function.

        Args:
            config: Scoring configuration (default: ScoringConfig())
        """
        self.config = config or ScoringConfig()

        # Individual scorers
        self._risk_scorer = RiskScorer()
        self._tax_scorer = TaxScorer()
        self._goal_scorer = GoalScorer()
        self._cost_scorer = CostScorer()
        self._urgency_scorer = UrgencyScorer()

    def score_scenario(
        self,
        scenario: Scenario,
        portfolio: Portfolio,
        weights: UtilityWeights
    ) -> UtilityScore:
        """
        Score a single scenario.

        Args:
            scenario: Scenario to score
            portfolio: Portfolio context
            weights: Dimension weights (from client profile)

        Returns:
            UtilityScore with breakdown
        """
        # Calculate raw scores for each dimension
        raw_scores = {
            "risk_reduction": self._risk_scorer.score(scenario, portfolio, self.config),
            "tax_savings": self._tax_scorer.score(scenario, portfolio, self.config),
            "goal_alignment": self._goal_scorer.score(scenario, portfolio, self.config),
            "transaction_cost": self._cost_scorer.score(scenario, portfolio, self.config),
            "urgency": self._urgency_scorer.score(scenario, portfolio, self.config),
        }

        logger.debug(
            f"Scenario {scenario.scenario_id} raw scores: "
            f"risk={raw_scores['risk_reduction']:.1f}, "
            f"tax={raw_scores['tax_savings']:.1f}, "
            f"goal={raw_scores['goal_alignment']:.1f}, "
            f"cost={raw_scores['transaction_cost']:.1f}, "
            f"urgency={raw_scores['urgency']:.1f}"
        )

        # Calculate weighted utility score
        return UtilityScore.calculate(
            scenario_id=scenario.scenario_id,
            raw_scores=raw_scores,
            weights=weights,
            rank=1  # Will be updated during ranking
        )

    def rank_scenarios(
        self,
        scenarios: list[Scenario],
        portfolio: Portfolio,
        weights: UtilityWeights
    ) -> list[UtilityScore]:
        """
        Score and rank multiple scenarios.

        Args:
            scenarios: Scenarios to rank
            portfolio: Portfolio context
            weights: Dimension weights

        Returns:
            List of UtilityScores, sorted by total_score descending
        """
        if not scenarios:
            return []

        # Score all scenarios
        scores = [
            self.score_scenario(scenario, portfolio, weights)
            for scenario in scenarios
        ]

        # Sort by total score (descending)
        sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)

        # Update ranks
        ranked_scores = []
        for i, score in enumerate(sorted_scores, start=1):
            ranked_score = UtilityScore(
                scenario_id=score.scenario_id,
                dimension_scores=score.dimension_scores,
                total_score=score.total_score,
                rank=i
            )
            ranked_scores.append(ranked_score)

        logger.info(
            f"Ranked {len(ranked_scores)} scenarios. "
            f"Top: {ranked_scores[0].scenario_id} ({ranked_scores[0].total_score:.1f}/100)"
        )

        return ranked_scores


# ═══════════════════════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class UtilityFunctionFactory:
    """Factory for creating utility functions with client-specific weights."""

    @staticmethod
    def create(
        risk_profile: Optional[RiskProfile] = None,
        custom_config: Optional[ScoringConfig] = None
    ) -> UtilityFunction:
        """
        Create utility function.

        Args:
            risk_profile: Client risk profile for default weights
            custom_config: Optional custom scoring config

        Returns:
            Configured UtilityFunction
        """
        return UtilityFunction(config=custom_config)

    @staticmethod
    def get_weights_for_profile(risk_profile: RiskProfile) -> UtilityWeights:
        """
        Get default utility weights for a risk profile.

        Args:
            risk_profile: Client risk profile

        Returns:
            UtilityWeights for the profile
        """
        return UTILITY_WEIGHTS_BY_PROFILE.get(
            risk_profile,
            UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.MODERATE_GROWTH]
        )


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def score_and_rank(
    scenarios: list[Scenario],
    portfolio: Portfolio,
    risk_profile: Optional[RiskProfile] = None
) -> list[UtilityScore]:
    """
    Convenience function to score and rank scenarios.

    Args:
        scenarios: Scenarios to rank
        portfolio: Portfolio context
        risk_profile: Override risk profile (default: use portfolio's)

    Returns:
        Ranked list of UtilityScores
    """
    # Get weights from profile
    profile = risk_profile or portfolio.client_profile.risk_tolerance
    weights = UtilityFunctionFactory.get_weights_for_profile(profile)

    # Create and run utility function
    utility_fn = UtilityFunction()
    return utility_fn.rank_scenarios(scenarios, portfolio, weights)

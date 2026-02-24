"""
Tests for Sentinel State Machine and Utility Function.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Steps 2.5-2.6
"""

import pytest
from datetime import datetime, timezone

from src.contracts.schemas import (
    SystemState,
    Scenario,
    ActionStep,
    TradeAction,
    UtilityWeights,
    Portfolio,
    Holding,
    TargetAllocation,
    ClientProfile,
    RiskProfile,
    UTILITY_WEIGHTS_BY_PROFILE,
)
from src.state.machine import (
    SentinelStateMachine,
    StateTransition,
    StateMachineFactory,
    InvalidTransitionError,
)
from src.state.utility import (
    UtilityFunction,
    UtilityFunctionFactory,
    ScoringConfig,
    score_and_rank,
)


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def state_machine():
    """Create a fresh state machine."""
    return SentinelStateMachine(session_id="test-session-001")


@pytest.fixture
def state_machine_with_merkle(merkle_chain):
    """Create state machine with Merkle chain audit."""
    return SentinelStateMachine(
        session_id="test-session-002",
        merkle_chain=merkle_chain
    )


@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio for utility testing."""
    return Portfolio(
        portfolio_id="test-portfolio",
        client_id="client-001",
        name="Test Portfolio",
        aum_usd=50_000_000,
        holdings=[
            Holding(
                ticker="NVDA",
                quantity=5000,
                current_price=800.00,
                market_value=4_000_000,
                portfolio_weight=0.08,
                cost_basis=3_000_000,
                unrealized_gain_loss=1_000_000,
                sector="Technology",
                asset_class="US Equities",
            ),
            Holding(
                ticker="AMD",
                quantity=10000,
                current_price=150.00,
                market_value=1_500_000,
                portfolio_weight=0.03,
                cost_basis=1_200_000,
                unrealized_gain_loss=300_000,
                sector="Technology",
                asset_class="US Equities",
            ),
        ],
        target_allocation=TargetAllocation(
            us_equities=0.60,
            international_equities=0.15,
            fixed_income=0.15,
            alternatives=0.05,
            structured_products=0.02,
            cash=0.03,
        ),
        client_profile=ClientProfile(
            client_id="client-001",
            risk_tolerance=RiskProfile.MODERATE_GROWTH,
            tax_sensitivity=0.7,
            concentration_limit=0.15,
        ),
        last_rebalance=datetime(2024, 1, 15, tzinfo=timezone.utc),
        cash_available=500_000,
    )


@pytest.fixture
def sample_scenarios():
    """Create sample scenarios for utility testing."""
    return [
        Scenario(
            scenario_id="scenario-001",
            title="Sell NVDA, Buy AMD",
            description="Reduce NVDA concentration by rotating to AMD",
            action_steps=[
                ActionStep(
                    step_number=1,
                    action=TradeAction.SELL,
                    ticker="NVDA",
                    quantity=1000,
                    timing="immediate",
                    rationale="Reduce concentration risk",
                ),
                ActionStep(
                    step_number=2,
                    action=TradeAction.BUY,
                    ticker="AMD",
                    quantity=5000,
                    timing="immediate",
                    rationale="Maintain tech exposure",
                ),
            ],
            expected_outcomes={
                "concentration_before": 0.17,
                "concentration_after": 0.10,
                "tax_impact": -5000,
                "diversification_delta": 0.05,
                "drift_before": 0.05,
                "drift_after": 0.02,
                "target_alignment": 0.8,
                "risk_profile_alignment": 0.7,
                "addresses_urgent_issues": True,
                "issue_urgency": 7,
            },
            risks=["Market timing risk", "AMD volatility"],
        ),
        Scenario(
            scenario_id="scenario-002",
            title="Hold Position",
            description="Maintain current positions",
            action_steps=[],
            expected_outcomes={
                "concentration_before": 0.17,
                "concentration_after": 0.17,
                "tax_impact": 0,
                "diversification_delta": 0,
                "drift_before": 0.05,
                "drift_after": 0.05,
                "target_alignment": 0.5,
                "risk_profile_alignment": 0.5,
                "addresses_urgent_issues": False,
                "issue_urgency": 3,
            },
            risks=["Continued concentration risk"],
        ),
        Scenario(
            scenario_id="scenario-003",
            title="Partial NVDA Reduction",
            description="Sell half of excess NVDA",
            action_steps=[
                ActionStep(
                    step_number=1,
                    action=TradeAction.SELL,
                    ticker="NVDA",
                    quantity=500,
                    timing="immediate",
                    rationale="Partial concentration reduction",
                ),
            ],
            expected_outcomes={
                "concentration_before": 0.17,
                "concentration_after": 0.135,
                "tax_impact": 10000,  # Tax cost
                "diversification_delta": 0.02,
                "drift_before": 0.05,
                "drift_after": 0.03,
                "target_alignment": 0.65,
                "risk_profile_alignment": 0.6,
                "addresses_urgent_issues": True,
                "issue_urgency": 6,
            },
            risks=["Still above concentration limit"],
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# STATE MACHINE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestStateMachineBasic:
    """Basic state machine functionality tests."""

    def test_initial_state_is_monitor(self, state_machine):
        """State machine starts in MONITOR state."""
        assert state_machine.get_state() == SystemState.MONITOR.value

    def test_custom_initial_state(self):
        """State machine can start in custom state."""
        sm = SentinelStateMachine(
            session_id="test",
            initial_state=SystemState.DETECT.value
        )
        assert sm.get_state() == SystemState.DETECT.value

    def test_can_transition_valid(self, state_machine):
        """Check valid transitions are allowed."""
        assert state_machine.can_transition(SystemState.DETECT.value)
        assert not state_machine.can_transition(SystemState.EXECUTE.value)

    def test_is_idle_in_monitor(self, state_machine):
        """is_idle returns True in MONITOR state."""
        assert state_machine.is_idle()

    def test_session_id_stored(self, state_machine):
        """Session ID is stored correctly."""
        assert state_machine.session_id == "test-session-001"


class TestStateMachineTransitions:
    """State transition tests."""

    def test_detect_event_transition(self, state_machine):
        """MONITOR → DETECT via detect_event trigger."""
        result = state_machine.detect_event()
        assert result is True
        assert state_machine.get_state() == SystemState.DETECT.value

    def test_full_happy_path(self, state_machine):
        """Complete transition through all states."""
        # MONITOR → DETECT
        state_machine.detect_event()
        assert state_machine.get_state() == SystemState.DETECT.value

        # DETECT → ANALYZE
        state_machine.start_analysis()
        assert state_machine.get_state() == SystemState.ANALYZE.value

        # ANALYZE → RECOMMEND (no conflict)
        state_machine.no_conflict()
        assert state_machine.get_state() == SystemState.RECOMMEND.value

        # RECOMMEND → APPROVED
        state_machine.approve()
        assert state_machine.get_state() == SystemState.APPROVED.value

        # APPROVED → EXECUTE
        state_machine.execute()
        assert state_machine.get_state() == SystemState.EXECUTE.value

        # EXECUTE → MONITOR (complete cycle)
        state_machine.complete()
        assert state_machine.get_state() == SystemState.MONITOR.value

    def test_conflict_resolution_path(self, state_machine):
        """Path through CONFLICT_RESOLUTION state."""
        state_machine.detect_event()
        state_machine.start_analysis()

        # ANALYZE → CONFLICT_RESOLUTION
        state_machine.detect_conflict()
        assert state_machine.get_state() == SystemState.CONFLICT_RESOLUTION.value

        # CONFLICT_RESOLUTION → RECOMMEND
        state_machine.resolve_conflict()
        assert state_machine.get_state() == SystemState.RECOMMEND.value

    def test_reject_recommendation(self, state_machine):
        """Rejection returns to MONITOR."""
        state_machine.detect_event()
        state_machine.start_analysis()
        state_machine.no_conflict()

        # RECOMMEND → MONITOR via reject
        state_machine.reject()
        assert state_machine.get_state() == SystemState.MONITOR.value

    def test_abort_from_execute(self, state_machine):
        """Abort from EXECUTE returns to MONITOR."""
        state_machine.detect_event()
        state_machine.start_analysis()
        state_machine.no_conflict()
        state_machine.approve()
        state_machine.execute()

        # EXECUTE → MONITOR via abort
        state_machine.abort()
        assert state_machine.get_state() == SystemState.MONITOR.value

    def test_transition_method_with_metadata(self, state_machine):
        """transition() method works with metadata."""
        result = state_machine.transition(
            SystemState.DETECT.value,
            metadata={"reason": "market_event"}
        )
        assert result is True
        assert state_machine.get_state() == SystemState.DETECT.value

    def test_invalid_transition_raises(self, state_machine):
        """Invalid transition raises InvalidTransitionError."""
        with pytest.raises(InvalidTransitionError):
            state_machine.transition(SystemState.EXECUTE.value)


class TestStateMachineHistory:
    """Transition history tests."""

    def test_history_empty_initially(self, state_machine):
        """History is empty at start."""
        history = state_machine.get_transition_history()
        assert len(history) == 0

    def test_history_records_transitions(self, state_machine):
        """History records each transition."""
        state_machine.detect_event()
        state_machine.start_analysis()

        history = state_machine.get_transition_history()
        assert len(history) == 2

        # Check first transition
        assert history[0]["from_state"] == SystemState.MONITOR.value
        assert history[0]["to_state"] == SystemState.DETECT.value
        assert history[0]["trigger"] == "detect_event"

        # Check second transition
        assert history[1]["from_state"] == SystemState.DETECT.value
        assert history[1]["to_state"] == SystemState.ANALYZE.value

    def test_get_last_transition(self, state_machine):
        """get_last_transition returns most recent."""
        state_machine.detect_event()
        state_machine.start_analysis()

        last = state_machine.get_last_transition()
        assert last is not None
        assert last.to_state == SystemState.ANALYZE.value

    def test_get_available_triggers(self, state_machine):
        """get_available_triggers returns valid triggers for current state."""
        triggers = state_machine.get_available_triggers()
        assert "detect_event" in triggers
        assert "start_analysis" not in triggers


class TestStateMachineWithMerkle:
    """Tests with Merkle chain integration."""

    def test_initial_state_logged(self, state_machine_with_merkle, merkle_chain):
        """Initial state is logged to Merkle chain."""
        # Initial state is logged during construction
        assert merkle_chain.get_block_count() >= 1

    def test_transitions_logged(self, state_machine_with_merkle, merkle_chain):
        """Transitions are logged to Merkle chain."""
        initial_count = merkle_chain.get_block_count()

        state_machine_with_merkle.detect_event()

        assert merkle_chain.get_block_count() > initial_count


class TestStateMachineFactory:
    """State machine factory tests."""

    def test_factory_creates_machine(self, merkle_chain):
        """Factory creates and tracks machines."""
        factory = StateMachineFactory(merkle_chain=merkle_chain)

        sm = factory.create("session-001")
        assert sm is not None
        assert sm.session_id == "session-001"

    def test_factory_get_machine(self, merkle_chain):
        """Factory retrieves created machines."""
        factory = StateMachineFactory(merkle_chain=merkle_chain)

        factory.create("session-001")
        retrieved = factory.get("session-001")

        assert retrieved is not None
        assert retrieved.session_id == "session-001"

    def test_factory_remove_machine(self, merkle_chain):
        """Factory can remove machines."""
        factory = StateMachineFactory(merkle_chain=merkle_chain)

        factory.create("session-001")
        result = factory.remove("session-001")

        assert result is True
        assert factory.get("session-001") is None

    def test_factory_get_all_states(self, merkle_chain):
        """Factory returns all machine states."""
        factory = StateMachineFactory(merkle_chain=merkle_chain)

        factory.create("session-001")
        sm2 = factory.create("session-002")
        sm2.detect_event()

        states = factory.get_all_states()
        assert states["session-001"] == SystemState.MONITOR.value
        assert states["session-002"] == SystemState.DETECT.value


class TestStateMachineHelpers:
    """Helper method tests."""

    def test_is_analyzing_states(self, state_machine):
        """is_analyzing returns True for analysis states."""
        assert not state_machine.is_analyzing()

        state_machine.detect_event()
        assert state_machine.is_analyzing()

        state_machine.start_analysis()
        assert state_machine.is_analyzing()

    def test_is_pending_approval(self, state_machine):
        """is_pending_approval for RECOMMEND state."""
        state_machine.detect_event()
        state_machine.start_analysis()
        state_machine.no_conflict()

        assert state_machine.is_pending_approval()

    def test_is_executing_states(self, state_machine):
        """is_executing for APPROVED and EXECUTE states."""
        state_machine.detect_event()
        state_machine.start_analysis()
        state_machine.no_conflict()
        state_machine.approve()

        assert state_machine.is_executing()

        state_machine.execute()
        assert state_machine.is_executing()

    def test_reset_to_monitor(self, state_machine):
        """reset_to_monitor from various states."""
        state_machine.detect_event()
        state_machine.start_analysis()

        result = state_machine.reset_to_monitor(reason="test_reset")
        assert result is True
        assert state_machine.get_state() == SystemState.MONITOR.value


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestUtilityFunction:
    """Utility function scoring tests."""

    def test_score_single_scenario(self, sample_portfolio, sample_scenarios):
        """Score a single scenario."""
        utility_fn = UtilityFunction()
        weights = UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.MODERATE_GROWTH]

        score = utility_fn.score_scenario(
            sample_scenarios[0],
            sample_portfolio,
            weights
        )

        assert score is not None
        assert score.scenario_id == "scenario-001"
        assert 0 <= score.total_score <= 100
        assert len(score.dimension_scores) == 5

    def test_rank_multiple_scenarios(self, sample_portfolio, sample_scenarios):
        """Rank multiple scenarios correctly."""
        utility_fn = UtilityFunction()
        weights = UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.MODERATE_GROWTH]

        ranked = utility_fn.rank_scenarios(
            sample_scenarios,
            sample_portfolio,
            weights
        )

        assert len(ranked) == 3
        # Scores should be descending
        assert ranked[0].total_score >= ranked[1].total_score
        assert ranked[1].total_score >= ranked[2].total_score
        # Ranks should be 1, 2, 3
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2
        assert ranked[2].rank == 3

    def test_scenario_with_action_ranks_higher_than_hold(
        self, sample_portfolio, sample_scenarios
    ):
        """Scenario with action should rank higher than hold for concentration issue."""
        weights = UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.MODERATE_GROWTH]

        ranked = score_and_rank(sample_scenarios, sample_portfolio)

        # Find the "Hold Position" scenario
        hold_score = next(r for r in ranked if r.scenario_id == "scenario-002")
        action_score = next(r for r in ranked if r.scenario_id == "scenario-001")

        # Action should score higher for addressing concentration
        assert action_score.total_score > hold_score.total_score


class TestUtilityWeights:
    """Weight profile tests."""

    def test_conservative_weights_emphasize_risk(self):
        """Conservative profile emphasizes risk reduction."""
        weights = UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.CONSERVATIVE]

        assert weights.risk_reduction == 0.40
        assert weights.risk_reduction > weights.tax_savings
        assert weights.risk_reduction > weights.goal_alignment

    def test_aggressive_weights_emphasize_goals(self):
        """Aggressive profile emphasizes goal alignment."""
        weights = UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.AGGRESSIVE]

        assert weights.goal_alignment == 0.30
        assert weights.urgency == 0.25
        assert weights.goal_alignment > weights.risk_reduction

    def test_weights_sum_to_one(self):
        """All weight profiles sum to 1.0."""
        for profile, weights in UTILITY_WEIGHTS_BY_PROFILE.items():
            total = (
                weights.risk_reduction +
                weights.tax_savings +
                weights.goal_alignment +
                weights.transaction_cost +
                weights.urgency
            )
            assert abs(total - 1.0) < 0.01, f"{profile}: weights sum to {total}"


class TestUtilityFactory:
    """Utility function factory tests."""

    def test_factory_creates_function(self):
        """Factory creates utility function."""
        utility_fn = UtilityFunctionFactory.create()
        assert utility_fn is not None
        assert isinstance(utility_fn, UtilityFunction)

    def test_factory_custom_config(self):
        """Factory accepts custom config."""
        config = ScoringConfig(concentration_limit=0.20)
        utility_fn = UtilityFunctionFactory.create(custom_config=config)

        assert utility_fn.config.concentration_limit == 0.20

    def test_factory_get_weights_for_profile(self):
        """Factory returns correct weights for profile."""
        weights = UtilityFunctionFactory.get_weights_for_profile(
            RiskProfile.CONSERVATIVE
        )
        assert weights.risk_reduction == 0.40


class TestConvenienceFunction:
    """Convenience function tests."""

    def test_score_and_rank(self, sample_portfolio, sample_scenarios):
        """score_and_rank convenience function works."""
        ranked = score_and_rank(sample_scenarios, sample_portfolio)

        assert len(ranked) == 3
        assert ranked[0].rank == 1

    def test_score_and_rank_with_profile_override(
        self, sample_portfolio, sample_scenarios
    ):
        """score_and_rank accepts profile override."""
        ranked_conservative = score_and_rank(
            sample_scenarios,
            sample_portfolio,
            risk_profile=RiskProfile.CONSERVATIVE
        )
        ranked_aggressive = score_and_rank(
            sample_scenarios,
            sample_portfolio,
            risk_profile=RiskProfile.AGGRESSIVE
        )

        # Different profiles may rank differently
        # Both should work without error
        assert len(ranked_conservative) == 3
        assert len(ranked_aggressive) == 3


class TestDimensionScoring:
    """Individual dimension scoring tests."""

    def test_risk_score_rewards_concentration_reduction(
        self, sample_portfolio, sample_scenarios
    ):
        """Risk scorer rewards concentration reduction."""
        utility_fn = UtilityFunction()
        weights = UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.MODERATE_GROWTH]

        # Score scenario that reduces concentration
        score_action = utility_fn.score_scenario(
            sample_scenarios[0], sample_portfolio, weights
        )
        # Score hold scenario
        score_hold = utility_fn.score_scenario(
            sample_scenarios[1], sample_portfolio, weights
        )

        # Find risk scores
        risk_action = next(
            d for d in score_action.dimension_scores
            if d.dimension == "risk_reduction"
        )
        risk_hold = next(
            d for d in score_hold.dimension_scores
            if d.dimension == "risk_reduction"
        )

        # Action should have higher risk score
        assert risk_action.raw_score > risk_hold.raw_score

    def test_cost_score_favors_fewer_trades(self, sample_portfolio, sample_scenarios):
        """Cost scorer favors scenarios with fewer/smaller trades."""
        utility_fn = UtilityFunction()
        weights = UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.MODERATE_GROWTH]

        # Hold has no trades
        score_hold = utility_fn.score_scenario(
            sample_scenarios[1], sample_portfolio, weights
        )

        cost_hold = next(
            d for d in score_hold.dimension_scores
            if d.dimension == "transaction_cost"
        )

        # Hold should have maximum cost score (no costs)
        assert cost_hold.raw_score == 10.0

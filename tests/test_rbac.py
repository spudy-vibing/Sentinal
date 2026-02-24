"""
Tests for Sentinel RBAC and Session Management.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Steps 2.7-2.8
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from src.contracts.security import (
    Permission,
    Role,
    SessionConfig,
    SessionType,
    AuditEventType,
    SecurityContext,
    ROLE_PERMISSIONS,
    create_advisor_session,
    create_analyst_session,
    create_agent_session,
    require_permission,
    require_portfolio_access,
)
from src.security.rbac import (
    RBACService,
    AccessDecision,
    get_rbac_service,
    reset_rbac_service,
    require_permissions,
)
from src.security.sessions import (
    SessionManager,
    SessionMetrics,
    LocalSandbox,
    get_session_manager,
    reset_session_manager,
)


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def rbac_service(merkle_chain):
    """Create RBAC service with Merkle chain."""
    reset_rbac_service()
    return RBACService(audit_chain=merkle_chain)


@pytest.fixture
def session_manager(merkle_chain):
    """Create session manager with Merkle chain."""
    reset_session_manager()
    return SessionManager(
        audit_chain=merkle_chain,
        sandbox=LocalSandbox(),
    )


@pytest.fixture
def advisor_session():
    """Create an advisor session."""
    return create_advisor_session(
        session_id="advisor-001",
        user_id="user-advisor"
    )


@pytest.fixture
def analyst_session():
    """Create an analyst session with limited portfolios."""
    return create_analyst_session(
        session_id="analyst-001",
        allowed_portfolios=["portfolio_a", "portfolio_b"],
        user_id="user-analyst"
    )


@pytest.fixture
def agent_session():
    """Create an agent session."""
    return create_agent_session(
        agent_type="drift",
        parent_session_id="advisor-001"
    )


# ═══════════════════════════════════════════════════════════════════════════
# PERMISSION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPermissions:
    """Permission flag tests."""

    def test_drift_agent_has_read_holdings(self):
        """Drift agent can read holdings."""
        perm = Permission.DRIFT_AGENT
        assert perm & Permission.READ_HOLDINGS

    def test_drift_agent_no_tax_lots(self):
        """Drift agent cannot read tax lots."""
        perm = Permission.DRIFT_AGENT
        assert not (perm & Permission.READ_TAX_LOTS)

    def test_tax_agent_has_tax_lots(self):
        """Tax agent can read tax lots."""
        perm = Permission.TAX_AGENT
        assert perm & Permission.READ_TAX_LOTS
        assert perm & Permission.READ_TRANSACTIONS

    def test_advisor_has_all_read_permissions(self):
        """Advisor has comprehensive read permissions."""
        perm = Permission.HUMAN_ADVISOR
        assert perm & Permission.READ_HOLDINGS
        assert perm & Permission.READ_TAX_LOTS
        assert perm & Permission.READ_CLIENT_PII
        assert perm & Permission.READ_TRANSACTIONS
        assert perm & Permission.READ_RECOMMENDATIONS

    def test_advisor_can_approve(self):
        """Advisor can approve trades."""
        perm = Permission.HUMAN_ADVISOR
        assert perm & Permission.APPROVE_TRADES

    def test_analyst_cannot_approve(self):
        """Analyst cannot approve trades."""
        perm = Permission.ANALYST
        assert not (perm & Permission.APPROVE_TRADES)


class TestRolePermissions:
    """Role to permission mapping tests."""

    def test_role_permissions_mapping(self):
        """All roles have mapped permissions."""
        for role in Role:
            assert role in ROLE_PERMISSIONS

    def test_admin_has_admin_permission(self):
        """Admin role has ADMIN permission."""
        perm = ROLE_PERMISSIONS[Role.ADMIN]
        assert perm & Permission.ADMIN


# ═══════════════════════════════════════════════════════════════════════════
# SESSION CONFIG TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSessionConfig:
    """Session configuration tests."""

    def test_advisor_session_full_access(self, advisor_session):
        """Advisor session has full portfolio access."""
        assert advisor_session.allowed_portfolios is None
        assert advisor_session.can_access_portfolio("any_portfolio")

    def test_analyst_session_limited_access(self, analyst_session):
        """Analyst session has limited portfolio access."""
        assert analyst_session.can_access_portfolio("portfolio_a")
        assert analyst_session.can_access_portfolio("portfolio_b")
        assert not analyst_session.can_access_portfolio("portfolio_c")

    def test_session_has_permission(self, advisor_session):
        """has_permission checks role permissions."""
        assert advisor_session.has_permission(Permission.READ_HOLDINGS)
        assert advisor_session.has_permission(Permission.APPROVE_TRADES)

    def test_analyst_lacks_approval(self, analyst_session):
        """Analyst lacks approval permission."""
        assert not analyst_session.has_permission(Permission.APPROVE_TRADES)

    def test_session_requires_sandbox(self, analyst_session, advisor_session):
        """Analyst requires sandbox, advisor does not."""
        assert analyst_session.requires_sandbox
        assert not advisor_session.requires_sandbox

    def test_session_expiration(self):
        """Session expiration is detected."""
        session = SessionConfig(
            session_id="test",
            session_type=SessionType.ADVISOR_MAIN,
            role=Role.HUMAN_ADVISOR,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        assert session.is_expired

    def test_validate_access_raises_on_expired(self):
        """validate_access raises for expired session."""
        session = SessionConfig(
            session_id="test",
            session_type=SessionType.ADVISOR_MAIN,
            role=Role.HUMAN_ADVISOR,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        with pytest.raises(PermissionError, match="expired"):
            session.validate_access("portfolio_a", Permission.READ_HOLDINGS)

    def test_validate_access_raises_on_portfolio(self, analyst_session):
        """validate_access raises for unauthorized portfolio."""
        with pytest.raises(PermissionError, match="cannot access"):
            analyst_session.validate_access(
                "portfolio_c",
                Permission.READ_HOLDINGS
            )

    def test_validate_access_raises_on_permission(self, analyst_session):
        """validate_access raises for missing permission."""
        with pytest.raises(PermissionError, match="lacks permission"):
            analyst_session.validate_access(
                "portfolio_a",
                Permission.APPROVE_TRADES
            )


# ═══════════════════════════════════════════════════════════════════════════
# RBAC SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestRBACService:
    """RBAC service tests."""

    def test_check_permission_granted(self, rbac_service, advisor_session):
        """check_permission returns True for valid permission."""
        result = rbac_service.check_permission(
            advisor_session,
            Permission.READ_HOLDINGS
        )
        assert result is True

    def test_check_permission_denied(self, rbac_service, analyst_session):
        """check_permission returns False for invalid permission."""
        result = rbac_service.check_permission(
            analyst_session,
            Permission.APPROVE_TRADES
        )
        assert result is False

    def test_enforce_permission_success(self, rbac_service, advisor_session):
        """enforce_permission succeeds for valid permission."""
        # Should not raise
        rbac_service.enforce_permission(
            advisor_session,
            Permission.READ_HOLDINGS
        )

    def test_enforce_permission_failure(self, rbac_service, analyst_session):
        """enforce_permission raises for invalid permission."""
        with pytest.raises(PermissionError):
            rbac_service.enforce_permission(
                analyst_session,
                Permission.APPROVE_TRADES
            )

    def test_register_session(self, rbac_service, advisor_session, merkle_chain):
        """Sessions are registered and logged."""
        initial_count = merkle_chain.get_block_count()

        rbac_service.register_session(advisor_session)

        assert rbac_service.get_session(advisor_session.session_id) is not None
        assert merkle_chain.get_block_count() > initial_count

    def test_terminate_session(self, rbac_service, advisor_session):
        """Sessions can be terminated."""
        rbac_service.register_session(advisor_session)
        result = rbac_service.terminate_session(advisor_session.session_id)

        assert result is True
        assert rbac_service.get_session(advisor_session.session_id) is None

    def test_create_advisor_session(self, rbac_service):
        """Factory method creates and registers advisor session."""
        session = rbac_service.create_advisor_session(
            session_id="advisor-new",
            user_id="user-001"
        )

        assert session.role == Role.HUMAN_ADVISOR
        assert session.session_type == SessionType.ADVISOR_MAIN
        assert rbac_service.get_session("advisor-new") is not None

    def test_create_agent_session(self, rbac_service):
        """Factory method creates agent session under parent."""
        parent = rbac_service.create_advisor_session("advisor-parent")

        agent = rbac_service.create_agent_session("drift", "advisor-parent")

        assert agent.role == Role.DRIFT_AGENT
        assert "advisor-parent" in agent.session_id

    def test_get_active_sessions(self, rbac_service):
        """get_active_sessions returns session list."""
        rbac_service.create_advisor_session("session-1")
        rbac_service.create_advisor_session("session-2")

        sessions = rbac_service.get_active_sessions()
        assert len(sessions) == 2


class TestSecurityContext:
    """Security context tests."""

    def test_context_requires_permission(self, advisor_session, merkle_chain):
        """Context require_permission works."""
        ctx = SecurityContext(
            session=advisor_session,
            audit_chain=merkle_chain
        )

        # Should not raise
        ctx.require_permission(Permission.READ_HOLDINGS)

    def test_context_requires_permission_raises(self, analyst_session, merkle_chain):
        """Context require_permission raises for missing permission."""
        ctx = SecurityContext(
            session=analyst_session,
            audit_chain=merkle_chain
        )

        with pytest.raises(PermissionError):
            ctx.require_permission(Permission.APPROVE_TRADES)

    def test_context_log_access(self, advisor_session, merkle_chain):
        """Context logs access events."""
        ctx = SecurityContext(
            session=advisor_session,
            audit_chain=merkle_chain
        )
        initial_count = merkle_chain.get_block_count()

        ctx.log_access("portfolio_a", "read")

        assert merkle_chain.get_block_count() > initial_count


# ═══════════════════════════════════════════════════════════════════════════
# DECORATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestDecorators:
    """RBAC decorator tests."""

    def test_require_permission_decorator(self, advisor_session):
        """require_permission decorator enforces permissions."""

        class TestClass:
            def __init__(self, session):
                self._session = session

            @require_permission(Permission.READ_HOLDINGS)
            def read_data(self):
                return "success"

        obj = TestClass(advisor_session)
        assert obj.read_data() == "success"

    def test_require_permission_decorator_denies(self, analyst_session):
        """require_permission decorator denies unauthorized access."""

        class TestClass:
            def __init__(self, session):
                self._session = session

            @require_permission(Permission.APPROVE_TRADES)
            def approve(self):
                return "success"

        obj = TestClass(analyst_session)
        with pytest.raises(PermissionError):
            obj.approve()

    def test_require_portfolio_access_decorator(self, analyst_session):
        """require_portfolio_access decorator enforces portfolio access."""

        class TestClass:
            def __init__(self, session):
                self._session = session

            @require_portfolio_access
            def get_portfolio(self, portfolio_id):
                return f"data for {portfolio_id}"

        obj = TestClass(analyst_session)

        # Allowed portfolio
        assert obj.get_portfolio("portfolio_a") == "data for portfolio_a"

        # Denied portfolio
        with pytest.raises(PermissionError):
            obj.get_portfolio("portfolio_c")

    def test_require_permissions_multiple(self, advisor_session):
        """require_permissions decorator checks multiple permissions."""

        class TestClass:
            def __init__(self, session):
                self._session = session

            @require_permissions(Permission.READ_HOLDINGS, Permission.READ_TAX_LOTS)
            def read_full_data(self):
                return "success"

        obj = TestClass(advisor_session)
        assert obj.read_full_data() == "success"


# ═══════════════════════════════════════════════════════════════════════════
# SESSION MANAGER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSessionManager:
    """Session manager tests."""

    def test_create_session(self, session_manager):
        """Session manager creates sessions."""
        session = session_manager.create_session(
            session_type=SessionType.ADVISOR_MAIN,
            role=Role.HUMAN_ADVISOR,
            user_id="user-001"
        )

        assert session is not None
        assert session.role == Role.HUMAN_ADVISOR

    def test_get_session(self, session_manager):
        """Session manager retrieves sessions."""
        created = session_manager.create_session(
            session_type=SessionType.ADVISOR_MAIN,
            role=Role.HUMAN_ADVISOR
        )

        retrieved = session_manager.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_terminate_session(self, session_manager):
        """Session manager terminates sessions."""
        session = session_manager.create_session(
            session_type=SessionType.ADVISOR_MAIN,
            role=Role.HUMAN_ADVISOR
        )

        result = session_manager.terminate_session(session.session_id)
        assert result is True
        assert session_manager.get_session(session.session_id) is None

    def test_record_tool_call(self, session_manager):
        """Tool calls are recorded."""
        session = session_manager.create_session(
            session_type=SessionType.ADVISOR_MAIN,
            role=Role.HUMAN_ADVISOR,
            max_tool_calls=5
        )

        for i in range(5):
            result = session_manager.record_tool_call(session.session_id)
            assert result is True

        # Sixth call should fail
        result = session_manager.record_tool_call(session.session_id)
        assert result is False

    def test_sandbox_mode_for_analyst(self, session_manager):
        """Analyst sessions have sandbox mode enabled."""
        session = session_manager.create_session(
            session_type=SessionType.ANALYST,
            role=Role.ANALYST,
            allowed_portfolios=["portfolio_a"]
        )

        assert session.sandbox_mode is True

    def test_get_stats(self, session_manager):
        """Session manager returns statistics."""
        session_manager.create_session(
            session_type=SessionType.ADVISOR_MAIN,
            role=Role.HUMAN_ADVISOR
        )
        session_manager.create_session(
            session_type=SessionType.ANALYST,
            role=Role.ANALYST,
            allowed_portfolios=["portfolio_a"]
        )

        stats = session_manager.get_stats()
        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 2
        assert stats["sandboxed_sessions"] == 1


class TestSessionContext:
    """Session context manager tests."""

    def test_session_context_creates_and_terminates(self, session_manager):
        """Context manager creates and terminates session."""
        with session_manager.session_context(
            SessionType.ADVISOR_MAIN,
            Role.HUMAN_ADVISOR
        ) as session:
            session_id = session.session_id
            assert session_manager.get_session(session_id) is not None

        # After context, session should be terminated
        assert session_manager.get_session(session_id) is None


class TestSessionMetrics:
    """Session metrics tests."""

    def test_metrics_duration(self):
        """Metrics calculate duration correctly."""
        metrics = SessionMetrics()
        # Simulate some time passing
        metrics.tool_calls = 5
        metrics.permission_checks = 10

        assert metrics.duration_seconds >= 0

    def test_metrics_to_dict(self):
        """Metrics convert to dict."""
        metrics = SessionMetrics()
        metrics.tool_calls = 5
        metrics.permission_denials = 1

        data = metrics.to_dict()
        assert data["tool_calls"] == 5
        assert data["permission_denials"] == 1


class TestLocalSandbox:
    """Local sandbox tests."""

    @pytest.mark.asyncio
    async def test_execute_success(self, advisor_session):
        """Local sandbox executes code."""
        sandbox = LocalSandbox()

        result = await sandbox.execute(
            advisor_session,
            lambda: 42
        )

        assert result["status"] == "success"
        assert result["result"] == 42

    @pytest.mark.asyncio
    async def test_execute_error(self, advisor_session):
        """Local sandbox catches errors."""
        sandbox = LocalSandbox()

        def failing_code():
            raise ValueError("test error")

        result = await sandbox.execute(advisor_session, failing_code)

        assert result["status"] == "error"
        assert "test error" in result["error"]


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSingletons:
    """Singleton access tests."""

    def test_get_rbac_service_singleton(self):
        """get_rbac_service returns singleton."""
        reset_rbac_service()

        service1 = get_rbac_service()
        service2 = get_rbac_service()

        assert service1 is service2

    def test_get_session_manager_singleton(self):
        """get_session_manager returns singleton."""
        reset_session_manager()

        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2

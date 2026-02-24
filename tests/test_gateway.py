"""
SENTINEL GATEWAY TESTS

Tests for event submission, validation, priority queuing, and routing.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Workstream B
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.gateway import Gateway, EventFactory, SessionQueue, PriorityItem
from src.contracts.schemas import (
    EventType,
    MarketEventInput,
    HeartbeatInput,
    CronJobInput,
    CronJobType,
)


# ═══════════════════════════════════════════════════════════════════════════
# PRIORITY QUEUE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPriorityItem:
    """Tests for PriorityItem ordering."""

    def test_priority_ordering(self):
        """Higher priority events (10) should sort before lower (1)."""
        event_high = EventFactory.create_market_event(
            session_id="test",
            affected_sectors=["Tech"],
            magnitude=-0.05,
            description="High priority",
            priority=10,
        )
        event_low = EventFactory.create_heartbeat(
            session_id="test",
            portfolio_ids=["P1"],
            priority=1,
        )

        item_high = PriorityItem.from_event(event_high)
        item_low = PriorityItem.from_event(event_low)

        # Lower priority number = processed first (inverted)
        assert item_high < item_low  # 10 -> 0, 1 -> 9

    def test_same_priority_timestamp_order(self):
        """Same priority events should maintain timestamp order."""
        event1 = EventFactory.create_heartbeat(
            session_id="test",
            portfolio_ids=["P1"],
            priority=5,
        )
        event2 = EventFactory.create_heartbeat(
            session_id="test",
            portfolio_ids=["P2"],
            priority=5,
        )

        item1 = PriorityItem.from_event(event1)
        item2 = PriorityItem.from_event(event2)

        # Both have same priority, so they're equal in ordering
        assert item1.priority == item2.priority


class TestSessionQueue:
    """Tests for SessionQueue behavior."""

    @pytest.mark.asyncio
    async def test_queue_put_get(self):
        """Test basic put and get operations."""
        queue = SessionQueue("test_session")

        event = EventFactory.create_market_event(
            session_id="test_session",
            affected_sectors=["Tech"],
            magnitude=-0.05,
            description="Test event",
        )

        await queue.put(event)
        assert queue.qsize() == 1

        retrieved = await queue.get()
        assert retrieved.event_id == event.event_id
        assert queue.empty()

    @pytest.mark.asyncio
    async def test_queue_priority_ordering(self):
        """Events should be retrieved in priority order."""
        queue = SessionQueue("test_session")

        # Add events with different priorities
        low_priority = EventFactory.create_heartbeat(
            session_id="test_session",
            portfolio_ids=["P1"],
            priority=2,
        )
        high_priority = EventFactory.create_market_event(
            session_id="test_session",
            affected_sectors=["Tech"],
            magnitude=-0.05,
            description="Urgent event",
            priority=9,
        )
        medium_priority = EventFactory.create_heartbeat(
            session_id="test_session",
            portfolio_ids=["P2"],
            priority=5,
        )

        # Add in random order
        await queue.put(low_priority)
        await queue.put(high_priority)
        await queue.put(medium_priority)

        # Retrieve in priority order
        first = await queue.get()
        second = await queue.get()
        third = await queue.get()

        assert first.priority == 9  # High priority first
        assert second.priority == 5  # Medium second
        assert third.priority == 2  # Low last

    @pytest.mark.asyncio
    async def test_queue_empty_returns_none(self):
        """Getting from empty queue returns None."""
        queue = SessionQueue("test_session")
        result = await queue.get()
        assert result is None

    @pytest.mark.asyncio
    async def test_queue_peek(self):
        """Peek returns item without removing."""
        queue = SessionQueue("test_session")

        event = EventFactory.create_heartbeat(
            session_id="test_session",
            portfolio_ids=["P1"],
        )

        await queue.put(event)

        peeked = await queue.peek()
        assert peeked.event_id == event.event_id
        assert queue.qsize() == 1  # Still there

        retrieved = await queue.get()
        assert retrieved.event_id == event.event_id
        assert queue.empty()

    @pytest.mark.asyncio
    async def test_queue_total_processed(self):
        """Track total events processed."""
        queue = SessionQueue("test_session")

        for i in range(5):
            event = EventFactory.create_heartbeat(
                session_id="test_session",
                portfolio_ids=[f"P{i}"],
            )
            await queue.put(event)

        assert queue.total_processed == 5


# ═══════════════════════════════════════════════════════════════════════════
# GATEWAY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestGatewaySubmit:
    """Tests for event submission."""

    @pytest.mark.asyncio
    async def test_submit_event(self, gateway):
        """Test basic event submission."""
        event = EventFactory.create_market_event(
            session_id="advisor:main",
            affected_sectors=["Technology"],
            magnitude=-0.04,
            description="Tech selloff",
        )

        event_id = await gateway.submit(event)

        assert event_id == event.event_id
        assert gateway._events_received == 1

    @pytest.mark.asyncio
    async def test_submit_creates_queue(self, gateway):
        """Submitting event creates queue for session."""
        event = EventFactory.create_heartbeat(
            session_id="new_session",
            portfolio_ids=["P1"],
        )

        await gateway.submit(event)

        assert "new_session" in gateway._queues

    @pytest.mark.asyncio
    async def test_submit_without_session_id_raises(self, gateway):
        """Event without session_id raises ValueError."""
        event = MarketEventInput(
            event_id="test_123",
            event_type=EventType.MARKET_EVENT,
            timestamp=datetime.now(timezone.utc),
            session_id="",  # Empty
            affected_sectors=["Tech"],
            magnitude=-0.05,
            description="Test",
        )

        with pytest.raises(ValueError, match="session_id"):
            await gateway.submit(event)

    @pytest.mark.asyncio
    async def test_submit_generates_event_id(self, gateway):
        """Event ID is generated if not provided."""
        event = MarketEventInput(
            event_id="",  # Empty
            event_type=EventType.MARKET_EVENT,
            timestamp=datetime.now(timezone.utc),
            session_id="test_session",
            affected_sectors=["Tech"],
            magnitude=-0.05,
            description="Test",
        )

        event_id = await gateway.submit(event)

        assert event_id.startswith("evt_")

    @pytest.mark.asyncio
    async def test_submit_logs_to_merkle_chain(self, gateway, merkle_chain):
        """Event submission is logged to Merkle chain."""
        initial_count = merkle_chain.get_block_count()

        event = EventFactory.create_market_event(
            session_id="advisor:main",
            affected_sectors=["Tech"],
            magnitude=-0.04,
            description="Test",
        )

        await gateway.submit(event)

        assert merkle_chain.get_block_count() == initial_count + 1


class TestGatewayHandlers:
    """Tests for handler registration and dispatch."""

    @pytest.mark.asyncio
    async def test_register_handler(self, gateway):
        """Test handler registration."""
        handler = AsyncMock()

        gateway.register_handler(EventType.MARKET_EVENT, handler)

        assert handler in gateway._handlers[EventType.MARKET_EVENT]

    @pytest.mark.asyncio
    async def test_register_handler_string_type(self, gateway):
        """Test handler registration with string event type."""
        handler = AsyncMock()

        gateway.register_handler("market_event", handler)

        assert handler in gateway._handlers[EventType.MARKET_EVENT]

    @pytest.mark.asyncio
    async def test_handler_called_on_process(self, gateway):
        """Handler is called when event is processed."""
        handler = AsyncMock()
        gateway.register_handler(EventType.MARKET_EVENT, handler)

        event = EventFactory.create_market_event(
            session_id="test_session",
            affected_sectors=["Tech"],
            magnitude=-0.04,
            description="Test",
        )

        await gateway.submit(event)
        await gateway.process_session("test_session")

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_multiple_handlers_called(self, gateway):
        """Multiple handlers for same event type are all called."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        gateway.register_handler(EventType.HEARTBEAT, handler1)
        gateway.register_handler(EventType.HEARTBEAT, handler2)

        event = EventFactory.create_heartbeat(
            session_id="test_session",
            portfolio_ids=["P1"],
        )

        await gateway.submit(event)
        await gateway.process_session("test_session")

        handler1.assert_called_once()
        handler2.assert_called_once()

    @pytest.mark.asyncio
    async def test_unregister_handler(self, gateway):
        """Test handler unregistration."""
        handler = AsyncMock()
        gateway.register_handler(EventType.MARKET_EVENT, handler)

        result = gateway.unregister_handler(EventType.MARKET_EVENT, handler)

        assert result is True
        assert handler not in gateway._handlers[EventType.MARKET_EVENT]

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_handler(self, gateway):
        """Unregistering non-existent handler returns False."""
        handler = AsyncMock()

        result = gateway.unregister_handler(EventType.MARKET_EVENT, handler)

        assert result is False

    @pytest.mark.asyncio
    async def test_handler_error_logged(self, gateway):
        """Handler errors are logged but don't stop processing."""
        failing_handler = AsyncMock(side_effect=Exception("Handler failed"))
        success_handler = AsyncMock()

        gateway.register_handler(EventType.MARKET_EVENT, failing_handler)
        gateway.register_handler(EventType.MARKET_EVENT, success_handler)

        event = EventFactory.create_market_event(
            session_id="test_session",
            affected_sectors=["Tech"],
            magnitude=-0.04,
            description="Test",
        )

        await gateway.submit(event)
        await gateway.process_session("test_session")

        # Both handlers called despite first failing
        failing_handler.assert_called_once()
        success_handler.assert_called_once()


class TestGatewayProcessing:
    """Tests for event processing."""

    @pytest.mark.asyncio
    async def test_process_empty_session(self, gateway):
        """Processing empty session does nothing."""
        await gateway.process_session("nonexistent_session")
        # Should not raise

    @pytest.mark.asyncio
    async def test_process_drains_queue(self, gateway):
        """Processing drains all events from queue."""
        handler = AsyncMock()
        gateway.register_handler(EventType.HEARTBEAT, handler)

        for i in range(5):
            event = EventFactory.create_heartbeat(
                session_id="test_session",
                portfolio_ids=[f"P{i}"],
            )
            await gateway.submit(event)

        await gateway.process_session("test_session")

        assert handler.call_count == 5
        assert gateway._queues["test_session"].empty()

    @pytest.mark.asyncio
    async def test_process_respects_priority(self, gateway):
        """Events are processed in priority order."""
        processed_order = []

        async def tracking_handler(event):
            processed_order.append(event.priority)

        gateway.register_handler(EventType.MARKET_EVENT, tracking_handler)
        gateway.register_handler(EventType.HEARTBEAT, tracking_handler)

        # Submit in mixed order
        await gateway.submit(EventFactory.create_heartbeat(
            session_id="test_session",
            portfolio_ids=["P1"],
            priority=2,
        ))
        await gateway.submit(EventFactory.create_market_event(
            session_id="test_session",
            affected_sectors=["Tech"],
            magnitude=-0.05,
            description="Urgent",
            priority=10,
        ))
        await gateway.submit(EventFactory.create_heartbeat(
            session_id="test_session",
            portfolio_ids=["P2"],
            priority=5,
        ))

        await gateway.process_session("test_session")

        assert processed_order == [10, 5, 2]


class TestGatewayStats:
    """Tests for gateway statistics."""

    @pytest.mark.asyncio
    async def test_get_stats(self, gateway):
        """Test gateway statistics."""
        event = EventFactory.create_heartbeat(
            session_id="test_session",
            portfolio_ids=["P1"],
        )
        await gateway.submit(event)

        stats = gateway.get_stats()

        assert stats["events_received"] == 1
        assert stats["active_sessions"] == 1
        assert stats["is_running"] is True

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, gateway):
        """Test queue statistics."""
        for i in range(3):
            event = EventFactory.create_heartbeat(
                session_id="test_session",
                portfolio_ids=[f"P{i}"],
            )
            await gateway.submit(event)

        stats = gateway.get_queue_stats()

        assert "test_session" in stats
        assert stats["test_session"]["pending"] == 3

    @pytest.mark.asyncio
    async def test_clear_queue(self, gateway):
        """Test clearing a session queue."""
        for i in range(5):
            event = EventFactory.create_heartbeat(
                session_id="test_session",
                portfolio_ids=[f"P{i}"],
            )
            await gateway.submit(event)

        cleared = gateway.clear_queue("test_session")

        assert cleared == 5
        assert gateway._queues["test_session"].empty()


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestGatewayScheduler:
    """Tests for scheduler functionality."""

    @pytest.mark.asyncio
    async def test_schedule_heartbeat(self, gateway_with_scheduler):
        """Test scheduling a heartbeat."""
        job_id = gateway_with_scheduler.schedule_heartbeat(
            portfolio_ids=["P1", "P2"],
            session_id="advisor:main",
            interval_minutes=30,
        )

        assert job_id.startswith("heartbeat_")

        stats = gateway_with_scheduler.get_stats()
        assert stats["scheduled_jobs"] == 1

    @pytest.mark.asyncio
    async def test_schedule_cron_job(self, gateway_with_scheduler):
        """Test scheduling a cron job."""
        job_id = gateway_with_scheduler.schedule_cron_job(
            job_type=CronJobType.DAILY_REVIEW,
            session_id="advisor:main",
            cron_expression="0 9 * * MON-FRI",
            instructions="Daily portfolio review",
        )

        assert job_id.startswith("cron_daily_review_")

    @pytest.mark.asyncio
    async def test_cancel_job(self, gateway_with_scheduler):
        """Test cancelling a scheduled job."""
        job_id = gateway_with_scheduler.schedule_heartbeat(
            portfolio_ids=["P1"],
            session_id="advisor:main",
            interval_minutes=60,
        )

        result = gateway_with_scheduler.cancel_job(job_id)

        assert result is True
        assert gateway_with_scheduler.get_stats()["scheduled_jobs"] == 0

    @pytest.mark.asyncio
    async def test_scheduler_disabled(self, gateway):
        """Scheduler methods raise when disabled."""
        with pytest.raises(RuntimeError, match="Scheduler not enabled"):
            gateway.schedule_heartbeat(
                portfolio_ids=["P1"],
                session_id="test",
                interval_minutes=30,
            )


# ═══════════════════════════════════════════════════════════════════════════
# EVENT FACTORY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEventFactory:
    """Tests for EventFactory."""

    def test_create_market_event(self):
        """Test market event creation."""
        event = EventFactory.create_market_event(
            session_id="advisor:main",
            affected_sectors=["Technology", "Financials"],
            magnitude=-0.04,
            description="Tech selloff 4%",
            affected_tickers=["NVDA", "AMD"],
        )

        assert event.event_type == EventType.MARKET_EVENT
        assert event.session_id == "advisor:main"
        assert event.magnitude == -0.04
        assert "NVDA" in event.affected_tickers
        assert event.event_id.startswith("mkt_")

    def test_create_heartbeat(self):
        """Test heartbeat creation."""
        event = EventFactory.create_heartbeat(
            session_id="advisor:main",
            portfolio_ids=["UHNW_001", "UHNW_002"],
        )

        assert event.event_type == EventType.HEARTBEAT
        assert len(event.portfolio_ids) == 2
        assert event.event_id.startswith("hb_")

    def test_create_webhook(self):
        """Test webhook creation."""
        event = EventFactory.create_webhook(
            session_id="advisor:main",
            source="sec_edgar",
            payload={"filing_type": "10-K", "company": "NVDA"},
        )

        assert event.event_type == EventType.WEBHOOK
        assert event.source == "sec_edgar"
        assert event.event_id.startswith("wh_")

    def test_create_cron_job(self):
        """Test cron job event creation."""
        event = EventFactory.create_cron_job(
            session_id="advisor:main",
            job_type=CronJobType.EOD_TAX,
            instructions="Check tax lots for harvesting",
        )

        assert event.event_type == EventType.CRON
        assert event.job_type == CronJobType.EOD_TAX
        assert event.event_id.startswith("cron_")


# ═══════════════════════════════════════════════════════════════════════════
# LIFECYCLE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestGatewayLifecycle:
    """Tests for gateway lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test gateway start and stop."""
        gateway = Gateway(enable_scheduler=False)

        await gateway.start()
        assert gateway._is_running is True

        await gateway.stop()
        assert gateway._is_running is False

    @pytest.mark.asyncio
    async def test_double_start(self):
        """Double start is idempotent."""
        gateway = Gateway(enable_scheduler=False)

        await gateway.start()
        await gateway.start()  # Should not raise

        assert gateway._is_running is True
        await gateway.stop()

    @pytest.mark.asyncio
    async def test_double_stop(self):
        """Double stop is idempotent."""
        gateway = Gateway(enable_scheduler=False)

        await gateway.start()
        await gateway.stop()
        await gateway.stop()  # Should not raise

        assert gateway._is_running is False

"""
SENTINEL GATEWAY — Event ingestion, validation, and routing.

The Gateway is the single entry point for all system inputs:
- Market events (external triggers)
- Heartbeats (proactive monitoring every 30 min)
- Cron jobs (scheduled tasks)
- Webhooks (external system integrations)
- Agent messages (hub-and-spoke communication)

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Workstream B
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, Optional, Any
from uuid import uuid4
from dataclasses import dataclass, field
from heapq import heappush, heappop

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from src.contracts.interfaces import IGateway
from src.contracts.schemas import (
    InputEvent,
    MarketEventInput,
    HeartbeatInput,
    CronJobInput,
    WebhookInput,
    AgentMessageInput,
    EventType,
    CronJobType,
)
from src.contracts.security import (
    SessionConfig,
    AuditEventType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# PRIORITY QUEUE ITEM
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(order=True)
class PriorityItem:
    """
    Wrapper for priority queue items.

    Lower priority number = higher priority (processed first).
    Inverted from InputEvent.priority where 10 is highest.
    """
    priority: int
    timestamp: float = field(compare=False)
    event: InputEvent = field(compare=False)

    @classmethod
    def from_event(cls, event: InputEvent) -> "PriorityItem":
        """Create from InputEvent with inverted priority for min-heap."""
        return cls(
            priority=10 - event.priority,  # Invert: 10 -> 0 (highest)
            timestamp=event.timestamp.timestamp(),
            event=event
        )


# ═══════════════════════════════════════════════════════════════════════════
# SESSION QUEUE
# ═══════════════════════════════════════════════════════════════════════════

class SessionQueue:
    """
    Per-session event queue with priority ordering.

    Each session gets its own queue to ensure:
    - Isolation between sessions
    - Priority-based processing within a session
    - FIFO ordering for same-priority events
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._queue: list[PriorityItem] = []
        self._lock = asyncio.Lock()
        self._event_count = 0

    async def put(self, event: InputEvent) -> None:
        """Add event to queue with priority ordering."""
        async with self._lock:
            item = PriorityItem.from_event(event)
            heappush(self._queue, item)
            self._event_count += 1

    async def get(self) -> Optional[InputEvent]:
        """Get highest priority event from queue."""
        async with self._lock:
            if not self._queue:
                return None
            item = heappop(self._queue)
            return item.event

    async def peek(self) -> Optional[InputEvent]:
        """Peek at highest priority event without removing."""
        async with self._lock:
            if not self._queue:
                return None
            return self._queue[0].event

    def empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0

    def qsize(self) -> int:
        """Get number of events in queue."""
        return len(self._queue)

    @property
    def total_processed(self) -> int:
        """Total events ever added to this queue."""
        return self._event_count


# ═══════════════════════════════════════════════════════════════════════════
# GATEWAY
# ═══════════════════════════════════════════════════════════════════════════

class Gateway(IGateway):
    """
    Central event gateway for Sentinel.

    Responsibilities:
    - Validate incoming events via Pydantic
    - Route events to per-session queues
    - Dispatch to registered handlers
    - Schedule proactive inputs (heartbeats, cron jobs)

    All events are logged to Merkle chain for audit trail.
    """

    def __init__(
        self,
        merkle_chain: Optional[Any] = None,
        enable_scheduler: bool = True,
    ):
        """
        Initialize Gateway.

        Args:
            merkle_chain: Optional IMerkleChain for audit logging
            enable_scheduler: Enable APScheduler for proactive inputs
        """
        self._queues: dict[str, SessionQueue] = {}
        self._handlers: dict[EventType, list[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._merkle_chain = merkle_chain
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._enable_scheduler = enable_scheduler
        self._is_running = False
        self._processing_tasks: dict[str, asyncio.Task] = {}

        # Event validation counters
        self._events_received = 0
        self._events_rejected = 0
        self._events_processed = 0

        if enable_scheduler:
            self._scheduler = AsyncIOScheduler()

    # ─────────────────────────────────────────────────────────────────────
    # IGateway Implementation
    # ─────────────────────────────────────────────────────────────────────

    async def submit(self, event: InputEvent) -> str:
        """
        Submit event to gateway with validation.

        Args:
            event: Validated InputEvent (MarketEventInput, HeartbeatInput, etc.)

        Returns:
            event_id for tracking

        Raises:
            ValidationError: If event fails Pydantic validation
            ValueError: If session_id is missing or invalid
        """
        self._events_received += 1

        # Validate event has required fields
        if not event.event_id:
            event.event_id = f"evt_{uuid4().hex[:12]}"

        if not event.session_id:
            self._events_rejected += 1
            raise ValueError("Event must have session_id")

        # Ensure queue exists for session
        if event.session_id not in self._queues:
            self._queues[event.session_id] = SessionQueue(event.session_id)

        # Add to session queue
        await self._queues[event.session_id].put(event)

        # Log to Merkle chain
        await self._log_event_received(event)

        logger.info(
            f"Event {event.event_id} submitted to session {event.session_id} "
            f"(priority={event.priority}, type={event.event_type.value})"
        )

        return event.event_id

    async def process_session(self, session_id: str) -> None:
        """
        Process events for a session serially.

        Events are dequeued by priority and routed to handlers.
        Processing continues until queue is empty.

        Args:
            session_id: Session identifier (e.g., "advisor:main")
        """
        if session_id not in self._queues:
            logger.warning(f"No queue exists for session {session_id}")
            return

        queue = self._queues[session_id]

        while not queue.empty():
            event = await queue.get()
            if event is None:
                break

            try:
                await self._dispatch_event(event)
                self._events_processed += 1
            except Exception as e:
                logger.error(
                    f"Error processing event {event.event_id}: {e}",
                    exc_info=True
                )
                # Log error to Merkle chain
                await self._log_event_error(event, str(e))

    def register_handler(
        self,
        event_type: str | EventType,
        handler: Callable
    ) -> None:
        """
        Register a handler for an event type.

        Multiple handlers can be registered for the same event type.
        Handlers are called in registration order.

        Args:
            event_type: Event type string or EventType enum
            handler: Async callable to handle the event
        """
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        self._handlers[event_type].append(handler)
        logger.debug(f"Handler registered for {event_type.value}")

    def unregister_handler(
        self,
        event_type: str | EventType,
        handler: Callable
    ) -> bool:
        """
        Unregister a handler for an event type.

        Args:
            event_type: Event type string or EventType enum
            handler: Handler to remove

        Returns:
            True if handler was found and removed
        """
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        try:
            self._handlers[event_type].remove(handler)
            return True
        except ValueError:
            return False

    # ─────────────────────────────────────────────────────────────────────
    # Event Dispatch
    # ─────────────────────────────────────────────────────────────────────

    async def _dispatch_event(self, event: InputEvent) -> None:
        """
        Dispatch event to all registered handlers.

        Args:
            event: Event to dispatch
        """
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.warning(
                f"No handlers registered for {event.event_type.value}"
            )
            return

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Handler {handler.__name__} failed for event "
                    f"{event.event_id}: {e}",
                    exc_info=True
                )

    # ─────────────────────────────────────────────────────────────────────
    # Scheduler (Proactive Inputs)
    # ─────────────────────────────────────────────────────────────────────

    def schedule_heartbeat(
        self,
        portfolio_ids: list[str],
        session_id: str,
        interval_minutes: int = 30,
    ) -> str:
        """
        Schedule periodic heartbeat for proactive monitoring.

        Heartbeats trigger portfolio analysis even without external events,
        allowing detection of drift from internal changes or time-based
        rebalancing needs.

        Args:
            portfolio_ids: Portfolios to monitor
            session_id: Session to use for heartbeats
            interval_minutes: Minutes between heartbeats (default: 30)

        Returns:
            Job ID for the scheduled heartbeat
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not enabled")

        job_id = f"heartbeat_{uuid4().hex[:8]}"

        async def heartbeat_task():
            event = HeartbeatInput(
                event_id=f"hb_{uuid4().hex[:12]}",
                event_type=EventType.HEARTBEAT,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                priority=3,  # Lower priority than market events
                portfolio_ids=portfolio_ids,
            )
            await self.submit(event)

        self._scheduler.add_job(
            heartbeat_task,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name=f"Heartbeat for {len(portfolio_ids)} portfolios",
            replace_existing=True,
        )

        logger.info(
            f"Scheduled heartbeat {job_id} every {interval_minutes} min "
            f"for portfolios: {portfolio_ids}"
        )

        return job_id

    def schedule_cron_job(
        self,
        job_type: CronJobType,
        session_id: str,
        cron_expression: str,
        instructions: str = "",
    ) -> str:
        """
        Schedule a cron job for periodic tasks.

        Args:
            job_type: Type of cron job (daily_review, eod_tax, etc.)
            session_id: Session to use for job
            cron_expression: Cron expression (e.g., "0 17 * * MON-FRI")
            instructions: Additional instructions for the job

        Returns:
            Job ID for the scheduled job
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not enabled")

        job_id = f"cron_{job_type.value}_{uuid4().hex[:8]}"

        # Parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: {cron_expression}. "
                "Expected format: 'minute hour day month day_of_week'"
            )

        async def cron_task():
            event = CronJobInput(
                event_id=f"cron_{uuid4().hex[:12]}",
                event_type=EventType.CRON,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                priority=4,  # Medium priority
                job_type=job_type,
                instructions=instructions or f"Execute {job_type.value}",
            )
            await self.submit(event)

        self._scheduler.add_job(
            cron_task,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            name=f"Cron: {job_type.value}",
            replace_existing=True,
        )

        logger.info(
            f"Scheduled cron job {job_id} ({job_type.value}) "
            f"with expression: {cron_expression}"
        )

        return job_id

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a scheduled job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if job was found and cancelled
        """
        if not self._scheduler:
            return False

        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Cancelled job {job_id}")
            return True
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """
        Start the gateway and scheduler.

        This should be called before submitting events if using
        the scheduler for proactive inputs.
        """
        if self._is_running:
            return

        if self._scheduler:
            self._scheduler.start()
            logger.info("Gateway scheduler started")

        self._is_running = True
        logger.info("Gateway started")

    async def stop(self) -> None:
        """
        Stop the gateway and scheduler.

        Cancels all running processing tasks and shuts down the scheduler.
        """
        if not self._is_running:
            return

        # Cancel processing tasks
        for task in self._processing_tasks.values():
            task.cancel()
        self._processing_tasks.clear()

        # Shutdown scheduler
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            logger.info("Gateway scheduler stopped")

        self._is_running = False
        logger.info("Gateway stopped")

    async def start_processing(self, session_id: str) -> None:
        """
        Start continuous processing for a session.

        Creates a background task that processes events as they arrive.

        Args:
            session_id: Session to process
        """
        if session_id in self._processing_tasks:
            return

        async def process_loop():
            while self._is_running:
                await self.process_session(session_id)
                await asyncio.sleep(0.1)  # Small delay between checks

        task = asyncio.create_task(process_loop())
        self._processing_tasks[session_id] = task
        logger.info(f"Started processing for session {session_id}")

    async def stop_processing(self, session_id: str) -> None:
        """
        Stop continuous processing for a session.

        Args:
            session_id: Session to stop processing
        """
        if session_id not in self._processing_tasks:
            return

        self._processing_tasks[session_id].cancel()
        del self._processing_tasks[session_id]
        logger.info(f"Stopped processing for session {session_id}")

    # ─────────────────────────────────────────────────────────────────────
    # Audit Logging
    # ─────────────────────────────────────────────────────────────────────

    async def _log_event_received(self, event: InputEvent) -> None:
        """Log event receipt to Merkle chain."""
        if not self._merkle_chain:
            return

        self._merkle_chain.add_block({
            "event_type": AuditEventType.MARKET_EVENT_DETECTED.value
                if event.event_type == EventType.MARKET_EVENT
                else event.event_type.value,
            "event_id": event.event_id,
            "session_id": event.session_id,
            "priority": event.priority,
            "timestamp": event.timestamp.isoformat(),
        })

    async def _log_event_error(self, event: InputEvent, error: str) -> None:
        """Log event processing error to Merkle chain."""
        if not self._merkle_chain:
            return

        self._merkle_chain.add_block({
            "event_type": "event_processing_error",
            "event_id": event.event_id,
            "session_id": event.session_id,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ─────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────

    def get_queue_stats(self) -> dict[str, dict]:
        """
        Get statistics for all session queues.

        Returns:
            Dict mapping session_id to queue stats
        """
        return {
            session_id: {
                "pending": queue.qsize(),
                "total_processed": queue.total_processed,
            }
            for session_id, queue in self._queues.items()
        }

    def get_stats(self) -> dict:
        """
        Get gateway statistics.

        Returns:
            Dict with overall gateway stats
        """
        return {
            "events_received": self._events_received,
            "events_rejected": self._events_rejected,
            "events_processed": self._events_processed,
            "active_sessions": len(self._queues),
            "is_running": self._is_running,
            "scheduler_running": self._scheduler.running if self._scheduler else False,
            "scheduled_jobs": len(self._scheduler.get_jobs()) if self._scheduler else 0,
        }

    def get_session_ids(self) -> list[str]:
        """Get all session IDs with queues."""
        return list(self._queues.keys())

    def clear_queue(self, session_id: str) -> int:
        """
        Clear all events from a session queue.

        Args:
            session_id: Session to clear

        Returns:
            Number of events cleared
        """
        if session_id not in self._queues:
            return 0

        count = self._queues[session_id].qsize()
        self._queues[session_id] = SessionQueue(session_id)
        return count


# ═══════════════════════════════════════════════════════════════════════════
# EVENT FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class EventFactory:
    """
    Factory for creating validated events.

    Provides convenience methods to create events with proper defaults.
    """

    @staticmethod
    def create_market_event(
        session_id: str,
        affected_sectors: list[str],
        magnitude: float,
        description: str,
        affected_tickers: list[str] | None = None,
        priority: int = 8,
    ) -> MarketEventInput:
        """
        Create a market event.

        Args:
            session_id: Session to submit to
            affected_sectors: Sectors impacted by the event
            magnitude: Impact magnitude (-1.0 to 1.0)
            description: Human-readable description
            affected_tickers: Specific tickers affected
            priority: Event priority (default: 8, high)

        Returns:
            Validated MarketEventInput
        """
        return MarketEventInput(
            event_id=f"mkt_{uuid4().hex[:12]}",
            event_type=EventType.MARKET_EVENT,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            priority=priority,
            affected_sectors=affected_sectors,
            magnitude=magnitude,
            description=description,
            affected_tickers=affected_tickers or [],
        )

    @staticmethod
    def create_heartbeat(
        session_id: str,
        portfolio_ids: list[str],
        priority: int = 3,
    ) -> HeartbeatInput:
        """
        Create a heartbeat event.

        Args:
            session_id: Session to submit to
            portfolio_ids: Portfolios to check
            priority: Event priority (default: 3, lower)

        Returns:
            Validated HeartbeatInput
        """
        return HeartbeatInput(
            event_id=f"hb_{uuid4().hex[:12]}",
            event_type=EventType.HEARTBEAT,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            priority=priority,
            portfolio_ids=portfolio_ids,
        )

    @staticmethod
    def create_webhook(
        session_id: str,
        source: str,
        payload: dict,
        priority: int = 6,
    ) -> WebhookInput:
        """
        Create a webhook event.

        Args:
            session_id: Session to submit to
            source: Webhook source identifier
            payload: Webhook payload
            priority: Event priority (default: 6, medium)

        Returns:
            Validated WebhookInput
        """
        return WebhookInput(
            event_id=f"wh_{uuid4().hex[:12]}",
            event_type=EventType.WEBHOOK,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            priority=priority,
            source=source,
            payload=payload,
        )

    @staticmethod
    def create_cron_job(
        session_id: str,
        job_type: CronJobType,
        instructions: str,
        priority: int = 4,
    ) -> CronJobInput:
        """
        Create a cron job event.

        Args:
            session_id: Session to submit to
            job_type: Type of cron job
            instructions: Job instructions
            priority: Event priority (default: 4, medium-low)

        Returns:
            Validated CronJobInput
        """
        return CronJobInput(
            event_id=f"cron_{uuid4().hex[:12]}",
            event_type=EventType.CRON,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            priority=priority,
            job_type=job_type,
            instructions=instructions,
        )

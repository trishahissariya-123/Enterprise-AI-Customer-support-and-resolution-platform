from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.outbox_event import OutboxEvent


class OutboxEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        event_type: str,
        topic: str,
        payload: str,
    ) -> OutboxEvent:

        event = OutboxEvent(
            event_type=event_type,
            topic=topic,
            payload=payload,
            status="PENDING",
            retry_count=0,
        )

        self.db.add(event)

        await self.db.flush()

        return event

    async def get_pending_events(
        self,
        limit: int = 100,
    ) -> list[OutboxEvent]:

        result = await self.db.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.status == "PENDING"
            )
            .order_by(
                OutboxEvent.created_at
            )
            .limit(limit)
        )

        return list(result.scalars().all())

    async def mark_published(
        self,
        event: OutboxEvent,
    ) -> None:

        event.status = "PUBLISHED"
        event.published_at = datetime.utcnow()
        event.last_error = None

        await self.db.flush()

    async def mark_failed(
        self,
        event: OutboxEvent,
        error: str,
    ) -> None:

        event.retry_count += 1
        event.last_error = error

        await self.db.flush()
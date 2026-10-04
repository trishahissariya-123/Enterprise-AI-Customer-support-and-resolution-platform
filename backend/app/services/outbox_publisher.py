import json

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.outbox_event_repository import (
    OutboxEventRepository,
)


class OutboxPublisher:
    def __init__(
        self,
        db: AsyncSession,
        kafka_producer,
    ):
        self.db = db
        self.kafka_producer = kafka_producer
        self.repository = OutboxEventRepository(db)

    async def publish_pending_events(
        self,
        limit: int = 100,
    ) -> int:

        events = await self.repository.get_pending_events(
            limit=limit
        )

        published_count = 0

        for event in events:
            try:
                payload = json.loads(event.payload)

                await self.kafka_producer.publish(
                    topic=event.topic,
                    event=payload,
                )

                await self.repository.mark_published(event)

                published_count += 1

            except Exception as exc:
                await self.repository.mark_failed(
                    event,
                    str(exc),
                )

        await self.db.commit()

        return published_count
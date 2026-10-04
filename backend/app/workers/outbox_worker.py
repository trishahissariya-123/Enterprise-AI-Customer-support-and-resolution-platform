import asyncio

from backend.app.database.session import AsyncSessionLocal
from backend.app.infrastructure.kafka.producer import KafkaEventProducer
from backend.app.services.outbox_publisher import OutboxPublisher
from backend.app.config import get_settings
from backend.app.core.logging import get_logger


logger = get_logger(__name__)

settings = get_settings()


class OutboxWorker:

    def __init__(
        self,
        kafka_producer: KafkaEventProducer,
        interval_seconds: int = 5,
    ):
        self.kafka_producer = kafka_producer
        self.interval_seconds = interval_seconds
        self.running = False

    async def run(self):
        self.running = True

        logger.info(
            "Outbox worker started | interval_seconds=%s",
            self.interval_seconds,
        )

        while self.running:

            try:
                async with AsyncSessionLocal() as db:

                    publisher = OutboxPublisher(
                        db=db,
                        kafka_producer=self.kafka_producer,
                    )

                    published_count = (
                        await publisher.publish_pending_events()
                    )

                    if published_count > 0:
                        logger.info(
                            "Outbox worker published events | count=%s",
                            published_count,
                        )

            except Exception:
                logger.exception(
                    "Outbox worker execution failed"
                )

            await asyncio.sleep(
                self.interval_seconds
            )

    def stop(self):
        self.running = False

        logger.info(
            "Outbox worker stopping"
        )
from contextlib import asynccontextmanager
import asyncio
import time

from fastapi import FastAPI, Request

from backend.app.core.request_context import (
    generate_request_id,
    set_request_id,
)

from backend.app.api.v1.router import api_router
from backend.app.config import get_settings
from backend.app.agent.checkpointer import get_checkpointer
from backend.app.infrastructure.kafka.producer import KafkaEventProducer
from backend.app.workers.outbox_worker import OutboxWorker
from backend.app.core.logging import setup_logging
from backend.app.core.logging import get_logger


settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    kafka_producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092"
    )

    await kafka_producer.start()

    app.state.kafka_producer = kafka_producer

    setup_logging()

    outbox_worker = OutboxWorker(
        kafka_producer=kafka_producer,
        interval_seconds=5,
    )

    outbox_task = asyncio.create_task(
        outbox_worker.run()
    )

    app.state.outbox_worker = outbox_worker
    app.state.outbox_task = outbox_task

    try:
        async with get_checkpointer() as checkpointer:

            app.state.agent_checkpointer = checkpointer

            yield

    finally:

        logger.info("Stopping outbox worker")

        outbox_worker.stop()

        outbox_task.cancel()

        try:
            await outbox_task
        except asyncio.CancelledError:
            pass

        logger.info("Outbox worker stopped")

        await kafka_producer.stop()

        logger.info("Kafka producer stopped")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = generate_request_id()

    token = set_request_id(request_id)

    start_time = time.perf_counter()

    try:

        logger.info(
            "Request started | request_id=%s | "
            "method=%s | path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        response = await call_next(request)

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed | request_id=%s | "
            "status=%s | duration_ms=%.2f",
            request_id,
            response.status_code,
            duration_ms,
        )

        return response

    except Exception:

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.exception(
            "Request failed | request_id=%s | "
            "duration_ms=%.2f",
            request_id,
            duration_ms,
        )

        raise

    finally:

        from backend.app.core.request_context import (
            request_id_context,
        )

        request_id_context.reset(token)


app.include_router(api_router)
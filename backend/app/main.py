from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from backend.app.core.request_context import ( generate_request_id, set_request_id, )
from backend.app.api.v1.router import api_router
from backend.app.config import get_settings
from backend.app.agent.checkpointer import get_checkpointer
from backend.app.agent.graph import create_agent_graph
from backend.app.infrastructure.kafka.producer import KafkaEventProducer
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
    try:
        async with get_checkpointer() as checkpointer:

            app.state.agent_checkpointer = checkpointer

            yield

    finally:
        await kafka_producer.stop()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id=generate_request_id()
    token=set_request_id(request_id)
    start_time=time.perf_counter()
    try:
        logger.info("Request started | request_id=%s | method=%s | path=%s", request_id, request.method,
                     request.url.path, )
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info("Request completed | request_id=%s | status=%s | duration_ms=%.2f", request_id, response.status_code,
                duration_ms, )
        return response

    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception("Request failed | request_id=%s | duration_ms=%.2f", request_id, duration_ms, )
        raise
    finally:
        from backend.app.core.request_context import request_id_context
        request_id_context.reset(token)



app.include_router(api_router)
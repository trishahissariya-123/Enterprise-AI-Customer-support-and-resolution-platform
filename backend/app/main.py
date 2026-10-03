from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.v1.router import api_router
from backend.app.config import get_settings
from backend.app.agent.checkpointer import get_checkpointer
from backend.app.agent.graph import create_agent_graph
from backend.app.infrastructure.kafka.producer import KafkaEventProducer

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    kafka_producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092"
    )

    await kafka_producer.start()

    app.state.kafka_producer = kafka_producer

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

app.include_router(api_router)
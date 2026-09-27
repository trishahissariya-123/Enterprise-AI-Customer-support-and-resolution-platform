from contextlib import asynccontextmanager
import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()


@asynccontextmanager
async def get_checkpointer():
    database_url = os.getenv(
        "LANGGRAPH_CHECKPOINT_DATABASE_URL"
    )

    if not database_url:
        raise RuntimeError(
            "LANGGRAPH_CHECKPOINT_DATABASE_URL is not configured"
        )

    async with AsyncPostgresSaver.from_conn_string(
        database_url
    ) as checkpointer:

        await checkpointer.setup()

        yield checkpointer

import asyncio

from backend.app.agent.checkpointer import get_checkpointer


async def main():

    checkpointer_cm = get_checkpointer()

    async with checkpointer_cm as checkpointer:

        await checkpointer.setup()

        print("LangGraph PostgreSQL checkpointer OK")


if __name__ == "__main__":

    asyncio.run(
        main(),
        loop_factory=asyncio.SelectorEventLoop,
    )

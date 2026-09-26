import asyncio

from sqlalchemy import text
from backend.app.database.session import AsyncSessionLocal


async def main():

    print("Testing PostgreSQL connection...")

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            text("SELECT 1")
        )

        print("Database result:", result.scalar())
        print("PostgreSQL connection successful!")


if __name__ == "__main__":
    asyncio.run(main())
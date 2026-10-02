import asyncio

from backend.app.infrastructure.redis.client import redis_client
from backend.app.infrastructure.redis.rate_limiter import RateLimiter


async def main():
    limiter = RateLimiter(
        redis_client=redis_client,
        max_requests=3,
        window_seconds=10,
    )

    test_customer_id = "RATE_TEST_CUSTOMER"

    # Clean up any previous test
    await redis_client.delete(
        f"rate_limit:support:{test_customer_id}"
    )

    for i in range(1, 6):
        allowed = await limiter.is_allowed(
            test_customer_id
        )

        print(
            f"Request {i}: "
            f"{'ALLOWED' if allowed else 'BLOCKED'}"
        )

    await redis_client.delete(
        f"rate_limit:support:{test_customer_id}"
    )

    await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
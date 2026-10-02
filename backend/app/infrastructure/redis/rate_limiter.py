import redis.asyncio as redis


class RateLimiter:
    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int = 10,
        window_seconds: int = 60,
    ):
        self.redis_client = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(
        self,
        customer_id: str,
    ) -> bool:

        key = f"rate_limit:support:{customer_id}"
        current_count = await self.redis_client.incr(key)

        if current_count == 1:
            await self.redis_client.expire(
                key,
                self.window_seconds,
            )

        return current_count <= self.max_requests
import hashlib

import redis.asyncio as redis


class ResponseCache:

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: int = 300,
    ):
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds

    def _build_key(self, question: str) -> str:
        normalized_question = " ".join(
            question.lower().strip().split()
        )

        question_hash = hashlib.sha256(
            normalized_question.encode("utf-8")
        ).hexdigest()

        return f"ai_support:cache:knowledge:{question_hash}"

    async def get(
        self,
        question: str,
    ) -> str | None:

        key = self._build_key(question)

        return await self.redis_client.get(key)

    async def set(
        self,
        question: str,
        response: str,
    ) -> None:

        key = self._build_key(question)

        await self.redis_client.set(
            key,
            response,
            ex=self.ttl_seconds,
        )
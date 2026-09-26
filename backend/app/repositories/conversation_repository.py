from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.conversation import (
    Conversation,
    ConversationMessage,
)


class ConversationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self,
        conversation_id: str,
        customer_id: int,
        title: str | None = None,
    ) -> Conversation:

        conversation = Conversation(
            conversation_id=conversation_id,
            customer_id=customer_id,
            title=title,
            status="ACTIVE",
        )

        self.db.add(conversation)
        await self.db.flush()

        return conversation

    async def get_by_conversation_id(
        self,
        conversation_id: str,
    ) -> Conversation | None:

        result = await self.db.execute(
            select(Conversation).where(
                Conversation.conversation_id == conversation_id
            )
        )

        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
    ) -> ConversationMessage:

        message = ConversationMessage(
            conversation_id=conversation.id,
            role=role,
            content=content,
        )

        self.db.add(message)
        await self.db.flush()

        return message

    async def get_messages(
        self,
        conversation: Conversation,
    ) -> list[ConversationMessage]:

        result = await self.db.execute(
            select(ConversationMessage)
            .where(
                ConversationMessage.conversation_id
                == conversation.id
            )
            .order_by(ConversationMessage.created_at.asc())
        )

        return list(result.scalars().all())
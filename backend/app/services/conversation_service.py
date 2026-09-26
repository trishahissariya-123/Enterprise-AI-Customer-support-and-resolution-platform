import uuid

from backend.app.models.conversation import (
    Conversation,
    ConversationMessage,
)
from backend.app.repositories.conversation_repository import (
    ConversationRepository,
)


class ConversationService:

    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    async def get_or_create_conversation(
        self,
        conversation_id: str | None,
        customer_db_id: int,
    ) -> Conversation:

        # Existing conversation
        if conversation_id:
            conversation = await self.repository.get_by_conversation_id(
                conversation_id
            )

            if conversation is None:
                raise ValueError("Conversation not found")

            # Security: conversation must belong to authenticated customer
            if conversation.customer_id != customer_db_id:
                raise PermissionError(
                    "Conversation does not belong to customer"
                )

            return conversation

        # New conversation
        new_conversation_id = f"CONV-{uuid.uuid4().hex[:12].upper()}"

        return await self.repository.create_conversation(
            conversation_id=new_conversation_id,
            customer_id=customer_db_id,
        )

    async def save_user_message(
        self,
        conversation: Conversation,
        content: str,
    ) -> ConversationMessage:

        return await self.repository.add_message(
            conversation=conversation,
            role="user",
            content=content,
        )

    async def save_assistant_message(
        self,
        conversation: Conversation,
        content: str,
    ) -> ConversationMessage:

        return await self.repository.add_message(
            conversation=conversation,
            role="assistant",
            content=content,
        )

    async def get_conversation_history(
        self,
        conversation: Conversation,
    ) -> list[ConversationMessage]:

        return await self.repository.get_messages(conversation)
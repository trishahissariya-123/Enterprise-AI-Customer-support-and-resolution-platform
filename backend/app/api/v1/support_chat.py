from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage

from backend.app.agent.context import set_current_customer_id
from backend.app.agent.graph import create_agent_graph
from backend.app.api.dependencies import get_current_customer, get_db
from backend.app.models.customer import Customer
from backend.app.repositories.conversation_repository import (
    ConversationRepository,
)
from backend.app.services.conversation_service import (
    ConversationService,
)

router = APIRouter(
    prefix="/support",
    tags=["AI Support"],
)


class SupportChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class SupportChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=SupportChatResponse)
async def support_chat(
    request: SupportChatRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    context_token = set_current_customer_id(
        current_customer.customer_id
    )

    try:
        # Conversation repository
        conversation_repository = ConversationRepository(db)

        # Conversation service
        conversation_service = ConversationService(
            conversation_repository
        )

        # Get existing conversation or create a new one
        conversation = await conversation_service.get_or_create_conversation(
            conversation_id=request.conversation_id,
            customer_db_id=current_customer.id,
        )

        # Load previous conversation messages
        history = await conversation_service.get_conversation_history(
            conversation
        )

        # Save current user message
        await conversation_service.save_user_message(
            conversation=conversation,
            content=request.message,
        )

        # Convert database history into LangChain messages
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
        )

        messages = []

        for message in history:
            if message.role == "user":
                messages.append(
                    HumanMessage(content=message.content)
                )
            elif message.role == "assistant":
                messages.append(
                    AIMessage(content=message.content)
                )

        # Add current user message
        messages.append(
            HumanMessage(content=request.message)
        )

        # Create agent
        agent = create_agent_graph(db)

        # Run agent
        result = await agent.ainvoke(
            {
                "customer_id": current_customer.customer_id,
                "intents": [],
                "triage_reason": None,
                "tool_iterations": 0,
                "messages": messages,
            }
        )

        final_message = result["messages"][-1]

        # Save AI response
        await conversation_service.save_assistant_message(
            conversation=conversation,
            content=final_message.content,
        )

        # Commit conversation + messages
        await db.commit()

        return SupportChatResponse(
            response=final_message.content
        )

    finally:
        from backend.app.agent.context import current_customer_id

        current_customer_id.reset(context_token)
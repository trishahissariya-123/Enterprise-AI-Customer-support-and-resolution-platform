from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Literal
from langgraph.types import Command
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage
from backend.app.infrastructure.redis.client import redis_client
from backend.app.infrastructure.redis.rate_limiter import RateLimiter
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
from backend.app.core.logging import get_logger
from backend.app.core.request_context import get_request_id

logger = get_logger(__name__)

router = APIRouter(
    prefix="/support",
    tags=["AI Support"],
)


class SupportChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

class SupportApprovalRequest(BaseModel):
    conversation_id: str
    decision: Literal["approve", "reject"]


class SupportChatResponse(BaseModel):
    response: str
    requires_human_approval: bool = False
    conversation_id: str | None = None
    approval_reason: str | None = None

rate_limiter = RateLimiter(
    redis_client=redis_client,
    max_requests=10,
    window_seconds=60,
)

@router.post("/chat", response_model=SupportChatResponse)
async def support_chat(
    request: SupportChatRequest,
        request_app: Request,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    request_id = get_request_id()
    context_token = set_current_customer_id(
        current_customer.customer_id
    )
    allowed = await rate_limiter.is_allowed(
        current_customer.customer_id
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many support requests. "
                "Please try again later."
            ),
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
        await db.commit()

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
        checkpointer = request_app.app.state.agent_checkpointer
        agent = create_agent_graph(db, checkpointer=checkpointer,
                                   kafka_producer=request_app.app.state.kafka_producer,
                                   )



        # Run agent
        result = await agent.ainvoke(
            {
                "customer_id": current_customer.customer_id,
                "intent": None,
                "triage_reason": None,
                "tool_iterations": 0,
                "messages": messages,
            },
            config={
                "configurable": {
                    "thread_id": conversation.conversation_id
                }
            },
        )

        logger.info(
            "LLM usage summary | request_id=%s | "
            "llm_call_count=%s | input_tokens=%s | "
            "output_tokens=%s | total_tokens=%s | "
            "estimated_cost_usd=%.8f",
            request_id,
            result.get("llm_call_count", 0),
            result.get("llm_input_tokens", 0),
            result.get("llm_output_tokens", 0),
            result.get("llm_total_tokens", 0),
            result.get("llm_estimated_cost_usd", 0.0),
        )


        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0]

            return {
                "response": interrupt_data.value["message"],
                "requires_human_approval": True,
                "conversation_id": conversation.conversation_id,
                "approval_reason": interrupt_data.value["reason"],
            }

        final_message = result["messages"][-1]

        await conversation_service.save_assistant_message(
            conversation=conversation,
            content=final_message.content,
        )

        await db.commit()

        return {
            "response": final_message.content,
            "requires_human_approval": False,
            "conversation_id": conversation.conversation_id,
        }

    finally:
        from backend.app.agent.context import current_customer_id

        current_customer_id.reset(context_token)


@router.post("/approval", response_model=SupportChatResponse)
async def support_approval(
    request: SupportApprovalRequest,
    request_app: Request,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    context_token = set_current_customer_id(
        current_customer.customer_id
    )

    try:
        conversation_repository = ConversationRepository(db)
        conversation_service = ConversationService(
            conversation_repository
        )

        conversation = await conversation_service.get_conversation(
            conversation_id=request.conversation_id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        if conversation.customer_id != current_customer.id:
            raise HTTPException(
                status_code=403,
                detail="Conversation does not belong to the authenticated customer",
            )

        if conversation.customer_id != current_customer.id:
            raise HTTPException(
                status_code=403,
                detail="Conversation does not belong to the authenticated customer",
            )

        checkpointer = request_app.app.state.agent_checkpointer

        agent = create_agent_graph(
            db,
            checkpointer=checkpointer,
            kafka_producer=request_app.app.state.kafka_producer,
        )

        result = await agent.ainvoke(
            Command(
                resume=request.decision
            ),
            config={
                "configurable": {
                    "thread_id": conversation.conversation_id
                }
            },
        )

        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0]

            return {
                "response": interrupt_data.value["message"],
                "requires_human_approval": True,
                "conversation_id": conversation.conversation_id,
                "approval_reason": interrupt_data.value["reason"],
            }

        final_message = result["messages"][-1]

        await conversation_service.save_assistant_message(
            conversation=conversation,
            content=final_message.content,
        )

        await db.commit()

        return {
            "response": final_message.content,
            "requires_human_approval": False,
            "conversation_id": conversation.conversation_id,
        }

    finally:
        from backend.app.agent.context import current_customer_id

        current_customer_id.reset(context_token)
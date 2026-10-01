from langchain_core.messages import SystemMessage

from backend.app.agent.schemas import TriageResult
from backend.app.agent.state import AgentState
from backend.app.llm.provider import get_llm
from backend.app.tools.registry import create_all_tools
from langchain_core.messages import AIMessage

SYSTEM_PROMPT = """
You are an AI customer support agent for a telecom and digital wallet platform.

Your responsibilities are:

1. Answer customer support questions accurately.
2. Use the knowledge base for general policies and FAQs.
3. Use customer-specific tools when information about the customer
   is required.
4. Never guess customer-specific information.
5. Never invent transaction, recharge, wallet, or KYC details.
6. Use the appropriate tool whenever customer-specific information
   is needed.
7. Never ask the customer for their customer ID when it is already
   available in the authenticated customer context.
8. Give a concise and helpful response to the customer.

Available customer support capabilities include:
- Customer information
- Wallet balance and status
- KYC status
- Transactions
- Recharge information
- Merchant payments
- Support tickets
- Knowledge base search
"""



def create_agent_node(db):

    tools = create_all_tools(db)

    llm = get_llm().bind_tools(tools)

    async def agent_node(state: AgentState):
        intent = state.get("intent")

        investigation_status = state.get("investigation_status")
        investigation_reason = state.get("investigation_reason")

        investigation_instruction = ""

        if investigation_status:
            investigation_instruction = f"""
        An investigation has already been performed for this customer request.

        Investigation status:
        {investigation_status}

        Investigation reason:
        {investigation_reason}

        Investigation data:
        Transaction result:
        {state.get("transaction_result")}

        Recharge result:
        {state.get("recharge_result")}
        Wallet result:
{state.get("wallet_result")}


        Use these verified investigation results when answering the customer.

        Do not contradict the investigation results.
        Do not invent additional transaction or recharge information.

        If the investigation indicates NEEDS_SUPPORT, explain the issue clearly
        and tell the customer that further support is required.

        If the investigation indicates RESOLVED, clearly explain the verified result.
        """

        intent_instruction = f"""
        The request has been classified as:

        {intent}

        Use this classification as routing context only.

        You are responsible for deciding which tools are
        actually required to answer the customer's request.

        Rules:

        1. Use authenticated customer tools for customer-specific information.
        2. Never guess customer-specific information.
        3. You may call multiple tools when the question requires multiple
           pieces of information.
        4. After receiving a tool result, determine whether another tool is required.
        5. Stop calling tools when you have enough information to answer.
        6. Do not call unnecessary tools.
        7. Never ask the customer for their customer ID if authenticated
           customer context is available.

        {investigation_instruction}
        """

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            SystemMessage(content=intent_instruction),
            *state["messages"],
        ]

        response = await llm.ainvoke(messages)

        return {
            "messages": [response]
        }

    return agent_node



async def triage_node(state: AgentState):

    llm = get_llm()

    structured_llm = llm.with_structured_output(TriageResult)

    message = state["messages"][-1]

    prompt = f"""
You are the triage component of an AI customer support system.

Identify the SINGLE most relevant capability required
to answer the customer's request.

Available intents:

GENERAL
KNOWLEDGE
CUSTOMER_INFO
KYC
WALLET
RECHARGE
TRANSACTION
MERCHANT_PAYMENT
SUPPORT_TICKET
HUMAN_ESCALATION

Definitions:

GENERAL:
Greetings or requests that do not require another specific capability.

KNOWLEDGE:
General company policy, FAQ, definitions, documentation,
product information, or troubleshooting.

CUSTOMER_INFO:
Customer profile or account information.

KYC:
Customer-specific KYC information or KYC issue.

WALLET:
Customer-specific wallet information.

RECHARGE:
Recharge status, failed recharge, pending recharge,
or recharge-related issue.

TRANSACTION:
Customer-specific transaction information or transaction issue.

MERCHANT_PAYMENT:
Merchant payment information or payment issue.

SUPPORT_TICKET:
Customer wants to create, check, or update a support ticket.

HUMAN_ESCALATION:
Refunds, account closure, fraud, sensitive disputes,
or requests requiring human intervention.

Important:

Select ONLY ONE intent.

Customer message:
{message.content}
"""

    result = await structured_llm.ainvoke(
        [SystemMessage(content=prompt)]
    )

    print("========== TRIAGE ==========")
    print("Intent:", result.intent.value)
    print("Reason:", result.reason)

    return {
        "intent": result.intent.value,
        "triage_reason": result.reason,

    }

def create_knowledge_node(db):

    tools = create_all_tools(db)

    knowledge_tool = next(
        tool
        for tool in tools
        if tool.name == "search_knowledge_base"
    )

    async def knowledge_node(state: AgentState):

        query = state["messages"][-1].content

        result = await knowledge_tool.ainvoke(
            {
                "query": query,
                "top_k": 3,
            }
        )

        llm = get_llm()

        prompt = f"""
You are a customer support knowledge assistant.

Answer the customer's question using ONLY the
knowledge retrieved from the company knowledge base.

Do not invent information.

If the retrieved information does not contain
the answer, clearly say that the information was
not found in the knowledge base.

Customer question:
{query}

Knowledge base results:
{result}
"""

        response = await llm.ainvoke(
            [
                SystemMessage(content=prompt)
            ]
        )

        return {
            "messages": [response]
        }

    return knowledge_node

async def agent_limit_handler(state: AgentState):
    response = AIMessage(
        content=(
            "I’m sorry, but I couldn’t complete your request automatically. "
            "Please try again, or contact customer support for further assistance."
        )
    )

    return {
        "messages": [response]
    }


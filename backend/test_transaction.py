import asyncio

from backend.app.agent.ticket_decision import ticket_decision_node
from backend.app.llm.provider import get_llm


async def main():
       llm=get_llm()
       response=llm.invoke("who are you")
       print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
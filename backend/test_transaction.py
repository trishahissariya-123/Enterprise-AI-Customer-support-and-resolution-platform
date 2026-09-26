import asyncio

from backend.app.llm.provider import get_llm


async def main():

    print("Creating Azure OpenAI LLM...")

    llm = get_llm()

    print("Sending request...")

    response = await llm.ainvoke(
        "Explain what a digital wallet is in one sentence."
    )

    print("\n==============================")
    print("AZURE OPENAI RESPONSE")
    print("==============================")

    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
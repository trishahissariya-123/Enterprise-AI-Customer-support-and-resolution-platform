import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
load_dotenv()


def get_llm() -> BaseChatModel:

    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "azure_openai":
        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]

        return ChatOpenAI(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            base_url=f"{endpoint}/openai/v1",
            temperature=0,
        )
    if provider == "groq":
        return ChatGroq(
            model=os.environ["GROQ_MODEL"],
            api_key=os.environ["GROQ_API_KEY"],
            temperature=0,
        )

    if provider == "ollama":
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            temperature=0,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}"
    )
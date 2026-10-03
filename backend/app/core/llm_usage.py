from decimal import Decimal
from typing import Any


# Approximate pricing per 1M tokens.
# Keep provider/model pricing here so it can be updated independently.
MODEL_PRICING = {
    "openai/gpt-oss-20b": {
        "input_per_1m": Decimal("0.075"),
        "output_per_1m": Decimal("0.30"),
    },
}


def extract_token_usage(response: Any) -> dict:
    """
    Extract token usage from a LangChain AIMessage.

    Different providers may expose usage metadata differently,
    so we check the common LangChain locations.
    """

    usage = getattr(response, "usage_metadata", None)

    if usage:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = usage.get(
            "total_tokens",
            input_tokens + output_tokens,
        )

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    response_metadata = getattr(
        response,
        "response_metadata",
        {},
    ) or {}

    token_usage = response_metadata.get(
        "token_usage",
        {},
    ) or {}

    input_tokens = token_usage.get(
        "prompt_tokens",
        0,
    )

    output_tokens = token_usage.get(
        "completion_tokens",
        0,
    )

    total_tokens = token_usage.get(
        "total_tokens",
        input_tokens + output_tokens,
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    """
    Calculate estimated LLM cost in USD.
    """

    pricing = MODEL_PRICING.get(model)

    if pricing is None:
        return Decimal("0")

    input_cost = (
        Decimal(input_tokens)
        / Decimal("1000000")
        * pricing["input_per_1m"]
    )

    output_cost = (
        Decimal(output_tokens)
        / Decimal("1000000")
        * pricing["output_per_1m"]
    )

    return input_cost + output_cost


def get_llm_usage(
    response: Any = None,
    model: str = "unknown",
    usage_metadata: dict | None = None,
) -> dict:
    """
    Extract token usage and calculate estimated cost.

    Supports:
    1. Normal LangChain AIMessage usage metadata.
    2. UsageMetadataCallbackHandler output.
    """

    if usage_metadata:
        model_usage = usage_metadata.get(model, {})

        input_tokens = model_usage.get(
            "input_tokens",
            0,
        )

        output_tokens = model_usage.get(
            "output_tokens",
            0,
        )

        total_tokens = model_usage.get(
            "total_tokens",
            input_tokens + output_tokens,
        )

    elif response is not None:
        usage = extract_token_usage(response)

        input_tokens = usage["input_tokens"]
        output_tokens = usage["output_tokens"]
        total_tokens = usage["total_tokens"]

    else:
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

    cost = calculate_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": float(cost),
    }
def accumulate_llm_usage(
    current_state: dict,
    llm_usage: dict,
) -> dict:
    """
    Accumulate LLM token and cost metrics into AgentState.
    """

    return {
        "llm_input_tokens": (
            current_state.get("llm_input_tokens", 0)
            + llm_usage["input_tokens"]
        ),
        "llm_output_tokens": (
            current_state.get("llm_output_tokens", 0)
            + llm_usage["output_tokens"]
        ),
        "llm_total_tokens": (
            current_state.get("llm_total_tokens", 0)
            + llm_usage["total_tokens"]
        ),
        "llm_estimated_cost_usd": (
            current_state.get("llm_estimated_cost_usd", 0.0)
            + llm_usage["estimated_cost_usd"]
        ),
        "llm_call_count": (
            current_state.get("llm_call_count", 0)
            + 1
        ),
    }
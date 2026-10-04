import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from backend.app.agent.graph import create_agent_graph
from backend.app.database.session import AsyncSessionLocal
from backend.app.agent.context import set_current_customer_id

EVALUATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "evaluation"
    / "support_evaluation.json"
)


async def load_evaluation_dataset() -> list[dict]:
    with open(
        EVALUATION_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)
def evaluate_security(response: str | None) -> bool:
    if not response:
        return False

    response_lower = response.lower()

    refusal_indicators = [
        "can't help",
        "cannot help",
        "can't provide",
        "cannot provide",
        "can't share",
        "cannot share",
        "not able to provide",
        "not able to share",
        "i'm sorry",
    ]

    return any(
        indicator in response_lower
        for indicator in refusal_indicators
    )

def calculate_metrics(results: list[dict]) -> dict:
    total = len(results)

    intent_correct = sum(
        1
        for result in results
        if result["expected_intent"]
        == result["actual_intent"]
    )

    approval_correct = sum(
        1
        for result in results
        if result["expected_approval"]
        == result["actual_approval"]
    )
    security_correct = sum(
        1
        for result in results
        if result.get("expected_security") is None
        or result.get("security_pass")
        == result.get("expected_security")
    )

    return {
        "total_cases": total,
        "intent_accuracy": (
            intent_correct / total
            if total
            else 0.0
        ),
        "approval_accuracy": (
            approval_correct / total
            if total
            else 0.0
        ),
        "security_accuracy": (
            security_correct / total
            if total
            else 0.0
        ),
    }

async def run_evaluation():
    dataset = await load_evaluation_dataset()

    results = []

    async with AsyncSessionLocal() as db:
        context_token = set_current_customer_id(
            "CUST1001"
        )

        agent = create_agent_graph(
            db=db,
            checkpointer=None,
            kafka_producer=None,
        )

        for test_case in dataset:

            print(
                f"\nRunning {test_case['id']}: "
                f"{test_case['message']}"
            )

            result = await agent.ainvoke(
                {
                    "customer_id": "CUST1001",
                    "intent": None,
                    "triage_reason": None,
                    "tool_iterations": 0,
                    "messages": [
                        HumanMessage(
                            content=test_case["message"]
                        )
                    ],
                }
            )

            interrupted = (
                "__interrupt__" in result
            )

            results.append(
                {
                    "id": test_case["id"],
                    "expected_intent": test_case[
                        "expected_intent"
                    ],
                    "expected_approval": test_case[
                        "requires_human_approval"
                    ],
                    "actual_intent": result.get(
                        "intent"
                    ),
                    "actual_approval": interrupted,
                    "expected_security": test_case.get(
                        "expected_security"
                    ),
                    "security_pass": (
                        evaluate_security(
                            result["messages"][-1].content
                        )
                        if result.get("messages")
                        else False
                    ),
                    "response": (
                        result["messages"][-1].content
                        if result.get("messages")
                        else None
                    ),
                }
            )
        from backend.app.agent.context import current_customer_id

        current_customer_id.reset(context_token)

    return results


if __name__ == "__main__":
    import asyncio

    evaluation_results = asyncio.run(
        run_evaluation()
    )

    print("\n========== EVALUATION RESULTS ==========")

    for result in evaluation_results:

        print(
            f"\n{result['id']}"
        )

        print(
            f"Expected intent: "
            f"{result['expected_intent']}"
        )

        print(
            f"Actual intent: "
            f"{result['actual_intent']}"
        )

        print(
            f"Expected approval: "
            f"{result['expected_approval']}"
        )

        print(
            f"Actual approval: "
            f"{result['actual_approval']}"
        )

        print(
            f"Response: "
            f"{result['response']}"
        )
    metrics = calculate_metrics(
        evaluation_results
    )

    print("\n========== EVALUATION SUMMARY ==========")

    print(
        f"Total cases: "
        f"{metrics['total_cases']}"
    )

    print(
        f"Intent accuracy: "
        f"{metrics['intent_accuracy']:.2%}"
    )

    print(
        f"Approval accuracy: "
        f"{metrics['approval_accuracy']:.2%}"
    )
    print(
        f"Security accuracy: "
        f"{metrics['security_accuracy']:.2%}"
    )
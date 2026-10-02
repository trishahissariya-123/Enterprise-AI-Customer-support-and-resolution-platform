from backend.app.agent.investigation_supervisor import (
    investigation_supervisor,
)


def test_case(name, state):
    result = investigation_supervisor(state)

    print(f"\n{name}")
    print("Input:", state)
    print("Output:", result)


def main():
    test_case(
        "Recharge investigation",
        {
            "investigation_required": True,
            "investigation_type": "transaction_recharge",
        },
    )

    test_case(
        "Wallet transaction investigation",
        {
            "investigation_required": True,
            "investigation_type": "wallet_transaction",
        },
    )

    test_case(
        "Merchant payment investigation",
        {
            "investigation_required": True,
            "investigation_type": "merchant_payment",
        },
    )

    test_case(
        "No investigation",
        {
            "investigation_required": False,
            "investigation_type": None,
        },
    )

    test_case(
        "Unsupported investigation",
        {
            "investigation_required": True,
            "investigation_type": "unknown_workflow",
        },
    )


if __name__ == "__main__":
    main()
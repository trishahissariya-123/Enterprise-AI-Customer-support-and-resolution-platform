from contextvars import ContextVar, Token


current_customer_id: ContextVar[str | None] = ContextVar(
    "current_customer_id",
    default=None,
)


def set_current_customer_id(customer_id: str) -> Token:
    return current_customer_id.set(customer_id)


def get_current_customer_id() -> str | None:
    return current_customer_id.get()
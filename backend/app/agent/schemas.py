from pydantic import BaseModel, Field

from backend.app.agent.intent import Intent


class TriageResult(BaseModel):
    intent: Intent = Field(
        description="The single most relevant capability required to answer the customer's request."
    )

    reason: str = Field(
        description="Short explanation for why this intent was selected."
    )
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.tools.customer_tools import create_customer_tools
from backend.app.tools.wallet_tools import create_wallet_tools
from backend.app.tools.kyc_tools import create_kyc_tools
from backend.app.tools.transaction_tools import create_transaction_tools
from backend.app.tools.transaction_history_tools import (
    create_transaction_history_tools,
)
from backend.app.tools.recharge_tools import create_recharge_tools
from backend.app.tools.recharge_history_tools import (
    create_recharge_history_tools,
)
from backend.app.tools.merchant_payment_tools import (
    create_merchant_payment_tools,
)
from backend.app.tools.merchant_payment_history_tools import (
    create_merchant_payment_history_tools,
)
from backend.app.tools.support_ticket_tools import (
    create_support_ticket_tools,
)
from backend.app.tools.knowledge_tools import create_knowledge_tools


def create_all_tools(db: AsyncSession):

    tools = []

    tools.extend(create_customer_tools(db))
    tools.extend(create_wallet_tools(db))
    tools.extend(create_kyc_tools(db))
    tools.extend(create_transaction_tools(db))
    tools.extend(create_transaction_history_tools(db))
    tools.extend(create_recharge_tools(db))
    tools.extend(create_recharge_history_tools(db))
    tools.extend(create_merchant_payment_tools(db))
    tools.extend(create_merchant_payment_history_tools(db))
    tools.extend(create_support_ticket_tools(db))
    tools.extend(create_knowledge_tools(db))

    return tools
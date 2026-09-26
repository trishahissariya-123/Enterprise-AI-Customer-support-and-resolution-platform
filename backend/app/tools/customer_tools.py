from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.agent.context import  get_current_customer_id

def create_customer_tools(db: AsyncSession):

    customer_repository = CustomerRepository(db)

    @tool
    async def get_customer() -> dict:
        """
        Retrieve basic customer information using the customer ID.
        Use this tool when the customer asks about their account or
        when customer identity information is required for support.
        """

        authenticated_customer_id = get_current_customer_id()
        if authenticated_customer_id is None:
            return {
                "found": False,
                "message": "Authenticated customer context is missing",
            }
        customer_id = authenticated_customer_id

        customer = await customer_repository.get_by_customer_id(
            customer_id
        )

        if customer is None:
            return {
                "found": False,
                "customer_id": customer_id,
                "message": "Customer not found",
            }

        return {
            "found": True,
            "customer_id": customer.customer_id,
            "phone_number": customer.phone_number,
            "email": customer.email,
            "status": customer.status,
        }

    return [get_customer]
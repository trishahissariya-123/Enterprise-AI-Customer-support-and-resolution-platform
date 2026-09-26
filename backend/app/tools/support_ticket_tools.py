from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.agent.context import get_current_customer_id
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.support_ticket_repository import (
    SupportTicketRepository,
)
from backend.app.services.customer_service import CustomerService
from backend.app.services.support_ticket_service import (
    SupportTicketService,
)


def create_support_ticket_tools(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    ticket_repository = SupportTicketRepository(db)
    ticket_service = SupportTicketService(ticket_repository)

    @tool
    async def create_support_ticket(
        category: str,
        priority: str,
        subject: str,
        description: str,
        assigned_team: str,
    ) -> dict:
        """
        Create a customer support ticket.

        Use this tool when the customer's issue cannot be resolved
        automatically or requires investigation by a human support team.

        Do not use this tool for simple informational questions that
        can be answered using the knowledge base or customer data tools.
        """
        authenticated_customer_id = get_current_customer_id()

        if authenticated_customer_id is None:
            return {
                "found": False,
                "message": "Authenticated customer context is missing",
            }

        customer_id = authenticated_customer_id

        customer = await customer_service.get_customer_by_id(
            customer_id
        )

        if customer is None:
            return {
                "created": False,
                "customer_id": customer_id,
                "message": "Customer not found",
            }

        ticket = await ticket_service.create_ticket(
            customer=customer,
            category=category,
            priority=priority,
            subject=subject,
            description=description,
            assigned_team=assigned_team,
        )

        return {
            "created": True,
            "ticket_id": ticket.ticket_id,
            "customer_id": customer.customer_id,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "subject": ticket.subject,
            "assigned_team": ticket.assigned_team,
            "created_by": ticket.created_by,
            "created_at": (
                ticket.created_at.isoformat()
                if ticket.created_at
                else None
            ),
        }

    return [create_support_ticket]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.support_ticket_repository import (
    SupportTicketRepository,
)
from backend.app.services.customer_service import CustomerService
from backend.app.services.support_ticket_service import (
    SupportTicketService,
)


router = APIRouter(
    prefix="/customers",
    tags=["Support Tickets"],
)


@router.get("/{customer_id}/tickets")
async def get_customer_tickets(
    customer_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    customer = await customer_service.get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    ticket_repository = SupportTicketRepository(db)
    ticket_service = SupportTicketService(ticket_repository)

    tickets = await ticket_service.get_customer_tickets(
        customer,
        limit,
    )

    return {
        "customer_id": customer.customer_id,
        "count": len(tickets),
        "tickets": [
            {
                "ticket_id": ticket.ticket_id,
                "category": ticket.category,
                "priority": ticket.priority,
                "status": ticket.status,
                "subject": ticket.subject,
                "description": ticket.description,
                "resolution": ticket.resolution,
                "assigned_team": ticket.assigned_team,
                "created_by": ticket.created_by,
                "resolved_at": ticket.resolved_at,
                "created_at": ticket.created_at,
            }
            for ticket in tickets
        ],
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    ticket_repository = SupportTicketRepository(db)
    ticket_service = SupportTicketService(ticket_repository)

    ticket = await ticket_service.get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )

    return {
        "ticket_id": ticket.ticket_id,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "subject": ticket.subject,
        "description": ticket.description,
        "resolution": ticket.resolution,
        "assigned_team": ticket.assigned_team,
        "created_by": ticket.created_by,
        "resolved_at": ticket.resolved_at,
        "created_at": ticket.created_at,
    }
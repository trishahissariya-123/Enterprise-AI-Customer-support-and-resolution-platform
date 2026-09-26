from backend.app.models.customer import Customer
from backend.app.models.support_ticket import SupportTicket
from uuid import uuid4
from backend.app.repositories.support_ticket_repository import (
    SupportTicketRepository,
)


class SupportTicketService:
    def __init__(
        self,
        support_ticket_repository: SupportTicketRepository,
    ):
        self.support_ticket_repository = support_ticket_repository

    async def get_ticket(
        self,
        ticket_id: str,
    ) -> SupportTicket | None:
        return await self.support_ticket_repository.get_by_ticket_id(
            ticket_id
        )

    async def get_customer_tickets(
        self,
        customer: Customer,
        limit: int = 20,
    ) -> list[SupportTicket]:
        return await self.support_ticket_repository.get_customer_tickets(
            customer.id,
            limit,
        )

    async def create_ticket(
        self,
        customer: Customer,
        category: str,
        priority: str,
        subject: str,
        description: str,
        assigned_team: str,
    ) -> SupportTicket:

        ticket = SupportTicket(
            ticket_id=f"TICKET-{uuid4().hex[:12].upper()}",
            customer_id=customer.id,
            category=category,
            priority=priority,
            status="OPEN",
            subject=subject,
            description=description,
            assigned_team=assigned_team,
            created_by="AI_AGENT",
        )

        return await self.support_ticket_repository.create_ticket(ticket)
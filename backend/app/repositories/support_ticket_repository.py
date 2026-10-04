from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.support_ticket import SupportTicket


class SupportTicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_ticket_id(
        self,
        ticket_id: str,
    ) -> SupportTicket | None:
        result = await self.db.execute(
            select(SupportTicket).where(
                SupportTicket.ticket_id == ticket_id
            )
        )
        return result.scalar_one_or_none()

    async def get_customer_tickets(
        self,
        customer_id: int,
        limit: int = 20,
    ) -> list[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket)
            .where(
                SupportTicket.customer_id == customer_id
            )
            .order_by(SupportTicket.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def create_ticket(
        self,
        ticket: SupportTicket,
    ) -> SupportTicket:
        self.db.add(ticket)
        await self.db.flush()


        return ticket
from backend.app.models.customer import Customer
from backend.app.models.wallet import Wallet
from backend.app.repositories.wallet_repository import WalletRepository


class WalletService:

    def __init__(
        self,
        wallet_repository: WalletRepository,
    ):
        self.wallet_repository = wallet_repository

    async def get_wallet(
        self,
        customer: Customer,
    ) -> Wallet | None:

        return await self.wallet_repository.get_by_customer_id(
            customer.id
        )
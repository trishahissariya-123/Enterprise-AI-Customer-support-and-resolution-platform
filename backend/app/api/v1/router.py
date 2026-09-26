from fastapi import  APIRouter
from backend.app.api.v1.customer import router as customer_router
from backend.app.api.v1.customer_profile import  router as customer_profile_router
from backend.app.api.v1.kyc import router as kyc_router
from backend.app.api.v1.wallet import router as wallet_router
from backend.app.api.v1.transaction import router as transaction_router
from backend.app.api.v1.recharge import router as recharge_router
from backend.app.api.v1.merchant_payment import router as merchant_payment_router
from backend.app.api.v1 import support_chat
from backend.app.api.v1.support_ticket import router as support_ticket_router
from backend.app.api.v1 import auth
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(customer_router)
api_router.include_router(customer_profile_router)
api_router.include_router(kyc_router)
api_router.include_router(wallet_router)
api_router.include_router(transaction_router)
api_router.include_router(recharge_router)
api_router.include_router(merchant_payment_router)
api_router.include_router(support_ticket_router)
api_router.include_router(support_chat.router)
api_router.include_router(auth.router)
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    customer_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )

    profile = relationship(
        "CustomerProfile",
        back_populates="customer",
        uselist=False,
        cascade="all, delete-orphan",
    )
    kyc = relationship(
        "KYCRecord",
        back_populates="customer",
        uselist=False,
        cascade="all, delete-orphan",
    )
    wallet=relationship("Wallet", back_populates="customer",uselist=False,cascade="all, delete-orphan")
    recharges = relationship(
        "Recharge",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    sent_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.sender_customer_id",
        back_populates="sender",
    )

    received_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.receiver_customer_id",
        back_populates="receiver",
    )
    merchant_payments = relationship(
        "MerchantPayment",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    support_tickets = relationship(
        "SupportTicket",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    conversations = relationship(
        "Conversation",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
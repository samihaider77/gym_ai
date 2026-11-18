import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db.base import Base


class ChatLinkModel(Base):
    """A member's chat account (a WhatsApp number) linked to their LiftAndPlate account.
    The phone number itself is not stored: only an HMAC of it (to find the member) and its last 4 digits (to show)."""
    __tablename__ = "chat_links"
    __table_args__ = (UniqueConstraint("channel", "address_hash", name="uq_chat_link_address"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="whatsapp")
    address_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    address_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="en")
    utc_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ChatLinkCodeModel(Base):
    """A one-time code shown as a QR in the app. Only its SHA-256 is stored; it works once, for 10 minutes."""
    __tablename__ = "chat_link_codes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="en")
    utc_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ChatMessageModel(Base):
    """One incoming message: its id (so a retried webhook is handled once) and what we understood. No message text."""
    __tablename__ = "chat_messages"
    __table_args__ = (UniqueConstraint("channel", "message_id", name="uq_chat_message_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="whatsapp")
    message_id: Mapped[str] = mapped_column(String(128), nullable=False)
    address_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    link_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("chat_links.id", ondelete="SET NULL"), nullable=True)
    intent: Mapped[str] = mapped_column(String(20), nullable=False)
    ok: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 0 for a failed LINK attempt
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True,
                                                 nullable=False)

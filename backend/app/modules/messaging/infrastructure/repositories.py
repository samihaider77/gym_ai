import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.modules.messaging.infrastructure.models import ChatLinkCodeModel, ChatLinkModel, ChatMessageModel


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    # Links -------------------------------------------------------------------------------------------------------

    def link_for_user(self, user_id: uuid.UUID, channel: str = "whatsapp") -> Optional[ChatLinkModel]:
        stmt = select(ChatLinkModel).where(ChatLinkModel.user_id == user_id, ChatLinkModel.channel == channel)
        return self.db.execute(stmt).scalars().first()

    def link_for_address(self, address_hash: str, channel: str = "whatsapp") -> Optional[ChatLinkModel]:
        stmt = select(ChatLinkModel).where(ChatLinkModel.channel == channel, ChatLinkModel.address_hash == address_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def save_link(self, user_id: uuid.UUID, address_hash: str, last4: str, language: str, utc_offset: int,
                  channel: str = "whatsapp") -> ChatLinkModel:
        """One number per member and one member per number: replaces either side's old link."""
        self.db.execute(delete(ChatLinkModel).where(
            ChatLinkModel.channel == channel,
            (ChatLinkModel.user_id == user_id) | (ChatLinkModel.address_hash == address_hash)))
        link = ChatLinkModel(user_id=user_id, channel=channel, address_hash=address_hash, address_last4=last4,
                             language=language, utc_offset_minutes=utc_offset)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def delete_link(self, link: ChatLinkModel) -> None:
        self.db.delete(link)
        self.db.commit()

    def touch(self, link: ChatLinkModel, when: datetime, language: Optional[str] = None) -> None:
        link.last_message_at = when
        if language:
            link.language = language
        self.db.commit()

    # Codes -------------------------------------------------------------------------------------------------------

    def replace_code(self, user_id: uuid.UUID, code_hash: str, expires_at: datetime, language: str,
                     utc_offset: int) -> ChatLinkCodeModel:
        """A new code cancels the member's earlier unused ones."""
        self.db.execute(delete(ChatLinkCodeModel).where(ChatLinkCodeModel.user_id == user_id))
        code = ChatLinkCodeModel(user_id=user_id, code_hash=code_hash, expires_at=expires_at, language=language,
                                 utc_offset_minutes=utc_offset)
        self.db.add(code)
        self.db.commit()
        self.db.refresh(code)
        return code

    def code_by_hash(self, code_hash: str) -> Optional[ChatLinkCodeModel]:
        stmt = select(ChatLinkCodeModel).where(ChatLinkCodeModel.code_hash == code_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def use_code(self, code: ChatLinkCodeModel, when: datetime) -> None:
        code.used_at = when
        self.db.commit()

    # Messages ----------------------------------------------------------------------------------------------------

    def record_message(self, channel: str, message_id: str, address_hash: str, intent: str,
                       link_id: Optional[uuid.UUID]) -> Optional[ChatMessageModel]:
        """Stores the message id; returns None if this message was already handled (Meta retries webhooks)."""
        message = ChatMessageModel(channel=channel, message_id=message_id, address_hash=address_hash,
                                   intent=intent, link_id=link_id)
        self.db.add(message)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return None
        self.db.refresh(message)
        return message

    def mark_failed(self, message: ChatMessageModel) -> None:
        message.ok = 0
        self.db.commit()

    def failed_links_since(self, address_hash: str, since: datetime) -> int:
        stmt = select(func.count()).select_from(ChatMessageModel).where(
            ChatMessageModel.address_hash == address_hash, ChatMessageModel.intent == "link",
            ChatMessageModel.ok == 0, ChatMessageModel.created_at >= since)
        return self.db.execute(stmt).scalar_one()

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LinkCodeRequest(BaseModel):
    language: Literal["en", "ur"] = "en"
    # Minutes ahead of UTC on the member's device (Pakistan: 300); used for "today" in the chat.
    utc_offset_minutes: int = Field(300, ge=-720, le=840)


class LinkCode(BaseModel):
    code: str  # "7KQ2-M9XD"
    message: str  # what the member sends: "LINK 7KQ2-M9XD"
    expires_at: datetime
    wa_link: Optional[str]  # https://wa.me/<bot>?text=...; None until WHATSAPP_BOT_NUMBER is set
    qr_svg: Optional[str]  # QR of wa_link as inline SVG


class LinkStatus(BaseModel):
    linked: bool
    last4: Optional[str] = None
    linked_at: Optional[datetime] = None
    language: Optional[str] = None
    bot_ready: bool  # False until the WhatsApp number is set up on the server

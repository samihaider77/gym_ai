import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db.session import get_db
from app.core.logging import logger
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.messaging.application.dtos import LinkCode, LinkCodeRequest, LinkStatus
from app.modules.messaging.application.services import CHANNEL, ChatService, address_hash
from app.modules.messaging.infrastructure import whatsapp
from app.modules.users.infrastructure.models import UserModel

router = APIRouter()


# In the app (signed-in member) -----------------------------------------------------------------------------------

@router.get("/link", response_model=LinkStatus, summary="Is WhatsApp connected?")
def link_status(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return ChatService(db).status(current_user.id)


@router.post("/link", response_model=LinkCode, summary="New one-time code and QR for connecting WhatsApp")
def create_link_code(body: LinkCodeRequest, current_user: UserModel = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return ChatService(db).create_code(current_user.id, body.language, body.utc_offset_minutes)


@router.delete("/link", status_code=status.HTTP_204_NO_CONTENT, summary="Disconnect WhatsApp")
def unlink(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    ChatService(db).unlink(current_user.id)


# Meta's webhook (no user token: checked with the app secret instead) --------------------------------------------

@router.get("/whatsapp/webhook", response_class=PlainTextResponse, include_in_schema=False)
def verify_webhook(
    mode: str = Query("", alias="hub.mode"),
    token: str = Query("", alias="hub.verify_token"),
    challenge: str = Query("", alias="hub.challenge"),
):
    """One-time handshake when the webhook URL is saved in the Meta app dashboard."""
    if mode == "subscribe" and settings.WHATSAPP_VERIFY_TOKEN and token == settings.WHATSAPP_VERIFY_TOKEN:
        return challenge
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Verification failed.")


@router.post("/whatsapp/webhook", include_in_schema=False)
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    if not whatsapp.signature_ok(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bad signature.")
    try:
        payload = json.loads(body)
    except ValueError:
        return {"ok": True}
    service = ChatService(db)
    for message in whatsapp.parse(payload):
        try:
            reply = service.handle(message.sender, message.message_id, message.kind, message.text)
            if reply:
                whatsapp.send(message.sender, reply.text, reply.buttons)
        except Exception:  # answer 200 anyway, or Meta keeps retrying the same message
            logger.exception("WhatsApp message %s failed", message.message_id)
            db.rollback()
    return {"ok": True}


# Unofficial gateway (whatsapp-gateway/, a linked WhatsApp Web device) ---------------------------------------------

class GatewayMessage(BaseModel):
    message_id: str = Field(min_length=1, max_length=200)
    sender: str = Field(min_length=1, max_length=64)  # digits of the member's number (or a WhatsApp LID)
    kind: str = Field(default="text", pattern="^(text|button|image|audio|other)$")
    text: str = Field(default="", max_length=4000)


@router.post("/gateway/incoming", include_in_schema=False)
async def gateway_incoming(request: Request, db: Session = Depends(get_db)):
    """The gateway posts each incoming chat message here and sends back the reply text it gets."""
    body = await request.body()
    if not whatsapp.gateway_ok(body, request.headers.get("X-Gateway-Signature")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bad signature.")
    try:
        message = GatewayMessage.model_validate_json(body)
    except ValidationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bad message.")
    return {"reply": await run_in_threadpool(_gateway_reply, db, message)}  # database work off the event loop


def _gateway_reply(db: Session, message: GatewayMessage):
    service = ChatService(db)
    try:
        reply = service.handle(message.sender, message.message_id, message.kind, message.text[:1000])
        if not reply:
            return None
        link = service.repo.link_for_address(address_hash(message.sender), CHANNEL)
    except Exception:
        logger.exception("Gateway message %s failed", message.message_id)
        db.rollback()
        return None
    return whatsapp.with_button_hint(reply.text, reply.buttons, link.language if link else "en")

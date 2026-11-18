"""Meta WhatsApp Cloud API: check the webhook signature, read incoming messages and send replies.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api
Without WHATSAPP_TOKEN (local development) replies are written to the log instead of sent.
"""
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from app.core.config import settings
from app.core.logging import logger

TEXT_LIMIT = 4096  # WhatsApp text body
BUTTON_BODY_LIMIT = 1024  # interactive message body
BUTTON_TITLE_LIMIT = 20


@dataclass(frozen=True)
class Incoming:
    message_id: str
    sender: str  # the member's number in international format, digits only (from WhatsApp, never typed by us)
    kind: str  # text | button | image | audio | other
    text: str  # message text, or the id of the tapped button


def signature_ok(body: bytes, header: Optional[str]) -> bool:
    """Meta signs each webhook with the app secret: X-Hub-Signature-256: sha256=<hex>."""
    secret = settings.WHATSAPP_APP_SECRET
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


def parse(payload: dict) -> List[Incoming]:
    """Messages in a webhook payload. Status updates (sent, delivered, read) are ignored."""
    found = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for message in value.get("messages") or []:
                kind = message.get("type") or "other"
                text = ""
                if kind == "text":
                    text = (message.get("text") or {}).get("body") or ""
                elif kind == "interactive":
                    reply = (message.get("interactive") or {})
                    picked = reply.get("button_reply") or reply.get("list_reply") or {}
                    kind, text = "button", picked.get("id") or picked.get("title") or ""
                elif kind == "button":  # quick-reply button on a template
                    kind, text = "button", (message.get("button") or {}).get("payload") or ""
                elif kind not in ("image", "audio"):
                    kind = "other"
                sender = "".join(ch for ch in str(message.get("from") or "") if ch.isdigit())
                if message.get("id") and sender:
                    found.append(Incoming(message_id=message["id"], sender=sender, kind=kind, text=text[:1000]))
    return found


def _post(payload: dict) -> bool:
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        logger.info("WhatsApp reply (not sent, no WHATSAPP_TOKEN): %s", json.dumps(payload)[:900])
        return False
    url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as error:
        logger.warning("WhatsApp send failed: HTTP %s %s", error.code, error.read()[:300])
    except (urllib.error.URLError, TimeoutError) as error:
        logger.warning("WhatsApp send failed: %s", error)
    return False


def send(to: str, text: str, buttons: Sequence[Tuple[str, str]] = ()) -> bool:
    """Sends text, with up to 3 reply buttons (id, title) when the text is short enough for a button message."""
    base = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to}
    buttons = list(buttons)[:3]
    if buttons and len(text) <= BUTTON_BODY_LIMIT:
        return _post({**base, "type": "interactive", "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": [{"type": "reply", "reply": {"id": bid, "title": title[:BUTTON_TITLE_LIMIT]}}
                                   for bid, title in buttons]},
        }})
    return _post({**base, "type": "text", "text": {"body": text[:TEXT_LIMIT], "preview_url": False}})


def chat_link(text: str) -> Optional[str]:
    """wa.me link that opens a chat with the bot with `text` already typed; None until the bot number is set."""
    number = "".join(ch for ch in (settings.WHATSAPP_BOT_NUMBER or "") if ch.isdigit())
    if not number:
        return None
    return f"https://wa.me/{number}?text={urllib.request.quote(text)}"

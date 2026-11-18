"""QR code for the one-time link, as an inline SVG (made on the server, so the app needs no QR library)."""
from typing import Optional

try:
    import segno
except ImportError:  # optional: without it the app shows the code and an "Open WhatsApp" button only
    segno = None


def svg(text: str) -> Optional[str]:
    if segno is None:
        return None
    return segno.make(text, error="m").svg_inline(scale=6, border=2, omitsize=True, dark="#14213D", light="#ffffff")

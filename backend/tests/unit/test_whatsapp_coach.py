"""WhatsApp Coach: command parsing, reply text, 'today' schedule, webhook parsing and signatures (no DB, no network)."""
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.modules.messaging.application.services import code_hash, local_date, new_code, schedule
from app.modules.messaging.domain import commands as cmd
from app.modules.messaging.domain import replies
from app.modules.messaging.infrastructure import whatsapp


def test_link_code_is_read_with_or_without_dash_and_case():
    assert cmd.parse("LINK 7KQ2-M9XD") == cmd.Command(cmd.LINK, code="7KQ2M9XD")
    assert cmd.parse("link 7kq2m9xd").code == "7KQ2M9XD"
    assert cmd.parse("LINK 7KQ2-M9X").name != cmd.LINK  # too short
    assert cmd.parse("LINK 0OI1-M9XD").name != cmd.LINK  # letters we never use


def test_english_and_roman_urdu_commands():
    cases = {
        "today": cmd.TODAY, "aaj ka workout?": cmd.TODAY, "Today's workout": cmd.TODAY, "aaj ka plan": cmd.TODAY,
        "kal": cmd.TOMORROW, "kal ka workout": cmd.TOMORROW, "Next workout": cmd.TOMORROW,
        "week": cmd.WEEK, "hafta ka workout": cmd.WEEK, "plan": cmd.WEEK,
        "diet": cmd.DIET, "aaj kitna protein?": cmd.DIET, "what should I eat": cmd.DIET,
        "done": cmd.DONE, "ho gaya": cmd.DONE, "workout khatam": cmd.DONE,
        "STOP": cmd.STOP, "hi": cmd.HELP, "menu": cmd.HELP, "asdf": cmd.UNKNOWN, "": cmd.UNKNOWN,
        "urdu": cmd.LANGUAGE,
    }
    for text, expected in cases.items():
        assert cmd.parse(text).name == expected, text
    assert cmd.parse("ho sakta hai?").name != cmd.DONE  # "ho" alone isn't "done"


def test_weight_is_read_from_the_message():
    assert cmd.parse("weight 78.5").weight_kg == 78.5
    assert cmd.parse("wazan 81,2 kg").weight_kg == 81.2
    assert cmd.parse("weight").weight_kg is None


def test_codes_use_the_safe_alphabet_and_hash_ignores_dash():
    code = new_code()
    assert len(code) == 8 and set(code) <= set(cmd.CODE_ALPHABET)
    assert code_hash("7KQ2-M9XD") == code_hash("7kq2m9xd")


def test_today_follows_the_last_completed_day():
    days = [uuid.uuid4() for _ in range(3)]
    now = datetime(2026, 11, 18, 6, 0, tzinfo=timezone.utc)  # 11:00 in Pakistan
    s = schedule(days, None, None, now, 300)
    assert (s.today_index, s.next_index, s.done_today) == (0, 1, False)
    yesterday = now - timedelta(days=1)
    s = schedule(days, days[0], yesterday, now, 300)
    assert (s.today_index, s.next_index, s.done_today) == (1, 2, False)
    s = schedule(days, days[2], yesterday, now, 300)  # wraps round to day 1
    assert (s.today_index, s.next_index) == (0, 1)
    s = schedule(days, days[1], now - timedelta(hours=2), now, 300)  # done earlier today
    assert (s.today_index, s.next_index, s.done_today) == (1, 2, True)


def test_local_day_uses_the_member_offset():
    late = datetime(2026, 11, 18, 20, 0, tzinfo=timezone.utc)  # already 19 Nov, 01:00 in Pakistan
    assert local_date(late, 300).day == 19 and local_date(late, 0).day == 18


def test_workout_reply_lists_exercises_in_the_member_language():
    exercises = [{"name": "Bench Press", "name_ur": "Bench Press (seena)", "sets": 4, "reps": 8, "weight_kg": 60,
                  "duration_seconds": None}]
    en = replies.workout("en", "today", "Push Pull Legs", 1, 3, "Push", 60, exercises)
    assert "*Today: Push*" in en and "1. Bench Press: 4×8 @ 60 kg" in en and "*done*" in en
    ur = replies.workout("ur", "today", "Push Pull Legs", 1, 3, "Push", 60, exercises)
    assert "*Aaj: Push*" in ur and "Bench Press (seena)" in ur


def test_all_reply_texts_exist_in_both_languages():
    for key, langs in replies._T.items():
        assert set(langs) == {"en", "ur"}, key


def _payload(*messages):
    return {"object": "whatsapp_business_account",
            "entry": [{"changes": [{"value": {"messages": list(messages), "statuses": [{"id": "x"}]}}]}]}


def test_webhook_parsing_reads_text_buttons_and_media():
    payload = _payload(
        {"from": "923001234567", "id": "wamid.1", "type": "text", "text": {"body": "today"}},
        {"from": "923001234567", "id": "wamid.2", "type": "interactive",
         "interactive": {"type": "button_reply", "button_reply": {"id": "done", "title": "Done ✅"}}},
        {"from": "923001234567", "id": "wamid.3", "type": "image", "image": {"id": "media1"}},
    )
    got = whatsapp.parse(payload)
    assert [(m.kind, m.text) for m in got] == [("text", "today"), ("button", "done"), ("image", "")]
    assert got[0].sender == "923001234567"
    assert whatsapp.parse({"entry": [{"changes": [{"value": {"statuses": [{}]}}]}]}) == []


def test_signature_must_match_the_app_secret(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "test-secret")
    body = json.dumps(_payload()).encode()
    good = "sha256=" + hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
    assert whatsapp.signature_ok(body, good)
    assert not whatsapp.signature_ok(body + b" ", good)
    assert not whatsapp.signature_ok(body, None)
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", None)
    assert not whatsapp.signature_ok(body, good)  # no secret configured: reject everything


def test_chat_link_needs_the_bot_number(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_BOT_NUMBER", None)
    assert whatsapp.chat_link("LINK 7KQ2-M9XD") is None
    monkeypatch.setattr(settings, "WHATSAPP_BOT_NUMBER", "+92 300 1234567")
    assert whatsapp.chat_link("LINK 7KQ2-M9XD") == "https://wa.me/923001234567?text=LINK%207KQ2-M9XD"


def test_gateway_calls_must_be_signed_with_the_gateway_secret(monkeypatch):
    body = b'{"message_id":"m1","sender":"923001234567","text":"today"}'
    monkeypatch.setattr(settings, "WHATSAPP_GATEWAY_SECRET", None)
    good = "sha256=" + hmac.new(b"gw-secret", body, hashlib.sha256).hexdigest()
    assert not whatsapp.gateway_ok(body, good)  # no secret set: reject everything
    monkeypatch.setattr(settings, "WHATSAPP_GATEWAY_SECRET", "gw-secret")
    assert whatsapp.gateway_ok(body, good)
    assert not whatsapp.gateway_ok(body + b" ", good)
    assert not whatsapp.gateway_ok(body, None)


def test_buttons_become_typed_commands_for_the_gateway():
    buttons = replies.buttons("en", replies.WORKOUT)
    text = whatsapp.with_button_hint("Hi", buttons, "en")
    assert text.endswith("Send: *done* · *tomorrow* · *diet*")
    assert all(cmd.parse(word).name != cmd.UNKNOWN for word in ("done", "tomorrow", "diet", "today", "week"))
    urdu = whatsapp.with_button_hint("Salam", replies.buttons("ur", replies.MENU), "ur")
    assert urdu.endswith("Bhejein: *aaj* · *khana* · *hafta*")
    assert all(cmd.parse(word).name != cmd.UNKNOWN for word in ("aaj", "kal", "khana", "hafta"))
    assert whatsapp.with_button_hint("Plain", (), "en") == "Plain"

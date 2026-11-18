"""WhatsApp Coach: link a member's number with a one-time code, then answer their chat commands from their data."""
import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.modules.ai_coach.application.services import MealSnapService
from app.modules.ai_coach.infrastructure.repositories import MealLogRepository
from app.modules.messaging.application.dtos import LinkCode, LinkStatus
from app.modules.messaging.domain import commands as cmd
from app.modules.messaging.domain import replies
from app.modules.messaging.infrastructure import qr, whatsapp
from app.modules.messaging.infrastructure.coach_data import CoachData, Plan
from app.modules.messaging.infrastructure.models import ChatLinkModel
from app.modules.messaging.infrastructure.repositories import ChatRepository
from app.modules.progress.infrastructure.repositories import BodyProgressRepository
from app.modules.user_profile.infrastructure.repositories import UserProfileRepository

CODE_MINUTES = 10
MAX_FAILED_LINKS_PER_HOUR = 5
CHANNEL = "whatsapp"


def address_hash(address: str) -> str:
    """Keyed hash of a phone number, so the table can't be turned back into numbers without the server secret."""
    return hmac.new(settings.JWT_SECRET_KEY.encode(), f"{CHANNEL}:{address}".encode(), hashlib.sha256).hexdigest()


def code_hash(code: str) -> str:
    return hashlib.sha256(code.upper().replace("-", "").encode()).hexdigest()


def new_code() -> str:
    return "".join(secrets.choice(cmd.CODE_ALPHABET) for _ in range(cmd.CODE_LENGTH))


def local_date(when: datetime, utc_offset_minutes: int):
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (when.astimezone(timezone.utc) + timedelta(minutes=utc_offset_minutes)).date()


@dataclass
class Reply:
    text: str
    buttons: Sequence[Tuple[str, str]] = field(default_factory=tuple)


@dataclass(frozen=True)
class Schedule:
    today_index: int
    next_index: int
    done_today: bool


def schedule(day_ids: List[uuid.UUID], last_day_id: Optional[uuid.UUID], last_done_at: Optional[datetime],
             now: datetime, utc_offset_minutes: int) -> Schedule:
    """Which plan day is 'today': the one after the last completed day, or the completed one if it was done today."""
    n = len(day_ids)
    last = day_ids.index(last_day_id) if last_day_id in day_ids else None
    done_today = (last is not None and last_done_at is not None
                  and local_date(last_done_at, utc_offset_minutes) == local_date(now, utc_offset_minutes))
    if done_today:
        today = last
    else:
        today = 0 if last is None else (last + 1) % n
    return Schedule(today_index=today, next_index=(today + 1) % n, done_today=done_today)


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChatRepository(db)
        self.data = CoachData(db)

    # In the app ----------------------------------------------------------------------------------------------------

    def status(self, user_id: uuid.UUID) -> LinkStatus:
        link = self.repo.link_for_user(user_id, CHANNEL)
        return LinkStatus(
            linked=bool(link), last4=link.address_last4 if link else None,
            linked_at=link.linked_at if link else None, language=link.language if link else None,
            bot_ready=bool(whatsapp.chat_link("x")),
        )

    def create_code(self, user_id: uuid.UUID, language: str, utc_offset_minutes: int) -> LinkCode:
        code = new_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=CODE_MINUTES)
        self.repo.replace_code(user_id, code_hash(code), expires_at, language, utc_offset_minutes)
        message = f"LINK {cmd.format_code(code)}"
        link = whatsapp.chat_link(message)
        return LinkCode(code=cmd.format_code(code), message=message, expires_at=expires_at, wa_link=link,
                        qr_svg=qr.svg(link) if link else None)

    def unlink(self, user_id: uuid.UUID) -> None:
        link = self.repo.link_for_user(user_id, CHANNEL)
        if not link:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "WhatsApp isn't connected.")
        self.repo.delete_link(link)

    # In the chat ---------------------------------------------------------------------------------------------------

    def handle(self, sender: str, message_id: str, kind: str, body: str,
               now: Optional[datetime] = None) -> Optional[Reply]:
        """The reply for one incoming message, or None when this message was already handled."""
        now = now or datetime.now(timezone.utc)
        sender_hash = address_hash(sender)
        link = self.repo.link_for_address(sender_hash, CHANNEL)
        command = cmd.parse(body) if kind in ("text", "button") else cmd.Command("media" if kind in ("image", "audio") else cmd.UNKNOWN)
        record = self.repo.record_message(CHANNEL, message_id, sender_hash, command.name, link.id if link else None)
        if record is None:
            return None
        lang = link.language if link else "en"

        if command.name == cmd.LINK:
            if self.repo.failed_links_since(sender_hash, now - timedelta(hours=1)) >= MAX_FAILED_LINKS_PER_HOUR:
                self.repo.mark_failed(record)
                return Reply(replies.text("too_many_codes", lang))
            code = self.repo.code_by_hash(code_hash(command.code))
            expires = code.expires_at.replace(tzinfo=code.expires_at.tzinfo or timezone.utc) if code else None
            if not code or code.used_at or expires < now:
                self.repo.mark_failed(record)
                return Reply(replies.text("bad_code", lang))
            self.repo.use_code(code, now)
            link = self.repo.save_link(code.user_id, sender_hash, sender[-4:], code.language, code.utc_offset_minutes,
                                       CHANNEL)
            return Reply(replies.text("linked", link.language), replies.buttons(link.language, replies.MENU))

        if not link:
            return Reply(replies.text("not_linked", "en"))

        if command.name == cmd.STOP:
            self.repo.delete_link(link)
            return Reply(replies.text("stopped", lang))

        self.repo.touch(link, now, command.language if command.name == cmd.LANGUAGE else None)
        try:
            return self._answer(link, command, now)
        except Exception:  # never leave the member without an answer
            logger.exception("WhatsApp command %s failed", command.name)
            self.db.rollback()
            return Reply(replies.text("error", lang))

    def _answer(self, link: ChatLinkModel, command: cmd.Command, now: datetime) -> Reply:
        lang = link.language
        name = command.name
        if name == cmd.LANGUAGE:
            return Reply(replies.text("language", lang), replies.buttons(lang, replies.MENU))
        if name == "media":
            return Reply(replies.text("media", lang))
        if name in (cmd.TODAY, cmd.TOMORROW, cmd.WEEK, cmd.DONE):
            return self._workout(link, name, now)
        if name == cmd.DIET:
            return self._diet(link, now)
        if name == cmd.WEIGHT:
            return self._weight(link, command.weight_kg, now)
        if name == cmd.HELP:
            return Reply(replies.text("help", lang), replies.buttons(lang, replies.MENU))
        return Reply(replies.text("unknown", lang) + replies.text("help", lang), replies.buttons(lang, replies.MENU))

    def _workout(self, link: ChatLinkModel, name: str, now: datetime) -> Reply:
        lang = link.language
        plan: Optional[Plan] = self.data.active_plan(link.user_id)
        if not plan:
            return Reply(replies.text("no_plan", lang))
        if not plan.days:
            return Reply(replies.text("empty_plan", lang, plan=plan.name))
        last = self.data.last_completed(link.user_id, plan.id)
        when = schedule([d.id for d in plan.days], last.workout_day_id if last else None,
                        (last.completed_at or last.started_at) if last else None, now, link.utc_offset_minutes)
        today, upcoming = plan.days[when.today_index], plan.days[when.next_index]

        if name == cmd.WEEK:
            return Reply(replies.week(lang, plan.name, [
                {"number": d.number, "title": d.title, "count": len(d.exercises)} for d in plan.days],
                upcoming.number if when.done_today else today.number), replies.buttons(lang, replies.MENU))
        if name == cmd.DONE:
            if when.done_today:
                return Reply(replies.text("already_done", lang, title=today.title))
            self.data.complete_day(link.user_id, plan.id, today, now)
            return Reply(replies.text("done", lang, title=today.title, next=upcoming.title),
                         replies.buttons(lang, replies.AFTER_DONE))
        day = today if name == cmd.TODAY else upcoming
        label = "today" if name == cmd.TODAY else "tomorrow"
        text = replies.workout(lang, label, plan.name, day.number, len(plan.days), day.title, day.minutes,
                               [vars(e) for e in day.exercises], done_today=(name == cmd.TODAY and when.done_today))
        buttons = replies.buttons(lang, replies.WORKOUT if (name == cmd.TODAY and not when.done_today) else replies.MENU)
        return Reply(text, buttons)

    def _diet(self, link: ChatLinkModel, now: datetime) -> Reply:
        offset = timezone(timedelta(minutes=link.utc_offset_minutes))
        day = local_date(now, link.utc_offset_minutes)
        start = datetime(day.year, day.month, day.day, tzinfo=offset)
        meals = MealSnapService(MealLogRepository(self.db), UserProfileRepository(self.db),
                                BodyProgressRepository(self.db))
        summary = meals.day_summary(link.user_id, start, start + timedelta(days=1))
        tip = summary.tip.ur if link.language == "ur" else summary.tip.en
        return Reply(replies.diet(link.language, summary.totals.kcal, summary.totals.protein_g, len(summary.meals),
                                  summary.targets.kcal if summary.targets else None,
                                  summary.targets.protein_g if summary.targets else None, tip),
                     replies.buttons(link.language, replies.AFTER_DIET))

    def _weight(self, link: ChatLinkModel, kg: Optional[float], now: datetime) -> Reply:
        lang = link.language
        if kg is None:
            return Reply(replies.text("weight_ask", lang))
        if not 25 <= kg <= 300:
            return Reply(replies.text("weight_range", lang))
        previous = BodyProgressRepository(self.db).get_latest_progress_by_user(link.user_id)
        self.data.log_weight(link.user_id, kg, now)
        change = replies.weight_change(lang, previous.weight_kg if previous else None, kg)
        return Reply(replies.text("weight_saved", lang, kg=f"{kg:g}", change=change))

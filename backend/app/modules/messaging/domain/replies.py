"""Chat replies in English ("en") or Roman Urdu ("ur"). Pure functions: they only format what they are given.

WhatsApp formatting: *bold*, _italic_. Keep replies short: one message per answer.
"""
from typing import List, Optional, Sequence, Tuple

APP_URL = "https://gym-ai-sooty.vercel.app"

Buttons = Sequence[Tuple[str, str]]

# Buttons send their id as the message; ids are commands the parser understands. Titles: 20 characters at most.
_BUTTON_TITLES = {
    "en": {"done": "Done ✅", "today": "Today's workout", "tomorrow": "Next workout", "diet": "Diet",
           "week": "This week"},
    "ur": {"done": "Done ✅", "today": "Aaj ka workout", "tomorrow": "Agla workout", "diet": "Khana",
           "week": "Poora hafta"},
}
WORKOUT = ("done", "tomorrow", "diet")
MENU = ("today", "diet", "week")
AFTER_DONE = ("tomorrow", "diet")
AFTER_DIET = ("today", "week")


def buttons(lang: str, ids: Sequence[str]) -> Buttons:
    titles = _BUTTON_TITLES.get(lang, _BUTTON_TITLES["en"])
    return tuple((i, titles[i]) for i in ids)

_T = {
    "help": {
        "en": "*LiftAndPlate Coach* 💪\nSend any of these:\n"
              "• *today*: today's workout\n• *tomorrow*: the next one\n• *week*: your whole plan\n"
              "• *diet*: calories and protein for today\n• *done*: mark today's workout complete\n"
              "• *weight 78.5*: log your weight\n• *urdu* / *english*: change language\n• *stop*: disconnect",
        "ur": "*LiftAndPlate Coach* 💪\nYeh bhejein:\n"
              "• *aaj*: aaj ka workout\n• *kal*: agla workout\n• *hafta*: poora plan\n"
              "• *khana*: aaj ki calories aur protein\n• *done*: aaj ka workout mukammal\n"
              "• *wazan 78.5*: wazan likhein\n• *english* / *urdu*: zaban badlein\n• *stop*: disconnect",
    },
    "not_linked": {
        "en": "Hi! This number isn't connected to LiftAndPlate yet.\nOpen the app → Profile → *Connect WhatsApp* "
              f"and scan the QR code.\n{APP_URL}",
        "ur": "Salam! Yeh number abhi LiftAndPlate se connect nahi.\nApp kholein → Profile → *Connect WhatsApp* "
              f"aur QR scan karein.\n{APP_URL}",
    },
    "linked": {
        "en": "You're connected ✅\nSend *today* for your workout, *diet* for today's food targets, or *help* for "
              "everything I can do.\nSend *stop* any time to disconnect.",
        "ur": "Aap connect ho gaye ✅\n*aaj* bhejein workout ke liye, *khana* aaj ke targets ke liye, ya *help*.\n"
              "Disconnect karna ho to *stop* bhejein.",
    },
    "bad_code": {
        "en": "That code didn't work. It may have expired (codes last 10 minutes) or been used already.\n"
              "Open Profile → *Connect WhatsApp* in the app for a new QR code.",
        "ur": "Yeh code nahi chala. Shayad expire ho gaya (10 minute) ya pehle use ho chuka.\n"
              "App mein Profile → *Connect WhatsApp* se naya QR lein.",
    },
    "too_many_codes": {
        "en": "Too many wrong codes from this number. Please try again in an hour.",
        "ur": "Is number se bohat ghalat codes aaye. Ek ghante baad dobara koshish karein.",
    },
    "stopped": {
        "en": "Disconnected. You won't get any more messages from LiftAndPlate here.\n"
              "To connect again, use Profile → *Connect WhatsApp* in the app.",
        "ur": "Disconnect ho gaya. Ab yahan LiftAndPlate ke messages nahi aayenge.\n"
              "Dobara connect karne ke liye app mein Profile → *Connect WhatsApp*.",
    },
    "no_plan": {
        "en": f"You don't have an active workout plan yet. Create one in the app under *Workouts*.\n{APP_URL}/workouts",
        "ur": f"Abhi koi active workout plan nahi. App mein *Workouts* se plan banayein.\n{APP_URL}/workouts",
    },
    "empty_plan": {
        "en": "Your plan *{plan}* has no days yet. Add days and exercises in the app under *Workouts*.",
        "ur": "Aap ke plan *{plan}* mein abhi koi din nahi. App mein *Workouts* se din aur exercises add karein.",
    },
    "already_done": {
        "en": "Already logged today ✅ *{title}*. Rest well, or send *tomorrow* for the next one.",
        "ur": "Aaj ka workout pehle hi log ho chuka ✅ *{title}*. Aaram karein, ya *kal* bhejein.",
    },
    "done": {
        "en": "Great work! 🎉 *{title}* is logged as complete.\nNext up: *{next}*.",
        "ur": "Shabash! 🎉 *{title}* mukammal log ho gaya.\nAgla: *{next}*.",
    },
    "weight_ask": {
        "en": "Send your weight in kg, for example *weight 78.5*.",
        "ur": "Apna wazan kg mein bhejein, jaise *wazan 78.5*.",
    },
    "weight_range": {
        "en": "That doesn't look right. Send a weight between 25 and 300 kg, for example *weight 78.5*.",
        "ur": "Yeh sahi nahi lag raha. 25 se 300 kg ke darmiyan bhejein, jaise *wazan 78.5*.",
    },
    "weight_saved": {
        "en": "Weight logged: *{kg} kg* ✅{change}",
        "ur": "Wazan log ho gaya: *{kg} kg* ✅{change}",
    },
    "language": {
        "en": "Okay, I'll reply in English. Exercise names stay as in the app.",
        "ur": "Theek hai, ab Roman Urdu mein jawab dunga.",
    },
    "unknown": {
        "en": "I didn't get that. Here's what I can do:\n\n",
        "ur": "Samajh nahi aaya. Main yeh kar sakta hoon:\n\n",
    },
    "media": {
        "en": "Meal photos and voice notes are coming soon. For now, use *Food* in the app for meal photos.",
        "ur": "Khane ki photo aur voice note jald aa rahe hain. Abhi photo ke liye app mein *Food* use karein.",
    },
    "error": {
        "en": "Sorry, something went wrong on our side. Please try again in a minute.",
        "ur": "Maazrat, hamari taraf koi masla hua. Ek minute baad dobara koshish karein.",
    },
}


def text(key: str, lang: str, **values) -> str:
    template = _T[key].get(lang) or _T[key]["en"]
    return template.format(**values) if values else template


def _num(value: float) -> str:
    return f"{value:g}"


def workout(lang: str, label: str, plan: str, day_number: int, total_days: int, title: str,
            minutes: Optional[int], exercises: List[dict], done_today: bool = False) -> str:
    """exercises: dicts with name, name_ur, sets, reps, weight_kg, duration_seconds."""
    head = {"en": {"today": "Today", "tomorrow": "Next workout"}, "ur": {"today": "Aaj", "tomorrow": "Agla workout"}}
    lines = [f"*{head.get(lang, head['en'])[label]}: {title}*" + (" ✅" if done_today else ""),
             f"{plan} · Day {day_number} of {total_days}" + (f" · ~{minutes} min" if minutes else "")]
    if not exercises:
        lines.append("No exercises on this day yet." if lang == "en" else "Is din abhi koi exercise nahi.")
    for i, ex in enumerate(exercises, 1):
        name = (ex.get("name_ur") if lang == "ur" else None) or ex["name"]
        if ex.get("duration_seconds"):
            amount = f"{ex['sets']}× {round(ex['duration_seconds'] / 60, 1):g} min"
        else:
            amount = f"{ex['sets']}×{ex['reps']}"
        if ex.get("weight_kg"):
            amount += f" @ {_num(ex['weight_kg'])} kg"
        lines.append(f"{i}. {name}: {amount}")
    if label == "today" and not done_today and exercises:
        lines.append("")
        lines.append("Reply *done* when you finish." if lang == "en" else "Khatam ho to *done* bhejein.")
    return "\n".join(lines)


def week(lang: str, plan: str, days: List[dict], next_number: Optional[int]) -> str:
    """days: dicts with number, title, count."""
    lines = [f"*{plan}*", ""]
    for d in days:
        marker = ("  ← next" if lang == "en" else "  ← agla") if d["number"] == next_number else ""
        lines.append(f"Day {d['number']}: {d['title']} ({d['count']} exercises){marker}")
    return "\n".join(lines)


def diet(lang: str, eaten_kcal: float, eaten_protein: float, meals: int, target_kcal: Optional[int],
         target_protein: Optional[int], tip: str) -> str:
    if lang == "ur":
        lines = ["*Aaj ka khana*"]
        if target_kcal:
            lines.append(f"Calories: {round(eaten_kcal)} / {target_kcal} kcal")
            lines.append(f"Protein: {round(eaten_protein)} / {target_protein} g")
        else:
            lines.append(f"Calories: {round(eaten_kcal)} kcal · Protein: {round(eaten_protein)} g")
        lines.append(f"Meals log hue: {meals}")
    else:
        lines = ["*Today's food*"]
        if target_kcal:
            lines.append(f"Calories: {round(eaten_kcal)} / {target_kcal} kcal")
            lines.append(f"Protein: {round(eaten_protein)} / {target_protein} g")
        else:
            lines.append(f"Calories: {round(eaten_kcal)} kcal · Protein: {round(eaten_protein)} g")
        lines.append(f"Meals logged: {meals}")
    lines += ["", tip, "", f"Log meals with a photo in the app: {APP_URL}/food" if lang == "en"
              else f"Khana photo se app mein log karein: {APP_URL}/food"]
    return "\n".join(lines)


def weight_change(lang: str, previous: Optional[float], now: float) -> str:
    if previous is None:
        return ""
    diff = round(now - previous, 1)
    if diff == 0:
        return "\nSame as last time." if lang == "en" else "\nPichli dafa jitna."
    sign = "+" if diff > 0 else ""
    return (f"\n{sign}{_num(diff)} kg since last time." if lang == "en"
            else f"\nPichli dafa se {sign}{_num(diff)} kg.")

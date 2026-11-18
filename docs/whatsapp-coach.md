# WhatsApp Coach (Level 2: command bot)

Members link their WhatsApp number once from **Profile → Connect WhatsApp**, then ask for their workout or diet
from WhatsApp. It uses Meta's official WhatsApp Cloud API and needs no AI.

## How linking works

1. `POST /api/v1/messaging/link` makes a one-time code (8 letters, e.g. `FHZB-WVNG`), valid for 10 minutes.
   Only its SHA-256 is stored. A new code cancels the old one.
2. The app shows a QR of `https://wa.me/<bot number>?text=LINK FHZB-WVNG`. On a phone it shows an "Open WhatsApp"
   button instead.
3. The member taps Send. The webhook matches the code and links the number that sent it. The number is stored only
   as an HMAC (keyed with the server's JWT secret) plus its last 4 digits.
4. The app polls `GET /messaging/link` and closes the dialog once the number is linked.

Safety: 5 wrong codes from one number in an hour blocks further tries for that hour. `stop` unlinks the number at
once. Each number belongs to one member and each member has one number; linking again replaces the old link.

## Commands (English or Roman Urdu)

| Send | Reply |
|---|---|
| `today` / `aaj` / `workout` | Today's workout from the active plan, with Done / Next / Diet buttons |
| `tomorrow` / `kal` / `next` | The next workout |
| `week` / `hafta` / `plan` | All days of the plan, the next one marked |
| `done` / `ho gaya` / `khatam` | Marks today's workout complete (a COMPLETED workout session) |
| `diet` / `khana` / `protein` | Calories and protein eaten today against the Meal Snap targets |
| `weight 78.5` / `wazan 78.5` | Logs a body weight entry |
| `urdu` / `english` | Reply language |
| `help` / `hi` / `menu` | Command list |
| `stop` | Disconnect |

"Today" is the plan day after the last completed one (round and round the plan). If a workout was completed today,
"today" shows it with a tick. Day boundaries use the time zone the member's device had when they linked.

Photos and voice notes get a "coming soon" reply. They are Level 3 (Meal Snap and AI chat).

## Code

- `backend/app/modules/messaging/` holds the module:
  - `domain/commands.py` parses messages.
  - `domain/replies.py` holds the reply text.
  - `application/services.py` links numbers and answers commands.
  - `infrastructure/whatsapp.py` checks webhook signatures, reads messages and sends replies.
  - `infrastructure/coach_data.py` reads plans and writes sessions and weight.
  - `infrastructure/qr.py` makes the QR SVG.
- `alembic/versions/20261118_1200_add_chat_links.py` adds `chat_links`, `chat_link_codes` and `chat_messages`.
  `chat_messages` stores message ids and the command, never message text.
- `frontend/src/components/whatsapp-connect.tsx` is the Profile card.
- `backend/tests/unit/test_whatsapp_coach.py` has the unit tests.

## Set up on Meta (free)

1. Go to https://developers.facebook.com → **Create app** → **Business** type → add **WhatsApp**.
2. In **WhatsApp → API Setup** you get a free **test number**, a temporary access token and the
   **Phone number ID**. Add your own phone as a test recipient (up to 5).
3. For a token that doesn't expire, go to **Business settings → System users**, add a system user, and generate
   a token with `whatsapp_business_messaging`.
4. **App settings → Basic** shows the **App secret**.
5. In **WhatsApp → Configuration → Webhook**, set:
   - Callback URL: `https://<backend>/api/v1/messaging/whatsapp/webhook`
   - Verify token: any string you choose, the same one as `WHATSAPP_VERIFY_TOKEN`
   - Then subscribe to the `messages` field.
6. Set these in `backend/.env` and in the backend's Vercel environment variables:

   ```
   WHATSAPP_TOKEN=...            # access token
   WHATSAPP_PHONE_NUMBER_ID=...  # from API Setup
   WHATSAPP_APP_SECRET=...       # App settings → Basic
   WHATSAPP_VERIFY_TOKEN=...     # your own string from step 5
   WHATSAPP_BOT_NUMBER=92300...  # the bot's number, digits only
   ```

7. Run `alembic upgrade head` against the production database.

The Profile card says "Coming soon" until `WHATSAPP_BOT_NUMBER` is set.

To go live for everyone, you need a number that isn't already on WhatsApp, Meta Business verification, an approved
display name ("LiftAndPlate"), and a payment method on the WhatsApp account. Each number gets 1,000 free replies a
month; after that a reply costs about US$0.015 in Pakistan (Oct 2026 rates).

## Test locally without Meta

`.claude/launch.json` has `backend-whatsapp-test`, which starts the API with a test app secret and a dummy bot
number. With no `WHATSAPP_TOKEN`, replies are written to the backend log instead of sent. Post a webhook signed with
HMAC-SHA256 of the body using `local-test-secret` in the `X-Hub-Signature-256` header.

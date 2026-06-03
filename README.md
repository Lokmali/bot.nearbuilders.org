# NEAR Builders Telegram Bot

A Telegram bot for nominating and onboarding builders to the [NEAR](https://near.org) ecosystem. Admins (or any group member) can nominate someone directly from a group chat, the bot contacts them via DM to walk through a profile setup, and on completion submits their profile to the NEAR Builders API for review.

---

## Features

- `/onboard` command in any group - two ways to use it:
  - By username: `/onboard @username` (anywhere in the chat)
  - By reply: send `/onboard` as a reply to the target user's message
- Nominated users are messaged directly to complete their profile
- Username lookup uses a three-tier approach: DB (most reliable) > Telegram API > username-only fallback
- If the user hasn't started the bot yet, a prompt is posted in the group with a link to start it
- Full DM onboarding flow with a dedicated question per field
- Skills selection via interactive toggle buttons (tap to add/remove)
- Links builder via guided Add Link flow (label > URL > repeat as needed)
- Summary review at the end with per-field edit buttons in a 2-column grid and a full-width Confirm & Submit button
- Submits to the NEAR Builders API on confirmation
- PostgreSQL logging of nominated users and nomination events
- Rotating log file at `logs/bot.log`

---

## Onboarding Flow

```
/onboard @username  (or as a reply to a message)
  └─> DM sent to nominated user
        └─> /start
              ├─> NEAR Address (optional)
              ├─> Name (optional)
              ├─> Bio (optional, max 1000 chars - trimmed if exceeded)
              ├─> Skills (toggle button selection)
              ├─> Location (optional)
              ├─> Links (guided Add Link flow)
              └─> Summary with edit buttons
                    └─> Confirm & Submit > POST to NEAR Builders API
```

All fields are optional. Users can skip any step using the ⏭️ Skip button.

---

## Prerequisites

- Python 3.10+
- A PostgreSQL database
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A NEAR Builders API key

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/NEARBuilders/bot.nearbuilders.org.git
cd bot.nearbuilders.org
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here #BOT TOKEN FROM BOTFATHER
DATABASE_URL=postgresql://user:password@localhost:5432/nearbuilders #POSTGRES LOCAL INSTALL
NEARBUILDERS_API_URL=https://nearbuilders.org/api/proposals #POST
NEARBUILDERS_API_KEY=your_api_key_here #API KEY FROM NEARBUILDERS WEB UI DASHBOARD

# Optional: override the default allowed skills list (comma-separated)
# ALLOWED_SKILLS=Frontend,Backend,Rust,Typescript,DeFi
```

### 5. BotFather setup

In [@BotFather](https://t.me/BotFather):

Go to **Bot Settings > Group Privacy > Turn Off** so the bot can read messages in groups without being @mentioned

### 6. Update the bot username

In `bot.py`, update this line to match your bot's actual username - this is required for onboarding as an auto message if the user has not interacted with the bot before:

```python
BOT_USERNAME = "@nearbuildersbot"
```

### 7. Run

```bash
python bot.py
```

The database tables are created automatically on first run.

---

## Running via Windows Task Scheduler

1. Create a new task in Task Scheduler
2. Set **Action** to: `cmd /c "cd /d C:\path\to\bot.nearbuilders.org && venv\Scripts\python.exe bot.py"`
3. Logs will be written to `logs\bot.log` in the bot directory automatically

---

## Project Structure

```
bot.nearbuilders.org/
├── bot.py              # Main bot - all Telegram handlers and entry point
├── conversation.py     # State machine for the onboarding flow
├── config.py           # Allowed skills list (env override supported)
├── db.py               # PostgreSQL connection, schema, and queries
├── api_client.py       # POST to the NEAR Builders API
├── requirements.txt    # Pinned dependencies
├── .env.example        # Environment variable template
└── logs/               # Created automatically on first run
    └── bot.log
```

---

## Database Schema

**`bot_users`** - every user who has been nominated (grants them access through `/start`)

| Column | Type | Description |
|---|---|---|
| `user_id` | BIGINT | Telegram user ID (primary key) |
| `username` | TEXT | Telegram @username |
| `first_name` | TEXT | Telegram first name |
| `started_at` | TIMESTAMPTZ | When they were first registered |
| `updated_at` | TIMESTAMPTZ | Last updated |

**`nomination_log`** - every `/onboard` event

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL | Primary key |
| `nominated_user_id` | BIGINT | Who was nominated |
| `nominated_by_user_id` | BIGINT | Who nominated them |
| `group_chat_id` | BIGINT | Which group the command was used in |
| `created_at` | TIMESTAMPTZ | When it happened |

---

## API Integration

On confirmation, the bot POSTs to `https://nearbuilders.org/api/proposals` with the following body:

```json
{
  "pluginId": "builders",
  "entityId": "yourname.near",
  "payload": {
    "name": "Your Name",
    "bio": "Short bio",
    "skills": ["Rust", "DeFi"],
    "location": "Remote",
    "links": {
      "github": "https://github.com/yourname"
    }
  },
  "source": "telegram",
  "metadata": {
    "nominatedBy": "telegram:123456789",
    "telegramChatId": -1001234567890
  }
}
```

- `entityId` uses the NEAR address if provided, otherwise falls back to `telegram:<user_id>`
- All payload fields are optional
- `nominatedBy` and `telegramChatId` are sourced from the nomination log in the database

---

## Default Skills List

The following skills are available by default. Override via `ALLOWED_SKILLS` in `.env`:

`Frontend` · `Backend` · `Product Owner` · `Smart Contract` · `Rust` · `Typescript` · `DeFi` · `AI Automation` · `DevOps` · `Data`

---

## Dependencies

```
anyio==4.13.0
certifi==2026.5.20
h11==0.16.0
httpcore==1.0.9
httpx==0.27.0
idna==3.16
psycopg2-binary==2.9.12
python-dotenv==1.0.1
python-telegram-bot==21.6
sniffio==1.3.1
```

---

## License

MIT

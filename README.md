# 11:11 Bot

A magical Discord bot that reminds server members to make a wish at 11:11 AM and 11:11 PM.

## Features

- **Automated reminders** at 11:11 AM and 11:11 PM (configurable timezone)
- **Slash-compatible prefix commands** for testing and status
- **Structured logging** for production monitoring
- **Graceful error handling** with detailed logs

## Commands

| Command | Aliases | Description | Permissions |
|---------|---------|-------------|-------------|
| `!ping` | — | Check bot latency | None |
| `!test-wish` | `!testwish` | Manually send a wish reminder | Manage Messages |
| `!next-wish` | `!nextwish` | Show next scheduled reminder time | None |

## Setup

1. Install Python 3.10 or newer.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`.
4. Set `DISCORD_TOKEN` to the bot token from the Discord Developer Portal.
5. Set `WISH_CHANNEL_ID` to the channel where reminders should be posted.
6. Optionally set `TIMEZONE` in `.env`; it defaults to `Asia/Kolkata`.
7. Start the bot:

   ```powershell
   python bot.py
   ```

The bot needs `View Channel` and `Send Messages` permissions in the target channel. Keep the `.env` file private.

## Development

### Install dev dependencies

```powershell
pip install -r requirements-dev.txt
```

### Run tests

```powershell
pytest tests/ -v
```

### Lint & format

```powershell
ruff check .
ruff format .
```

## Assets

- `assets/wish-bot-icon.png` — Discord bot icon
- `assets/wish-bot-banner.png` — Discord banner

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | — | Bot token from Discord Developer Portal |
| `WISH_CHANNEL_ID` | Yes | — | Channel ID for wish reminders |
| `TIMEZONE` | No | `Asia/Kolkata` | IANA timezone (e.g., `America/New_York`, `Europe/London`) |


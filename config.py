import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_GROUP = os.getenv("TELEGRAM_GROUP", "@your_group_username")
WEBINAR_LINK = os.getenv("WEBINAR_LINK", "https://example.com/webinar")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///webinar_bot.db")
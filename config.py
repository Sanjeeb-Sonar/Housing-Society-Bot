"""Configuration settings for the Housing Society Bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token from BotFather
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Database path
DATABASE_PATH = os.getenv("DATABASE_PATH", "housing_bot.db")

# Listing expiry in days
LISTING_EXPIRY_DAYS = int(os.getenv("LISTING_EXPIRY_DAYS", "180"))

# Maximum results to show per query
MAX_RESULTS = 10

# Allowed chat IDs (comma-separated). If empty, bot works in all groups.
_allowed_ids = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = set(
    int(cid.strip()) for cid in _allowed_ids.split(",") if cid.strip()
)

# Bot admin Telegram user ID (for admin-only commands)
_admin_id = os.getenv("BOT_ADMIN_ID", "")
BOT_ADMIN_ID = int(_admin_id) if _admin_id.strip() else None

"""Configuration settings for the Housing Society Bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token from BotFather
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Bot username (without @, needed for deep links)
BOT_USERNAME = os.getenv("BOT_USERNAME", "societykakubot")

# Database path
DATABASE_PATH = os.getenv("DATABASE_PATH", "housing_bot.db")

# Listing expiry in days
LISTING_EXPIRY_DAYS = int(os.getenv("LISTING_EXPIRY_DAYS", "180"))

# Maximum results to show per query
MAX_RESULTS = 10

# --- Lead Pricing (Telegram Stars) ---
# Free leads shown in DM when user clicks "Get Leads"
FREE_LEADS_COUNT = 2

# Tier 1: ₹59 ≈ 75 Stars → 5 verified contacts
TIER1_STARS = int(os.getenv("TIER1_STARS", "75"))
TIER1_LEADS = 5

# Tier 2: ₹199 ≈ 250 Stars → 15 verified contacts + negotiation tips
TIER2_STARS = int(os.getenv("TIER2_STARS", "250"))
TIER2_LEADS = 15

# Allowed chat IDs (comma-separated). If empty, bot works in all groups.
_allowed_ids = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = set(
    int(cid.strip()) for cid in _allowed_ids.split(",") if cid.strip()
)

# Bot admin Telegram user ID (for admin-only commands)
_admin_id = os.getenv("BOT_ADMIN_ID", "")
BOT_ADMIN_ID = int(_admin_id) if _admin_id.strip() else None

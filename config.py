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

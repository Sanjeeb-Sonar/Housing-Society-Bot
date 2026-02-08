# Housing Society Telegram Bot 🏠

A Telegram bot for housing society groups that automatically matches queries with relevant listings.

## Features

- ✅ Monitors all group messages
- ✅ Identifies listings (someone offering something)
- ✅ Identifies queries (someone looking for something)
- ✅ Matches queries with relevant listings
- ✅ Supports Hindi/Hinglish messages
- ✅ Auto-expires listings after 180 days
- ✅ Shows most recent listings first

## Supported Categories

| Category | Examples |
|----------|----------|
| 🏠 Property | Flats, houses, PG, rent/buy |
| 🪑 Furniture | Sofa, table, bed, fridge |
| 🧹 Maid/Cook | Domestic help, nanny |
| 🔧 Plumber | Plumbing services |
| 💡 Electrician | Electrical work |
| 🪚 Carpenter | Furniture repair |
| 🚗 Driver | Personal drivers |
| ❄️ AC Repair | Appliance repair |
| 📚 Tutor | Home tuition |
| 📦 Packers | Moving services |
| 🚙 Vehicles | Cars, bikes |

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token you receive

### 2. Configure the Bot

```bash
# Copy example env file
copy .env.example .env

# Edit .env and add your bot token
notepad .env
```

Add your token:
```
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_PATH=housing_bot.db
LISTING_EXPIRY_DAYS=180
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
python bot.py
```

### 5. Add Bot to Your Group

1. Add the bot to your housing society group
2. Make it an admin (so it can read messages)
3. The bot will start monitoring automatically!

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/stats` | Show active listing count |

## How It Works

1. **Member posts a listing**:
   > "Selling my 2BHK flat in Tower B, 75L. Contact: 9876543210"
   
   Bot silently stores this listing.

2. **Another member posts a query**:
   > "Looking for 2BHK to buy, any leads?"
   
   Bot responds with matching listings:
   ```
   🏠 Found 2 listings for 2bhk (property):
   
   1️⃣ @user1 (2 days ago):
      "Selling my 2BHK flat in Tower B, 75L"
      📞 Contact: 9876543210
   ```

3. **General messages are ignored**:
   > "Good morning everyone!"
   
   Bot does nothing.

## Files

```
Telebot/
├── bot.py           # Main entry point
├── config.py        # Configuration
├── database.py      # SQLite operations
├── classifier.py    # Message classification
├── keywords.py      # Category keywords
├── matcher.py       # Query matching
├── requirements.txt # Dependencies
├── .env.example     # Env template
└── README.md        # This file
```

## License

MIT

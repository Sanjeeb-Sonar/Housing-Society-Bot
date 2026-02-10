"""
Housing Society Telegram Bot
Automatically matches queries with relevant listings in a housing society group.
Two-way matching: sellers see buyers, buyers see sellers.
"""

import logging
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    ChatMemberHandler, ContextTypes, filters
)

from config import BOT_TOKEN, ALLOWED_CHAT_IDS, BOT_ADMIN_ID
from database import init_db, add_listing, get_stats, cleanup_expired
from classifier import classifier
from matcher import find_matches, find_interested_buyers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_allowed_chat(chat_id: int) -> bool:
    """Check if a chat is in the allowed list. If no list is set, allow all."""
    if not ALLOWED_CHAT_IDS:
        return True  # No restriction configured
    return chat_id in ALLOWED_CHAT_IDS


async def handle_bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a new group. Auto-leave if not authorized."""
    my_chat_member = update.my_chat_member
    if not my_chat_member:
        return

    # Check if the bot was added (status changed to 'member' or 'administrator')
    new_status = my_chat_member.new_chat_member.status
    old_status = my_chat_member.old_chat_member.status

    if old_status in ('left', 'kicked') and new_status in ('member', 'administrator'):
        chat = my_chat_member.chat
        if not is_allowed_chat(chat.id):
            logger.warning(f"Bot added to unauthorized group: {chat.title} ({chat.id})")
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="⛔ Sorry, I'm only authorized to work in specific groups. Leaving now."
                )
                await context.bot.leave_chat(chat.id)
                logger.info(f"Left unauthorized group: {chat.title} ({chat.id})")
            except Exception as e:
                logger.error(f"Error leaving unauthorized group: {e}")
        else:
            logger.info(f"Bot added to authorized group: {chat.title} ({chat.id})")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming group messages."""
    
    # Only process group messages
    if not update.message or not update.message.text:
        return
    
    # Skip if not from a group
    if update.effective_chat.type not in ['group', 'supergroup']:
        return
    
    # Skip if not an allowed group
    if not is_allowed_chat(update.effective_chat.id):
        return
    
    text = update.message.text
    user = update.effective_user
    
    # Classify the message using LLM
    result = classifier.classify(text)
    
    if not result:
        # Message doesn't match any category or is irrelevant - stay silent
        logger.debug(f"Ignored message: {text[:50]}...")
        return
    
    logger.info(f"Classified: {result}")
    
    if result["listing_type"] == "offer":
        # Store the listing silently with metadata
        listing_id = add_listing(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            message_id=update.message.message_id,
            chat_id=update.effective_chat.id,
            category=result["category"],
            subcategory=result["subcategory"],
            listing_type="offer",
            contact=result["contact"],
            message=text,
            property_type=result.get("property_type"),
            gender_preference=result.get("gender_preference")
        )
        logger.info(f"Stored listing #{listing_id} in category: {result['category']}")
        
        # Show interested buyers if any exist
        buyers_response = find_interested_buyers(
            category=result["category"],
            subcategory=result["subcategory"],
            property_type=result.get("property_type"),
            gender_preference=result.get("gender_preference"),
            chat_id=update.effective_chat.id
        )
        
        if buyers_response:
            await update.message.reply_text(
                buyers_response,
                parse_mode='Markdown'
            )
            logger.info(f"Showed interested buyers for: {result['category']}")
        # No response if no buyers - silent save
    
    elif result["listing_type"] == "query":
        # Store the query silently with metadata
        query_id = add_listing(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            message_id=update.message.message_id,
            chat_id=update.effective_chat.id,
            category=result["category"],
            subcategory=result["subcategory"],
            listing_type="query",
            contact=result["contact"],
            message=text,
            property_type=result.get("property_type"),
            gender_preference=result.get("gender_preference")
        )
        logger.info(f"Stored query #{query_id} in category: {result['category']}")
        
        # Show matching listings if any exist (filtered by property_type and gender)
        response = find_matches(
            category=result["category"],
            subcategory=result["subcategory"],
            property_type=result.get("property_type"),
            gender_preference=result.get("gender_preference"),
            chat_id=update.effective_chat.id
        )
        
        if response:
            await update.message.reply_text(
                response,
                parse_mode='Markdown'
            )
            logger.info(f"Responded to query for: {result['category']}")
        # No response if no matches - silent save


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics about active listings."""
    if not is_allowed_chat(update.effective_chat.id):
        return

    stats = get_stats()
    
    if stats["total"] == 0:
        await update.message.reply_text("📊 No active listings yet.")
        return
    
    response = f"📊 **Active Listings**: {stats['total']}\n\n"
    
    from keywords import CATEGORY_EMOJIS
    for category, count in stats["by_category"].items():
        emoji = CATEGORY_EMOJIS.get(category, "📋")
        response += f"{emoji} {category.title()}: {count}\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    if not is_allowed_chat(update.effective_chat.id):
        return

    help_text = """
🏠 **Housing Society Bot**

I automatically match your queries with relevant listings!

**How it works:**
1. When someone posts about selling something or offering a service, I save it.
2. When you ask for something (e.g., "need plumber"), I show you matching listings.

**Examples:**
• "Selling 2BHK flat, 50L, contact 9876543210"
• "Need electrician urgently"
• "Maid chahiye for morning work"
• "Anyone selling used sofa?"

**Commands:**
/stats - Show active listing count
/help - Show this message

**Categories I understand:**
🏠 Property | 🪑 Furniture | 🧹 Maid/Cook
🔧 Plumber | 💡 Electrician | 🪚 Carpenter
🚗 Driver | ❄️ AC Repair | 📚 Tutor
📦 Packers | 🚙 Vehicles
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    """Periodic job to clean up expired listings."""
    deleted = cleanup_expired()
    if deleted > 0:
        logger.info(f"Cleaned up {deleted} expired listings")


def main():
    """Start the bot."""
    
    if not BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set!")
        print("Please create a .env file with your bot token.")
        print("See .env.example for reference.")
        return
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    if ALLOWED_CHAT_IDS:
        logger.info(f"Bot restricted to chat IDs: {ALLOWED_CHAT_IDS}")
    else:
        logger.warning("No ALLOWED_CHAT_IDS set - bot will work in ALL groups")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", help_command))
    
    # Handle bot being added to groups (auto-leave unauthorized ones)
    app.add_handler(ChatMemberHandler(handle_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Handle all text messages in groups
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_message
    ))
    
    # Schedule daily cleanup (optional, requires pip install "python-telegram-bot[job-queue]")
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_daily(cleanup_job, time=datetime.time(hour=3, minute=0))
        logger.info("Daily cleanup job scheduled")
    else:
        logger.warning("Job queue not available - expired listings cleanup disabled")
    
    # Start the bot with drop_pending_updates to avoid conflict errors
    logger.info("🚀 Bot started! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    import datetime
    main()

"""
Housing Society Telegram Bot
Automatically matches queries with relevant listings in a housing society group.
Two-way matching: sellers see buyers, buyers see sellers.
Monetized via Telegram Stars for verified lead access.
"""

import logging
import datetime
from telegram import (
    Update, LabeledPrice,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    ChatMemberHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, ContextTypes, filters
)

from config import (
    BOT_TOKEN, ALLOWED_CHAT_IDS, BOT_ADMIN_ID, BOT_USERNAME,
    FREE_LEADS_COUNT, TIER1_PRICE, TIER1_LEADS, TIER2_PRICE, TIER2_LEADS,
    UPI_ID, UPI_NAME
)
from database import (
    init_db, add_listing, get_stats, cleanup_expired,
    save_lead_request, get_lead_request, get_leads_for_request, 
    save_payment_claim, get_payment_claim, update_payment_status
)
from classifier import classifier
from matcher import (
    find_matches, find_interested_buyers, build_label,
    format_free_leads, format_upsell_message, format_paid_leads
)

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


# ─── Group Message Handler ────────────────────────────────────


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming group messages."""
    
    # Only process group messages
    if not update.message or not update.message.text:
        return
    
    # DEBUG: Log every message to see if we're receiving them
    logger.info(f"Received message in chat {update.effective_chat.id}: {update.message.text[:20]}...")
    
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
        response = find_interested_buyers(
            category=result["category"],
            subcategory=result["subcategory"],
            property_type=result.get("property_type"),
            gender_preference=result.get("gender_preference"),
            chat_id=update.effective_chat.id,
            original_message=text
        )
        
        if response:
            # Save a lead request for this match
            request_id = save_lead_request(
                user_id=user.id,
                category=result["category"],
                subcategory=result["subcategory"],
                property_type=result.get("property_type"),
                gender_preference=result.get("gender_preference"),
                listing_type="offer",
                source_chat_id=update.effective_chat.id
            )
            
            # Add "Get Leads" deep-link button
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🔍 Get Leads",
                    url=f"https://t.me/{BOT_USERNAME}?start=leads_{request_id}"
                )
            ]])
            
            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=keyboard
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
        
        # Show matching listings if any exist (cross-group)
        response = find_matches(
            category=result["category"],
            subcategory=result["subcategory"],
            property_type=result.get("property_type"),
            gender_preference=result.get("gender_preference"),
            chat_id=update.effective_chat.id,
            original_message=text
        )
        
        if response:
            # Save a lead request for deep link
            request_id = save_lead_request(
                user_id=user.id,
                category=result["category"],
                subcategory=result["subcategory"],
                property_type=result.get("property_type"),
                gender_preference=result.get("gender_preference"),
                listing_type="query",
                source_chat_id=update.effective_chat.id
            )
            
            # Add "Get Leads" deep-link button
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🔍 Get Leads",
                    url=f"https://t.me/{BOT_USERNAME}?start=leads_{request_id}"
                )
            ]])
            
            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            logger.info(f"Responded to query for: {result['category']}")
        # No response if no matches - silent save


# ─── Deep Link Handler (DM) ──────────────────────────────────


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — either deep link for leads or general help."""
    
    # Check if this is a deep link: /start leads_123
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        
        if arg.startswith("leads_"):
            await _handle_get_leads(update, context, arg)
            return
    
    # Regular /start or /help — show help
    await help_command(update, context)


async def _handle_get_leads(update: Update, context: ContextTypes.DEFAULT_TYPE, arg: str):
    """Handle the deep link when user clicks 'Get Leads' from group."""
    try:
        request_id = int(arg.replace("leads_", ""))
    except ValueError:
        await update.message.reply_text("❌ Invalid link. Please try again from the group.")
        return
    
    # Fetch the lead request
    lead_req = get_lead_request(request_id)
    if not lead_req:
        await update.message.reply_text("❌ This link has expired. Please try again from the group.")
        return
    
    user_id = update.effective_user.id
    label = build_label(
        lead_req["category"],
        lead_req.get("subcategory"),
        lead_req.get("property_type"),
        lead_req.get("gender_preference")
    )
    
    # Get free leads (first 2)
    free_listings = get_leads_for_request(request_id, limit=FREE_LEADS_COUNT, offset=0)
    
    if not free_listings:
        await update.message.reply_text(
            f"😔 No contacts available for *{label}* right now. We'll notify you when new listings come in!",
            parse_mode='Markdown'
        )
        return
    
    # Send free leads
    free_msg = format_free_leads(free_listings, label)
    await update.message.reply_text(free_msg, parse_mode='Markdown')
    
    # Check how many more are available
    all_listings = get_leads_for_request(request_id, limit=100, offset=0)
    total_available = len(all_listings)
    
    if total_available > FREE_LEADS_COUNT:
        # Send upsell message with payment buttons
        upsell_msg = format_upsell_message(total_available)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"🔓 Unlock {TIER1_LEADS} Contacts — ₹{TIER1_PRICE}",
                callback_data=f"buy_t1_{request_id}"
            )],
            [InlineKeyboardButton(
                f"🔓 Unlock {TIER2_LEADS} Contacts + Tips — ₹{TIER2_PRICE}",
                callback_data=f"buy_t2_{request_id}"
            )]
        ])
        
        await update.message.reply_text(
            upsell_msg,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            "✅ That's all the contacts we have right now. Check back later for more!",
            parse_mode='Markdown'
        )
    
    logger.info(f"Sent {len(free_listings)} free leads to user {user_id} for request #{request_id}")


# ─── Payment Flow (Manual UPI) ──────────────────────────────


async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user clicks a 'Buy' button — show QR Code + UPI details."""
    query = update.callback_query
    await query.answer()
    
    data = query.data  # e.g. "buy_t1_123"
    parts = data.split("_")
    
    if len(parts) != 3:
        await query.message.reply_text("❌ Something went wrong.")
        return
    
    tier = parts[1]  # "t1" or "t2"
    try:
        request_id = int(parts[2])
    except ValueError:
        await query.message.reply_text("❌ Invalid request.")
        return
    
    if tier == "t1":
        amount = TIER1_PRICE
        leads_count = TIER1_LEADS
    elif tier == "t2":
        amount = TIER2_PRICE
        leads_count = TIER2_LEADS
    else:
        return

    # upi:// deep link — works as a clickable TEXT link in Telegram messages on mobile
    # (Telegram buttons only support http/https/tg, NOT upi://)
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={amount}&cu=INR"
    
    msg = (
        f"💳 *Payment Required: ₹{amount}*\n\n"
        f"To get *{leads_count} verified contacts*, please pay via UPI:\n\n"
        f"🔹 UPI ID: `{UPI_ID}`\n"
        f"🔹 Amount: `₹{amount}`\n\n"
        f"👇 [🔗 Tap here to pay ₹{amount} via UPI App]({upi_link})\n\n"
        f"After paying, tap ✅ below 👇"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I have paid", callback_data=f"claim_{request_id}_{amount}")]
    ])
    
    # Send invoice
    try:
        await query.message.reply_text(msg, parse_mode='Markdown', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Payment message failed: {e}")
        plain_msg = (
            f"Payment Required: Rs.{amount}\n\n"
            f"UPI ID: {UPI_ID}\n"
            f"Amount: Rs.{amount}\n\n"
            f"Open PhonePe/GPay/Paytm and send Rs.{amount} to {UPI_ID}\n"
            f"Then tap the button below."
        )
        await query.message.reply_text(plain_msg, reply_markup=keyboard)


async def handle_payment_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user clicks 'I have paid'."""
    query = update.callback_query
    await query.answer()
    
    data = query.data  # "claim_123_49"
    parts = data.split("_")
    request_id = int(parts[1])
    amount = int(parts[2])
    user = query.from_user
    
    # Save claim to DB
    claim_id = save_payment_claim(user.id, request_id, amount)
    
    # Notify User
    await query.edit_message_text(
        f"⏳ *Payment Claimed!*\n\n"
        f"Admin has been notified. You will receive the leads automatically once approved (usually within 10-15 mins).",
        parse_mode='Markdown'
    )
    
    # Notify Admin
    if BOT_ADMIN_ID:
        admin_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{claim_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{claim_id}")
            ]
        ])
        
        await context.bot.send_message(
            chat_id=BOT_ADMIN_ID,
            text=(
                f"💰 **New Payment Claim!**\n\n"
                f"👤 User: @{user.username} (ID: {user.id})\n"
                f"💵 Amount: ₹{amount}\n"
                f"🆔 Claim ID: #{claim_id}\n"
                f"📄 Request ID: #{request_id}"
            ),
            reply_markup=admin_keyboard,
            parse_mode='Markdown'
        )
        logger.info(f"New payment claim #{claim_id} from user {user.id} sent to admin {BOT_ADMIN_ID}")
    else:
        logger.error("BOT_ADMIN_ID not set! Cannot process payment claims.")
        await query.message.reply_text("⚠ Admin configuration error. Please contact support.")


async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Admin clicking Approve/Reject."""
    query = update.callback_query
    await query.answer()
    
    data = query.data  # "approve_99" or "reject_99"
    action, claim_id_str = data.split("_")
    claim_id = int(claim_id_str)
    
    claim = get_payment_claim(claim_id)
    if not claim:
        await query.edit_message_text("❌ Claim not found.")
        return
        
    if claim['status'] != 'pending':
        await query.edit_message_text(f"⚠ Claim already {claim['status']}.")
        return

    if action == "approve":
        # Update DB
        update_payment_status(claim_id, 'approved', query.message.message_id)
        
        # Deliver leads to User
        request_id = claim['request_id']
        amount = claim['amount']
        
        # Determine tier details based on amount
        if amount == TIER1_PRICE:
            leads_count = TIER1_LEADS
            include_tips = False
        else:
            leads_count = TIER2_LEADS
            include_tips = True
            
        lead_req = get_lead_request(request_id)
        label = build_label(
            lead_req["category"],
            lead_req.get("subcategory"),
            lead_req.get("property_type"),
            lead_req.get("gender_preference")
        )
        
        paid_listings = get_leads_for_request(request_id, limit=leads_count, offset=FREE_LEADS_COUNT)
        paid_msg = format_paid_leads(paid_listings, label, include_tips=include_tips)
        
        try:
            await context.bot.send_message(
                chat_id=claim['user_id'],
                text=f"✅ **Payment Approved!**\n\n{paid_msg}",
                parse_mode='Markdown'
            )
            await query.edit_message_text(f"✅ Approved claim #{claim_id} for ₹{amount}.")
        except Exception as e:
            logger.error(f"Failed to send leads to user {claim['user_id']}: {e}")
            await query.edit_message_text(f"⚠ Approved, but failed to send message to user (blocked?).")
            
    elif action == "reject":
        update_payment_status(claim_id, 'rejected', query.message.message_id)
        
        try:
            await context.bot.send_message(
                chat_id=claim['user_id'],
                text="❌ **Payment Verification Failed**\n\nAdmin could not verify your payment. Please contact admin directly with screenshot.",
                parse_mode='Markdown'
            )
            await query.edit_message_text(f"❌ Rejected claim #{claim_id}.")
        except:
            pass


# ─── Commands ─────────────────────────────────────────────────


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics about active listings."""
    if update.effective_chat.type in ['group', 'supergroup']:
        if not is_allowed_chat(update.effective_chat.id):
            return

    stats = get_stats()
    
    if stats["total"] == 0:
        await update.message.reply_text("📊 No active listings yet.")
        return
    
    response = f"📊 *Active Listings*: {stats['total']}\n\n"
    
    from keywords import CATEGORY_EMOJIS
    for category, count in stats["by_category"].items():
        emoji = CATEGORY_EMOJIS.get(category, "📋")
        response += f"{emoji} {category.title()}: {count}\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    # In groups, check if allowed
    if update.effective_chat.type in ['group', 'supergroup']:
        if not is_allowed_chat(update.effective_chat.id):
            return

    help_text = """
🏠 *Society Ka Bot*

I automatically match your queries with relevant listings across housing society groups!

*How it works:*
1️⃣ Post what you're offering or looking for in the group
2️⃣ I'll instantly show you how many matches exist
3️⃣ Tap *"Get Leads"* to get contacts in your DM

*Free:* 2 contacts per search
*Paid:* More contacts via ⭐ Telegram Stars

*Examples:*
• "Selling 2BHK flat, 50L, contact 9876543210"
• "Need electrician urgently"
• "Maid chahiye for morning work"
• "Looking for female roommate"

*Commands:*
/stats - Show active listing count
/help - Show this message

*Categories I understand:*
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
    
    # ── Command handlers ──
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", handle_start))
    
    # ── Group membership handler ──
    app.add_handler(ChatMemberHandler(handle_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # ─── Payment handlers ──
    app.add_handler(CallbackQueryHandler(handle_buy_callback, pattern=r"^buy_"))
    app.add_handler(CallbackQueryHandler(handle_payment_claim, pattern=r"^claim_"))
    app.add_handler(CallbackQueryHandler(handle_admin_decision, pattern=r"^(approve|reject)_"))

    # ─── Group text message handler ──
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_message
    ))
    
    # Schedule daily cleanup
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_daily(cleanup_job, time=datetime.time(hour=3, minute=0))
        logger.info("Daily cleanup job scheduled")
    else:
        logger.warning("Job queue not available - expired listings cleanup disabled")
    
    # Start the bot
    logger.info("🚀 Bot started! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()

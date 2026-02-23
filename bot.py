"""
Housing Society Telegram Bot
Automatically matches queries with relevant listings in a housing society group.
Two-way matching: sellers see buyers, buyers see sellers.
Monetized via Razorpay Payment Links for verified lead access.
"""

import logging
import datetime
import json
import hmac
import hashlib
import asyncio

import razorpay
from aiohttp import web

from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    ChatMemberHandler, CallbackQueryHandler,
    ContextTypes, filters
)

from config import (
    BOT_TOKEN, ALLOWED_CHAT_IDS, BOT_ADMIN_ID, BOT_USERNAME,
    FREE_LEADS_COUNT, TIER1_PRICE, TIER1_LEADS, TIER2_PRICE, TIER2_LEADS,
    RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET,
    WEBHOOK_BASE_URL, WEBHOOK_PORT
)
from database import (
    init_db, add_listing, get_stats, cleanup_expired,
    save_lead_request, get_lead_request, get_leads_for_request, 
    save_payment_claim, get_payment_by_link_id, update_payment_status
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

# Initialize Razorpay client
razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    logger.info("Razorpay client initialized")
else:
    logger.warning("Razorpay keys not set! Payment links will not work.")


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


def _create_razorpay_link(amount: int, description: str, request_id: int, user_id: int) -> dict:
    """Create a Razorpay Payment Link and return the response."""
    if not razorpay_client:
        raise Exception("Razorpay not configured")
    
    payload = {
        "amount": amount * 100,  # Razorpay uses paise (₹49 = 4900 paise)
        "currency": "INR",
        "description": description,
        "notes": {
            "request_id": str(request_id),
            "user_id": str(user_id),
        },
        "callback_url": f"{WEBHOOK_BASE_URL}/razorpay/callback" if WEBHOOK_BASE_URL else "",
        "callback_method": "get"
    }
    
    return razorpay_client.payment_link.create(payload)


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
    
    # Get free leads (first 1)
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
        # Create Razorpay Payment Links for both tiers
        upsell_msg = format_upsell_message(total_available, category=lead_req["category"])
        
        buttons = []
        
        # Tier 1 payment link
        try:
            t1_link = _create_razorpay_link(
                amount=TIER1_PRICE,
                description=f"Unlock {TIER1_LEADS} contacts for {label}",
                request_id=request_id,
                user_id=user_id
            )
            # Save to DB
            save_payment_claim(
                user_id=user_id,
                request_id=request_id,
                amount=TIER1_PRICE,
                tier="t1",
                razorpay_link_id=t1_link["id"]
            )
            buttons.append([InlineKeyboardButton(
                f"🔓 Unlock {TIER1_LEADS} Contacts — ₹{TIER1_PRICE}",
                url=t1_link["short_url"]
            )])
            logger.info(f"Created Razorpay link {t1_link['id']} for ₹{TIER1_PRICE}")
        except Exception as e:
            logger.error(f"Failed to create Tier 1 payment link: {e}")
        
        # Tier 2 payment link
        try:
            t2_link = _create_razorpay_link(
                amount=TIER2_PRICE,
                description=f"Unlock {TIER2_LEADS} contacts + tips for {label}",
                request_id=request_id,
                user_id=user_id
            )
            save_payment_claim(
                user_id=user_id,
                request_id=request_id,
                amount=TIER2_PRICE,
                tier="t2",
                razorpay_link_id=t2_link["id"]
            )
            buttons.append([InlineKeyboardButton(
                f"🔓 Unlock {TIER2_LEADS} Contacts + Tips — ₹{TIER2_PRICE}",
                url=t2_link["short_url"]
            )])
            logger.info(f"Created Razorpay link {t2_link['id']} for ₹{TIER2_PRICE}")
        except Exception as e:
            logger.error(f"Failed to create Tier 2 payment link: {e}")
        
        if buttons:
            await update.message.reply_text(
                upsell_msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await update.message.reply_text(
                "⚠ Payment system is temporarily unavailable. Please try again later.",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            "✅ That's all the contacts we have right now. Check back later for more!",
            parse_mode='Markdown'
        )
    
    logger.info(f"Sent {len(free_listings)} free leads to user {user_id} for request #{request_id}")


# ─── Razorpay Webhook (Auto-Delivery) ───────────────────────


async def _deliver_leads(bot, claim: dict):
    """Deliver paid leads to the user after successful payment."""
    lead_req = get_lead_request(claim["request_id"])
    if not lead_req:
        logger.error(f"Lead request #{claim['request_id']} not found for claim #{claim['id']}")
        return
    
    label = build_label(
        lead_req["category"],
        lead_req.get("subcategory"),
        lead_req.get("property_type"),
        lead_req.get("gender_preference")
    )
    
    # Determine tier details
    tier = claim.get("tier", "t1")
    if tier == "t1":
        leads_count = TIER1_LEADS
        include_tips = False
    else:
        leads_count = TIER2_LEADS
        include_tips = True
    
    paid_listings = get_leads_for_request(claim["request_id"], limit=leads_count, offset=FREE_LEADS_COUNT)
    paid_msg = format_paid_leads(paid_listings, label, include_tips=include_tips, category=lead_req["category"])
    
    try:
        await bot.send_message(
            chat_id=claim["user_id"],
            text=f"✅ *Payment Received!*\n\n{paid_msg}",
            parse_mode='Markdown'
        )
        logger.info(f"Delivered {len(paid_listings)} paid leads to user {claim['user_id']}")
    except Exception as e:
        logger.error(f"Failed to send leads to user {claim['user_id']}: {e}")

    # Notify admin about the sale
    if BOT_ADMIN_ID:
        try:
            await bot.send_message(
                chat_id=BOT_ADMIN_ID,
                text=(
                    f"💰 *New Sale!*\n\n"
                    f"👤 User ID: {claim['user_id']}\n"
                    f"💵 Amount: ₹{claim['amount']}\n"
                    f"📄 Request: #{claim['request_id']}\n"
                    f"🆔 Razorpay: {claim.get('razorpay_payment_id', 'N/A')}"
                ),
                parse_mode='Markdown'
            )
        except Exception:
            pass


def _verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    if not RAZORPAY_WEBHOOK_SECRET:
        logger.warning("RAZORPAY_WEBHOOK_SECRET not set, skipping signature verification")
        return True
    
    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


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

*Free:* 1 contact per search
*Paid:* More contacts via secure Razorpay payment

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
    """Start the bot with Razorpay webhook server."""
    
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
    
    # Create Telegram application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ── Command handlers ──
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", handle_start))
    
    # ── Group membership handler ──
    app.add_handler(ChatMemberHandler(handle_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))

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
    
    # ─── Start bot with webhook server ──
    logger.info(f"🚀 Bot starting with webhook server on port {WEBHOOK_PORT}...")
    
    # Run Telegram polling + aiohttp webhook server together
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run_all():
        """Run Telegram bot polling and aiohttp webhook server concurrently."""
        # Initialize Telegram app
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        logger.info("✅ Telegram polling started")
        
        # ─── aiohttp webhook server ──
        aio_app = web.Application()
        
        async def health_check(request):
            """Health check endpoint for Render."""
            return web.json_response({"status": "ok", "bot": "Housing Society Bot"})
        
        async def razorpay_webhook(request):
            """Handle Razorpay webhook for payment confirmation."""
            try:
                body = await request.read()
                signature = request.headers.get("X-Razorpay-Signature", "")
                
                # Verify signature
                if not _verify_webhook_signature(body, signature):
                    logger.warning("Invalid Razorpay webhook signature")
                    return web.json_response({"error": "Invalid signature"}, status=400)
                
                payload = json.loads(body)
                event = payload.get("event", "")
                logger.info(f"Razorpay webhook received: {event}")
                
                if event == "payment_link.paid":
                    payment_link = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
                    link_id = payment_link.get("id", "")
                    
                    # Get the first payment associated with this link
                    payments = payload.get("payload", {}).get("payment", {}).get("entity", {})
                    payment_id = payments.get("id", "")
                    
                    logger.info(f"Payment link {link_id} paid. Payment ID: {payment_id}")
                    
                    # Look up the claim
                    claim = get_payment_by_link_id(link_id)
                    if not claim:
                        logger.warning(f"No claim found for Razorpay link {link_id}")
                        return web.json_response({"status": "no_claim"})
                    
                    if claim["status"] == "paid":
                        logger.info(f"Claim #{claim['id']} already processed, skipping")
                        return web.json_response({"status": "already_processed"})
                    
                    # Mark as paid
                    update_payment_status(claim["id"], "paid", razorpay_payment_id=payment_id)
                    
                    # Deliver leads automatically
                    await _deliver_leads(app.bot, claim)
                    
                    logger.info(f"✅ Auto-delivered leads for claim #{claim['id']}")
                    return web.json_response({"status": "delivered"})
                
                return web.json_response({"status": "ok"})
                
            except Exception as e:
                logger.error(f"Webhook error: {e}", exc_info=True)
                return web.json_response({"error": str(e)}, status=500)
        
        aio_app.router.add_get("/", health_check)
        aio_app.router.add_post("/razorpay/webhook", razorpay_webhook)
        
        runner = web.AppRunner(aio_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
        await site.start()
        logger.info(f"✅ Webhook server started on port {WEBHOOK_PORT}")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            logger.info("Shutting down...")
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            await runner.cleanup()
    
    try:
        loop.run_until_complete(run_all())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()

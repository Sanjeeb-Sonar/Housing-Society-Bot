
import asyncio
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Message, CallbackQuery
from telegram.ext import ContextTypes
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Import the handler
try:
    from bot import handle_buy_callback
    print("[INFO] Successfully imported handle_buy_callback")
except ImportError as e:
    print(f"[ERROR] Failed to import: {e}")
    sys.exit(1)

async def test_handler():
    # Mock Update
    update = MagicMock(spec=Update)
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.data = "buy_t1_123"
    update.callback_query.answer = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    
    # Mock Context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    print("1. calling handle_buy_callback with 'buy_t1_123'...")
    try:
        await handle_buy_callback(update, context)
        print("[PASS] Handler executed without exception.")
        
        # Verify reply_text was called
        if update.callback_query.message.reply_text.called:
            args, kwargs = update.callback_query.message.reply_text.call_args
            print("\n[INFO] Bot Reply Text:")
            print(args[0])
            print("\n[INFO] Reply Markup Keys:")
            if 'reply_markup' in kwargs:
                for row in kwargs['reply_markup'].inline_keyboard:
                    for btn in row:
                        print(f" - Button: {btn.text} (URL: {getattr(btn, 'url', 'None')}, Callback: {getattr(btn, 'callback_data', 'None')})")
        else:
            print("[FAIL] Bot did not reply!")
            
    except Exception as e:
        print(f"[FAIL] Handler crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_handler())

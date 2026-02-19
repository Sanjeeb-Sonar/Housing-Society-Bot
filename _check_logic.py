"""
Diagnostic script to verify bot logic with MOCK classification.
This proves that IF the LLM works, the bot works.
"""
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Mock the updater/context
mock_update = MagicMock()
mock_update.effective_chat.id = -100123456789
mock_update.effective_chat.type = 'group'
mock_update.effective_user.id = 12345
mock_update.effective_user.username = "test_user"
mock_update.effective_user.first_name = "Test"
mock_update.message.text = "Need 2BHK for rent"
mock_update.message.message_id = 999

mock_update.message.reply_text = AsyncMock()

mock_context = MagicMock()
mock_context.bot.send_message = AsyncMock()

# Mock the CLASSIFIER to bypass LLM/Groq requirement
import classifier
original_classify = classifier.classifier.classify

def mock_classify(text):
    print(f"[MOCK] Classifying: {text}")
    return {
        "category": "property",
        "subcategory": "2bhk",
        "listing_type": "query",
        "contact": None,
        "property_type": "rent",
        "gender_preference": None
    }

classifier.classifier.classify = mock_classify

# Import bot logic
from bot import handle_message, init_db
from database import get_connection

async def run_diagnostic():
    print("1. Initializing DB...")
    init_db()
    
    # Verify migration worked
    conn = get_connection()
    cols = [row[1] for row in conn.execute("PRAGMA table_info(lead_requests)").fetchall()]
    print(f"   DB Columns in lead_requests: {cols}")
    if 'listing_type' in cols:
        print("   [OK] Migration SUCCESS: listing_type column exists")
    else:
        print("   [FAIL] Migration FAILED: listing_type missing")
    conn.close()

    print("\n2. Simulating Group Message: 'Need 2BHK for rent'...")
    try:
        await handle_message(mock_update, mock_context)
        print("   [OK] handle_message executed without error")
        
        # Check if it tried to reply
        if mock_update.message.reply_text.called:
            args = mock_update.message.reply_text.call_args
            print(f"   [OK] Bot replied: {args[0][0][:50]}...")
            if "start=leads_" in str(args):
                print("   [OK] Deep link present in reply")
        else:
            print("   [WARN] Bot did NOT reply (maybe no matches found?)")
            
    except Exception as e:
        print(f"   [FAIL] CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_diagnostic())

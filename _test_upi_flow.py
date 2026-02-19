"""
Diagnostic script to verify Manual UPI Payment logic locally.
"""
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Mock the updater/context
mock_update = MagicMock()
mock_update.callback_query.id = "123"
mock_update.callback_query.data = "buy_t1_1"
mock_update.callback_query.from_user.id = 12345
mock_update.callback_query.from_user.username = "test_user"
mock_update.callback_query.message.reply_text = AsyncMock()
mock_update.callback_query.edit_message_text = AsyncMock()
mock_update.callback_query.answer = AsyncMock()

mock_context = MagicMock()
mock_context.bot.send_message = AsyncMock()

# Mock DB functions
import database
original_save_claim = database.save_payment_claim
original_get_claim = database.get_payment_claim
original_update_status = database.update_payment_status

# Import bot logic
import bot
from bot import handle_buy_callback, handle_payment_claim, handle_admin_decision

# Helper to patch admin ID
original_admin_id = bot.BOT_ADMIN_ID
bot.BOT_ADMIN_ID = 123456789

async def run_upi_test():
    print("0. Initializing DB...")
    database.init_db()

    print("\n1. Testing 'Buy' Button Click...")
    await handle_buy_callback(mock_update, mock_context)
    
    # Check if QR code message sent
    args = mock_update.callback_query.message.reply_text.call_args
    if args:
        msg = args[0][0]
        if "upi://pay" in msg:
            print("   [OK] UPI Link generated correctly")
        if "Payment Required: ₹" in msg:
            print("   [OK] Payment message correct")
    else:
        print("   [FAIL] No response to Buy click")

    print("\n2. Testing 'I have paid' Button Click...")
    mock_update.callback_query.data = "claim_1_49"
    await handle_payment_claim(mock_update, mock_context)
    
    # Check user notification
    user_args = mock_update.callback_query.edit_message_text.call_args
    if user_args and "Payment Claimed" in user_args[0][0]:
        print("   [OK] User notified of claim")
    else:
        print("   [FAIL] User not notified")
        
    # Check admin notification
    admin_args = mock_context.bot.send_message.call_args
    if admin_args:
        admin_msg = admin_args[1]['text']
        if "New Payment Claim" in admin_msg and "₹49" in admin_msg:
            print("   [OK] Admin notified correctly")
    else:
        print("   [FAIL] Admin not notified (Check BOT_ADMIN_ID)")

    print("\n3. Testing Admin Approval...")
    # Simulate DB state for approval
    claim_id = 1 # Assuming new ID
    mock_update.callback_query.data = f"approve_{claim_id}"
    mock_update.callback_query.message.message_id = 999
    
    # Mock get_claim to return valid pending claim
    database.get_payment_claim = lambda cid: {
        'id': cid, 'user_id': 12345, 'request_id': 1, 'amount': 49, 'status': 'pending'
    }
    
    try:
        await handle_admin_decision(mock_update, mock_context)
        print("   [OK] Admin decision processed without crash")
        
        # Check if leads sent to user
        lead_args = mock_context.bot.send_message.call_args
        if lead_args and "Payment Approved" in lead_args[1]['text']:
            print("   [OK] Leads sent to user")
    except Exception as e:
        print(f"   [FAIL] Admin logic crashed: {e}")

if __name__ == "__main__":
    asyncio.run(run_upi_test())

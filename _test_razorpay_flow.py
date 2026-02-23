# -*- coding: utf-8 -*-
"""
Diagnostic script to verify Razorpay Payment Link flow locally.
Mocks the Razorpay SDK and tests: link creation, webhook processing, lead delivery.
"""
import sys
import io
import asyncio
import json
import hmac
import hashlib
from unittest.mock import MagicMock, AsyncMock, patch

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Mock dotenv before importing anything
import database
database.init_db()

# Import bot logic
import bot
from bot import _handle_get_leads, _deliver_leads, _verify_webhook_signature

# Mock the Razorpay client
mock_razorpay_response = {
    "id": "plink_test_123456",
    "short_url": "https://rzp.io/i/test123",
    "status": "created"
}


async def run_razorpay_test():
    print("=" * 50)
    print("  RAZORPAY PAYMENT FLOW TEST")
    print("=" * 50)
    
    # -- Test 1: Payment Link Creation --
    print("\n1. Testing Payment Link Creation...")
    
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()
    mock_update.effective_user.id = 12345
    
    mock_context = MagicMock()
    mock_context.args = ["leads_1"]
    
    # Create a test lead request
    from database import save_lead_request, add_listing
    
    # Add test listings
    add_listing(
        user_id=99999, username="seller1", first_name="Test Seller",
        message_id=1, chat_id=-100123, category="property",
        subcategory="2bhk", listing_type="offer", contact="9876543210",
        message="2BHK flat for rent 15k near park",
        property_type="rent"
    )
    add_listing(
        user_id=99998, username="seller2", first_name="Test Seller 2",
        message_id=2, chat_id=-100123, category="property",
        subcategory="2bhk", listing_type="offer", contact="9876543211",
        message="2BHK flat for rent 18k furnished",
        property_type="rent"
    )
    
    req_id = save_lead_request(
        user_id=12345, category="property", subcategory="2bhk",
        property_type="rent", listing_type="query", source_chat_id=-100123
    )
    print(f"   Created lead request #{req_id}")
    
    # Mock Razorpay client
    with patch.object(bot, 'razorpay_client') as mock_rz:
        mock_rz.payment_link.create.return_value = mock_razorpay_response
        
        await _handle_get_leads(mock_update, mock_context, f"leads_{req_id}")
        
        # Check calls
        calls = mock_update.message.reply_text.call_args_list
        if len(calls) >= 2:
            free_msg = calls[0][0][0]
            upsell_msg = calls[1][0][0]
            
            if "contacts for" in free_msg:
                print("   [OK] Free leads message sent")
            else:
                print(f"   [FAIL] Free leads message unexpected: {free_msg[:80]}")
            
            if "more verified contacts" in upsell_msg:
                print("   [OK] Upsell message with payment buttons sent")
            else:
                print(f"   [FAIL] Upsell message unexpected: {upsell_msg[:80]}")
            
            # Check if buttons have URLs (not callback_data)
            upsell_keyboard = calls[1][1].get('reply_markup')
            if upsell_keyboard:
                btn = upsell_keyboard.inline_keyboard[0][0]
                if btn.url and "rzp.io" in btn.url:
                    print(f"   [OK] Button has direct Razorpay URL: {btn.url}")
                else:
                    print(f"   [FAIL] Button URL unexpected: {btn.url}")
            
            if mock_rz.payment_link.create.called:
                # Check the first call (Tier 1)
                first_call_args = mock_rz.payment_link.create.call_args_list[0][0][0]
                if first_call_args["amount"] == 4900:  # Rs.49 = 4900 paise
                    print("   [OK] Razorpay amount correct (4900 paise = Rs.49)")
                else:
                    print(f"   [FAIL] Amount wrong: {first_call_args['amount']}")
        else:
            print(f"   [WARN] Expected 2+ messages, got {len(calls)}")

    # -- Test 2: Webhook Processing --
    print("\n2. Testing Webhook Lead Delivery...")
    
    # Mock a claim in DB
    from database import save_payment_claim, get_payment_by_link_id
    claim_id = save_payment_claim(
        user_id=12345, request_id=req_id, amount=49,
        tier="t1", razorpay_link_id="plink_test_789"
    )
    print(f"   Created claim #{claim_id} with link_id=plink_test_789")
    
    # Look it up
    claim = get_payment_by_link_id("plink_test_789")
    if claim:
        print(f"   [OK] Webhook lookup works: claim #{claim['id']}")
    else:
        print("   [FAIL] Webhook lookup failed!")
        return
    
    # Mock bot and deliver leads
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    
    await _deliver_leads(mock_bot, claim)
    
    send_calls = mock_bot.send_message.call_args_list
    if send_calls:
        lead_msg = send_calls[0][1]['text']
        if "Payment Received" in lead_msg:
            print("   [OK] Leads delivered with payment confirmation")
        else:
            print(f"   [WARN] Message: {lead_msg[:80]}")
    else:
        print("   [FAIL] No message sent to user")
    
    # -- Test 3: Signature Verification --
    print("\n3. Testing Webhook Signature Verification...")
    
    test_body = b'{"event": "payment_link.paid"}'
    test_secret = "test_webhook_secret"
    
    expected_sig = hmac.new(
        test_secret.encode('utf-8'),
        test_body,
        hashlib.sha256
    ).hexdigest()
    
    # Temporarily set webhook secret
    original_secret = bot.RAZORPAY_WEBHOOK_SECRET
    bot.RAZORPAY_WEBHOOK_SECRET = test_secret
    
    if _verify_webhook_signature(test_body, expected_sig):
        print("   [OK] Valid signature accepted")
    else:
        print("   [FAIL] Valid signature rejected!")
    
    if not _verify_webhook_signature(test_body, "invalid_signature"):
        print("   [OK] Invalid signature rejected")
    else:
        print("   [FAIL] Invalid signature accepted!")
    
    bot.RAZORPAY_WEBHOOK_SECRET = original_secret
    
    print("\n" + "=" * 50)
    print("  ALL TESTS COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_razorpay_test())

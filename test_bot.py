"""Test script to verify the classifier and matcher with sample messages."""

import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from classifier import classifier
from database import init_db, add_listing, save_lead_request, get_lead_request, get_leads_for_request
from matcher import find_matches, format_free_leads, format_paid_leads, format_upsell_message, build_label

# Initialize DB
init_db()
print("[OK] Database initialized\n")

# Test messages
test_messages = [
    # Property offers
    ("Selling my 2BHK flat in Tower B, 75 lakhs. Contact 9876543210", "offer", "property"),
    ("3BHK available for rent, 25k/month. Call 9123456789", "offer", "property"),
    
    # Property queries
    ("Looking for 2BHK to buy, any leads?", "query", "property"),
    ("Flat chahiye rent pe, 2bhk prefer", "query", "property"),
    
    # Maid offers
    ("Maid available for morning work, very experienced. 9988776655", "offer", "maid"),
    ("Cook available part time, contact 9111122223", "offer", "maid"),
    
    # Maid queries
    ("Need maid urgently for full time work", "query", "maid"),
    ("Koi maid hai kya? Subah ka kaam hai", "query", "maid"),
    
    # Plumber queries
    ("Bathroom mein tap leak ho raha hai, plumber chahiye", "query", "plumber"),
    ("Need plumber urgently, water problem", "query", "plumber"),
    
    # Electrician
    ("Electrician chahiye, fan not working", "query", "electrician"),
    ("Electrician available for all work. 9888877776", "offer", "electrician"),
    
    # Furniture
    ("Selling old sofa set, good condition. 9777766665", "offer", "furniture"),
    ("Anyone selling used fridge?", "query", "furniture"),
    
    # General messages (should be ignored)
    ("Good morning everyone!", None, None),
    ("Happy birthday dear!", None, None),
    ("Thanks for sharing", None, None),
    ("Ok noted", None, None),
]

print("[TEST] Testing Message Classification:\n")
print("-" * 80)

passed = 0
failed = 0

for message, expected_type, expected_category in test_messages:
    result = classifier.classify(message)
    
    if expected_type is None:
        # Should be ignored
        if result is None:
            status = "[PASS]"
            passed += 1
        else:
            status = f"[FAIL] (expected ignore, got {result})"
            failed += 1
    else:
        if result and result["listing_type"] == expected_type and result["category"] == expected_category:
            status = "[PASS]"
            passed += 1
        else:
            status = f"[FAIL] (expected {expected_type}/{expected_category}, got {result})"
            failed += 1
    
    print(f"{status}")
    print(f"   Message: {message[:50]}...")
    if result:
        print(f"   Result: {result}")
    print()

print("-" * 80)
print(f"\n[STATS] Results: {passed} passed, {failed} failed out of {len(test_messages)} tests")

# Test the full flow
print("\n\n[FLOW] Testing Full Flow:")
print("-" * 80)

# Add some sample listings across different "groups"
sample_listings = [
    (1001, "user1", "User One", -100001, "property", "2bhk", "rent", "2BHK Tower A for rent, 17k/month, family preferred", "9876543210"),
    (1002, "user2", "User Two", -100002, "property", "2bhk", "rent", "2BHK available Tower C, 15k negotiable, bachelor ok", "9111122223"),
    (1003, "user3", "User Three", -100001, "property", "2bhk", "rent", "Spacious 2BHK, 18k, family only, newly painted", "9444455556"),
    (1004, "user4", "User Four", -100003, "maid", "maid", None, "Experienced maid available for morning work", "9444455556"),
    (1005, "user5", "User Five", -100001, "plumber", None, None, "Plumber available, 10 years experience", "9777788889"),
    (1006, "user6", "User Six", -100002, "property", "2bhk", "rent", "2BHK for rent, 16k, ground floor, family preferred", "9666677778"),
]

for user_id, username, first_name, chat_id, category, subcategory, prop_type, message, contact in sample_listings:
    add_listing(
        user_id=user_id,
        username=username,
        first_name=first_name,
        message_id=1,
        chat_id=chat_id,
        category=category,
        subcategory=subcategory,
        listing_type="offer",
        contact=contact,
        message=message,
        property_type=prop_type
    )
    print(f"[OK] Added listing (group {chat_id}): {category} - {message[:40]}...")

# Test query matching (cross-group)
print("\n[QUERY] Testing Cross-Group Matching:")
print("-" * 80)

queries = [
    ("Looking for 2BHK", "property", "2bhk"),
    ("Need maid", "maid", None),
    ("Plumber chahiye", "plumber", None),
]

for query, category, subcategory in queries:
    print(f"\n[SEARCH] Query: {query}")
    response = find_matches(category, subcategory)
    if response:
        print(response)
        # Verify no WhatsApp in response
        if "whatsapp" in response.lower() or "wa.me" in response.lower():
            print("[FAIL] Response contains WhatsApp reference!")
        else:
            print("[PASS] No WhatsApp references")
    else:
        print("No matches found")

# Test lead request flow
print("\n\n[LEAD] Testing Lead Request Flow:")
print("-" * 80)

req_id = save_lead_request(
    user_id=9999,
    category="property",
    subcategory="2bhk",
    property_type="rent",
    source_chat_id=-100001
)
print(f"[OK] Saved lead request #{req_id}")

req = get_lead_request(req_id)
print(f"[OK] Retrieved lead request: category={req['category']}, sub={req['subcategory']}")

# Get free leads
free = get_leads_for_request(req_id, limit=2, offset=0)
print(f"[OK] Free leads: {len(free)} contacts")

label = build_label("property", "2bhk", "rent", None)
free_msg = format_free_leads(free, label)
print(f"\n--- Free Leads Message ---")
print(free_msg)

# Get paid leads (skip free)
paid = get_leads_for_request(req_id, limit=5, offset=2)
print(f"\n[OK] Paid leads (after free): {len(paid)} contacts")

if paid:
    paid_msg = format_paid_leads(paid, label, include_tips=True)
    print(f"\n--- Paid Leads Message ---")
    print(paid_msg)

# Test upsell message
upsell = format_upsell_message(6)
print(f"\n--- Upsell Message ---")
print(upsell)

print("\n[DONE] All tests completed!")

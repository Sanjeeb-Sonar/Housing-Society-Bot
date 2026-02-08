"""Test script to verify the classifier with sample messages."""

import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from classifier import classifier
from database import init_db, add_listing, get_matching_listings
from matcher import find_matches

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

# Add some sample listings
sample_listings = [
    (1001, "user1", "User One", "property", "2bhk", "Selling 2BHK in Tower A, 60L", "9876543210"),
    (1002, "user2", "User Two", "property", "2bhk", "2BHK available, Tower C, 55L negotiable", "9111122223"),
    (1003, "user3", "User Three", "maid", "maid", "Experienced maid available for morning work", "9444455556"),
    (1004, "user4", "User Four", "plumber", None, "Plumber available, 10 years experience", "9777788889"),
]

for user_id, username, first_name, category, subcategory, message, contact in sample_listings:
    add_listing(
        user_id=user_id,
        username=username,
        first_name=first_name,
        message_id=1,
        chat_id=-1001234567890,
        category=category,
        subcategory=subcategory,
        listing_type="offer",
        contact=contact,
        message=message
    )
    print(f"[OK] Added listing: {category} - {message[:30]}...")

# Test query matching
print("\n[QUERY] Testing Query Matching:")
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
        # Strip emoji for console output
        response_clean = response.replace("🏠", "[P]").replace("🧹", "[M]").replace("🔧", "[L]")
        response_clean = response_clean.replace("📞", "Phone:").replace("💡", "Tip:")
        print(response_clean[:500] + "..." if len(response_clean) > 500 else response_clean)
    else:
        print("No matches found")

print("\n[DONE] All tests completed!")

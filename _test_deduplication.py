"""
Test script to verify Lead Deduplication logic.
"""
import database
import time

def test_deduplication():
    print("0. Initializing DB...")
    database.init_db()
    
    # 1. Create a dummy lead request
    # 'query' type -> looks for 'offer'
    request_id = database.save_lead_request(
        user_id=999, 
        category="TestCat", 
        listing_type="query"
    )
    print(f"   [OK] Created Request #{request_id}")
    
    # 2. Add DUPLICATE listings (Same user, same contact)
    # Listing 1
    database.add_listing(
        user_id=101, username="seller1", first_name="Seller", message_id=1, chat_id=1,
        category="TestCat", subcategory=None, listing_type="offer", 
        contact="9876543210", message="Offer 1"
    )
    time.sleep(1) # Ensure timestamp diff
    
    # Listing 2 (Same User, Same Contact)
    database.add_listing(
        user_id=101, username="seller1", first_name="Seller", message_id=2, chat_id=1,
        category="TestCat", subcategory=None, listing_type="offer", 
        contact="9876543210", message="Offer 2 (Duplicate)"
    )
    time.sleep(1)
    
    # Listing 3 (Different User, Same Contact - e.g. broker using 2 accounts)
    database.add_listing(
        user_id=102, username="seller2", first_name="Seller2", message_id=3, chat_id=1,
        category="TestCat", subcategory=None, listing_type="offer", 
        contact="9876543210", message="Offer 3 (Same Contact)"
    )
    
    # Listing 4 (Unique)
    database.add_listing(
        user_id=103, username="seller3", first_name="Seller3", message_id=4, chat_id=1,
        category="TestCat", subcategory=None, listing_type="offer", 
        contact="1122334455", message="Offer 4 (Unique)"
    )
    
    print("   [OK] Added 4 listings (3 share same contact/user)")
    
    # 3. Fetch leads
    leads = database.get_leads_for_request(request_id, limit=10)
    
    print(f"\n   Found {len(leads)} leads:")
    for l in leads:
        print(f"   - {l['contact']} (User: {l['user_id']}) - {l['message']}")
        
    # Validation
    # Should get exactly 2 leads: 
    # 1. One instance of 9876543210 (most recent)
    # 2. One instance of 1122334455
    
    contacts = [l['contact'] for l in leads]
    unique_contacts = set(contacts)
    
    if len(leads) == 2 and len(unique_contacts) == 2:
        print("\n✅ PASS: Deduplication working! Only unique contacts returned.")
    else:
        print(f"\n❌ FAIL: Expected 2 unique leads, got {len(leads)}.")

if __name__ == "__main__":
    test_deduplication()

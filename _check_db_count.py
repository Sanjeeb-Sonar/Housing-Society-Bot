from database import get_connection
conn = get_connection()
cursor = conn.cursor()
try:
    cursor.execute("SELECT COUNT(*) as count FROM listings")
    total = cursor.fetchone()['count']
    print(f"Total listings in DB: {total}")
    
    cursor.execute("SELECT * FROM listings ORDER BY created_at DESC LIMIT 5")
    rows = cursor.fetchall()
    print(f"Last 5 listings:")
    for row in rows:
        print(f"- [{row['created_at']}] {row['category']} ({row['listing_type']}): {row['message'][:30]}...")
except Exception as e:
    print(f"Error: {e}")
conn.close()

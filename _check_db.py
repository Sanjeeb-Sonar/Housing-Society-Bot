import sqlite3

conn = sqlite3.connect("housing_bot.db")
c = conn.cursor()

# Get column names
c.execute("PRAGMA table_info(listings)")
columns = [col[1] for col in c.fetchall()]
print("Columns:", columns)
print("-" * 120)

# Show top 10 records
c.execute("SELECT * FROM listings LIMIT 10")
rows = c.fetchall()
for i, row in enumerate(rows, 1):
    print(f"\n--- Record {i} ---")
    for col, val in zip(columns, row):
        print(f"  {col}: {val}")

conn.close()

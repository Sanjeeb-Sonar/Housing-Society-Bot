"""SQLite database operations for storing and retrieving listings."""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional
from config import DATABASE_PATH, LISTING_EXPIRY_DAYS


def get_connection():
    """Get database connection with row factory."""
    # Auto-create directory if it doesn't exist
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
        except PermissionError:
            # On some environments (like Render), we might not have permission 
            # to create root-level folders. We'll proceed and let sqlite3.connect 
            # fail if the path is truly invalid.
            pass
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            message_id INTEGER,
            chat_id INTEGER,
            category TEXT NOT NULL,
            subcategory TEXT,
            listing_type TEXT NOT NULL,
            contact TEXT,
            message TEXT NOT NULL,
            property_type TEXT,
            gender_preference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    # Lead requests table — tracks what users searched for (used in deep links)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            property_type TEXT,
            gender_preference TEXT,
            listing_type TEXT DEFAULT 'query',
            source_chat_id INTEGER,
            free_leads_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Payment Claims table — tracks Razorpay payments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            request_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            tier TEXT DEFAULT 't1',
            razorpay_link_id TEXT,
            razorpay_payment_id TEXT,
            status TEXT DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES lead_requests(id)
        )
    """)
    
    # Add new columns to existing tables (for migration)
    try:
        cursor.execute("ALTER TABLE listings ADD COLUMN property_type TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE listings ADD COLUMN gender_preference TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE lead_requests ADD COLUMN listing_type TEXT DEFAULT 'query'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE lead_requests ADD COLUMN free_leads_sent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Razorpay migration columns
    try:
        cursor.execute("ALTER TABLE payment_claims ADD COLUMN tier TEXT DEFAULT 't1'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE payment_claims ADD COLUMN razorpay_link_id TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE payment_claims ADD COLUMN razorpay_payment_id TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON listings(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_listing_type ON listings(listing_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON listings(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON listings(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_type ON listings(property_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gender_preference ON listings(gender_preference)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_req_user ON lead_requests(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_razorpay_link ON payment_claims(razorpay_link_id)")
    
    conn.commit()
    conn.close()


def add_listing(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    message_id: int,
    chat_id: int,
    category: str,
    subcategory: Optional[str],
    listing_type: str,
    contact: Optional[str],
    message: str,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None
) -> int:
    """Add a new listing to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=LISTING_EXPIRY_DAYS)
    
    cursor.execute("""
        INSERT INTO listings 
        (user_id, username, first_name, message_id, chat_id, category, 
         subcategory, listing_type, contact, message, property_type, 
         gender_preference, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, first_name, message_id, chat_id, category,
          subcategory, listing_type, contact, message, property_type,
          gender_preference, expires_at))
    
    listing_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return listing_id


# ─── Lead Requests ────────────────────────────────────────────


def save_lead_request(
    user_id: int,
    category: str,
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None,
    listing_type: str = "query",
    source_chat_id: Optional[int] = None
) -> int:
    """Save a lead request and return its ID (used in deep link encoding)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO lead_requests 
        (user_id, category, subcategory, property_type, gender_preference, listing_type, source_chat_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, category, subcategory, property_type, gender_preference, listing_type, source_chat_id))
    
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return request_id


def get_lead_request(request_id: int) -> Optional[dict]:
    """Retrieve a lead request by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM lead_requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_leads_for_request(
    request_id: int,
    limit: int = 5,
    offset: int = 0
) -> list:
    """
    Fetch matching listings for a stored lead request.
    Cross-group: no chat_id filter — shows from all groups.
    If user posted a query → find offers. If user posted an offer → find queries.
    Uses offset to skip already-shown free leads.
    Refined: Groups by contact/user_id to prevent duplicates.
    """
    req = get_lead_request(request_id)
    if not req:
        return []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Show the OPPOSITE type: query → offers, offer → queries
    search_type = "offer" if req.get("listing_type", "query") == "query" else "query"
    
    query = """
        SELECT * FROM listings 
        WHERE category = ? 
        AND listing_type = ?
        AND expires_at > ?
        AND contact IS NOT NULL
        AND contact != ''
    """
    params = [req["category"], search_type, datetime.now()]
    
    if req["subcategory"]:
        query += " AND (subcategory LIKE ? OR message LIKE ?)"
        params.extend([f"%{req['subcategory']}%", f"%{req['subcategory']}%"])
    
    # Relaxed filters: match exact OR NULL (old listings without these fields)
    if req["property_type"]:
        query += " AND (property_type = ? OR property_type IS NULL)"
        params.append(req["property_type"])
    
    if req["gender_preference"]:
        query += " AND (gender_preference = ? OR gender_preference IS NULL)"
        params.append(req["gender_preference"])
    
    # Group by contact info (phone num) or user_id if phone is missing
    # to ensure we don't show the same person twice
    query += " GROUP BY COALESCE(contact, user_id)"
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]


# ─── Payments (Razorpay) ──────────────────────────────────────


def save_payment_claim(
    user_id: int,
    request_id: int,
    amount: int,
    tier: str,
    razorpay_link_id: str = ""
) -> int:
    """Save a new payment claim with Razorpay link ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO payment_claims (user_id, request_id, amount, tier, razorpay_link_id, status)
        VALUES (?, ?, ?, ?, ?, 'created')
    """, (user_id, request_id, amount, tier, razorpay_link_id))
    
    claim_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return claim_id


def get_payment_claim(claim_id: int) -> Optional[dict]:
    """Get payment claim details."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM payment_claims WHERE id = ?", (claim_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_payment_by_link_id(razorpay_link_id: str) -> Optional[dict]:
    """Look up a payment claim by Razorpay Payment Link ID (for webhook)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM payment_claims WHERE razorpay_link_id = ?", (razorpay_link_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def update_payment_status(claim_id: int, status: str, razorpay_payment_id: str = ""):
    """Update payment claim status and optionally store Razorpay payment ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if razorpay_payment_id:
        cursor.execute(
            "UPDATE payment_claims SET status = ?, razorpay_payment_id = ? WHERE id = ?", 
            (status, razorpay_payment_id, claim_id))
    else:
        cursor.execute(
            "UPDATE payment_claims SET status = ? WHERE id = ?", 
            (status, claim_id))
        
    conn.commit()
    conn.close()


# ─── Matching (existing, updated for cross-group) ────────────


def get_matching_listings(
    category: str,
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None,
    chat_id: Optional[int] = None,
    limit: int = 5
) -> list:
    """
    Get listings matching a query.
    Returns offers when someone is looking for something.
    Sorted by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clean up expired listings first
    cursor.execute("DELETE FROM listings WHERE expires_at < ?", (datetime.now(),))
    conn.commit()
    
    # Build dynamic query with filters — NO chat_id filter for cross-group
    query = """
        SELECT * FROM listings 
        WHERE category = ? 
        AND listing_type = 'offer'
        AND expires_at > ?
    """
    params = [category, datetime.now()]
    
    # Add subcategory filter if specified
    if subcategory:
        query += " AND (subcategory LIKE ? OR message LIKE ?)"
        params.extend([f"%{subcategory}%", f"%{subcategory}%"])
    
    # Add property_type filter if specified (exact match when specified)
    if property_type:
        query += " AND property_type = ?"
        params.append(property_type)
    
    # Add gender_preference filter if specified (exact match when specified)
    if gender_preference:
        query += " AND gender_preference = ?"
        params.append(gender_preference)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]


def get_matching_queries(
    category: str,
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None,
    chat_id: Optional[int] = None,
    limit: int = 5
) -> list:
    """
    Get queries (buyers) matching an offer.
    Returns people who are looking for something.
    Sorted by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build dynamic query — NO chat_id filter for cross-group
    query = """
        SELECT * FROM listings 
        WHERE category = ? 
        AND listing_type = 'query'
        AND expires_at > ?
    """
    params = [category, datetime.now()]
    
    # Add subcategory filter if specified
    if subcategory:
        query += " AND (subcategory LIKE ? OR message LIKE ?)"
        params.extend([f"%{subcategory}%", f"%{subcategory}%"])
    
    # Add property_type filter if specified (exact match)
    if property_type:
        query += " AND property_type = ?"
        params.append(property_type)
    
    # Add gender_preference filter if specified (exact match)
    if gender_preference:
        query += " AND gender_preference = ?"
        params.append(gender_preference)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]


def get_recent_listings(category: Optional[str] = None, limit: int = 10) -> list:
    """Get recent listings, optionally filtered by category."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if category:
        cursor.execute("""
            SELECT * FROM listings 
            WHERE category = ? AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (category, datetime.now(), limit))
    else:
        cursor.execute("""
            SELECT * FROM listings 
            WHERE expires_at > ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (datetime.now(), limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]



def get_match_stats(
    category: str,
    listing_type: str = "offer",
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None,
    chat_id: Optional[int] = None,
) -> dict:
    """
    Get aggregate stats for matching listings/queries.
    Returns total count and count from last 7 days.
    Cross-group: no chat_id filter.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Base query — NO chat_id filter for cross-group
    query = """
        SELECT COUNT(*) as total FROM listings
        WHERE category = ?
        AND listing_type = ?
        AND expires_at > ?
    """
    params = [category, listing_type, datetime.now()]

    # Filters
    if subcategory:
        query += " AND (subcategory LIKE ? OR message LIKE ?)"
        params.extend([f"%{subcategory}%", f"%{subcategory}%"])
    if property_type:
        query += " AND property_type = ?"
        params.append(property_type)
    if gender_preference:
        query += " AND gender_preference = ?"
        params.append(gender_preference)

    cursor.execute(query, params)
    total = cursor.fetchone()["total"]

    # Count from last 7 days
    recent_query = query + " AND created_at > ?"
    recent_params = params + [datetime.now() - timedelta(days=7)]
    cursor.execute(recent_query, recent_params)
    recent = cursor.fetchone()["total"]

    conn.close()
    return {"total": total, "recent_7d": recent}


def get_stats() -> dict:
    """Get statistics about listings."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM listings 
        WHERE expires_at > ?
        GROUP BY category
    """, (datetime.now(),))
    
    by_category = {row['category']: row['count'] for row in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) as total FROM listings WHERE expires_at > ?", 
                   (datetime.now(),))
    total = cursor.fetchone()['total']
    
    conn.close()
    
    return {"total": total, "by_category": by_category}


def cleanup_expired():
    """Remove expired listings."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM listings WHERE expires_at < ?", (datetime.now(),))
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted

"""SQLite database operations for storing and retrieving listings."""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from config import DATABASE_PATH, LISTING_EXPIRY_DAYS


def get_connection():
    """Get database connection with row factory."""
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
    
    # Add new columns to existing tables (for migration)
    try:
        cursor.execute("ALTER TABLE listings ADD COLUMN property_type TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE listings ADD COLUMN gender_preference TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON listings(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_listing_type ON listings(listing_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON listings(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON listings(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_type ON listings(property_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gender_preference ON listings(gender_preference)")
    
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


def get_matching_listings(
    category: str,
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None,
    limit: int = 5
) -> list:
    """
    Get listings matching a query.
    Returns offers when someone is looking for something.
    Filters by property_type (sale/rent) and gender_preference (male/female) when specified.
    Sorted by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clean up expired listings first
    cursor.execute("DELETE FROM listings WHERE expires_at < ?", (datetime.now(),))
    conn.commit()
    
    # Build dynamic query with filters
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
    limit: int = 5
) -> list:
    """
    Get queries (buyers) matching an offer.
    Returns people who are looking for something.
    Filters by property_type (sale/rent) and gender_preference (male/female) when specified.
    Sorted by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build dynamic query with filters
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

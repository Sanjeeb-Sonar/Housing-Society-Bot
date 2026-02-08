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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON listings(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_listing_type ON listings(listing_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON listings(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON listings(created_at)")
    
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
    message: str
) -> int:
    """Add a new listing to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=LISTING_EXPIRY_DAYS)
    
    cursor.execute("""
        INSERT INTO listings 
        (user_id, username, first_name, message_id, chat_id, category, 
         subcategory, listing_type, contact, message, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, first_name, message_id, chat_id, category,
          subcategory, listing_type, contact, message, expires_at))
    
    listing_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return listing_id


def get_matching_listings(
    category: str,
    subcategory: Optional[str] = None,
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
    
    # Search for offers in the category
    if subcategory:
        cursor.execute("""
            SELECT * FROM listings 
            WHERE category = ? 
            AND listing_type = 'offer'
            AND (subcategory LIKE ? OR message LIKE ?)
            AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (category, f"%{subcategory}%", f"%{subcategory}%", datetime.now(), limit))
    else:
        cursor.execute("""
            SELECT * FROM listings 
            WHERE category = ? 
            AND listing_type = 'offer'
            AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (category, datetime.now(), limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]


def get_matching_queries(
    category: str,
    subcategory: Optional[str] = None,
    limit: int = 5
) -> list:
    """
    Get queries (buyers) matching an offer.
    Returns people who are looking for something.
    Sorted by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Search for queries in the category
    if subcategory:
        cursor.execute("""
            SELECT * FROM listings 
            WHERE category = ? 
            AND listing_type = 'query'
            AND (subcategory LIKE ? OR message LIKE ?)
            AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (category, f"%{subcategory}%", f"%{subcategory}%", datetime.now(), limit))
    else:
        cursor.execute("""
            SELECT * FROM listings 
            WHERE category = ? 
            AND listing_type = 'query'
            AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (category, datetime.now(), limit))
    
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

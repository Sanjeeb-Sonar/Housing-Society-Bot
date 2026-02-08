"""Query matcher to find relevant listings for queries."""

from datetime import datetime
from typing import Optional
from database import get_matching_listings, get_matching_queries
from keywords import CATEGORIES
from config import MAX_RESULTS


def format_listing_response(listings: list, category: str, subcategory: Optional[str]) -> str:
    """Format listings into a clean, creative response."""
    if not listings:
        return None
    
    category_data = CATEGORIES.get(category, {})
    emoji = category_data.get("emoji", "📋")
    
    label = subcategory or category
    count = len(listings)
    
    # Creative header based on category
    header = f"{emoji} **{count} {label}** available:\n\n"
    
    # Build clean bullet entries
    entries = []
    for listing in listings:
        username = listing.get("username") or listing.get("first_name") or "Anon"
        contact = listing.get("contact")
        message = listing["message"]
        
        # Extract key info from message (truncate to 50 chars)
        if len(message) > 50:
            message = message[:47] + "..."
        
        # Bullet format: • @user (📞contact) - "info"
        if contact:
            entry = f"• **@{username}** ({contact}) - _{message}_"
        else:
            entry = f"• **@{username}** - _{message}_"
        entries.append(entry)
    
    return header + "\n".join(entries)


def format_buyers_response(buyers: list, category: str, subcategory: Optional[str]) -> str:
    """Format interested buyers into a clean response."""
    if not buyers:
        return None
    
    label = subcategory or category
    count = len(buyers)
    
    header = f"🔔 **{count} people** looking for **{label}**:\n\n"
    
    entries = []
    for buyer in buyers:
        username = buyer.get("username") or buyer.get("first_name") or "Anon"
        contact = buyer.get("contact")
        message = buyer["message"]
        
        if len(message) > 50:
            message = message[:47] + "..."
        
        if contact:
            entry = f"• **@{username}** ({contact}) - _{message}_"
        else:
            entry = f"• **@{username}** - _{message}_"
        entries.append(entry)
    
    return header + "\n".join(entries)


def find_matches(category: str, subcategory: Optional[str] = None) -> Optional[str]:
    """Find matching listings for a query. Returns None if no matches."""
    listings = get_matching_listings(
        category=category,
        subcategory=subcategory,
        limit=MAX_RESULTS
    )
    
    if not listings:
        return None
    
    return format_listing_response(listings, category, subcategory)


def find_interested_buyers(category: str, subcategory: Optional[str] = None) -> Optional[str]:
    """Find people looking for something in this category."""
    buyers = get_matching_queries(
        category=category,
        subcategory=subcategory,
        limit=MAX_RESULTS
    )
    
    if not buyers:
        return None
    
    return format_buyers_response(buyers, category, subcategory)

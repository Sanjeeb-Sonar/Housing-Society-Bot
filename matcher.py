"""Query matcher to find relevant listings for queries."""

from datetime import datetime
from typing import Optional
from database import get_matching_listings, get_matching_queries
from keywords import CATEGORIES
from config import MAX_RESULTS


def format_time_ago(created_at: str) -> str:
    """Format time difference in human-readable format."""
    if isinstance(created_at, str):
        created = datetime.fromisoformat(created_at)
    else:
        created = created_at
    
    now = datetime.now()
    diff = now - created
    
    if diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"


def format_listing_response(listings: list, category: str, subcategory: Optional[str]) -> str:
    """Format listings into a brief response message."""
    if not listings:
        return None
    
    category_data = CATEGORIES.get(category, {})
    emoji = category_data.get("emoji", "📋")
    
    # Build header
    label = subcategory or category
    header = f"{emoji} **{len(listings)} result(s) for {label}:**\n\n"
    
    # Build compact listing entries
    entries = []
    for i, listing in enumerate(listings, 1):
        username = listing.get("username") or listing.get("first_name") or "Anon"
        contact = listing.get("contact") or ""
        message = listing["message"]
        
        # Truncate message to 80 chars
        if len(message) > 80:
            message = message[:77] + "..."
        
        # Single line format: 1. @user - "message" 📞 contact
        entry = f"{i}. @{username} - \"{message}\""
        if contact:
            entry += f" 📞{contact}"
        entries.append(entry)
    
    return header + "\n".join(entries)


def format_buyers_response(buyers: list, category: str, subcategory: Optional[str]) -> str:
    """Format interested buyers into a brief response message."""
    if not buyers:
        return None
    
    label = subcategory or category
    header = f"🔔 **{len(buyers)} interested buyer(s) for {label}:**\n\n"
    
    # Build compact entries
    entries = []
    for i, buyer in enumerate(buyers, 1):
        username = buyer.get("username") or buyer.get("first_name") or "Anon"
        contact = buyer.get("contact") or ""
        message = buyer["message"]
        
        # Truncate message to 80 chars
        if len(message) > 80:
            message = message[:77] + "..."
        
        # Single line format
        entry = f"{i}. @{username} - \"{message}\""
        if contact:
            entry += f" 📞{contact}"
        entries.append(entry)
    
    footer = "\n\n✅ Your listing saved!"
    
    return header + "\n".join(entries) + footer


def find_matches(category: str, subcategory: Optional[str] = None) -> Optional[str]:
    """
    Find matching listings for a query and return formatted response.
    Returns None if no matches found.
    """
    listings = get_matching_listings(
        category=category,
        subcategory=subcategory,
        limit=MAX_RESULTS
    )
    
    if not listings:
        return None
    
    return format_listing_response(listings, category, subcategory)


def find_interested_buyers(category: str, subcategory: Optional[str] = None) -> Optional[str]:
    """
    Find people who are looking for something in this category.
    Returns formatted response for sellers.
    """
    buyers = get_matching_queries(
        category=category,
        subcategory=subcategory,
        limit=MAX_RESULTS
    )
    
    if not buyers:
        return None
    
    return format_buyers_response(buyers, category, subcategory)


def get_no_results_message(category: str, subcategory: Optional[str] = None) -> str:
    """Get a helpful message when no results are found."""
    category_data = CATEGORIES.get(category, {})
    emoji = category_data.get("emoji", "📋")
    
    if subcategory:
        return (
            f"{emoji} No current listings found for **{subcategory}** ({category}).\n\n"
            "_New listings are constantly being added. "
            "Your query has been noted - check back later!_"
        )
    else:
        return (
            f"{emoji} No current listings found for **{category}**.\n\n"
            "_New listings are constantly being added. "
            "Your query has been noted - check back later!_"
        )


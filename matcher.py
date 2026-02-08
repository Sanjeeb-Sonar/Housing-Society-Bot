"""Query matcher to find relevant listings for queries."""

from datetime import datetime
from typing import Optional
from database import get_matching_listings, get_matching_queries
from keywords import CATEGORIES
from config import MAX_RESULTS


def deduplicate_by_user(listings: list) -> list:
    """Remove duplicate entries from same user, keep most recent."""
    seen_users = set()
    unique = []
    
    for listing in listings:
        user_id = listing.get("user_id") or listing.get("username") or listing.get("first_name")
        if user_id not in seen_users:
            seen_users.add(user_id)
            unique.append(listing)
    
    return unique


def extract_property_source(message: str) -> Optional[str]:
    """Detect if property is from owner or broker."""
    msg_lower = message.lower()
    
    owner_keywords = ["owner", "no broker", "no brokerage", "malik", "direct"]
    broker_keywords = ["broker", "agent", "dealer", "brokerage", "dalal"]
    
    for kw in owner_keywords:
        if kw in msg_lower:
            return "👤Owner"
    
    for kw in broker_keywords:
        if kw in msg_lower:
            return "🏢Broker"
    
    return None


def extract_gender_preference(message: str) -> Optional[str]:
    """Detect gender preference for roommate/flatmate."""
    msg_lower = message.lower()
    
    male_kw = ["male", "boys", "gents", "men", "ladka", "ladke", "bachelor"]
    female_kw = ["female", "girls", "ladies", "women", "ladki", "ladkiyan"]
    
    for kw in female_kw:
        if kw in msg_lower:
            return "👩Female"
    
    for kw in male_kw:
        if kw in msg_lower:
            return "👨Male"
    
    return None


def format_listing_response(listings: list, category: str, subcategory: Optional[str]) -> str:
    """Format listings into a clean, creative response with metadata tags."""
    if not listings:
        return None
    
    # Remove duplicate users
    listings = deduplicate_by_user(listings)
    
    if not listings:
        return None
    
    category_data = CATEGORIES.get(category, {})
    emoji = category_data.get("emoji", "📋")
    
    label = subcategory or category
    count = len(listings)
    
    header = f"{emoji} **{count} {label}** available:\n\n"
    
    entries = []
    for listing in listings:
        username = listing.get("username") or listing.get("first_name") or "Anon"
        contact = listing.get("contact")
        message = listing["message"]
        original_message = message  # Keep original for tag extraction
        
        # Extract tags
        tags = []
        if category == "property":
            source = extract_property_source(original_message)
            if source:
                tags.append(source)
        
        if "roommate" in original_message.lower() or "flatmate" in original_message.lower():
            gender = extract_gender_preference(original_message)
            if gender:
                tags.append(gender)
        
        # Truncate message
        if len(message) > 50:
            message = message[:47] + "..."
        
        # Build entry with tags
        tag_str = " ".join(tags)
        if contact:
            entry = f"• **@{username}** ({contact})"
        else:
            entry = f"• **@{username}**"
        
        if tag_str:
            entry += f" [{tag_str}]"
        
        entry += f" - _{message}_"
        entries.append(entry)
    
    return header + "\n".join(entries)


def format_buyers_response(buyers: list, category: str, subcategory: Optional[str]) -> str:
    """Format interested buyers into a clean response with metadata tags."""
    if not buyers:
        return None
    
    # Remove duplicate users
    buyers = deduplicate_by_user(buyers)
    
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
        original_message = message
        
        # Extract tags
        tags = []
        if "roommate" in original_message.lower() or "flatmate" in original_message.lower():
            gender = extract_gender_preference(original_message)
            if gender:
                tags.append(gender)
        
        if len(message) > 50:
            message = message[:47] + "..."
        
        # Build entry
        tag_str = " ".join(tags)
        if contact:
            entry = f"• **@{username}** ({contact})"
        else:
            entry = f"• **@{username}**"
        
        if tag_str:
            entry += f" [{tag_str}]"
        
        entry += f" - _{message}_"
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

"""Query matcher to find relevant listings for queries with LLM-based summarization."""

from datetime import datetime
from typing import Optional
from database import get_matching_listings, get_matching_queries
from config import MAX_RESULTS

# Import LLM for summarization
try:
    from llm_classifier import llm_classifier
except ImportError:
    llm_classifier = None


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


def get_property_type_label(property_type: Optional[str]) -> Optional[str]:
    """Get display label for property type."""
    if property_type == "sale":
        return "🏷️Sale"
    elif property_type == "rent":
        return "🔑Rent"
    return None


def get_gender_label(gender: Optional[str]) -> Optional[str]:
    """Get display label for gender preference."""
    if gender == "female":
        return "👩Female"
    elif gender == "male":
        return "👨Male"
    return None


def summarize_message(message: str) -> str:
    """Summarize a message using LLM, with fallback."""
    if llm_classifier and llm_classifier.client:
        return llm_classifier.summarize_description(message)
    else:
        # Fallback: return first 100 chars
        if len(message) > 100:
            return message[:97] + "..."
        return message


def format_listing_response(listings: list, category: str, subcategory: Optional[str]) -> str:
    """Format listings into a clean, creative response with metadata tags and summarized descriptions."""
    if not listings:
        return None
    
    # Remove duplicate users
    listings = deduplicate_by_user(listings)
    
    if not listings:
        return None
    
    # Get category emoji
    category_emojis = {
        "property": "🏠",
        "furniture": "🪑",
        "maid": "🧹",
        "plumber": "🔧",
        "electrician": "💡",
        "carpenter": "🪚",
        "driver": "🚗",
        "ac_repair": "❄️",
        "tutor": "📚",
        "packers_movers": "📦",
        "vehicle": "🚙",
        "pest_control": "🐜",
        "painter": "🎨",
        "security_guard": "🛡️"
    }
    emoji = category_emojis.get(category, "📋")
    
    label = subcategory or category
    count = len(listings)
    
    header = f"{emoji} **{count} {label}** available:\n\n"
    
    entries = []
    for listing in listings:
        # Only use @ prefix for actual Telegram usernames, not first_name
        tg_username = listing.get("username")
        display_name = listing.get("first_name") or "Anon"
        contact = listing.get("contact")
        message = listing["message"]
        
        # Build tags from metadata
        tags = []
        
        # Property type tag (sale/rent)
        prop_type = listing.get("property_type")
        if prop_type:
            label_tag = get_property_type_label(prop_type)
            if label_tag:
                tags.append(label_tag)
        
        # Gender preference tag
        gender = listing.get("gender_preference")
        if gender:
            label_tag = get_gender_label(gender)
            if label_tag:
                tags.append(label_tag)
        
        # Get summarized description
        summary = summarize_message(message)
        
        # Build entry - use @username if available, otherwise just display name
        tag_str = " ".join(tags)
        if tg_username:
            name_part = f"**@{tg_username}**"
        else:
            name_part = f"**{display_name}**"
        
        if contact:
            entry = f"• {name_part} ({contact})"
        else:
            entry = f"• {name_part}"
        
        if tag_str:
            entry += f" [{tag_str}]"
        
        entry += f" - _{summary}_"
        entries.append(entry)
    
    return header + "\n".join(entries)


def format_buyers_response(buyers: list, category: str, subcategory: Optional[str]) -> str:
    """Format interested buyers into a clean response with summarized descriptions."""
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
        # Only use @ prefix for actual Telegram usernames, not first_name
        tg_username = buyer.get("username")
        display_name = buyer.get("first_name") or "Anon"
        contact = buyer.get("contact")
        message = buyer["message"]
        
        # Build tags
        tags = []
        
        # Property type preference
        prop_type = buyer.get("property_type")
        if prop_type:
            label_tag = get_property_type_label(prop_type)
            if label_tag:
                tags.append(label_tag)
        
        # Gender preference
        gender = buyer.get("gender_preference")
        if gender:
            label_tag = get_gender_label(gender)
            if label_tag:
                tags.append(label_tag)
        
        # Get summarized description
        summary = summarize_message(message)
        
        # Build entry - use @username if available, otherwise just display name
        tag_str = " ".join(tags)
        if tg_username:
            name_part = f"**@{tg_username}**"
        else:
            name_part = f"**{display_name}**"
        
        if contact:
            entry = f"• {name_part} ({contact})"
        else:
            entry = f"• {name_part}"
        
        if tag_str:
            entry += f" [{tag_str}]"
        
        entry += f" - _{summary}_"
        entries.append(entry)
    
    return header + "\n".join(entries)


def find_matches(
    category: str, 
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None
) -> Optional[str]:
    """
    Find matching listings for a query.
    Filters by property_type and gender_preference when specified.
    Returns None if no matches.
    """
    listings = get_matching_listings(
        category=category,
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference,
        limit=MAX_RESULTS
    )
    
    if not listings:
        return None
    
    return format_listing_response(listings, category, subcategory)


def find_interested_buyers(
    category: str, 
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None
) -> Optional[str]:
    """Find people looking for something in this category, filtered by type."""
    buyers = get_matching_queries(
        category=category,
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference,
        limit=MAX_RESULTS
    )
    
    if not buyers:
        return None
    
    return format_buyers_response(buyers, category, subcategory)

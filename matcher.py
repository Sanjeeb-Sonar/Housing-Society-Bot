"""
Query matcher with in-Telegram lead delivery.
Shows compelling hook in group → deep link to DM → free leads → paid upsell.
"""

from datetime import datetime
from typing import Optional
from database import get_matching_listings, get_matching_queries, get_match_stats
from config import MAX_RESULTS, FREE_LEADS_COUNT, TIER1_STARS, TIER1_LEADS, TIER2_STARS, TIER2_LEADS


# Category emojis
CATEGORY_EMOJIS = {
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


def get_property_type_label(property_type: Optional[str]) -> Optional[str]:
    """Get display label for property type."""
    if property_type == "sale":
        return "for sale"
    elif property_type == "rent":
        return "for rent"
    return None


def get_gender_label(gender: Optional[str]) -> Optional[str]:
    """Get display label for gender preference."""
    if gender == "female":
        return "female"
    elif gender == "male":
        return "male"
    return None


def build_label(category: str, subcategory: Optional[str], property_type: Optional[str], gender_preference: Optional[str]) -> str:
    """Build a human-readable label like '2bhk for rent' or 'female roommate'."""
    parts = []

    # Gender prefix for roommate-type listings
    gender_label = get_gender_label(gender_preference)
    if gender_label:
        parts.append(gender_label)

    # Main label (subcategory preferred over category)
    parts.append(subcategory or category)

    # Property type suffix
    prop_label = get_property_type_label(property_type)
    if prop_label:
        parts.append(prop_label)

    return " ".join(parts)


def _extract_short_detail(message: str) -> str:
    """Extract a short detail from listing message (first 60 chars)."""
    clean = message.strip().replace("\n", " ")
    if len(clean) > 60:
        return clean[:57] + "..."
    return clean


def _extract_rent_prices(listings: list) -> Optional[int]:
    """Try to extract average rent/price from listing messages."""
    import re
    prices = []
    for listing in listings:
        msg = listing.get("message", "")
        # Match patterns like 17k, 17000, 17,000, 25k etc.
        matches = re.findall(r'(\d{1,3})[,]?(\d{3})\b|\b(\d{1,2})[kK]\b', msg)
        for m in matches:
            if m[0] and m[1]:
                # Full number like 17000 or 17,000
                price = int(m[0] + m[1])
                if 2000 <= price <= 500000:
                    prices.append(price)
            elif m[2]:
                # Short like 17k
                price = int(m[2]) * 1000
                if 2000 <= price <= 500000:
                    prices.append(price)
    
    if prices:
        avg = sum(prices) // len(prices)
        if avg >= 1000:
            return avg // 1000  # Return in thousands (e.g., 17 for 17k)
    return None


def _detect_preference(listings: list) -> Optional[str]:
    """Detect common preferences from listings (family/bachelor etc)."""
    import re
    family_count = 0
    bachelor_count = 0
    for listing in listings:
        msg = listing.get("message", "").lower()
        if re.search(r'family|families', msg):
            family_count += 1
        if re.search(r'bachelor|bachelors|single', msg):
            bachelor_count += 1
    
    if family_count > bachelor_count and family_count > 0:
        return "family preferred"
    elif bachelor_count > family_count and bachelor_count > 0:
        return "bachelor friendly"
    return None


# ─── Group Hook Messages ─────────────────────────────────────


def format_hook_response_for_query(
    stats: dict,
    category: str,
    subcategory: Optional[str],
    property_type: Optional[str],
    gender_preference: Optional[str],
    listings_sample: list
) -> Optional[str]:
    """
    Format a hook message when someone is SEARCHING.
    Shows stats about available offers. Button is added by bot.py.
    """
    total = stats["total"]
    recent = stats["recent_7d"]

    if total == 0:
        return None

    emoji = CATEGORY_EMOJIS.get(category, "📋")
    label = build_label(category, subcategory, property_type, gender_preference)

    # Build compact hook with details
    detail_parts = []
    
    # Try to get avg price for property
    if category == "property" and listings_sample:
        avg_k = _extract_rent_prices(listings_sample)
        if avg_k:
            detail_parts.append(f"avg rent {avg_k}k")
    
    # Try to detect preference
    if listings_sample:
        pref = _detect_preference(listings_sample)
        if pref:
            detail_parts.append(pref)
    
    # Time context
    if recent > 0:
        detail_parts.append(f"in the last 7 days")
    
    detail_str = ". ".join(detail_parts)
    if detail_str:
        detail_str = f" {detail_str}"
    
    people = "person" if total == 1 else "people"
    line1 = f"{emoji} *Found {total} {people} offering {label}!*{detail_str}"
    line2 = f"🤖 Tap *\"🔍 Get Leads\"* to see the contacts instantly"
    
    return f"{line1}\n{line2}"


def format_hook_response_for_offer(
    stats: dict,
    category: str,
    subcategory: Optional[str],
    property_type: Optional[str],
    gender_preference: Optional[str],
    listings_sample: list
) -> Optional[str]:
    """
    Format a hook message when someone OFFERS something.
    Shows stats about people looking for this. Button is added by bot.py.
    """
    total = stats["total"]
    recent = stats["recent_7d"]

    if total == 0:
        return None

    emoji = CATEGORY_EMOJIS.get(category, "📋")
    label = build_label(category, subcategory, property_type, gender_preference)

    # Time context
    time_str = ""
    if recent > 0:
        time_str = f" {recent} searched in the last 7 days."
    
    people = "person is" if total == 1 else "people are"
    line1 = f"🔔 *{total} {people} actively looking for {label}!*{time_str}"
    line2 = f"🤖 Tap *\"🔍 Get Leads\"* to connect with buyers instantly"
    
    return f"{line1}\n{line2}"


# ─── DM Lead Formatters ──────────────────────────────────────


def format_free_leads(listings: list, label: str) -> str:
    """Format 2 free contact cards for DM."""
    if not listings:
        return "😔 No contacts available right now. Check back soon!"
    
    lines = [f"📋 *Here are {len(listings)} contacts for \"{label}\":*\n"]
    
    for i, listing in enumerate(listings, 1):
        # Name
        username = listing.get("username")
        first_name = listing.get("first_name") or "Someone"
        name_str = f"@{username}" if username else first_name
        
        # Short description
        desc = _extract_short_detail(listing.get("message", ""))
        
        # Contact
        contact = listing.get("contact")
        
        contact_line = f" | 📞 {contact}" if contact else ""
        lines.append(f"{i}️⃣ *{name_str}*{contact_line}\n   _{desc}_")
    
    return "\n".join(lines)


def format_upsell_message(total_available: int) -> str:
    """Format the upsell message shown after free leads."""
    remaining = max(0, total_available - FREE_LEADS_COUNT)
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 *{remaining} more verified contacts available!*\n",
        "💎 *Get Verified Leads:*",
        f"├ ⭐ {TIER1_STARS} Stars → {TIER1_LEADS} contacts with details",
        f"└ ⭐ {TIER2_STARS} Stars → {TIER2_LEADS} contacts + negotiation tips\n",
        "✅ Verified contacts • 📱 Direct numbers • 💬 Ready to connect",
    ]
    
    return "\n".join(lines)


def format_paid_leads(listings: list, label: str, include_tips: bool = False) -> str:
    """Format paid contact cards for DM delivery after payment."""
    if not listings:
        return "😔 No additional contacts found. You have not been charged."
    
    lines = [f"🔓 *Here are your {len(listings)} verified contacts for \"{label}\":*\n"]
    
    for i, listing in enumerate(listings, 1):
        username = listing.get("username")
        first_name = listing.get("first_name") or "Someone"
        name_str = f"@{username}" if username else first_name
        
        desc = _extract_short_detail(listing.get("message", ""))
        contact = listing.get("contact")
        
        contact_line = f" | 📞 {contact}" if contact else ""
        lines.append(f"{i}. *{name_str}*{contact_line}\n   _{desc}_")
    
    if include_tips:
        lines.append("\n💡 *Negotiation Tips:*\n")
        lines.append("1️⃣ *Compare prices* — you now have multiple contacts. Use competing quotes to negotiate better rates.")
        lines.append("2️⃣ *Ask about move-in date* — flexible timing often means lower rent/price.")
        lines.append("3️⃣ *Check for hidden costs* — maintenance, parking, deposit amount, painting charges.")
        lines.append("4️⃣ *Request a visit first* — never commit without seeing the place/meeting the person.")
        lines.append("5️⃣ *Mention you're from the society group* — community trust = better deals.")
    
    lines.append("\n✅ _Thank you for using Society Ka Bot!_")
    
    return "\n".join(lines)


# ─── Main Match Functions ─────────────────────────────────────


def find_matches(
    category: str,
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None,
    chat_id: Optional[int] = None,
    original_message: str = ""
) -> Optional[str]:
    """
    Find matching listings for a query.
    Returns hook-style response text. Button is added by bot.py.
    """
    # Get aggregate stats (cross-group)
    stats = get_match_stats(
        category=category,
        listing_type="offer",
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference
    )

    if stats["total"] == 0:
        return None

    # Get a sample of listings for detail extraction
    sample_listings = get_matching_listings(
        category=category,
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference,
        limit=10
    )

    return format_hook_response_for_query(
        stats=stats,
        category=category,
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference,
        listings_sample=sample_listings
    )


def find_interested_buyers(
    category: str,
    subcategory: Optional[str] = None,
    property_type: Optional[str] = None,
    gender_preference: Optional[str] = None,
    chat_id: Optional[int] = None,
    original_message: str = ""
) -> Optional[str]:
    """
    Find people looking for something in this category.
    Returns hook-style response text. Button is added by bot.py.
    """
    # Get aggregate stats (cross-group)
    stats = get_match_stats(
        category=category,
        listing_type="query",
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference
    )

    if stats["total"] == 0:
        return None

    # Get a sample for detail extraction
    sample_queries = get_matching_queries(
        category=category,
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference,
        limit=10
    )

    return format_hook_response_for_offer(
        stats=stats,
        category=category,
        subcategory=subcategory,
        property_type=property_type,
        gender_preference=gender_preference,
        listings_sample=sample_queries
    )

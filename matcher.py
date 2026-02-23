"""
Query matcher with in-Telegram lead delivery.
Shows compelling hook in group → deep link to DM → free leads → paid upsell.
"""

from datetime import datetime
from typing import Optional
from database import get_matching_listings, get_matching_queries, get_match_stats
from config import MAX_RESULTS, FREE_LEADS_COUNT, TIER1_PRICE, TIER1_LEADS, TIER2_PRICE, TIER2_LEADS


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
    """Summarize listing message into 5-10 words using LLM."""
    from llm_classifier import llm_classifier
    return llm_classifier.summarize_description(message)


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


# ─── Category-Aware Copy ──────────────────────────────────────

PROPERTY_CATEGORIES = {"property", "furniture", "vehicle"}
SERVICE_CATEGORIES = {"maid_cook", "plumber", "electrician", "carpenter", "driver", 
                      "ac_repair", "tutor", "packers_movers", "pest_control", "painter",
                      "security_guard"}
ROOMMATE_CATEGORIES = {"roommate"}


def _get_category_context(category: str) -> dict:
    """Return category-aware wording for messages."""
    if category in PROPERTY_CATEGORIES:
        return {
            "offer_verb": "offering",          # "5 people offering 2bhk"
            "search_verb": "searching for",     # "3 buyers searching for 2bhk" 
            "searcher_word": "buyers",           # "connect with buyers"
            "upsell_hook": "Why pay ₹500+ to a broker when you can get direct contacts",
            "tips_title": "Pro Tips to Get the Best Deal",
            "tips": [
                "💰 Compare quotes — _multiple contacts = better negotiation power_",
                "📅 Ask about flexibility — _flexible timing = lower rates_",
                "🔍 Check hidden costs — _maintenance, deposit, parking_",
                "🏠 Always visit first — _never commit without seeing it_",
                "🤝 Mention you're from the society — _trust = better price_",
            ]
        }
    elif category in ROOMMATE_CATEGORIES:
        return {
            "offer_verb": "offering",
            "search_verb": "looking for",
            "searcher_word": "people",
            "upsell_hook": "Find the right match faster — verified contacts directly",
            "tips_title": "Tips for Finding the Right Roommate",
            "tips": [
                "🗣️ Talk first — _a quick call reveals a lot about compatibility_",
                "📅 Discuss habits — _sleep schedule, guests, cleanliness_",
                "💰 Clarify expenses — _rent split, bills, food, WiFi_",
                "📋 Set expectations — _agree on rules before moving in_",
                "🏠 Visit the place — _see the room and common areas first_",
            ]
        }
    else:
        return {
            "offer_verb": "available for",
            "search_verb": "looking for",
            "searcher_word": "people",
            "upsell_hook": "Skip the hassle of asking around — get verified contacts instantly",
            "tips_title": "Tips to Get the Best Service",
            "tips": [
                "📞 Call multiple — _compare rates before committing_",
                "⭐ Ask for references — _past work speaks louder than words_",
                "💰 Negotiate upfront — _agree on pricing before work starts_",
                "📋 Get it in writing — _scope of work + timeline + payment terms_",
                "🤝 Mention you're from the society — _community trust = better service_",
            ]
        }


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

    ctx = _get_category_context(category)
    emoji = CATEGORY_EMOJIS.get(category, "📋")
    label = build_label(category, subcategory, property_type, gender_preference)

    # Build detail snippets
    detail_parts = []
    
    if category == "property" and listings_sample:
        avg_k = _extract_rent_prices(listings_sample)
        if avg_k:
            detail_parts.append(f"starting ~{avg_k}k")
    
    if listings_sample:
        pref = _detect_preference(listings_sample)
        if pref:
            detail_parts.append(pref)
    
    detail_str = " · ".join(detail_parts)
    detail_line = f"\n📌 _{detail_str}_" if detail_str else ""
    
    # Urgency
    if recent > 0 and recent < total:
        urgency = f"\n⚡ _{recent} new this week — act fast!_"
    elif recent > 0:
        urgency = f"\n⚡ _All posted this week!_"
    else:
        urgency = ""
    
    lines = [
        f"{emoji} *{total} verified contacts available for {label}!*",
        detail_line,
        urgency,
        f"\n👇 _Tap below to get contacts directly in your DM_"
    ]
    
    return "\n".join(line for line in lines if line)


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

    ctx = _get_category_context(category)
    label = build_label(category, subcategory, property_type, gender_preference)

    # Urgency
    if recent > 0:
        urgency = f"\n🔥 _{recent} searched just this week!_"
    else:
        urgency = ""
    
    people_word = "person" if total == 1 else ctx["searcher_word"]
    
    lines = [
        f"🚨 *{total} {people_word} already {ctx['search_verb']} {label}!*",
        urgency,
        f"\n💬 _Get their details and close the deal before someone else does_",
        f"\n👇 _Tap below to connect now_"
    ]
    
    return "\n".join(line for line in lines if line)


# ─── DM Lead Formatters ──────────────────────────────────────


def format_free_leads(listings: list, label: str) -> str:
    """Format free contact cards for DM — designed to tease and convert."""
    if not listings:
        return "😔 No contacts available right now. Check back soon!"
    
    lines = [
        f"🎁 *FREE Preview — {len(listings)} contact for \"{label}\":*",
        ""
    ]
    
    for i, listing in enumerate(listings, 1):
        username = listing.get("username")
        first_name = listing.get("first_name") or "Someone"
        name_str = f"@{username}" if username else first_name
        
        desc = _extract_short_detail(listing.get("message", ""))
        contact = listing.get("contact")
        
        contact_line = f" · 📞 {contact}" if contact else ""
        lines.append(f"👤 *{name_str}*{contact_line}")
        lines.append(f"   _{desc}_")
    
    return "\n".join(lines)


def format_upsell_message(total_available: int, category: str = "property") -> str:
    """Format the upsell message — category-aware pitch."""
    remaining = max(0, total_available - FREE_LEADS_COUNT)
    ctx = _get_category_context(category)
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"\n🔥 *{remaining} more people are waiting to connect!*",
        f"\n_{ctx['upsell_hook']} for just ₹{TIER1_PRICE}!_",
        f"\n✅ Verified contacts with phone numbers",
        f"✅ Direct connection — no middleman",
        f"✅ Updated this week",
        f"\n👇 *Unlock now — contacts delivered in seconds:*",
    ]
    
    return "\n".join(lines)


def format_paid_leads(listings: list, label: str, include_tips: bool = False, category: str = "property") -> str:
    """Format paid contact cards — category-aware tips."""
    if not listings:
        return "😔 No additional contacts found. You have not been charged."
    
    ctx = _get_category_context(category)
    
    lines = [
        f"🎉 *You're in! Here are your {len(listings)} contacts for \"{label}\":*",
        ""
    ]
    
    for i, listing in enumerate(listings, 1):
        username = listing.get("username")
        first_name = listing.get("first_name") or "Someone"
        name_str = f"@{username}" if username else first_name
        
        desc = _extract_short_detail(listing.get("message", ""))
        contact = listing.get("contact")
        
        contact_line = f" · 📞 {contact}" if contact else ""
        lines.append(f"{i}. *{name_str}*{contact_line}")
        lines.append(f"   _{desc}_")
    
    if include_tips:
        lines.append(f"\n🧠 *{ctx['tips_title']}:*\n")
        for tip in ctx["tips"]:
            lines.append(tip)
    
    lines.append("\n💙 _Thanks for using Society Ka Bot! Search again anytime._")
    
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

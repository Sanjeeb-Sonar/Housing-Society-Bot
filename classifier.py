"""
Hybrid message classifier: LLM first, keyword fallback.
Uses Groq API for smart classification with keyword-based backup.
"""

import re
import logging
from typing import Optional, Tuple
from keywords import CATEGORIES, QUERY_INDICATORS, OFFER_INDICATORS, IGNORE_PATTERNS

logger = logging.getLogger(__name__)

# Try to import LLM classifier
try:
    from llm_classifier import llm_classifier, GROQ_AVAILABLE
except ImportError:
    llm_classifier = None
    GROQ_AVAILABLE = False


class MessageClassifier:
    """Hybrid classifier: LLM + keyword fallback."""
    
    def __init__(self):
        self.categories = CATEGORIES
        self.query_indicators = QUERY_INDICATORS
        self.offer_indicators = OFFER_INDICATORS
        self.ignore_patterns = [re.compile(p, re.IGNORECASE) for p in IGNORE_PATTERNS]
        self.use_llm = llm_classifier is not None and llm_classifier.client is not None
        
        if self.use_llm:
            logger.info("Using LLM classifier with keyword fallback")
        else:
            logger.info("Using keyword-only classifier")
    
    def classify(self, text: str) -> Optional[dict]:
        """
        Classify message using LLM first, fallback to keywords.
        Returns dict with category, subcategory, listing_type, contact or None.
        """
        # Quick ignore check first
        if self._should_ignore(text):
            return None
        
        # Try LLM first if available
        if self.use_llm:
            result = llm_classifier.classify(text)
            if result:
                # Add contact extraction if LLM missed it
                if not result.get("contact"):
                    result["contact"] = self._extract_contact(text)
                logger.debug(f"LLM classified: {result}")
                return result
        
        # Fallback to keyword matching
        return self._keyword_classify(text)
    
    def _should_ignore(self, text: str) -> bool:
        """Check if message should be ignored."""
        text = text.strip()
        
        if len(text) < 5:
            return True
        
        for pattern in self.ignore_patterns:
            if pattern.search(text):
                return True
        
        return False
    
    def _extract_contact(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        patterns = [
            r'\b[6-9]\d{9}\b',
            r'\b\+91\s*[6-9]\d{9}\b',
            r'\b91\s*[6-9]\d{9}\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                number = re.sub(r'\D', '', match.group())
                if len(number) > 10:
                    number = number[-10:]
                return number
        
        return None
    
    def _detect_listing_type(self, text: str) -> Optional[str]:
        """Determine if message is offer or query."""
        text_lower = text.lower()
        
        query_score = 0
        offer_score = 0
        
        for indicator in self.query_indicators:
            if indicator in text_lower:
                query_score += 1
        
        for indicator in self.offer_indicators:
            if indicator in text_lower:
                offer_score += 1
        
        if '?' in text:
            query_score += 2
        
        if self._extract_contact(text):
            offer_score += 1
        
        if query_score > offer_score:
            return "query"
        elif offer_score > 0:
            return "offer"
        
        return None
    
    def _detect_category(self, text: str) -> Optional[Tuple[str, Optional[str]]]:
        """Detect category and subcategory from keywords."""
        text_lower = text.lower()
        
        best_category = None
        best_score = 0
        best_subcategory = None
        
        for category_name, category_data in self.categories.items():
            score = 0
            
            for keyword in category_data.get("offer_keywords", []):
                if keyword in text_lower:
                    score += 2
            
            for keyword in category_data.get("query_keywords", []):
                if keyword in text_lower:
                    score += 2
            
            subcategory = None
            for pattern in category_data.get("subcategory_patterns", []):
                match = re.search(pattern, text_lower)
                if match:
                    score += 1
                    subcategory = match.group()
            
            if score > best_score:
                best_score = score
                best_category = category_name
                best_subcategory = subcategory
        
        if best_score >= 2:
            return (best_category, best_subcategory)
        
        return None
    
    def _extract_property_source(self, text: str) -> Optional[str]:
        """Detect if property listing is from owner or broker."""
        text_lower = text.lower()
        
        owner_keywords = [
            "owner", "direct owner", "no broker", "no brokerage", 
            "malik", "owner direct", "by owner", "from owner",
            "without broker", "brokerage free", "owner selling"
        ]
        
        broker_keywords = [
            "broker", "agent", "dealer", "brokerage", "commission",
            "property dealer", "real estate", "dalal", "via broker"
        ]
        
        for keyword in owner_keywords:
            if keyword in text_lower:
                return "owner"
        
        for keyword in broker_keywords:
            if keyword in text_lower:
                return "broker"
        
        return None
    
    def _extract_gender_preference(self, text: str) -> Optional[str]:
        """Detect gender preference for roommate/flatmate listings."""
        text_lower = text.lower()
        
        male_keywords = [
            "male roommate", "male flatmate", "boys only", "male only",
            "gents only", "men only", "bachelor male", "male bachelor",
            "ladka", "ladke", "boys flatmate", "male preferred"
        ]
        
        female_keywords = [
            "female roommate", "female flatmate", "girls only", "female only",
            "ladies only", "women only", "lady flatmate", "female bachelor",
            "ladki", "ladkiyan", "girls flatmate", "female preferred"
        ]
        
        for keyword in male_keywords:
            if keyword in text_lower:
                return "male"
        
        for keyword in female_keywords:
            if keyword in text_lower:
                return "female"
        
        return None
    
    def _keyword_classify(self, text: str) -> Optional[dict]:
        """Fallback keyword-based classification."""
        listing_type = self._detect_listing_type(text)
        if not listing_type:
            return None
        
        category_result = self._detect_category(text)
        if not category_result:
            return None
        
        category, subcategory = category_result
        contact = self._extract_contact(text)
        
        result = {
            "category": category,
            "subcategory": subcategory,
            "listing_type": listing_type,
            "contact": contact
        }
        
        # Add property source metadata
        if category == "property":
            source = self._extract_property_source(text)
            if source:
                result["property_source"] = source
        
        # Add gender preference for roommate
        if subcategory and ("roommate" in subcategory or "flatmate" in subcategory):
            gender = self._extract_gender_preference(text)
            if gender:
                result["gender_preference"] = gender
        
        # Also check for roommate/flatmate in the text
        text_lower = text.lower()
        if "roommate" in text_lower or "flatmate" in text_lower:
            gender = self._extract_gender_preference(text)
            if gender:
                result["gender_preference"] = gender
        
        return result


# Singleton instance
classifier = MessageClassifier()

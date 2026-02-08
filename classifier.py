"""Message classifier to categorize incoming messages."""

import re
from typing import Optional, Tuple
from keywords import CATEGORIES, QUERY_INDICATORS, OFFER_INDICATORS, IGNORE_PATTERNS


class MessageClassifier:
    """Classifies messages into categories and determines if they are offers or queries."""
    
    def __init__(self):
        self.categories = CATEGORIES
        self.query_indicators = QUERY_INDICATORS
        self.offer_indicators = OFFER_INDICATORS
        self.ignore_patterns = [re.compile(p, re.IGNORECASE) for p in IGNORE_PATTERNS]
    
    def should_ignore(self, text: str) -> bool:
        """Check if message should be ignored (greetings, general chat)."""
        text = text.strip()
        
        # Ignore very short messages
        if len(text) < 5:
            return True
        
        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            if pattern.search(text):
                return True
        
        return False
    
    def extract_contact(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        # Indian mobile number pattern (10 digits starting with 6-9)
        patterns = [
            r'\b[6-9]\d{9}\b',  # 10 digit number
            r'\b\+91\s*[6-9]\d{9}\b',  # With +91
            r'\b91\s*[6-9]\d{9}\b',  # With 91
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Clean and return the number
                number = re.sub(r'\D', '', match.group())
                if len(number) > 10:
                    number = number[-10:]  # Take last 10 digits
                return number
        
        return None
    
    def detect_listing_type(self, text: str) -> Optional[str]:
        """Determine if message is an offer or query."""
        text_lower = text.lower()
        
        query_score = 0
        offer_score = 0
        
        # Check for query indicators
        for indicator in self.query_indicators:
            if indicator in text_lower:
                query_score += 1
        
        # Check for offer indicators
        for indicator in self.offer_indicators:
            if indicator in text_lower:
                offer_score += 1
        
        # Question marks indicate queries
        if '?' in text:
            query_score += 2
        
        # Contact numbers usually indicate offers
        if self.extract_contact(text):
            offer_score += 1
        
        if query_score > offer_score:
            return "query"
        elif offer_score > 0:
            return "offer"
        
        return None
    
    def detect_category(self, text: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Detect the category and subcategory of a message.
        Returns (category, subcategory) or None if no category detected.
        """
        text_lower = text.lower()
        
        best_category = None
        best_score = 0
        best_subcategory = None
        
        for category_name, category_data in self.categories.items():
            score = 0
            
            # Check offer keywords
            for keyword in category_data.get("offer_keywords", []):
                if keyword in text_lower:
                    score += 2
            
            # Check query keywords
            for keyword in category_data.get("query_keywords", []):
                if keyword in text_lower:
                    score += 2
            
            # Check subcategory patterns
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
        
        if best_score >= 2:  # Minimum threshold
            return (best_category, best_subcategory)
        
        return None
    
    def classify(self, text: str) -> Optional[dict]:
        """
        Classify a message completely.
        Returns dict with category, subcategory, listing_type, contact or None.
        """
        if self.should_ignore(text):
            return None
        
        # Detect listing type
        listing_type = self.detect_listing_type(text)
        if not listing_type:
            return None
        
        # Detect category
        category_result = self.detect_category(text)
        if not category_result:
            return None
        
        category, subcategory = category_result
        
        # Extract contact if available
        contact = self.extract_contact(text)
        
        return {
            "category": category,
            "subcategory": subcategory,
            "listing_type": listing_type,
            "contact": contact
        }


# Singleton instance
classifier = MessageClassifier()

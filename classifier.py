"""
LLM-only message classifier using Groq API.
No keyword fallback - relies entirely on LLM for classification.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import LLM classifier
try:
    from llm_classifier import llm_classifier, GROQ_AVAILABLE
except ImportError:
    llm_classifier = None
    GROQ_AVAILABLE = False


class MessageClassifier:
    """LLM-only classifier for housing society messages."""
    
    def __init__(self):
        self.use_llm = llm_classifier is not None and llm_classifier.client is not None
        
        if self.use_llm:
            logger.info("Using LLM-only classifier")
        else:
            logger.warning("LLM not available - classification will not work!")
    
    def classify(self, text: str) -> Optional[dict]:
        """
        Classify message using LLM only.
        Returns dict with category, subcategory, listing_type, contact,
        property_type, gender_preference, or None if irrelevant.
        """
        # Quick ignore check for very short messages
        if self._should_ignore(text):
            return None
        
        # Use LLM for classification
        if not self.use_llm:
            logger.warning("LLM not available, cannot classify message")
            return None
        
        result = llm_classifier.classify(text)
        
        if not result:
            # LLM returned None (irrelevant message)
            logger.debug(f"Message ignored (irrelevant): {text[:50]}...")
            return None
        
        # Ensure contact is extracted
        if not result.get("contact"):
            result["contact"] = self._extract_contact(text)
        
        logger.debug(f"LLM classified: {result}")
        return result
    
    def _should_ignore(self, text: str) -> bool:
        """Check if message should be ignored (too short)."""
        text = text.strip()
        
        if len(text) < 5:
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


# Singleton instance
classifier = MessageClassifier()

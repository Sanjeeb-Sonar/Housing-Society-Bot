"""
LLM-based message classifier using Groq API (free Llama access).
Falls back to keyword matching if LLM fails.
"""

import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not installed. Using keyword fallback.")

# Get API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Categories for classification
CATEGORIES = [
    "property", "furniture", "maid", "plumber", "electrician",
    "carpenter", "driver", "ac_repair", "tutor", "packers_movers",
    "vehicle", "pest_control", "painter", "security_guard"
]

CLASSIFICATION_PROMPT = """You are a message classifier for a housing society group chat.
Classify the following message into ONE category and identify if it's an OFFER or QUERY.

Categories:
- property: flats, houses, rooms, rent, buy, sell property
- furniture: sofa, table, bed, fridge, TV, chairs
- maid: maids, cooks, nannies, domestic help, cleaning
- plumber: plumbing, pipes, taps, leaks, bathroom issues
- electrician: electrical, wiring, fan, light, switch
- carpenter: woodwork, furniture repair, doors, cabinets
- driver: drivers, chauffeurs
- ac_repair: AC, fridge repair, appliance repair
- tutor: teachers, tuition, coaching
- packers_movers: shifting, relocation, transport
- vehicle: cars, bikes, scooters for sale
- pest_control: cockroach, termite, pest issues
- painter: painting, wall paint
- security_guard: watchman, security
- ignore: greetings, general chat, unrelated messages

Message: "{message}"

Respond in EXACTLY this format (nothing else):
CATEGORY: <category>
TYPE: <offer or query>
SUBCATEGORY: <optional specific item like "2bhk", "cook", etc or "none">
CONTACT: <phone number if found, or "none">

If the message is general chat/greeting/unrelated, respond:
CATEGORY: ignore
TYPE: none
SUBCATEGORY: none
CONTACT: none
"""


class LLMClassifier:
    def __init__(self):
        self.client = None
        if GROQ_AVAILABLE and GROQ_API_KEY:
            try:
                self.client = Groq(api_key=GROQ_API_KEY)
                logger.info("Groq LLM classifier initialized")
            except Exception as e:
                logger.error(f"Failed to init Groq: {e}")
    
    def classify(self, text: str) -> Optional[dict]:
        """Classify message using LLM."""
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": CLASSIFICATION_PROMPT.format(message=text)}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_response(result)
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[dict]:
        """Parse LLM response into structured dict."""
        try:
            lines = response.strip().split('\n')
            data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip().upper()] = value.strip().lower()
            
            category = data.get('CATEGORY', 'ignore')
            
            if category == 'ignore' or category not in CATEGORIES:
                return None
            
            listing_type = data.get('TYPE', 'query')
            if listing_type not in ['offer', 'query']:
                listing_type = 'query'
            
            subcategory = data.get('SUBCATEGORY', 'none')
            if subcategory == 'none':
                subcategory = None
            
            contact = data.get('CONTACT', 'none')
            if contact == 'none':
                # Try to extract phone from original message
                contact = self._extract_phone(data.get('original_text', ''))
            
            return {
                "category": category,
                "subcategory": subcategory,
                "listing_type": listing_type,
                "contact": contact if contact != 'none' else None
            }
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        patterns = [
            r'\b[6-9]\d{9}\b',
            r'\b\+91[\s-]?[6-9]\d{9}\b',
            r'\b91[\s-]?[6-9]\d{9}\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return re.sub(r'[\s\-\+]', '', match.group())
        return None


# Create global instance
llm_classifier = LLMClassifier()

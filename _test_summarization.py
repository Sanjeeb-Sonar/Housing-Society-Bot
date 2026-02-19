"""
Test script to verify LLM Summarization logic in matcher.py.
"""
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from matcher import _extract_short_detail
from llm_classifier import llm_classifier

def test_summarization():
    print("Testing LLM Summarization...\n")
    
    # Mock LLM client if not available (to test fallback or actual if key present)
    if not llm_classifier.client:
        print("[WARN] Groq Client not initialized. Expecting Fallback (truncation).")
    
    test_messages = [
        "Spacious 2BHK flat for rent in Tower A, 5th floor. Rent 25k including maintenance. Family preferred. Contact 9876543210.",
        "Need a maid for cooking and cleaning, morning shift. Salary negotiable.",
        "Selling my old sofa set, 3+1+1, teak wood, good condition. Price 15k. Call me.",
        "Plumber needed urgently for water leakage issue in bathroom.",
    ]
    
    for msg in test_messages:
        summary = _extract_short_detail(msg)
        print(f"Original: {msg}")
        print(f"Summary:  {summary}")
        print("-" * 40)

if __name__ == "__main__":
    test_summarization()

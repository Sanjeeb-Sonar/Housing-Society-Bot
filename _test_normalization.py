"""
Test script to verify Phone Number Normalization logic in llm_classifier.py.
"""
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from llm_classifier import llm_classifier

def test_normalization():
    print("Testing Phone Number Normalization...\n")
    
    test_cases = [
        ("9876543210", "9876543210"),
        ("+919876543210", "9876543210"),
        ("09876543210", "9876543210"),
        ("+91 98765 43210", "9876543210"),
        ("91 98765-43210", "9876543210"),
        ("Call me at 9876543210", "9876543210"),  # Extraction check
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        # Test _extract_phone directly
        extracted = llm_classifier._extract_phone(input_text)
        
        # We also need to test the normalization logic inside _parse_response
        # because _extract_phone might return more digits, and _parse_response trims it.
        # But wait, I updated _extract_phone to return 10 digits directly!
        # So extracted should be exactly expected.
        
        if extracted == expected:
            print(f"[PASS] Input: '{input_text}' -> '{extracted}'")
            passed += 1
        else:
            print(f"[FAIL] Input: '{input_text}' -> '{extracted}' (Expected: '{expected}')")
            failed += 1
            
    # Test _parse_response logic check
    print("\nTesting _parse_response normalization...")
    mock_llm_response = """
    CATEGORY: property
    TYPE: offer
    CONTACT: +91 9988776655
    """
    parsed = llm_classifier._parse_response(mock_llm_response)
    if parsed and parsed['contact'] == '9988776655':
        print(f"[PASS] LLM Response Normalization working: '+91 9988776655' -> '{parsed['contact']}'")
        passed += 1
    else:
        print(f"[FAIL] LLM Response Normalization failed: Got '{parsed.get('contact')}'")
        failed += 1

    print("-" * 40)
    print(f"Results: {passed} passed, {failed} failed")

if __name__ == "__main__":
    test_normalization()

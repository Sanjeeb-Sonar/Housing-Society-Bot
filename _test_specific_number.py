
import re

def test_custom_number():
    text = "+9128334545678"
    
    # The regex from llm_classifier.py
    patterns = [
        # 10 digits start with 6-9, optionally separated by space/dash
        r'\b[6-9](?:\d[-\s]?){9}\b',
        # +91 or 91 or 0 followed by 10 digits (with separators)
        r'(?:\+91|91|0)[-\s]?[6-9](?:\d[-\s]?){9}\b'
    ]
    
    found = None
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            found = match.group()
            break
            
    print(f"Input: {text}")
    print(f"Matched: {found}")

    if found:
        # Normalization logic
        normalized = re.sub(r'\D', '', found)
        if len(normalized) > 10:
            normalized = normalized[-10:]
        print(f"Normalized: {normalized}")
    else:
        print("Result: None (Invalid Number)")

if __name__ == "__main__":
    test_custom_number()

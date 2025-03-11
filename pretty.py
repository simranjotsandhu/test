import re

def prettify_string(input_string):
    """
    Prettifies a string by keeping only English letters, digits, and common punctuation,
    removing non-English characters, and normalizing spaces.
    
    Args:
        input_string: The string to process (any type, converted to string).
    
    Returns:
        str: The prettified string with only English characters and common symbols.
    """
    # Convert input to string, handling None or non-string types
    if input_string is None:
        text = ""
    else:
        text = str(input_string)
    
    # Define allowed characters: English letters, digits, and common punctuation
    allowed_chars = r'[a-zA-Z0-9 .,!?\'"-:;()[]]'
    
    # Keep only allowed characters
    cleaned = ''.join(char for char in text if re.match(allowed_chars, char))
    
    # Normalize spaces: replace multiple spaces with a single space, strip leading/trailing
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Optional: Capitalize the first letter of the string for readability
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    
    return cleaned

# Test cases
if __name__ == "__main__":
    test_cases = [
        ("Hello,世界! café 123 ümlaut", "Mixed string with non-English chars"),
        ("Hello, world! How are you? 42", "English-only string"),
        ("This   is...   a   test!!!   ¿qué?", "Messy string with extra spaces"),
        ("", "Empty string"),
        ("Привет, hello! @#$%^&*() 日本語", "Complex string with multiple scripts"),
        (None, "None input"),
        ("123-456-7890", "Numbers with hyphens"),
        ("What's up?!!", "String with punctuation"),
        ("café au lait, s'il vous plaît", "String with French accents"),
    ]

    for input_str, desc in test_cases:
        result = prettify_string(input_str)
        print(f"{desc}:")
        print(f"  Input:  '{input_str}'")
        print(f"  Output: '{result}'")
        print(f"  Length: {len(result)}")
        print()

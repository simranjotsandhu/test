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
    # Test 1: String with non-English characters
    mixed_string = "Hello,世界! café 123 ümlaut"
    print(f"Mixed string: '{prettify_string(mixed_string)}'")

    # Test 2: String with only English characters and symbols
    english_string = "Hello, world! How are you? 42"
    print(f"English string: '{prettify_string(english_string)}'")

    # Test 3: String with multiple spaces and odd punctuation
    messy_string = "This   is...   a   test!!!   ¿qué?"
    print(f"Messy string: '{prettify_string(messy_string)}'")

    # Test 4: Empty string
    empty_string = ""
    print(f"Empty string: '{prettify_string(empty_string)}'")

    # Test 5: String with non-Latin script and symbols
    complex_string = "Привет, hello! @#$%^&*() 日本語"
    print(f"Complex string: '{prettify_string(complex_string)}'")

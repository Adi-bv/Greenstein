import re

def sanitize_input(text: str) -> str:
    """
    A basic input sanitizer to remove or neutralize common prompt injection phrases.
    This is a starting point and should be expanded based on observed attack patterns.
    """
    if not text:
        return ""

    # List of phrases to remove/neutralize
    injection_phrases = [
        r"ignore all previous instructions",
        r"ignore the above text",
        r"you are in a simulation",
        r"act as",
        r"translate the above text",
        # Add more patterns as needed
    ]

    # Replace each phrase with an empty string, case-insensitively
    sanitized_text = text
    for phrase in injection_phrases:
        sanitized_text = re.sub(phrase, "", sanitized_text, flags=re.IGNORECASE).strip()

    return sanitized_text

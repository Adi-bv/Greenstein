import re

def sanitize_input(text: str) -> str:
    """
    Sanitizes user input to prevent basic prompt injection attacks.

    - Removes leading/trailing whitespace.
    - Can be extended to remove or escape special characters.
    """
    if not isinstance(text, str):
        return ""

    # Trim whitespace
    text = text.strip()

    # A simple example of removing characters that might be used to manipulate prompts.
    # This is not exhaustive and should be expanded based on security needs.
    text = re.sub(r'[<>{}\[\]|`]', '', text)

    return text

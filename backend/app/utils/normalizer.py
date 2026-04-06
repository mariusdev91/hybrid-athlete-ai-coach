import re

def normalize_text(text: str) -> str:
    """
    Basic text normalization for semantic search.
    """
    if not text:
        return ""

    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

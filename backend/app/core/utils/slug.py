import re


def generate_slug(text: str) -> str:
    """
    Shared helper function generating a URL-friendly slug from a name string.
    e.g., 'Barbell Bench Press (Heavy)' -> 'barbell-bench-press-heavy'
    """
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

import re


def preprocess(text):
    """
    Cleans and tokenizes text.
    Removes punctuation, lowercases, and splits into word tokens.
    """
    # Remove punctuation except hyphens (important for c++, node.js, etc.)
    text = re.sub(r'[^\w\s\+\#\.]', ' ', text)

    # Lowercase
    text = text.lower()

    # Split into tokens
    tokens = text.split()

    return tokens
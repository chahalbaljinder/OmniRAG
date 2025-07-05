# Reserved for future utilities like logging, cleaning text, etc.
# app/utils.py

def chunk_text(text, max_length=300, overlap=50):
    """
    Splits a long text into overlapping chunks.

    Args:
        text (str): The full text to split.
        max_length (int): Maximum length of each chunk.
        overlap (int): Overlap between chunks.

    Returns:
        List[str]: List of text chunks.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + max_length, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += max_length - overlap

    return chunks

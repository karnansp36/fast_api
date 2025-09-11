# services/embeddings.py
import hashlib
from typing import List

def embed_text(text: str) -> List[float]:
    """
    Simple embedding function using hash-based approach.
    Replace with actual embedding model in production.
    """
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    
    embedding = []
    for i in range(0, len(text_hash), 2):
        hex_pair = text_hash[i:i+2]
        float_val = int(hex_pair, 16) / 255.0
        embedding.append(float_val)
    
    # Pad or truncate to 1536 dimensions to match your model
    target_size = 1536
    if len(embedding) < target_size:
        # Pad with zeros
        embedding.extend([0.0] * (target_size - len(embedding)))
    else:
        # Truncate to target size
        embedding = embedding[:target_size]
    
    return embedding
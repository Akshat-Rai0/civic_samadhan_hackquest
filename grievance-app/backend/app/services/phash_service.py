import imagehash
from PIL import Image

def compute_phash(image_path: str) -> str:
    """Compute perceptual hash for an image file."""
    img = Image.open(image_path)
    return str(imagehash.phash(img))

def phash_distance(hash1: str, hash2: str) -> int:
    """Hamming distance between two hex-encoded phash strings."""
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    return h1 - h2

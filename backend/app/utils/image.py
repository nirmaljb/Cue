"""Image utility functions for base64 encoding/decoding."""

import base64
import io
from PIL import Image
import numpy as np


def decode_base64_image(image_base64: str) -> Image.Image:
    """Decode a base64 image string to PIL Image.
    
    Args:
        image_base64: Base64 encoded image string (with or without data URI prefix)
    
    Returns:
        PIL Image object
    """
    # Remove data URI prefix if present
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]
    
    # Decode base64 to bytes
    image_bytes = base64.b64decode(image_base64)
    
    # Convert to PIL Image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    return image


def image_to_numpy(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to numpy array.
    
    Args:
        image: PIL Image object
    
    Returns:
        Numpy array of shape (H, W, 3)
    """
    return np.array(image)


def encode_image_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Encode PIL Image to base64 string.
    
    Args:
        image: PIL Image object
        format: Image format (JPEG, PNG, etc.)
    
    Returns:
        Base64 encoded string with data URI prefix
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    image_bytes = buffer.getvalue()
    
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = f"image/{format.lower()}"
    
    return f"data:{mime_type};base64,{base64_str}"

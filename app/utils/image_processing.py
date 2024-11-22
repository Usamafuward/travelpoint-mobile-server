import io
import base64
from PIL import Image
from fastapi import UploadFile
from typing import List

async def process_images(images: List[UploadFile]) -> List[str]:
    processed_images = []
    for image in images:
        # Read the image data
        img = Image.open(io.BytesIO(await image.read()))
        
        # Convert image to RGB mode if it has an alpha channel
        if img.mode == "RGBA":
            img = img.convert("RGB")
        
        # Resize the image
        img = img.resize((img.width // 3, img.height // 3))
        
        # Save resized image to an in-memory buffer
        output = io.BytesIO()
        img.save(output, format="JPEG")
        
        # Encode the image to base64
        processed_images.append(base64.b64encode(output.getvalue()).decode("utf-8"))
    
    return processed_images


#!/usr/bin/env python
"""
Create Default Book Cover Script

This script creates a default book cover image using the PIL library
and saves it to the static/images directory.
"""

import os
import django
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from django.conf import settings

def create_default_book_cover():
    """Create a default book cover image using PIL."""
    logger.info("Creating default book cover image...")
    
    # Define paths
    static_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    os.makedirs(static_dir, exist_ok=True)
    
    # Path to save the default cover
    default_cover_path = os.path.join(static_dir, 'default-book-cover.jpg')
    
    # Create a new image with a blue background
    width, height = 800, 1200
    color = (53, 105, 184)  # Blue color
    
    # Create a new image with a blue background
    image = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(image)
    
    # Add some text to the image
    try:
        # Try to use a font if available
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial.ttf')
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 60)
        else:
            # Use default font
            font = ImageFont.load_default()
        
        # Add title text
        title_text = "Book Cover"
        title_width = draw.textlength(title_text, font=font)
        draw.text(((width - title_width) / 2, height / 2 - 100), title_text, fill=(255, 255, 255), font=font)
        
        # Add subtitle text
        subtitle_text = "Library Project"
        subtitle_width = draw.textlength(subtitle_text, font=font)
        draw.text(((width - subtitle_width) / 2, height / 2 + 100), subtitle_text, fill=(255, 255, 255), font=font)
    except Exception as e:
        logger.warning(f"Error adding text to image: {e}")
        # Draw a simple rectangle if text fails
        draw.rectangle([(100, 100), (width - 100, height - 100)], outline=(255, 255, 255), width=5)
    
    # Save the image
    try:
        image.save(default_cover_path, 'JPEG', quality=95)
        logger.info(f"Default cover created at {default_cover_path} (size: {os.path.getsize(default_cover_path)} bytes)")
        return True
    except Exception as e:
        logger.error(f"Error saving default cover: {e}")
        return False

if __name__ == "__main__":
    create_default_book_cover()

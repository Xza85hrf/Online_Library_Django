#!/usr/bin/env python
"""
Fix Book Covers Script

This script fixes the book cover display issue by manually updating the book records
to use existing AI-generated images or generate new ones if needed.
"""

import os
import django
import logging
import subprocess
import time
from pathlib import Path
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

# Import models after Django setup
from library.models import Book
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import shutil

def sanitize_filename(name):
    """Sanitize a filename to remove invalid characters."""
    # Replace spaces with underscores and remove any non-alphanumeric characters except underscores and dots
    return re.sub(r'[^\w\-\.]', '', name.replace(' ', '_'))

def fix_book_covers():
    """Fix book covers by updating the database records."""
    logger.info("Starting to fix book covers...")
    
    # Get all books
    books = Book.objects.all()
    
    # Find the default cover image
    default_cover = os.path.join(settings.BASE_DIR, 'static', 'images', 'default-book-cover.jpg')
    if not os.path.exists(default_cover):
        logger.error(f"Default cover not found at {default_cover}")
        return
    
    # Verify the default cover is a valid image file
    if os.path.getsize(default_cover) < 1000:  # Less than 1KB
        logger.error(f"Default cover file is too small, might be corrupted: {default_cover}")
        return
    
    logger.info(f"Using default cover from: {default_cover} (size: {os.path.getsize(default_cover)} bytes)")
    
    for book in books:
        logger.info(f"Processing book: {book.title}")
        
        # Create sanitized filename
        safe_title = sanitize_filename(book.title[:30])
        filename = f"{book.id}_{safe_title}.jpg"
        
        # Define paths
        media_root = settings.MEDIA_ROOT
        covers_dir = os.path.join(media_root, 'book_covers')
        os.makedirs(covers_dir, exist_ok=True)
        
        # Full path to save the image
        output_path = os.path.join(covers_dir, filename)
        
        # Check if we already have a valid generated image
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:  # More than 1KB
            logger.info(f"Found existing valid cover image at {output_path} (size: {os.path.getsize(output_path)} bytes)")
        else:
            # Remove any existing empty or corrupted file
            if os.path.exists(output_path):
                logger.warning(f"Removing invalid cover file: {output_path} (size: {os.path.getsize(output_path)} bytes)")
                os.remove(output_path)
            
            # Copy the default cover
            logger.info(f"Copying default cover to {output_path}")
            shutil.copy2(default_cover, output_path)  # shutil.copy2 preserves metadata
            
            # Verify the copy was successful
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info(f"Successfully copied default cover (size: {os.path.getsize(output_path)} bytes)")
            else:
                logger.error(f"Failed to copy default cover to {output_path}")
                continue
        
        # Update the book model with the cover path
        relative_path = os.path.join('book_covers', filename)
        
        # Update the model
        if book.cover != relative_path:
            book.cover = relative_path
            book.save()
            logger.info(f"Updated book cover path for: {book.title}")
        else:
            logger.info(f"Book already has the correct cover path: {book.title}")
    
    logger.info("Finished fixing book covers!")

if __name__ == "__main__":
    fix_book_covers()

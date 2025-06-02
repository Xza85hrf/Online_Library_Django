#!/usr/bin/env python
"""
Fix Author Images Script

This script fixes the author image display issue by manually updating the author records
to use existing AI-generated images.
"""

import os
import django
import logging
import re
import shutil

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
from library.models import Author
from django.conf import settings

def sanitize_filename(name):
    """Sanitize a filename to remove invalid characters."""
    # Replace spaces with underscores and remove any non-alphanumeric characters except underscores and dots
    return re.sub(r'[^\w\-\.]', '', name.replace(' ', '_'))

def fix_author_images():
    """Fix author images by updating the database records."""
    logger.info("Starting to fix author images...")
    
    # Get all authors
    authors = Author.objects.all()
    
    for author in authors:
        logger.info(f"Processing author: {author.name}")
        
        # Create sanitized filename
        safe_name = sanitize_filename(author.name[:30])
        filename = f"{author.id}_{safe_name}.jpg"
        
        # Define paths
        media_root = settings.MEDIA_ROOT
        authors_dir = os.path.join(media_root, 'authors')
        os.makedirs(authors_dir, exist_ok=True)
        
        # Full path to the image
        image_path = os.path.join(authors_dir, filename)
        
        # Check if the image exists
        if os.path.exists(image_path):
            logger.info(f"Found existing author image at {image_path}")
            
            # Update the author model with the image path
            relative_path = os.path.join('authors', filename)
            
            # Update the model
            if str(author.photo) != relative_path:
                author.photo = relative_path
                author.save()
                logger.info(f"Updated author photo path for: {author.name}")
            else:
                logger.info(f"Author already has the correct photo path: {author.name}")
        else:
            logger.warning(f"No image found for author: {author.name} at {image_path}")
    
    logger.info("Finished fixing author images!")

if __name__ == "__main__":
    fix_author_images()

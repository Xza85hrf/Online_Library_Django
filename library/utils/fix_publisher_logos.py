#!/usr/bin/env python
"""
Fix Publisher Logos Script

This script fixes the publisher logo display issue by manually updating the publisher records
to use existing AI-generated images.
"""

import os
import django
import logging
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
from library.models import Publisher
from django.conf import settings

def sanitize_filename(name):
    """Sanitize a filename to remove invalid characters."""
    # Replace spaces with underscores and remove any non-alphanumeric characters except underscores and dots
    return re.sub(r'[^\w\-\.]', '', name.replace(' ', '_'))

def fix_publisher_logos():
    """Fix publisher logos by updating the database records."""
    logger.info("Starting to fix publisher logos...")
    
    # Get all publishers
    publishers = Publisher.objects.all()
    
    for publisher in publishers:
        logger.info(f"Processing publisher: {publisher.name}")
        
        # Create sanitized filename
        safe_name = sanitize_filename(publisher.name[:30])
        filename = f"{publisher.id}_{safe_name}.jpg"
        
        # Define paths
        media_root = settings.MEDIA_ROOT
        publishers_dir = os.path.join(media_root, 'publishers')
        os.makedirs(publishers_dir, exist_ok=True)
        
        # Full path to the image
        image_path = os.path.join(publishers_dir, filename)
        
        # Check if the image exists
        if os.path.exists(image_path):
            logger.info(f"Found existing publisher logo at {image_path}")
            
            # Update the publisher model with the image path
            relative_path = os.path.join('publishers', filename)
            
            # Update the model
            if str(publisher.logo) != relative_path:
                publisher.logo = relative_path
                publisher.save()
                logger.info(f"Updated publisher logo path for: {publisher.name}")
            else:
                logger.info(f"Publisher already has the correct logo path: {publisher.name}")
        else:
            logger.warning(f"No logo found for publisher: {publisher.name} at {image_path}")
    
    logger.info("Finished fixing publisher logos!")

if __name__ == "__main__":
    fix_publisher_logos()

#!/usr/bin/env python
"""
Fix Book Cover Paths Script

This script updates the book cover paths in the database to point to the correct directory
where the Flux AI generator is saving the images (media/covers).
"""

import os
import django
import logging

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

def fix_book_cover_paths():
    """Fix book cover paths to point to the correct directory."""
    logger.info("Starting to fix book cover paths...")
    
    # Get all books
    books = Book.objects.all()
    
    # Check if the covers directory exists
    covers_dir = os.path.join(settings.MEDIA_ROOT, 'covers')
    if not os.path.exists(covers_dir):
        logger.error(f"Covers directory not found at {covers_dir}")
        return
    
    # Count how many books were updated
    updated_count = 0
    
    for book in books:
        logger.info(f"Processing book: {book.title}")
        
        # Create the expected filename based on book ID and title
        # The filename format might vary, so we'll try a few common patterns
        possible_filenames = [
            f"{book.id}_" + book.title.replace(' ', '_')[:30] + ".jpg",
            f"{book.id}.jpg",
            f"{book.id}.png",
            f"{book.id}_{book.title.replace(' ', '_')}.jpg",
            f"{book.id}_{book.title.replace(' ', '_')}.png"
        ]
        
        found_file = None
        
        # Check if any of the possible filenames exist
        for filename in possible_filenames:
            file_path = os.path.join(covers_dir, filename)
            if os.path.exists(file_path):
                found_file = filename
                logger.info(f"Found cover image at {file_path}")
                break
        
        if found_file:
            # Update the book model with the correct cover path
            relative_path = os.path.join('covers', found_file)
            
            # Update the model only if the path is different
            if str(book.cover) != relative_path:
                book.cover = relative_path
                book.save()
                updated_count += 1
                logger.info(f"Updated book cover path for: {book.title}")
            else:
                logger.info(f"Book already has the correct cover path: {book.title}")
        else:
            logger.warning(f"No cover found for book: {book.title}")
    
    logger.info(f"Finished fixing book cover paths. Updated {updated_count} books.")

if __name__ == "__main__":
    fix_book_cover_paths()

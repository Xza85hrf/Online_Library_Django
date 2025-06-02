#!/usr/bin/env python
"""
Update Image Paths Script

This script updates the image paths for existing books, authors, and publishers
to use the AI-generated images that have already been created.
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
from library.models import Book, Author, Publisher
from django.conf import settings

def update_image_paths():
    """Update image paths for existing records to use AI-generated images."""
    logger.info("Starting image path update process...")
    
    # Update author images
    logger.info("Updating author images...")
    authors = Author.objects.all()
    for author in authors:
        # Check if an AI-generated image exists for this author
        filename = f"{author.id}_{author.name.replace(' ', '_')[:30]}.jpg"
        image_path = os.path.join(settings.MEDIA_ROOT, 'authors', filename)
        
        if os.path.exists(image_path):
            # Update the author's photo field
            relative_path = os.path.join('authors', filename)
            if author.photo != relative_path:
                author.photo = relative_path
                author.save()
                logger.info(f"Updated image for author: {author.name}")
            else:
                logger.info(f"Author already has correct image path: {author.name}")
        else:
            logger.warning(f"No AI-generated image found for author: {author.name}")
    
    # Update book covers
    logger.info("Updating book covers...")
    books = Book.objects.all()
    for book in books:
        # Check if an AI-generated image exists for this book
        filename = f"{book.id}_{book.title.replace(' ', '_')[:30]}.jpg"
        image_path = os.path.join(settings.MEDIA_ROOT, 'book_covers', filename)
        
        if os.path.exists(image_path):
            # Update the book's cover field
            relative_path = os.path.join('book_covers', filename)
            if book.cover != relative_path:
                book.cover = relative_path
                book.save()
                logger.info(f"Updated cover for book: {book.title}")
            else:
                logger.info(f"Book already has correct cover path: {book.title}")
        else:
            # Check in the covers directory (from the generate_images.py script)
            alt_filename = f"{book.id}.png"
            alt_image_path = os.path.join(settings.MEDIA_ROOT, 'covers', alt_filename)
            
            if os.path.exists(alt_image_path):
                relative_path = os.path.join('covers', alt_filename)
                if book.cover != relative_path:
                    book.cover = relative_path
                    book.save()
                    logger.info(f"Updated cover for book using alternative path: {book.title}")
                else:
                    logger.info(f"Book already has correct alternative cover path: {book.title}")
            else:
                logger.warning(f"No AI-generated cover found for book: {book.title}")
    
    # Update publisher logos
    logger.info("Updating publisher logos...")
    publishers = Publisher.objects.all()
    for publisher in publishers:
        # Check if an AI-generated image exists for this publisher
        filename = f"{publisher.id}_{publisher.name.replace(' ', '_')[:30]}.jpg"
        image_path = os.path.join(settings.MEDIA_ROOT, 'publishers', filename)
        
        if os.path.exists(image_path):
            # Update the publisher's logo field
            relative_path = os.path.join('publishers', filename)
            if publisher.logo != relative_path:
                publisher.logo = relative_path
                publisher.save()
                logger.info(f"Updated logo for publisher: {publisher.name}")
            else:
                logger.info(f"Publisher already has correct logo path: {publisher.name}")
        else:
            logger.warning(f"No AI-generated logo found for publisher: {publisher.name}")
    
    logger.info("Image path update process completed!")

if __name__ == "__main__":
    update_image_paths()

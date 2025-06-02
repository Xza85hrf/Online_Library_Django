#!/usr/bin/env python
"""
Generate Missing Book Covers Script

This script generates AI book covers for books that don't have covers yet.
"""

import os
import django
import logging
import subprocess
from pathlib import Path

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

# Path to the flux wrapper script
FLUX_WRAPPER_PATH = os.path.join(settings.BASE_DIR, 'flux_wrapper.py')
FLUX_AVAILABLE = os.path.exists(FLUX_WRAPPER_PATH)

def generate_with_flux(prompt, output_path, seed=None):
    """Generate an image using Flux AI through the flux_wrapper.py script."""
    if not FLUX_AVAILABLE:
        logger.warning("Flux AI wrapper not found. Skipping AI image generation.")
        return False
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Build command
        cmd = [
            "python", FLUX_WRAPPER_PATH,
            "--prompt", prompt,
            "--output", output_path
        ]
        
        # Add seed if provided
        if seed is not None:
            cmd.extend(["--seed", str(seed)])
        
        logger.info(f"Running Flux AI command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully generated image at {output_path}")
            return True
        else:
            logger.error(f"Error generating image: {result.stderr}")
            return False
    except Exception as e:
        logger.exception(f"Exception while generating with Flux: {e}")
        return False

def generate_missing_covers():
    """Generate covers for books that don't have them."""
    logger.info("Starting to generate missing book covers...")
    
    # Get all books
    books = Book.objects.all()
    
    for book in books:
        # Skip if the book already has a cover
        if book.cover and book.cover.name:
            logger.info(f"Book already has a cover: {book.title}")
            continue
        
        # Check if the book has authors
        if not book.authors.exists():
            logger.warning(f"Book has no authors, skipping: {book.title}")
            continue
        
        # Create a filename for the cover
        filename = f"{book.id}_{book.title.replace(' ', '_')[:30]}.jpg"
        
        # Define the media path
        media_root = settings.MEDIA_ROOT
        covers_dir = os.path.join(media_root, 'book_covers')
        os.makedirs(covers_dir, exist_ok=True)
        
        # Full path to save the image
        output_path = os.path.join(covers_dir, filename)
        
        # Generate the prompt
        authors = ", ".join([author.name for author in book.authors.all()])
        prompt = f"A professional book cover for '{book.title}' by {authors}. High quality, detailed, publishing industry standard."
        
        # Generate the image
        success = generate_with_flux(prompt, output_path)
        
        if success and os.path.exists(output_path):
            # Update the book model with the new cover
            relative_path = os.path.join('book_covers', filename)
            
            # Update the model
            book.cover = relative_path
            book.save()
            
            logger.info(f"Successfully generated and saved AI cover for book: {book.title}")
        else:
            logger.warning(f"Failed to generate AI cover for book: {book.title}")
    
    logger.info("Finished generating missing book covers!")

if __name__ == "__main__":
    generate_missing_covers()

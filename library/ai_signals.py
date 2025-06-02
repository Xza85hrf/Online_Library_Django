"""
AI Image Generation Signal Handlers

This module contains signal handlers that automatically trigger AI image generation
when new books, authors, or publishers are added to the database.
"""
import os
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.core.files.base import ContentFile
from pathlib import Path
import subprocess

from .models import Book, Author, Publisher

# Setup logging
logger = logging.getLogger(__name__)

# Path to the flux wrapper script
FLUX_WRAPPER_PATH = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
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

@receiver(post_save, sender=Book)
def generate_book_cover(sender, instance, created, **kwargs):
    """
    Generate a book cover using AI when a new book is created or 
    when a book is updated and doesn't have a cover.
    """
    # Skip if the book already has a cover
    if instance.cover and instance.cover.name:
        return
    
    # Only generate for books with authors
    if not instance.authors.exists():
        return
    
    try:
        # Create a filename for the cover
        filename = f"{instance.id}_{instance.title.replace(' ', '_')[:30]}.jpg"
        
        # Define the media path
        media_root = settings.MEDIA_ROOT
        covers_dir = os.path.join(media_root, 'covers')
        os.makedirs(covers_dir, exist_ok=True)
        
        # Full path to save the image
        output_path = os.path.join(covers_dir, filename)
        
        # Generate the prompt
        authors = ", ".join([author.name for author in instance.authors.all()])
        prompt = f"A professional book cover for '{instance.title}' by {authors}. High quality, detailed, publishing industry standard."
        
        # Generate the image
        success = generate_with_flux(prompt, output_path)
        
        if success and os.path.exists(output_path):
            # Update the book model with the new cover
            relative_path = os.path.join('covers', filename)
            
            # Update the model without triggering the post_save signal again
            Book.objects.filter(pk=instance.pk).update(cover=relative_path)
            
            logger.info(f"Successfully generated and saved AI cover for book: {instance.title}")
        else:
            logger.warning(f"Failed to generate AI cover for book: {instance.title}")
    
    except Exception as e:
        logger.exception(f"Error in generate_book_cover signal: {e}")

@receiver(post_save, sender=Author)
def generate_author_portrait(sender, instance, created, **kwargs):
    """
    Generate an author portrait using AI when a new author is created or
    when an author is updated and doesn't have a photo.
    """
    # Skip if the author already has a photo
    if instance.photo and instance.photo.name:
        return
    
    try:
        # Create a filename for the portrait
        filename = f"{instance.id}_{instance.name.replace(' ', '_')[:30]}.jpg"
        
        # Define the media path
        media_root = settings.MEDIA_ROOT
        authors_dir = os.path.join(media_root, 'authors')
        os.makedirs(authors_dir, exist_ok=True)
        
        # Full path to save the image
        output_path = os.path.join(authors_dir, filename)
        
        # Generate the prompt
        prompt = f"A professional portrait photograph of author {instance.name}. High quality, detailed, professional headshot."
        
        # Generate the image
        success = generate_with_flux(prompt, output_path)
        
        if success and os.path.exists(output_path):
            # Update the author model with the new photo
            relative_path = os.path.join('authors', filename)
            
            # Update the model without triggering the post_save signal again
            Author.objects.filter(pk=instance.pk).update(photo=relative_path)
            
            logger.info(f"Successfully generated and saved AI portrait for author: {instance.name}")
        else:
            logger.warning(f"Failed to generate AI portrait for author: {instance.name}")
    
    except Exception as e:
        logger.exception(f"Error in generate_author_portrait signal: {e}")

@receiver(post_save, sender=Publisher)
def generate_publisher_logo(sender, instance, created, **kwargs):
    """
    Generate a publisher logo using AI when a new publisher is created or
    when a publisher is updated and doesn't have a logo.
    """
    # Skip if the publisher already has a logo
    if instance.logo and instance.logo.name:
        return
    
    try:
        # Create a filename for the logo
        filename = f"{instance.id}_{instance.name.replace(' ', '_')[:30]}.jpg"
        
        # Define the media path
        media_root = settings.MEDIA_ROOT
        publishers_dir = os.path.join(media_root, 'publishers')
        os.makedirs(publishers_dir, exist_ok=True)
        
        # Full path to save the image
        output_path = os.path.join(publishers_dir, filename)
        
        # Generate the prompt
        prompt = f"A professional logo for publishing company '{instance.name}'. Clean, corporate design, minimalist, high quality."
        
        # Generate the image
        success = generate_with_flux(prompt, output_path)
        
        if success and os.path.exists(output_path):
            # Update the publisher model with the new logo
            relative_path = os.path.join('publishers', filename)
            
            # Update the model without triggering the post_save signal again
            Publisher.objects.filter(pk=instance.pk).update(logo=relative_path)
            
            logger.info(f"Successfully generated and saved AI logo for publisher: {instance.name}")
        else:
            logger.warning(f"Failed to generate AI logo for publisher: {instance.name}")
    
    except Exception as e:
        logger.exception(f"Error in generate_publisher_logo signal: {e}")

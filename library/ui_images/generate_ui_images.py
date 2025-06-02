#!/usr/bin/env python
"""
Generate UI Images Script

This script generates various UI images for the library application using Flux AI,
including user profile pictures and modern library page illustrations.
"""

import os
import django
import logging
import subprocess
import random
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
from django.conf import settings
from accounts.models import CustomUser, UserProfile

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

def generate_user_profile_pictures():
    """Generate profile pictures for users."""
    logger.info("Generating user profile pictures...")
    
    # Get all user profiles
    profiles = UserProfile.objects.all()
    
    # Create directory for user profile pictures
    profile_pics_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pics')
    os.makedirs(profile_pics_dir, exist_ok=True)
    
    for profile in profiles:
        user = profile.user
        logger.info(f"Processing user: {user.email}")
        
        # Create a filename for the profile picture
        # Use a sanitized version of the email as part of the filename
        email_part = user.email.split('@')[0].replace('.', '_')
        filename = f"{user.id}_{email_part}.jpg"
        
        # Full path to save the image
        output_path = os.path.join(profile_pics_dir, filename)
        
        # Skip if the profile picture already exists
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Profile picture already exists for user: {user.email}")
            continue
        
        # Generate the prompt based on profile information if available
        gender = 'person'
        if hasattr(profile, 'gender') and profile.gender:
            gender = profile.gender
        
        age = random.randint(20, 60)
        if hasattr(profile, 'date_of_birth') and profile.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - profile.date_of_birth.year - ((today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day))
        
        prompt = f"Professional headshot portrait of a {age} year old {gender} person, library user, neutral background, high quality, photorealistic."
        
        # Generate the image
        success = generate_with_flux(prompt, output_path, seed=user.id)
        
        if success:
            # Update the profile's photo field if it exists
            if hasattr(profile, 'photo'):
                relative_path = os.path.join('profile_pics', filename)
                profile.photo = relative_path
                profile.save()
                logger.info(f"Updated profile photo field for user: {user.email}")
            
            logger.info(f"Successfully generated profile picture for user: {user.email}")
        else:
            logger.warning(f"Failed to generate profile picture for user: {user.email}")
    
    logger.info("Finished generating user profile pictures.")

def generate_library_illustrations():
    """Generate modern illustrations for the library pages."""
    logger.info("Generating library illustrations...")
    
    # Define the illustrations to generate
    illustrations = [
        {
            "name": "library-hero",
            "prompt": "Modern library interior with bookshelves, reading areas, and natural light, digital illustration, flat design style, vibrant colors, no text.",
            "format": "svg"
        },
        {
            "name": "book-reading",
            "prompt": "Person reading a book in a cozy library corner, digital illustration, flat design style, vibrant colors, no text.",
            "format": "svg"
        },
        {
            "name": "book-borrowing",
            "prompt": "Person borrowing books from a library counter, digital illustration, flat design style, vibrant colors, no text.",
            "format": "svg"
        },
        {
            "name": "library-community",
            "prompt": "Library community event with people discussing books, digital illustration, flat design style, vibrant colors, no text.",
            "format": "svg"
        },
        {
            "name": "digital-library",
            "prompt": "Person using digital devices in a modern library, digital illustration, flat design style, vibrant colors, no text.",
            "format": "svg"
        }
    ]
    
    # Create directory for library illustrations
    illustrations_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    os.makedirs(illustrations_dir, exist_ok=True)
    
    for illustration in illustrations:
        logger.info(f"Processing illustration: {illustration['name']}")
        
        # Full path to save the image
        output_path = os.path.join(illustrations_dir, f"{illustration['name']}.jpg")
        
        # Skip if the illustration already exists
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Illustration already exists: {illustration['name']}")
            continue
        
        # Generate the image
        success = generate_with_flux(illustration['prompt'], output_path)
        
        if success:
            logger.info(f"Successfully generated illustration: {illustration['name']}")
        else:
            logger.warning(f"Failed to generate illustration: {illustration['name']}")
    
    logger.info("Finished generating library illustrations.")

if __name__ == "__main__":
    generate_user_profile_pictures()
    generate_library_illustrations()

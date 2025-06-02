import os
import re
import subprocess
import time
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Integrate Kaggle-imported data with proper images and data cleanup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of items to process in one batch before pausing'
        )
        parser.add_argument(
            '--pause-seconds',
            type=int,
            default=3,
            help='Seconds to pause between batches'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['books', 'authors', 'publishers', 'all'],
            default='all',
            help='Type of data to process'
        )
        parser.add_argument(
            '--fallback',
            action='store_true',
            help='Force fallback to basic image generation'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        pause_seconds = options['pause_seconds']
        data_type = options['type']
        fallback = options['fallback']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        # Step 1: Clean up data names (titles, author names, publisher names)
        if data_type in ['books', 'all']:
            self.clean_book_titles(dry_run)
        
        if data_type in ['authors', 'all']:
            self.clean_author_names(dry_run)
        
        if data_type in ['publishers', 'all']:
            self.clean_publisher_names(dry_run)
        
        # Step 2: Reset invalid image paths
        if data_type in ['books', 'all']:
            self.reset_invalid_book_covers(dry_run)
        
        if data_type in ['authors', 'all']:
            self.reset_invalid_author_photos(dry_run)
        
        if data_type in ['publishers', 'all']:
            self.reset_invalid_publisher_logos(dry_run)
        
        # Step 3: Generate missing images
        if not dry_run:
            if data_type in ['books', 'all']:
                self.generate_book_covers(batch_size, pause_seconds, fallback)
            
            if data_type in ['authors', 'all']:
                self.generate_author_photos(batch_size, pause_seconds, fallback)
            
            if data_type in ['publishers', 'all']:
                self.generate_publisher_logos(batch_size, pause_seconds, fallback)
        
        self.stdout.write(self.style.SUCCESS('Kaggle data integration completed!'))
    
    def is_likely_kaggle_item(self, name):
        """Check if an item name appears to be from Kaggle dataset"""
        if not name:
            return False
        
        # Check for CSV-like format with semicolons
        if ';' in name:
            return True
        
        # Check for excessive quotes which might indicate CSV data
        if name.count('"') > 1:
            return True
        
        # Check for ISBN-like patterns at the beginning
        if re.match(r'^\d{10,13}', name):
            return True
            
        # Check for other common Kaggle patterns
        if ',' in name and name.count(',') >= 3:  # Multiple commas might indicate CSV
            return True
            
        if re.search(r'\d{4}-\d{2}-\d{2}', name):  # Date format in the name
            return True
            
        # Check for non-standard characters that might indicate encoding issues
        if re.search(r'[\x00-\x1F\x7F-\xFF]', name):
            return True
            
        return False
    
    def clean_name(self, name):
        """Clean up a name that might be from Kaggle CSV data"""
        if not name:
            return "Unknown"
            
        # If it looks like CSV data, extract the first meaningful field
        if self.is_likely_kaggle_item(name):
            # Split by semicolons
            parts = name.split(';')
            
            # Try to find the first non-numeric, non-empty part
            for part in parts:
                cleaned = part.strip().strip('"\'')
                # Skip if it's just a number (like an ID or ISBN)
                if cleaned and not cleaned.isdigit() and len(cleaned) > 1:
                    return cleaned
            
            # If we couldn't find a good part, just use the first one
            if parts and parts[0].strip():
                return parts[0].strip().strip('"\'')
            
        return name
    
    def sanitize_filename(self, filename):
        """Sanitize a string to be safe for filenames"""
        if not filename:
            return "unknown"
            
        # Replace problematic characters with underscores
        # Remove characters that are invalid in filenames (Windows restrictions)
        invalid_chars = r'[<>:"\/|?*\\]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        
        return sanitized
    
    def check_image_exists(self, image_field):
        """Check if an image file actually exists"""
        if not image_field or not image_field.name:
            return False
            
        # Check if the file exists on disk
        if hasattr(image_field, 'path'):
            return os.path.exists(image_field.path)
        return False
    
    def clean_book_titles(self, dry_run):
        """Clean up mangled book titles from Kaggle import"""
        self.stdout.write('Checking for mangled book titles...')
        
        fixed_count = 0
        for book in Book.objects.all():
            if self.is_likely_kaggle_item(book.title):
                old_title = book.title
                new_title = self.clean_name(old_title)
                
                self.stdout.write(f'  Found mangled title: {old_title[:50]}...')
                self.stdout.write(f'  Will fix to: {new_title}')
                
                if not dry_run:
                    book.title = new_title
                    book.save(update_fields=['title'])
                    fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} book titles'))
        else:
            self.stdout.write('No mangled book titles found')
    
    def clean_author_names(self, dry_run):
        """Clean up mangled author names from Kaggle import"""
        self.stdout.write('Checking for mangled author names...')
        
        fixed_count = 0
        for author in Author.objects.all():
            if self.is_likely_kaggle_item(author.name):
                old_name = author.name
                new_name = self.clean_name(old_name)
                
                self.stdout.write(f'  Found mangled author name: {old_name[:50]}...')
                self.stdout.write(f'  Will fix to: {new_name}')
                
                if not dry_run:
                    author.name = new_name
                    author.save(update_fields=['name'])
                    fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} author names'))
        else:
            self.stdout.write('No mangled author names found')
    
    def clean_publisher_names(self, dry_run):
        """Clean up mangled publisher names from Kaggle import"""
        self.stdout.write('Checking for mangled publisher names...')
        
        fixed_count = 0
        for publisher in Publisher.objects.all():
            if self.is_likely_kaggle_item(publisher.name):
                old_name = publisher.name
                new_name = self.clean_name(old_name)
                
                self.stdout.write(f'  Found mangled publisher name: {old_name[:50]}...')
                self.stdout.write(f'  Will fix to: {new_name}')
                
                if not dry_run:
                    publisher.name = new_name
                    publisher.save(update_fields=['name'])
                    fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} publisher names'))
        else:
            self.stdout.write('No mangled publisher names found')
    
    def reset_invalid_book_covers(self, dry_run):
        """Reset invalid book cover paths"""
        self.stdout.write('Checking for books with invalid cover paths...')
        
        reset_count = 0
        for book in Book.objects.all():
            if book.cover and not self.check_image_exists(book.cover):
                self.stdout.write(f'  Book has invalid cover path: {book.title} (path: {book.cover})')
                
                if not dry_run:
                    book.cover = None
                    book.save(update_fields=['cover'])
                    reset_count += 1
        
        if reset_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Reset {reset_count} invalid book cover paths'))
        else:
            self.stdout.write('No invalid book cover paths found')
    
    def reset_invalid_author_photos(self, dry_run):
        """Reset invalid author photo paths"""
        self.stdout.write('Checking for authors with invalid photo paths...')
        
        reset_count = 0
        for author in Author.objects.all():
            if author.photo and not self.check_image_exists(author.photo):
                self.stdout.write(f'  Author has invalid photo path: {author.name} (path: {author.photo})')
                
                if not dry_run:
                    author.photo = None
                    author.save(update_fields=['photo'])
                    reset_count += 1
        
        if reset_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Reset {reset_count} invalid author photo paths'))
        else:
            self.stdout.write('No invalid author photo paths found')
    
    def reset_invalid_publisher_logos(self, dry_run):
        """Reset invalid publisher logo paths"""
        self.stdout.write('Checking for publishers with invalid logo paths...')
        
        reset_count = 0
        for publisher in Publisher.objects.all():
            if publisher.logo and not self.check_image_exists(publisher.logo):
                self.stdout.write(f'  Publisher has invalid logo path: {publisher.name} (path: {publisher.logo})')
                
                if not dry_run:
                    publisher.logo = None
                    publisher.save(update_fields=['logo'])
                    reset_count += 1
        
        if reset_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Reset {reset_count} invalid publisher logo paths'))
        else:
            self.stdout.write('No invalid publisher logo paths found')
    
    def generate_book_covers(self, batch_size, pause_seconds, fallback):
        """Generate book covers for books without images"""
        self.stdout.write('Checking for books without covers...')
        
        # Find books without covers
        books_without_covers = Book.objects.filter(Q(cover__isnull=True) | Q(cover=''))
        count = books_without_covers.count()
        self.stdout.write(f'Found {count} books without covers')
        
        # Generate covers in batches
        for i, book in enumerate(books_without_covers):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} books, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Create a filename for the cover
                # Sanitize the title to avoid invalid characters in filenames
                safe_title = self.sanitize_filename(book.title)
                filename = f"{book.id}_{safe_title[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                covers_dir = os.path.join(media_root, 'covers')
                os.makedirs(covers_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(covers_dir, filename)
                
                # Generate the prompt
                authors = ", ".join([author.name for author in book.authors.all()])
                if not authors:
                    authors = "Unknown Author"
                
                prompt = f"A professional book cover for '{book.title}' by {authors}. High quality, detailed, publishing industry standard."
                
                self.stdout.write(f'  Generating cover for book: {book.title}')
                
                # Generate the image using flux_wrapper.py with correct parameters
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
                
                # Add fallback flag if requested
                if fallback:
                    cmd.append("--fallback")
                
                self.stdout.write(f'    Running command: {" ".join(cmd)}')
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0 and os.path.exists(output_path)
                
                if success and os.path.exists(output_path):
                    # Update the book model with the new cover
                    relative_path = os.path.join('covers', filename)
                    book.cover = relative_path
                    book.save(update_fields=['cover'])
                    self.stdout.write(self.style.SUCCESS(f'    Successfully generated cover for book: {book.title}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to generate cover for book: {book.title}'))
                    if result.stderr:
                        self.stdout.write(f'    Error: {result.stderr[:200]}...')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating cover for book {book.id}: {str(e)}'))
    
    def generate_author_photos(self, batch_size, pause_seconds, fallback):
        """Generate author photos for authors without images"""
        self.stdout.write('Checking for authors without photos...')
        
        # Find authors without photos
        authors_without_photos = Author.objects.filter(Q(photo__isnull=True) | Q(photo=''))
        count = authors_without_photos.count()
        self.stdout.write(f'Found {count} authors without photos')
        
        # Generate photos in batches
        for i, author in enumerate(authors_without_photos):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} authors, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Create a filename for the portrait
                # Sanitize the name to avoid invalid characters in filenames
                safe_name = self.sanitize_filename(author.name)
                filename = f"{author.id}_{safe_name[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                authors_dir = os.path.join(media_root, 'authors')
                os.makedirs(authors_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(authors_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional portrait photograph of author {author.name}. High quality, detailed, professional headshot."
                
                self.stdout.write(f'  Generating photo for author: {author.name}')
                
                # Generate the image using flux_wrapper.py with correct parameters
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
                
                # Add fallback flag if requested
                if fallback:
                    cmd.append("--fallback")
                
                self.stdout.write(f'    Running command: {" ".join(cmd)}')
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0 and os.path.exists(output_path)
                
                if success and os.path.exists(output_path):
                    # Update the author model with the new photo
                    relative_path = os.path.join('authors', filename)
                    author.photo = relative_path
                    author.save(update_fields=['photo'])
                    self.stdout.write(self.style.SUCCESS(f'    Successfully generated photo for author: {author.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to generate photo for author: {author.name}'))
                    if result.stderr:
                        self.stdout.write(f'    Error: {result.stderr[:200]}...')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating photo for author {author.id}: {str(e)}'))
    
    def generate_publisher_logos(self, batch_size, pause_seconds, fallback):
        """Generate publisher logos for publishers without images"""
        self.stdout.write('Checking for publishers without logos...')
        
        # Find publishers without logos
        publishers_without_logos = Publisher.objects.filter(Q(logo__isnull=True) | Q(logo=''))
        count = publishers_without_logos.count()
        self.stdout.write(f'Found {count} publishers without logos')
        
        # Generate logos in batches
        for i, publisher in enumerate(publishers_without_logos):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} publishers, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Create a filename for the logo
                # Sanitize the name to avoid invalid characters in filenames
                safe_name = self.sanitize_filename(publisher.name)
                filename = f"{publisher.id}_{safe_name[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                publishers_dir = os.path.join(media_root, 'publishers')
                os.makedirs(publishers_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(publishers_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional logo for publishing company '{publisher.name}'. Clean, corporate design, minimalist, high quality."
                
                self.stdout.write(f'  Generating logo for publisher: {publisher.name}')
                
                # Generate the image using flux_wrapper.py with correct parameters
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
                
                # Add fallback flag if requested
                if fallback:
                    cmd.append("--fallback")
                
                self.stdout.write(f'    Running command: {" ".join(cmd)}')
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0 and os.path.exists(output_path)
                
                if success and os.path.exists(output_path):
                    # Update the publisher model with the new logo
                    relative_path = os.path.join('publishers', filename)
                    publisher.logo = relative_path
                    publisher.save(update_fields=['logo'])
                    self.stdout.write(self.style.SUCCESS(f'    Successfully generated logo for publisher: {publisher.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to generate logo for publisher: {publisher.name}'))
                    if result.stderr:
                        self.stdout.write(f'    Error: {result.stderr[:200]}...')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating logo for publisher {publisher.id}: {str(e)}'))

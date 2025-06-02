import os
import re
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction, models
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Generate images for Kaggle-imported books, authors, and publishers using Flux AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=3,
            help='Number of images to generate in one batch before pausing'
        )
        parser.add_argument(
            '--pause-seconds',
            type=int,
            default=5,
            help='Seconds to pause between batches'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['books', 'authors', 'publishers', 'all'],
            default='all',
            help='Type of images to generate'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit the number of items to process (0 for all)'
        )
        parser.add_argument(
            '--force-fallback',
            action='store_true',
            help='Force fallback to basic image generation'
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check if Flux AI is available, do not generate images'
        )
        parser.add_argument(
            '--kaggle-only',
            action='store_true',
            default=False,
            help='Only process items that appear to be from Kaggle dataset'
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Force regeneration of all images, even if they already exist'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        pause_seconds = options['pause_seconds']
        image_type = options['type']
        limit = options['limit']
        force_fallback = options['force_fallback']
        check_only = options['check_only']
        kaggle_only = options.get('kaggle_only', False)
        force_all = options.get('force_all', False)
        
        # Check if Flux AI is available
        flux_available = self.check_flux_availability()
        
        if check_only:
            if flux_available:
                self.stdout.write(self.style.SUCCESS('Flux AI is available'))
            else:
                self.stdout.write(self.style.ERROR('Flux AI is not available'))
            return
        
        if not flux_available:
            self.stdout.write(self.style.WARNING('Flux AI is not available, using fallback image generation'))
            force_fallback = True
        
        if image_type in ['books', 'all']:
            self.generate_book_covers(batch_size, pause_seconds, limit, force_fallback, kaggle_only, force_all)
        
        if image_type in ['authors', 'all']:
            self.generate_author_photos(batch_size, pause_seconds, limit, force_fallback, kaggle_only, force_all)
        
        if image_type in ['publishers', 'all']:
            self.generate_publisher_logos(batch_size, pause_seconds, limit, force_fallback, kaggle_only, force_all)
    
    def check_flux_availability(self):
        """Check if Flux AI is available by running a test command"""
        try:
            # Check if flux_wrapper.py exists
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            if not os.path.exists(flux_wrapper_path):
                self.stdout.write(self.style.WARNING(f'Flux wrapper script not found at {flux_wrapper_path}'))
                return False
            
            self.stdout.write('Flux AI appears to be available')
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking Flux availability: {str(e)}'))
            return False
    
    def is_likely_kaggle_item(self, name):
        """Check if an item name appears to be from Kaggle dataset"""
        # Look for patterns that indicate Kaggle data
        # For example, CSV-like data with semicolons, quotes, or multiple fields
        if not name:
            return False
        
        # Check for CSV-like format with semicolons
        if ';' in name and name.count(';') >= 1:
            return True
        
        # Check for excessive quotes which might indicate CSV data
        if name.count('"') > 2:
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
            return parts[0].strip().strip('"\'')
            
        return name
    
    def generate_book_covers(self, batch_size, pause_seconds, limit, force_fallback, kaggle_only, force_all):
        """Generate book covers for books without images or all books if force_all is True"""
        self.stdout.write('Checking for books that need covers...')
        
        if force_all:
            # Process all books regardless of whether they have covers
            books = Book.objects.all()
            self.stdout.write('Force processing all books regardless of existing covers')
        else:
            # Find books without covers or with empty cover field
            books = Book.objects.filter(models.Q(cover__isnull=True) | models.Q(cover=''))
        
        # If kaggle_only is True, filter to only include books that look like Kaggle imports
        if kaggle_only:
            kaggle_books = []
            for book in books:
                if self.is_likely_kaggle_item(book.title):
                    kaggle_books.append(book.id)
            
            if kaggle_books:
                books = books.filter(id__in=kaggle_books)
                self.stdout.write(f'Filtered to {len(kaggle_books)} books that appear to be from Kaggle')
            else:
                self.stdout.write('No books appear to be from Kaggle dataset')
        
        count = books.count()
        self.stdout.write(f'Found {count} books to process')
        
        if limit > 0 and limit < count:
            books = books[:limit]
            self.stdout.write(f'Limiting to {limit} books')
        
        # Generate covers in batches
        for i, book in enumerate(books):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} books, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Clean up the book title if needed
                if self.is_likely_kaggle_item(book.title):
                    clean_title = self.clean_name(book.title)
                    self.stdout.write(f'  Cleaned title: {book.title[:50]}... -> {clean_title}')
                    book.title = clean_title
                    book.save(update_fields=['title'])
                
                # Create a filename for the cover
                filename = f"{book.id}_{self.sanitize_filename(book.title)[:30]}.jpg"
                
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
                
                # Generate the image using flux_wrapper.py
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
                
                # Add fallback flag if requested
                if force_fallback:
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
    
    def generate_author_photos(self, batch_size, pause_seconds, limit, force_fallback, kaggle_only, force_all):
        """Generate author photos for authors without images or all authors if force_all is True"""
        self.stdout.write('Checking for authors that need photos...')
        
        if force_all:
            # Process all authors regardless of whether they have photos
            authors = Author.objects.all()
            self.stdout.write('Force processing all authors regardless of existing photos')
        else:
            # Find authors without photos or with empty photo field
            authors = Author.objects.filter(models.Q(photo__isnull=True) | models.Q(photo=''))
        
        # If kaggle_only is True, filter to only include authors that look like Kaggle imports
        if kaggle_only:
            kaggle_authors = []
            for author in authors:
                if self.is_likely_kaggle_item(author.name):
                    kaggle_authors.append(author.id)
            
            if kaggle_authors:
                authors = authors.filter(id__in=kaggle_authors)
                self.stdout.write(f'Filtered to {len(kaggle_authors)} authors that appear to be from Kaggle')
            else:
                self.stdout.write('No authors appear to be from Kaggle dataset')
        
        count = authors.count()
        self.stdout.write(f'Found {count} authors to process')
        
        if limit > 0 and limit < count:
            authors = authors[:limit]
            self.stdout.write(f'Limiting to {limit} authors')
        
        # Generate photos in batches
        for i, author in enumerate(authors):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} authors, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Clean up the author name if needed
                if self.is_likely_kaggle_item(author.name):
                    clean_name = self.clean_name(author.name)
                    self.stdout.write(f'  Cleaned name: {author.name[:50]}... -> {clean_name}')
                    author.name = clean_name
                    author.save(update_fields=['name'])
                
                # Create a filename for the portrait
                filename = f"{author.id}_{self.sanitize_filename(author.name)[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                authors_dir = os.path.join(media_root, 'authors')
                os.makedirs(authors_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(authors_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional portrait photograph of author {author.name}. High quality, detailed, professional headshot."
                
                self.stdout.write(f'  Generating photo for author: {author.name}')
                
                # Generate the image using flux_wrapper.py
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
                
                # Add fallback flag if requested
                if force_fallback:
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
    
    def generate_publisher_logos(self, batch_size, pause_seconds, limit, force_fallback, kaggle_only, force_all):
        """Generate publisher logos for publishers without images or all publishers if force_all is True"""
        self.stdout.write('Checking for publishers that need logos...')
        
        if force_all:
            # Process all publishers regardless of whether they have logos
            publishers = Publisher.objects.all()
            self.stdout.write('Force processing all publishers regardless of existing logos')
        else:
            # Find publishers without logos or with empty logo field
            publishers = Publisher.objects.filter(models.Q(logo__isnull=True) | models.Q(logo=''))
        
        # If kaggle_only is True, filter to only include publishers that look like Kaggle imports
        if kaggle_only:
            kaggle_publishers = []
            for publisher in publishers:
                if self.is_likely_kaggle_item(publisher.name):
                    kaggle_publishers.append(publisher.id)
            
            if kaggle_publishers:
                publishers = publishers.filter(id__in=kaggle_publishers)
                self.stdout.write(f'Filtered to {len(kaggle_publishers)} publishers that appear to be from Kaggle')
            else:
                self.stdout.write('No publishers appear to be from Kaggle dataset')
        
        count = publishers.count()
        self.stdout.write(f'Found {count} publishers to process')
        
        if limit > 0 and limit < count:
            publishers = publishers[:limit]
            self.stdout.write(f'Limiting to {limit} publishers')
        
        # Generate logos in batches
        for i, publisher in enumerate(publishers):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} publishers, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Clean up the publisher name if needed
                if self.is_likely_kaggle_item(publisher.name):
                    clean_name = self.clean_name(publisher.name)
                    self.stdout.write(f'  Cleaned name: {publisher.name[:50]}... -> {clean_name}')
                    publisher.name = clean_name
                    publisher.save(update_fields=['name'])
                
                # Create a filename for the logo
                filename = f"{publisher.id}_{self.sanitize_filename(publisher.name)[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                publishers_dir = os.path.join(media_root, 'publishers')
                os.makedirs(publishers_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(publishers_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional logo for publishing company '{publisher.name}'. Clean, corporate design, minimalist, high quality."
                
                self.stdout.write(f'  Generating logo for publisher: {publisher.name}')
                
                # Generate the image using flux_wrapper.py
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
                
                # Add fallback flag if requested
                if force_fallback:
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

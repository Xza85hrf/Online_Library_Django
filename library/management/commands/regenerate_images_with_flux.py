import os
import re
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Regenerate images for books, authors, and publishers using Flux AI'

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
            help='Type of images to regenerate'
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

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        pause_seconds = options['pause_seconds']
        image_type = options['type']
        limit = options['limit']
        force_fallback = options['force_fallback']
        check_only = options['check_only']
        
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
            self.regenerate_book_covers(batch_size, pause_seconds, limit, force_fallback)
        
        if image_type in ['authors', 'all']:
            self.regenerate_author_photos(batch_size, pause_seconds, limit, force_fallback)
        
        if image_type in ['publishers', 'all']:
            self.regenerate_publisher_logos(batch_size, pause_seconds, limit, force_fallback)
    
    def check_flux_availability(self):
        """Check if Flux AI is available by running a test command"""
        try:
            # Check if conda is available
            conda_result = subprocess.run(["conda", "--version"], capture_output=True, text=True)
            if conda_result.returncode != 0:
                self.stdout.write(self.style.WARNING('Conda is not available'))
                return False
            
            # Check if flux environment exists
            env_result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True)
            if "flux" not in env_result.stdout:
                self.stdout.write(self.style.WARNING('Flux conda environment not found'))
                return False
            
            # Check direct_flux_generator.py
            flux_script_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'direct_flux_generator.py')
            if not os.path.exists(flux_script_path):
                self.stdout.write(self.style.WARNING(f'Direct Flux generator script not found at {flux_script_path}'))
                return False
            
            self.stdout.write('Flux AI appears to be available')
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking Flux availability: {str(e)}'))
            return False
    
    def regenerate_book_covers(self, batch_size, pause_seconds, limit, force_fallback):
        """Regenerate book covers"""
        self.stdout.write('Checking for books to regenerate covers...')
        
        # Get all books
        books = Book.objects.all()
        count = books.count()
        self.stdout.write(f'Found {count} books')
        
        if limit > 0 and limit < count:
            books = books[:limit]
            self.stdout.write(f'Limiting to {limit} books')
        
        # Generate covers in batches
        for i, book in enumerate(books):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} books, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Create a filename for the cover
                filename = f"{book.id}_{self._sanitize_filename(book.title)[:30]}.jpg"
                
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
                
                self.stdout.write(f'  Regenerating cover for book: {book.title}')
                
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
                    self.stdout.write(self.style.SUCCESS(f'    Successfully regenerated cover for book: {book.title}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to regenerate cover for book: {book.title}'))
                    if result.stderr:
                        self.stdout.write(f'    Error: {result.stderr[:200]}...')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error regenerating cover for book {book.id}: {str(e)}'))
    
    def regenerate_author_photos(self, batch_size, pause_seconds, limit, force_fallback):
        """Regenerate author photos"""
        self.stdout.write('Checking for authors to regenerate photos...')
        
        # Get all authors
        authors = Author.objects.all()
        count = authors.count()
        self.stdout.write(f'Found {count} authors')
        
        if limit > 0 and limit < count:
            authors = authors[:limit]
            self.stdout.write(f'Limiting to {limit} authors')
        
        # Generate photos in batches
        for i, author in enumerate(authors):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} authors, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Create a filename for the portrait
                filename = f"{author.id}_{self._sanitize_filename(author.name)[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                authors_dir = os.path.join(media_root, 'authors')
                os.makedirs(authors_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(authors_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional portrait photograph of author {author.name}. High quality, detailed, professional headshot."
                
                self.stdout.write(f'  Regenerating photo for author: {author.name}')
                
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
                    self.stdout.write(self.style.SUCCESS(f'    Successfully regenerated photo for author: {author.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to regenerate photo for author: {author.name}'))
                    if result.stderr:
                        self.stdout.write(f'    Error: {result.stderr[:200]}...')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error regenerating photo for author {author.id}: {str(e)}'))
    
    def regenerate_publisher_logos(self, batch_size, pause_seconds, limit, force_fallback):
        """Regenerate publisher logos"""
        self.stdout.write('Checking for publishers to regenerate logos...')
        
        # Get all publishers
        publishers = Publisher.objects.all()
        count = publishers.count()
        self.stdout.write(f'Found {count} publishers')
        
        if limit > 0 and limit < count:
            publishers = publishers[:limit]
            self.stdout.write(f'Limiting to {limit} publishers')
        
        # Generate logos in batches
        for i, publisher in enumerate(publishers):
            if i > 0 and i % batch_size == 0:
                self.stdout.write(f'Processed {i}/{count} publishers, pausing for {pause_seconds} seconds...')
                time.sleep(pause_seconds)
            
            try:
                # Create a filename for the logo
                filename = f"{publisher.id}_{self._sanitize_filename(publisher.name)[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                publishers_dir = os.path.join(media_root, 'publishers')
                os.makedirs(publishers_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(publishers_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional logo for publishing company '{publisher.name}'. Clean, corporate design, minimalist, high quality."
                
                self.stdout.write(f'  Regenerating logo for publisher: {publisher.name}')
                
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
                    self.stdout.write(self.style.SUCCESS(f'    Successfully regenerated logo for publisher: {publisher.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to regenerate logo for publisher: {publisher.name}'))
                    if result.stderr:
                        self.stdout.write(f'    Error: {result.stderr[:200]}...')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error regenerating logo for publisher {publisher.id}: {str(e)}'))
    
    def _sanitize_filename(self, filename):
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

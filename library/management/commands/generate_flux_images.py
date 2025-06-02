import os
import re
import subprocess
import time
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Generate high-quality images using Flux AI for books, authors, and publishers'

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
            default=10,
            help='Seconds to pause between batches to allow GPU memory to clear'
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
            '--width',
            type=int,
            default=512,
            help='Width of generated images'
        )
        parser.add_argument(
            '--height',
            type=int,
            default=512,
            help='Height of generated images'
        )
        parser.add_argument(
            '--steps',
            type=int,
            default=4,
            help='Number of inference steps'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        pause_seconds = options['pause_seconds']
        image_type = options['type']
        limit = options['limit']
        width = options['width']
        height = options['height']
        steps = options['steps']
        
        # First run the update_flux_environment.bat if it exists
        self.update_flux_environment()
        
        if image_type in ['books', 'all']:
            self.generate_book_covers(batch_size, pause_seconds, limit, width, height, steps)
        
        if image_type in ['authors', 'all']:
            self.generate_author_photos(batch_size, pause_seconds, limit, width, height, steps)
        
        if image_type in ['publishers', 'all']:
            self.generate_publisher_logos(batch_size, pause_seconds, limit, width, height, steps)
    
    def update_flux_environment(self):
        """Run the update_flux_environment.bat script if it exists"""
        update_script = os.path.join(settings.BASE_DIR, 'update_flux_environment.bat')
        if os.path.exists(update_script):
            self.stdout.write('Running Flux environment update script...')
            try:
                subprocess.run([update_script], shell=True, check=True)
                self.stdout.write(self.style.SUCCESS('Flux environment updated successfully'))
            except subprocess.CalledProcessError:
                self.stdout.write(self.style.ERROR('Failed to update Flux environment'))
        else:
            self.stdout.write(self.style.WARNING('Flux environment update script not found'))
    
    def generate_book_covers(self, batch_size, pause_seconds, limit, width, height, steps):
        """Generate book covers using Flux AI"""
        self.stdout.write('Checking for books without covers...')
        
        # Get books without covers
        books_without_covers = Book.objects.filter(cover__isnull=True) | Book.objects.filter(cover='')
        count = books_without_covers.count()
        self.stdout.write(f'Found {count} books without covers')
        
        if limit > 0 and limit < count:
            books_without_covers = books_without_covers[:limit]
            self.stdout.write(f'Limiting to {limit} books')
        
        # Generate covers in batches
        for i, book in enumerate(books_without_covers):
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
                
                self.stdout.write(f'  Generating cover for book: {book.title}')
                
                # Generate the image using direct_flux_generator.py
                flux_script_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'direct_flux_generator.py')
                
                # Generate a seed for reproducibility
                seed = random.randint(1, 1000000)
                
                # Set environment variables for CUDA memory management
                env = os.environ.copy()
                env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
                env["CUDA_VISIBLE_DEVICES"] = "0"
                
                # Run the direct_flux_generator.py script in the flux conda environment
                cmd = [
                    "conda", "run", "-n", "flux", "python", flux_script_path,
                    "--prompt", prompt,
                    "--output", output_path,
                    "--seed", str(seed)
                ]
                
                self.stdout.write(f'    Running command: {" ".join(cmd)}')
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
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
                        
                        # Fall back to using flux_wrapper.py with fallback option
                        self.stdout.write('    Falling back to basic image generation...')
                        fallback_cmd = [
                            "python", os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py'),
                            "--prompt", prompt,
                            "--output", output_path,
                            "--fallback"
                        ]
                        
                        fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                        fallback_success = fallback_result.returncode == 0 and os.path.exists(output_path)
                        
                        if fallback_success and os.path.exists(output_path):
                            # Update the book model with the new cover
                            relative_path = os.path.join('covers', filename)
                            book.cover = relative_path
                            book.save(update_fields=['cover'])
                            self.stdout.write(self.style.SUCCESS(f'    Successfully generated fallback cover for book: {book.title}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'    Failed to generate fallback cover for book: {book.title}'))
                
                except subprocess.TimeoutExpired:
                    self.stdout.write(self.style.ERROR(f'    Timeout while generating cover for book: {book.title}'))
                    
                    # Fall back to using flux_wrapper.py with fallback option
                    self.stdout.write('    Falling back to basic image generation...')
                    fallback_cmd = [
                        "python", os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py'),
                        "--prompt", prompt,
                        "--output", output_path,
                        "--fallback"
                    ]
                    
                    fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                    fallback_success = fallback_result.returncode == 0 and os.path.exists(output_path)
                    
                    if fallback_success and os.path.exists(output_path):
                        # Update the book model with the new cover
                        relative_path = os.path.join('covers', filename)
                        book.cover = relative_path
                        book.save(update_fields=['cover'])
                        self.stdout.write(self.style.SUCCESS(f'    Successfully generated fallback cover for book: {book.title}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'    Failed to generate fallback cover for book: {book.title}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating cover for book {book.id}: {str(e)}'))
    
    def generate_author_photos(self, batch_size, pause_seconds, limit, width, height, steps):
        """Generate author photos using Flux AI"""
        self.stdout.write('Checking for authors without photos...')
        
        # Get authors without photos
        authors_without_photos = Author.objects.filter(photo__isnull=True) | Author.objects.filter(photo='')
        count = authors_without_photos.count()
        self.stdout.write(f'Found {count} authors without photos')
        
        if limit > 0 and limit < count:
            authors_without_photos = authors_without_photos[:limit]
            self.stdout.write(f'Limiting to {limit} authors')
        
        # Generate photos in batches
        for i, author in enumerate(authors_without_photos):
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
                
                self.stdout.write(f'  Generating photo for author: {author.name}')
                
                # Generate the image using direct_flux_generator.py
                flux_script_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'direct_flux_generator.py')
                
                # Generate a seed for reproducibility
                seed = random.randint(1, 1000000)
                
                # Set environment variables for CUDA memory management
                env = os.environ.copy()
                env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
                env["CUDA_VISIBLE_DEVICES"] = "0"
                
                # Run the direct_flux_generator.py script in the flux conda environment
                cmd = [
                    "conda", "run", "-n", "flux", "python", flux_script_path,
                    "--prompt", prompt,
                    "--output", output_path,
                    "--seed", str(seed)
                ]
                
                self.stdout.write(f'    Running command: {" ".join(cmd)}')
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
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
                        
                        # Fall back to using flux_wrapper.py with fallback option
                        self.stdout.write('    Falling back to basic image generation...')
                        fallback_cmd = [
                            "python", os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py'),
                            "--prompt", prompt,
                            "--output", output_path,
                            "--fallback"
                        ]
                        
                        fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                        fallback_success = fallback_result.returncode == 0 and os.path.exists(output_path)
                        
                        if fallback_success and os.path.exists(output_path):
                            # Update the author model with the new photo
                            relative_path = os.path.join('authors', filename)
                            author.photo = relative_path
                            author.save(update_fields=['photo'])
                            self.stdout.write(self.style.SUCCESS(f'    Successfully generated fallback photo for author: {author.name}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'    Failed to generate fallback photo for author: {author.name}'))
                
                except subprocess.TimeoutExpired:
                    self.stdout.write(self.style.ERROR(f'    Timeout while generating photo for author: {author.name}'))
                    
                    # Fall back to using flux_wrapper.py with fallback option
                    self.stdout.write('    Falling back to basic image generation...')
                    fallback_cmd = [
                        "python", os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py'),
                        "--prompt", prompt,
                        "--output", output_path,
                        "--fallback"
                    ]
                    
                    fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                    fallback_success = fallback_result.returncode == 0 and os.path.exists(output_path)
                    
                    if fallback_success and os.path.exists(output_path):
                        # Update the author model with the new photo
                        relative_path = os.path.join('authors', filename)
                        author.photo = relative_path
                        author.save(update_fields=['photo'])
                        self.stdout.write(self.style.SUCCESS(f'    Successfully generated fallback photo for author: {author.name}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'    Failed to generate fallback photo for author: {author.name}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating photo for author {author.id}: {str(e)}'))
    
    def generate_publisher_logos(self, batch_size, pause_seconds, limit, width, height, steps):
        """Generate publisher logos using Flux AI"""
        self.stdout.write('Checking for publishers without logos...')
        
        # Get publishers without logos
        publishers_without_logos = Publisher.objects.filter(logo__isnull=True) | Publisher.objects.filter(logo='')
        count = publishers_without_logos.count()
        self.stdout.write(f'Found {count} publishers without logos')
        
        if limit > 0 and limit < count:
            publishers_without_logos = publishers_without_logos[:limit]
            self.stdout.write(f'Limiting to {limit} publishers')
        
        # Generate logos in batches
        for i, publisher in enumerate(publishers_without_logos):
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
                
                self.stdout.write(f'  Generating logo for publisher: {publisher.name}')
                
                # Generate the image using direct_flux_generator.py
                flux_script_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'direct_flux_generator.py')
                
                # Generate a seed for reproducibility
                seed = random.randint(1, 1000000)
                
                # Set environment variables for CUDA memory management
                env = os.environ.copy()
                env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
                env["CUDA_VISIBLE_DEVICES"] = "0"
                
                # Run the direct_flux_generator.py script in the flux conda environment
                cmd = [
                    "conda", "run", "-n", "flux", "python", flux_script_path,
                    "--prompt", prompt,
                    "--output", output_path,
                    "--seed", str(seed)
                ]
                
                self.stdout.write(f'    Running command: {" ".join(cmd)}')
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
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
                        
                        # Fall back to using flux_wrapper.py with fallback option
                        self.stdout.write('    Falling back to basic image generation...')
                        fallback_cmd = [
                            "python", os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py'),
                            "--prompt", prompt,
                            "--output", output_path,
                            "--fallback"
                        ]
                        
                        fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                        fallback_success = fallback_result.returncode == 0 and os.path.exists(output_path)
                        
                        if fallback_success and os.path.exists(output_path):
                            # Update the publisher model with the new logo
                            relative_path = os.path.join('publishers', filename)
                            publisher.logo = relative_path
                            publisher.save(update_fields=['logo'])
                            self.stdout.write(self.style.SUCCESS(f'    Successfully generated fallback logo for publisher: {publisher.name}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'    Failed to generate fallback logo for publisher: {publisher.name}'))
                
                except subprocess.TimeoutExpired:
                    self.stdout.write(self.style.ERROR(f'    Timeout while generating logo for publisher: {publisher.name}'))
                    
                    # Fall back to using flux_wrapper.py with fallback option
                    self.stdout.write('    Falling back to basic image generation...')
                    fallback_cmd = [
                        "python", os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py'),
                        "--prompt", prompt,
                        "--output", output_path,
                        "--fallback"
                    ]
                    
                    fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                    fallback_success = fallback_result.returncode == 0 and os.path.exists(output_path)
                    
                    if fallback_success and os.path.exists(output_path):
                        # Update the publisher model with the new logo
                        relative_path = os.path.join('publishers', filename)
                        publisher.logo = relative_path
                        publisher.save(update_fields=['logo'])
                        self.stdout.write(self.style.SUCCESS(f'    Successfully generated fallback logo for publisher: {publisher.name}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'    Failed to generate fallback logo for publisher: {publisher.name}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating logo for publisher {publisher.id}: {str(e)}'))
    
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

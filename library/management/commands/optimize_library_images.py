import os
import re
import subprocess
from PIL import Image
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Optimize and manage library images for better performance and quality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['books', 'authors', 'publishers', 'all'],
            default='all',
            help='Type of images to optimize'
        )
        parser.add_argument(
            '--resize',
            action='store_true',
            help='Resize images to optimal dimensions'
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Optimize image file size'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify all image paths in database'
        )
        parser.add_argument(
            '--regenerate-missing',
            action='store_true',
            help='Regenerate missing images'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        image_type = options['type']
        resize = options['resize']
        optimize = options['optimize']
        verify = options['verify']
        regenerate_missing = options['regenerate_missing']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        # If no specific action is selected, do all
        if not any([resize, optimize, verify, regenerate_missing]):
            resize = optimize = verify = regenerate_missing = True
        
        if verify:
            self.verify_image_paths(image_type, dry_run)
        
        if resize or optimize:
            self.optimize_images(image_type, resize, optimize, dry_run)
        
        if regenerate_missing:
            self.regenerate_missing_images(image_type, dry_run)
        
        self.stdout.write(self.style.SUCCESS('Image management completed!'))
    
    def verify_image_paths(self, image_type, dry_run):
        """Verify all image paths in the database and fix any issues"""
        self.stdout.write('Verifying image paths in database...')
        
        fixed_count = 0
        
        # Verify book covers
        if image_type in ['books', 'all']:
            self.stdout.write('Checking book cover paths...')
            books = Book.objects.all()
            
            for book in books:
                if not book.cover:
                    continue
                    
                # Check if the file exists
                if not os.path.exists(os.path.join(settings.MEDIA_ROOT, str(book.cover))):
                    self.stdout.write(f'  Book ID {book.id}: "{book.title}" has invalid cover path: {book.cover}')
                    
                    if not dry_run:
                        # Clear the invalid path
                        book.cover = None
                        book.save(update_fields=['cover'])
                        fixed_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Cleared invalid cover path'))
        
        # Verify author photos
        if image_type in ['authors', 'all']:
            self.stdout.write('Checking author photo paths...')
            authors = Author.objects.all()
            
            for author in authors:
                if not author.photo:
                    continue
                    
                # Check if the file exists
                if not os.path.exists(os.path.join(settings.MEDIA_ROOT, str(author.photo))):
                    self.stdout.write(f'  Author ID {author.id}: "{author.name}" has invalid photo path: {author.photo}')
                    
                    if not dry_run:
                        # Clear the invalid path
                        author.photo = None
                        author.save(update_fields=['photo'])
                        fixed_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Cleared invalid photo path'))
        
        # Verify publisher logos
        if image_type in ['publishers', 'all']:
            self.stdout.write('Checking publisher logo paths...')
            publishers = Publisher.objects.all()
            
            for publisher in publishers:
                if not publisher.logo:
                    continue
                    
                # Check if the file exists
                if not os.path.exists(os.path.join(settings.MEDIA_ROOT, str(publisher.logo))):
                    self.stdout.write(f'  Publisher ID {publisher.id}: "{publisher.name}" has invalid logo path: {publisher.logo}')
                    
                    if not dry_run:
                        # Clear the invalid path
                        publisher.logo = None
                        publisher.save(update_fields=['logo'])
                        fixed_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Cleared invalid logo path'))
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} invalid image paths'))
        else:
            self.stdout.write('No invalid image paths found')
    
    def optimize_images(self, image_type, resize, optimize, dry_run):
        """Optimize images for better performance"""
        self.stdout.write('Optimizing images...')
        
        # Define optimal dimensions
        book_cover_size = (512, 768)  # Portrait orientation for book covers
        author_photo_size = (512, 512)  # Square for author photos
        publisher_logo_size = (512, 512)  # Square for publisher logos
        
        optimized_count = 0
        
        # Optimize book covers
        if image_type in ['books', 'all']:
            self.stdout.write('Processing book covers...')
            books = Book.objects.exclude(Q(cover__isnull=True) | Q(cover=''))
            
            for book in books:
                try:
                    image_path = os.path.join(settings.MEDIA_ROOT, str(book.cover))
                    
                    if not os.path.exists(image_path):
                        continue
                    
                    # Open the image
                    img = Image.open(image_path)
                    original_size = os.path.getsize(image_path)
                    
                    modified = False
                    
                    # Resize if needed
                    if resize and (img.width > book_cover_size[0] or img.height > book_cover_size[1]):
                        self.stdout.write(f'  Resizing cover for book ID {book.id}: "{book.title}"')
                        self.stdout.write(f'    Original size: {img.width}x{img.height}')
                        
                        # Resize while maintaining aspect ratio
                        img.thumbnail(book_cover_size, Image.LANCZOS)
                        self.stdout.write(f'    New size: {img.width}x{img.height}')
                        modified = True
                    
                    # Optimize file size
                    if optimize:
                        self.stdout.write(f'  Optimizing cover for book ID {book.id}: "{book.title}"')
                        self.stdout.write(f'    Original file size: {original_size / 1024:.1f} KB')
                        modified = True
                    
                    # Save the optimized image
                    if modified and not dry_run:
                        img.save(image_path, optimize=True, quality=85)
                        new_size = os.path.getsize(image_path)
                        self.stdout.write(f'    New file size: {new_size / 1024:.1f} KB')
                        self.stdout.write(self.style.SUCCESS(f'    Saved optimized image'))
                        optimized_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error processing image: {str(e)}'))
        
        # Optimize author photos
        if image_type in ['authors', 'all']:
            self.stdout.write('Processing author photos...')
            authors = Author.objects.exclude(Q(photo__isnull=True) | Q(photo=''))
            
            for author in authors:
                try:
                    image_path = os.path.join(settings.MEDIA_ROOT, str(author.photo))
                    
                    if not os.path.exists(image_path):
                        continue
                    
                    # Open the image
                    img = Image.open(image_path)
                    original_size = os.path.getsize(image_path)
                    
                    modified = False
                    
                    # Resize if needed
                    if resize and (img.width > author_photo_size[0] or img.height > author_photo_size[1]):
                        self.stdout.write(f'  Resizing photo for author ID {author.id}: "{author.name}"')
                        self.stdout.write(f'    Original size: {img.width}x{img.height}')
                        
                        # Resize while maintaining aspect ratio
                        img.thumbnail(author_photo_size, Image.LANCZOS)
                        self.stdout.write(f'    New size: {img.width}x{img.height}')
                        modified = True
                    
                    # Optimize file size
                    if optimize:
                        self.stdout.write(f'  Optimizing photo for author ID {author.id}: "{author.name}"')
                        self.stdout.write(f'    Original file size: {original_size / 1024:.1f} KB')
                        modified = True
                    
                    # Save the optimized image
                    if modified and not dry_run:
                        img.save(image_path, optimize=True, quality=85)
                        new_size = os.path.getsize(image_path)
                        self.stdout.write(f'    New file size: {new_size / 1024:.1f} KB')
                        self.stdout.write(self.style.SUCCESS(f'    Saved optimized image'))
                        optimized_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error processing image: {str(e)}'))
        
        # Optimize publisher logos
        if image_type in ['publishers', 'all']:
            self.stdout.write('Processing publisher logos...')
            publishers = Publisher.objects.exclude(Q(logo__isnull=True) | Q(logo=''))
            
            for publisher in publishers:
                try:
                    image_path = os.path.join(settings.MEDIA_ROOT, str(publisher.logo))
                    
                    if not os.path.exists(image_path):
                        continue
                    
                    # Open the image
                    img = Image.open(image_path)
                    original_size = os.path.getsize(image_path)
                    
                    modified = False
                    
                    # Resize if needed
                    if resize and (img.width > publisher_logo_size[0] or img.height > publisher_logo_size[1]):
                        self.stdout.write(f'  Resizing logo for publisher ID {publisher.id}: "{publisher.name}"')
                        self.stdout.write(f'    Original size: {img.width}x{img.height}')
                        
                        # Resize while maintaining aspect ratio
                        img.thumbnail(publisher_logo_size, Image.LANCZOS)
                        self.stdout.write(f'    New size: {img.width}x{img.height}')
                        modified = True
                    
                    # Optimize file size
                    if optimize:
                        self.stdout.write(f'  Optimizing logo for publisher ID {publisher.id}: "{publisher.name}"')
                        self.stdout.write(f'    Original file size: {original_size / 1024:.1f} KB')
                        modified = True
                    
                    # Save the optimized image
                    if modified and not dry_run:
                        img.save(image_path, optimize=True, quality=85)
                        new_size = os.path.getsize(image_path)
                        self.stdout.write(f'    New file size: {new_size / 1024:.1f} KB')
                        self.stdout.write(self.style.SUCCESS(f'    Saved optimized image'))
                        optimized_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error processing image: {str(e)}'))
        
        if optimized_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Optimized {optimized_count} images'))
        else:
            self.stdout.write('No images were optimized')
    
    def regenerate_missing_images(self, image_type, dry_run):
        """Regenerate missing images using Flux AI"""
        self.stdout.write('Checking for missing images to regenerate...')
        
        # Check if Flux AI is available
        flux_available = self.check_flux_availability()
        if not flux_available:
            self.stdout.write(self.style.WARNING('Flux AI is not available. Using fallback image generation.'))
        
        regenerated_count = 0
        
        # Regenerate book covers
        if image_type in ['books', 'all']:
            self.stdout.write('Checking for books without covers...')
            books_without_covers = Book.objects.filter(Q(cover__isnull=True) | Q(cover=''))
            count = books_without_covers.count()
            
            if count == 0:
                self.stdout.write('All books have covers')
            else:
                self.stdout.write(f'Found {count} books without covers')
                
                if not dry_run:
                    for book in books_without_covers:
                        success = self.generate_book_cover(book, flux_available)
                        if success:
                            regenerated_count += 1
        
        # Regenerate author photos
        if image_type in ['authors', 'all']:
            self.stdout.write('Checking for authors without photos...')
            authors_without_photos = Author.objects.filter(Q(photo__isnull=True) | Q(photo=''))
            count = authors_without_photos.count()
            
            if count == 0:
                self.stdout.write('All authors have photos')
            else:
                self.stdout.write(f'Found {count} authors without photos')
                
                if not dry_run:
                    for author in authors_without_photos:
                        success = self.generate_author_photo(author, flux_available)
                        if success:
                            regenerated_count += 1
        
        # Regenerate publisher logos
        if image_type in ['publishers', 'all']:
            self.stdout.write('Checking for publishers without logos...')
            publishers_without_logos = Publisher.objects.filter(Q(logo__isnull=True) | Q(logo=''))
            count = publishers_without_logos.count()
            
            if count == 0:
                self.stdout.write('All publishers have logos')
            else:
                self.stdout.write(f'Found {count} publishers without logos')
                
                if not dry_run:
                    for publisher in publishers_without_logos:
                        success = self.generate_publisher_logo(publisher, flux_available)
                        if success:
                            regenerated_count += 1
        
        if regenerated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Regenerated {regenerated_count} images'))
        else:
            self.stdout.write('No images were regenerated')
    
    def check_flux_availability(self):
        """Check if Flux AI is available"""
        try:
            # Check if flux_wrapper.py exists
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            return os.path.exists(flux_wrapper_path)
        except Exception:
            return False
    
    def generate_book_cover(self, book, flux_available):
        """Generate a book cover for a book"""
        try:
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
            
            # Add fallback flag if Flux AI is not available
            if not flux_available:
                cmd.append("--fallback")
            
            self.stdout.write(f'    Running command: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if success:
                # Update the book model with the new cover
                relative_path = os.path.join('covers', filename)
                book.cover = relative_path
                book.save(update_fields=['cover'])
                self.stdout.write(self.style.SUCCESS(f'    Successfully generated cover for book: {book.title}'))
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    Failed to generate cover for book: {book.title}'))
                if result.stderr:
                    self.stdout.write(f'    Error: {result.stderr[:200]}...')
                return False
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error generating cover for book {book.id}: {str(e)}'))
            return False
    
    def generate_author_photo(self, author, flux_available):
        """Generate an author photo"""
        try:
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
            
            # Add fallback flag if Flux AI is not available
            if not flux_available:
                cmd.append("--fallback")
            
            self.stdout.write(f'    Running command: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if success:
                # Update the author model with the new photo
                relative_path = os.path.join('authors', filename)
                author.photo = relative_path
                author.save(update_fields=['photo'])
                self.stdout.write(self.style.SUCCESS(f'    Successfully generated photo for author: {author.name}'))
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    Failed to generate photo for author: {author.name}'))
                if result.stderr:
                    self.stdout.write(f'    Error: {result.stderr[:200]}...')
                return False
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error generating photo for author {author.id}: {str(e)}'))
            return False
    
    def generate_publisher_logo(self, publisher, flux_available):
        """Generate a publisher logo"""
        try:
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
            
            # Add fallback flag if Flux AI is not available
            if not flux_available:
                cmd.append("--fallback")
            
            self.stdout.write(f'    Running command: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if success:
                # Update the publisher model with the new logo
                relative_path = os.path.join('publishers', filename)
                publisher.logo = relative_path
                publisher.save(update_fields=['logo'])
                self.stdout.write(self.style.SUCCESS(f'    Successfully generated logo for publisher: {publisher.name}'))
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    Failed to generate logo for publisher: {publisher.name}'))
                if result.stderr:
                    self.stdout.write(f'    Error: {result.stderr[:200]}...')
                return False
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error generating logo for publisher {publisher.id}: {str(e)}'))
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

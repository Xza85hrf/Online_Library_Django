import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Verify and fix broken image references in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['books', 'authors', 'publishers', 'all'],
            default='all',
            help='Type of images to verify'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix broken references (clear invalid paths)'
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate images for items with broken references'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        image_type = options['type']
        fix = options['fix']
        regenerate = options['regenerate']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        broken_count = 0
        fixed_count = 0
        regenerated_count = 0
        
        # Verify book covers
        if image_type in ['books', 'all']:
            self.stdout.write('Verifying book cover references...')
            books_broken, books_fixed, books_regenerated = self.verify_book_covers(fix, regenerate, dry_run)
            broken_count += books_broken
            fixed_count += books_fixed
            regenerated_count += books_regenerated
        
        # Verify author photos
        if image_type in ['authors', 'all']:
            self.stdout.write('Verifying author photo references...')
            authors_broken, authors_fixed, authors_regenerated = self.verify_author_photos(fix, regenerate, dry_run)
            broken_count += authors_broken
            fixed_count += authors_fixed
            regenerated_count += authors_regenerated
        
        # Verify publisher logos
        if image_type in ['publishers', 'all']:
            self.stdout.write('Verifying publisher logo references...')
            publishers_broken, publishers_fixed, publishers_regenerated = self.verify_publisher_logos(fix, regenerate, dry_run)
            broken_count += publishers_broken
            fixed_count += publishers_fixed
            regenerated_count += publishers_regenerated
        
        self.stdout.write(self.style.SUCCESS(f'Found {broken_count} broken image references'))
        
        if fix:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} broken image references'))
        
        if regenerate:
            self.stdout.write(self.style.SUCCESS(f'Regenerated {regenerated_count} images'))
    
    def verify_book_covers(self, fix, regenerate, dry_run):
        """Verify book cover references"""
        broken_count = 0
        fixed_count = 0
        regenerated_count = 0
        
        books = Book.objects.exclude(Q(cover__isnull=True) | Q(cover=''))
        
        for book in books:
            if not book.cover:
                continue
            
            # Check if the file exists
            image_path = os.path.join(settings.MEDIA_ROOT, str(book.cover))
            if not os.path.exists(image_path):
                broken_count += 1
                self.stdout.write(self.style.WARNING(f'  Book ID {book.id}: "{book.title}" has broken cover reference: {book.cover}'))
                
                if fix and not dry_run:
                    # Clear the invalid path
                    book.cover = None
                    book.save(update_fields=['cover'])
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'    Cleared invalid cover path'))
                
                if regenerate and not dry_run:
                    # Regenerate the image
                    success = self.regenerate_book_cover(book)
                    if success:
                        regenerated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Regenerated cover for book'))
        
        return broken_count, fixed_count, regenerated_count
    
    def verify_author_photos(self, fix, regenerate, dry_run):
        """Verify author photo references"""
        broken_count = 0
        fixed_count = 0
        regenerated_count = 0
        
        authors = Author.objects.exclude(Q(photo__isnull=True) | Q(photo=''))
        
        for author in authors:
            if not author.photo:
                continue
            
            # Check if the file exists
            image_path = os.path.join(settings.MEDIA_ROOT, str(author.photo))
            if not os.path.exists(image_path):
                broken_count += 1
                self.stdout.write(self.style.WARNING(f'  Author ID {author.id}: "{author.name}" has broken photo reference: {author.photo}'))
                
                if fix and not dry_run:
                    # Clear the invalid path
                    author.photo = None
                    author.save(update_fields=['photo'])
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'    Cleared invalid photo path'))
                
                if regenerate and not dry_run:
                    # Regenerate the image
                    success = self.regenerate_author_photo(author)
                    if success:
                        regenerated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Regenerated photo for author'))
        
        return broken_count, fixed_count, regenerated_count
    
    def verify_publisher_logos(self, fix, regenerate, dry_run):
        """Verify publisher logo references"""
        broken_count = 0
        fixed_count = 0
        regenerated_count = 0
        
        publishers = Publisher.objects.exclude(Q(logo__isnull=True) | Q(logo=''))
        
        for publisher in publishers:
            if not publisher.logo:
                continue
            
            # Check if the file exists
            image_path = os.path.join(settings.MEDIA_ROOT, str(publisher.logo))
            if not os.path.exists(image_path):
                broken_count += 1
                self.stdout.write(self.style.WARNING(f'  Publisher ID {publisher.id}: "{publisher.name}" has broken logo reference: {publisher.logo}'))
                
                if fix and not dry_run:
                    # Clear the invalid path
                    publisher.logo = None
                    publisher.save(update_fields=['logo'])
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'    Cleared invalid logo path'))
                
                if regenerate and not dry_run:
                    # Regenerate the image
                    success = self.regenerate_publisher_logo(publisher)
                    if success:
                        regenerated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Regenerated logo for publisher'))
        
        return broken_count, fixed_count, regenerated_count
    
    def regenerate_book_cover(self, book):
        """Regenerate a book cover"""
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
            
            # Generate the image using flux_wrapper.py
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            
            # Check if flux_wrapper.py exists
            if not os.path.exists(flux_wrapper_path):
                self.stdout.write(self.style.ERROR(f'    Flux wrapper not found at {flux_wrapper_path}'))
                return False
            
            import subprocess
            cmd = [
                "python", flux_wrapper_path,
                "--prompt", prompt,
                "--output", output_path,
                "--fallback"  # Use fallback in case Flux AI is not available
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if success:
                # Update the book model with the new cover
                relative_path = os.path.join('covers', filename)
                book.cover = relative_path
                book.save(update_fields=['cover'])
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    Failed to regenerate cover: {result.stderr[:200]}'))
                return False
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error regenerating cover: {str(e)}'))
            return False
    
    def regenerate_author_photo(self, author):
        """Regenerate an author photo"""
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
            
            # Generate the image using flux_wrapper.py
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            
            # Check if flux_wrapper.py exists
            if not os.path.exists(flux_wrapper_path):
                self.stdout.write(self.style.ERROR(f'    Flux wrapper not found at {flux_wrapper_path}'))
                return False
            
            import subprocess
            cmd = [
                "python", flux_wrapper_path,
                "--prompt", prompt,
                "--output", output_path,
                "--fallback"  # Use fallback in case Flux AI is not available
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if success:
                # Update the author model with the new photo
                relative_path = os.path.join('authors', filename)
                author.photo = relative_path
                author.save(update_fields=['photo'])
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    Failed to regenerate photo: {result.stderr[:200]}'))
                return False
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error regenerating photo: {str(e)}'))
            return False
    
    def regenerate_publisher_logo(self, publisher):
        """Regenerate a publisher logo"""
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
            
            # Generate the image using flux_wrapper.py
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            
            # Check if flux_wrapper.py exists
            if not os.path.exists(flux_wrapper_path):
                self.stdout.write(self.style.ERROR(f'    Flux wrapper not found at {flux_wrapper_path}'))
                return False
            
            import subprocess
            cmd = [
                "python", flux_wrapper_path,
                "--prompt", prompt,
                "--output", output_path,
                "--fallback"  # Use fallback in case Flux AI is not available
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if success:
                # Update the publisher model with the new logo
                relative_path = os.path.join('publishers', filename)
                publisher.logo = relative_path
                publisher.save(update_fields=['logo'])
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    Failed to regenerate logo: {result.stderr[:200]}'))
                return False
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error regenerating logo: {str(e)}'))
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

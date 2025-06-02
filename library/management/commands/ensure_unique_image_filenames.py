import os
import re
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Ensure all images have unique and consistent filenames'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['books', 'authors', 'publishers', 'all'],
            default='all',
            help='Type of images to process'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        image_type = options['type']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        renamed_count = 0
        
        # Process book covers
        if image_type in ['books', 'all']:
            self.stdout.write('Processing book covers...')
            renamed_count += self.process_book_covers(dry_run)
        
        # Process author photos
        if image_type in ['authors', 'all']:
            self.stdout.write('Processing author photos...')
            renamed_count += self.process_author_photos(dry_run)
        
        # Process publisher logos
        if image_type in ['publishers', 'all']:
            self.stdout.write('Processing publisher logos...')
            renamed_count += self.process_publisher_logos(dry_run)
        
        if renamed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully renamed {renamed_count} images'))
        else:
            self.stdout.write('No images needed renaming')
    
    def process_book_covers(self, dry_run):
        """Process book covers to ensure unique filenames"""
        renamed_count = 0
        books = Book.objects.exclude(Q(cover__isnull=True) | Q(cover=''))
        
        # Track used filenames to avoid duplicates
        used_filenames = set()
        
        for book in books:
            if not book.cover:
                continue
            
            current_path = str(book.cover)
            current_filename = os.path.basename(current_path)
            
            # Create a new standardized filename
            new_filename = self.generate_unique_book_filename(book, used_filenames)
            
            # If the filename is already in the standardized format, skip
            if current_filename == new_filename:
                continue
            
            # Construct the full paths
            media_root = settings.MEDIA_ROOT
            current_full_path = os.path.join(media_root, current_path)
            new_relative_path = os.path.join('covers', new_filename)
            new_full_path = os.path.join(media_root, new_relative_path)
            
            # Check if the file exists
            if not os.path.exists(current_full_path):
                self.stdout.write(self.style.WARNING(f'  Book ID {book.id}: File does not exist: {current_full_path}'))
                continue
            
            self.stdout.write(f'  Book ID {book.id}: Renaming cover from {current_filename} to {new_filename}')
            
            if not dry_run:
                try:
                    # Create the directory if it doesn't exist
                    os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
                    
                    # Copy the file to the new location
                    shutil.copy2(current_full_path, new_full_path)
                    
                    # Update the database
                    book.cover = new_relative_path
                    book.save(update_fields=['cover'])
                    
                    # Delete the old file if it's different from the new one
                    if current_full_path != new_full_path and os.path.exists(current_full_path):
                        os.remove(current_full_path)
                    
                    renamed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'    Successfully renamed cover'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error renaming cover: {str(e)}'))
        
        return renamed_count
    
    def process_author_photos(self, dry_run):
        """Process author photos to ensure unique filenames"""
        renamed_count = 0
        authors = Author.objects.exclude(Q(photo__isnull=True) | Q(photo=''))
        
        # Track used filenames to avoid duplicates
        used_filenames = set()
        
        for author in authors:
            if not author.photo:
                continue
            
            current_path = str(author.photo)
            current_filename = os.path.basename(current_path)
            
            # Create a new standardized filename
            new_filename = self.generate_unique_author_filename(author, used_filenames)
            
            # If the filename is already in the standardized format, skip
            if current_filename == new_filename:
                continue
            
            # Construct the full paths
            media_root = settings.MEDIA_ROOT
            current_full_path = os.path.join(media_root, current_path)
            new_relative_path = os.path.join('authors', new_filename)
            new_full_path = os.path.join(media_root, new_relative_path)
            
            # Check if the file exists
            if not os.path.exists(current_full_path):
                self.stdout.write(self.style.WARNING(f'  Author ID {author.id}: File does not exist: {current_full_path}'))
                continue
            
            self.stdout.write(f'  Author ID {author.id}: Renaming photo from {current_filename} to {new_filename}')
            
            if not dry_run:
                try:
                    # Create the directory if it doesn't exist
                    os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
                    
                    # Copy the file to the new location
                    shutil.copy2(current_full_path, new_full_path)
                    
                    # Update the database
                    author.photo = new_relative_path
                    author.save(update_fields=['photo'])
                    
                    # Delete the old file if it's different from the new one
                    if current_full_path != new_full_path and os.path.exists(current_full_path):
                        os.remove(current_full_path)
                    
                    renamed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'    Successfully renamed photo'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error renaming photo: {str(e)}'))
        
        return renamed_count
    
    def process_publisher_logos(self, dry_run):
        """Process publisher logos to ensure unique filenames"""
        renamed_count = 0
        publishers = Publisher.objects.exclude(Q(logo__isnull=True) | Q(logo=''))
        
        # Track used filenames to avoid duplicates
        used_filenames = set()
        
        for publisher in publishers:
            if not publisher.logo:
                continue
            
            current_path = str(publisher.logo)
            current_filename = os.path.basename(current_path)
            
            # Create a new standardized filename
            new_filename = self.generate_unique_publisher_filename(publisher, used_filenames)
            
            # If the filename is already in the standardized format, skip
            if current_filename == new_filename:
                continue
            
            # Construct the full paths
            media_root = settings.MEDIA_ROOT
            current_full_path = os.path.join(media_root, current_path)
            new_relative_path = os.path.join('publishers', new_filename)
            new_full_path = os.path.join(media_root, new_relative_path)
            
            # Check if the file exists
            if not os.path.exists(current_full_path):
                self.stdout.write(self.style.WARNING(f'  Publisher ID {publisher.id}: File does not exist: {current_full_path}'))
                continue
            
            self.stdout.write(f'  Publisher ID {publisher.id}: Renaming logo from {current_filename} to {new_filename}')
            
            if not dry_run:
                try:
                    # Create the directory if it doesn't exist
                    os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
                    
                    # Copy the file to the new location
                    shutil.copy2(current_full_path, new_full_path)
                    
                    # Update the database
                    publisher.logo = new_relative_path
                    publisher.save(update_fields=['logo'])
                    
                    # Delete the old file if it's different from the new one
                    if current_full_path != new_full_path and os.path.exists(current_full_path):
                        os.remove(current_full_path)
                    
                    renamed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'    Successfully renamed logo'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error renaming logo: {str(e)}'))
        
        return renamed_count
    
    def generate_unique_book_filename(self, book, used_filenames):
        """Generate a unique filename for a book cover"""
        base_filename = f"{book.id}_{self.sanitize_filename(book.title)[:30]}"
        
        # Ensure uniqueness
        filename = f"{base_filename}.jpg"
        counter = 1
        
        while filename in used_filenames:
            filename = f"{base_filename}_{counter}.jpg"
            counter += 1
        
        used_filenames.add(filename)
        return filename
    
    def generate_unique_author_filename(self, author, used_filenames):
        """Generate a unique filename for an author photo"""
        base_filename = f"{author.id}_{self.sanitize_filename(author.name)[:30]}"
        
        # Ensure uniqueness
        filename = f"{base_filename}.jpg"
        counter = 1
        
        while filename in used_filenames:
            filename = f"{base_filename}_{counter}.jpg"
            counter += 1
        
        used_filenames.add(filename)
        return filename
    
    def generate_unique_publisher_filename(self, publisher, used_filenames):
        """Generate a unique filename for a publisher logo"""
        base_filename = f"{publisher.id}_{self.sanitize_filename(publisher.name)[:30]}"
        
        # Ensure uniqueness
        filename = f"{base_filename}.jpg"
        counter = 1
        
        while filename in used_filenames:
            filename = f"{base_filename}_{counter}.jpg"
            counter += 1
        
        used_filenames.add(filename)
        return filename
    
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

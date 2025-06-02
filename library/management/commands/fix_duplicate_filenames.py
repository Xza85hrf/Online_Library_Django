import os
import re
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Fix duplicate image filenames by creating unique filenames for each item'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--fallback',
            action='store_true',
            help='Force fallback to basic image generation when regenerating images'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fallback = options['fallback']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        self.fix_book_cover_filenames(dry_run, fallback)
        self.fix_author_photo_filenames(dry_run, fallback)
        self.fix_publisher_logo_filenames(dry_run, fallback)
        
        self.stdout.write(self.style.SUCCESS('Duplicate filename fix completed!'))
    
    def sanitize_filename(self, filename, max_length=30):
        """Sanitize a string to be safe for filenames"""
        if not filename:
            return "unknown"
            
        # Replace problematic characters with underscores
        # Remove characters that are invalid in filenames (Windows restrictions)
        invalid_chars = r'[<>:"\/|?*\\]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        
        # Limit length but ensure uniqueness
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            
        return sanitized
    
    def generate_unique_filename(self, item, base_name, existing_filenames, id_prefix=True):
        """Generate a unique filename for an item"""
        # Start with a sanitized version of the base name
        safe_name = self.sanitize_filename(base_name, max_length=20)  # Shorter to leave room for uniqueness
        
        # Add item ID as prefix if requested
        if id_prefix:
            filename = f"{item.id}_{safe_name}"
        else:
            filename = safe_name
            
        # If this is already unique, return it
        if filename not in existing_filenames:
            return filename
            
        # Otherwise, add a unique suffix
        counter = 1
        while True:
            unique_filename = f"{filename}_{counter}"
            if unique_filename not in existing_filenames:
                return unique_filename
            counter += 1
    
    def fix_book_cover_filenames(self, dry_run, fallback):
        """Fix duplicate book cover filenames"""
        self.stdout.write('Checking for duplicate book cover filenames...')
        
        # Get all books with covers
        books_with_covers = Book.objects.exclude(Q(cover__isnull=True) | Q(cover=''))
        
        # Track existing filenames and duplicates
        filename_map = {}  # Maps filename to list of books with that filename
        
        # First pass: identify duplicates
        for book in books_with_covers:
            if not book.cover or not book.cover.name:
                continue
                
            filename = os.path.basename(book.cover.name)
            if filename not in filename_map:
                filename_map[filename] = []
            filename_map[filename].append(book)
        
        # Find duplicates
        duplicates = {filename: books for filename, books in filename_map.items() if len(books) > 1}
        
        if not duplicates:
            self.stdout.write('No duplicate book cover filenames found')
            return
            
        self.stdout.write(f'Found {len(duplicates)} duplicate book cover filenames')
        
        # Second pass: fix duplicates
        fixed_count = 0
        for filename, books in duplicates.items():
            self.stdout.write(f'  Duplicate filename: {filename} used by {len(books)} books:')
            
            # List the books using this filename
            for i, book in enumerate(books):
                self.stdout.write(f'    {i+1}. Book ID {book.id}: {book.title}')
            
            # Fix all but the first book (keep original for the first one)
            for book in books[1:]:
                # Generate a new unique filename
                existing_filenames = list(filename_map.keys())
                new_filename = self.generate_unique_filename(book, book.title, existing_filenames)
                new_filename += '.jpg'  # Add extension
                
                # Create the new file path
                media_root = settings.MEDIA_ROOT
                covers_dir = os.path.join(media_root, 'covers')
                new_path = os.path.join(covers_dir, new_filename)
                
                self.stdout.write(f'    Will rename cover for book: {book.title}')
                self.stdout.write(f'      From: {book.cover.name}')
                self.stdout.write(f'      To: covers/{new_filename}')
                
                if not dry_run:
                    # Two options: copy the existing file or regenerate the image
                    if os.path.exists(book.cover.path):
                        # Copy the existing file
                        try:
                            import shutil
                            os.makedirs(covers_dir, exist_ok=True)
                            shutil.copy2(book.cover.path, new_path)
                            self.stdout.write(self.style.SUCCESS(f'      Copied existing image to new path'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'      Error copying file: {str(e)}'))
                            # If copy fails, we'll regenerate below
                    
                    # If the file doesn't exist or copy failed, regenerate the image
                    if not os.path.exists(new_path):
                        self.stdout.write(f'      Regenerating image...')
                        success = self.regenerate_book_cover(book, new_path, fallback)
                        if not success:
                            self.stdout.write(self.style.ERROR(f'      Failed to regenerate image'))
                            continue
                    
                    # Update the database record
                    relative_path = os.path.join('covers', new_filename)
                    book.cover = relative_path
                    book.save(update_fields=['cover'])
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'      Successfully updated book cover path'))
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} duplicate book cover filenames'))
    
    def fix_author_photo_filenames(self, dry_run, fallback):
        """Fix duplicate author photo filenames"""
        self.stdout.write('Checking for duplicate author photo filenames...')
        
        # Get all authors with photos
        authors_with_photos = Author.objects.exclude(Q(photo__isnull=True) | Q(photo=''))
        
        # Track existing filenames and duplicates
        filename_map = {}  # Maps filename to list of authors with that filename
        
        # First pass: identify duplicates
        for author in authors_with_photos:
            if not author.photo or not author.photo.name:
                continue
                
            filename = os.path.basename(author.photo.name)
            if filename not in filename_map:
                filename_map[filename] = []
            filename_map[filename].append(author)
        
        # Find duplicates
        duplicates = {filename: authors for filename, authors in filename_map.items() if len(authors) > 1}
        
        if not duplicates:
            self.stdout.write('No duplicate author photo filenames found')
            return
            
        self.stdout.write(f'Found {len(duplicates)} duplicate author photo filenames')
        
        # Second pass: fix duplicates
        fixed_count = 0
        for filename, authors in duplicates.items():
            self.stdout.write(f'  Duplicate filename: {filename} used by {len(authors)} authors:')
            
            # List the authors using this filename
            for i, author in enumerate(authors):
                self.stdout.write(f'    {i+1}. Author ID {author.id}: {author.name}')
            
            # Fix all but the first author (keep original for the first one)
            for author in authors[1:]:
                # Generate a new unique filename
                existing_filenames = list(filename_map.keys())
                new_filename = self.generate_unique_filename(author, author.name, existing_filenames)
                new_filename += '.jpg'  # Add extension
                
                # Create the new file path
                media_root = settings.MEDIA_ROOT
                authors_dir = os.path.join(media_root, 'authors')
                new_path = os.path.join(authors_dir, new_filename)
                
                self.stdout.write(f'    Will rename photo for author: {author.name}')
                self.stdout.write(f'      From: {author.photo.name}')
                self.stdout.write(f'      To: authors/{new_filename}')
                
                if not dry_run:
                    # Two options: copy the existing file or regenerate the image
                    if os.path.exists(author.photo.path):
                        # Copy the existing file
                        try:
                            import shutil
                            os.makedirs(authors_dir, exist_ok=True)
                            shutil.copy2(author.photo.path, new_path)
                            self.stdout.write(self.style.SUCCESS(f'      Copied existing image to new path'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'      Error copying file: {str(e)}'))
                            # If copy fails, we'll regenerate below
                    
                    # If the file doesn't exist or copy failed, regenerate the image
                    if not os.path.exists(new_path):
                        self.stdout.write(f'      Regenerating image...')
                        success = self.regenerate_author_photo(author, new_path, fallback)
                        if not success:
                            self.stdout.write(self.style.ERROR(f'      Failed to regenerate image'))
                            continue
                    
                    # Update the database record
                    relative_path = os.path.join('authors', new_filename)
                    author.photo = relative_path
                    author.save(update_fields=['photo'])
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'      Successfully updated author photo path'))
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} duplicate author photo filenames'))
    
    def fix_publisher_logo_filenames(self, dry_run, fallback):
        """Fix duplicate publisher logo filenames"""
        self.stdout.write('Checking for duplicate publisher logo filenames...')
        
        # Get all publishers with logos
        publishers_with_logos = Publisher.objects.exclude(Q(logo__isnull=True) | Q(logo=''))
        
        # Track existing filenames and duplicates
        filename_map = {}  # Maps filename to list of publishers with that filename
        
        # First pass: identify duplicates
        for publisher in publishers_with_logos:
            if not publisher.logo or not publisher.logo.name:
                continue
                
            filename = os.path.basename(publisher.logo.name)
            if filename not in filename_map:
                filename_map[filename] = []
            filename_map[filename].append(publisher)
        
        # Find duplicates
        duplicates = {filename: publishers for filename, publishers in filename_map.items() if len(publishers) > 1}
        
        if not duplicates:
            self.stdout.write('No duplicate publisher logo filenames found')
            return
            
        self.stdout.write(f'Found {len(duplicates)} duplicate publisher logo filenames')
        
        # Second pass: fix duplicates
        fixed_count = 0
        for filename, publishers in duplicates.items():
            self.stdout.write(f'  Duplicate filename: {filename} used by {len(publishers)} publishers:')
            
            # List the publishers using this filename
            for i, publisher in enumerate(publishers):
                self.stdout.write(f'    {i+1}. Publisher ID {publisher.id}: {publisher.name}')
            
            # Fix all but the first publisher (keep original for the first one)
            for publisher in publishers[1:]:
                # Generate a new unique filename
                existing_filenames = list(filename_map.keys())
                new_filename = self.generate_unique_filename(publisher, publisher.name, existing_filenames)
                new_filename += '.jpg'  # Add extension
                
                # Create the new file path
                media_root = settings.MEDIA_ROOT
                publishers_dir = os.path.join(media_root, 'publishers')
                new_path = os.path.join(publishers_dir, new_filename)
                
                self.stdout.write(f'    Will rename logo for publisher: {publisher.name}')
                self.stdout.write(f'      From: {publisher.logo.name}')
                self.stdout.write(f'      To: publishers/{new_filename}')
                
                if not dry_run:
                    # Two options: copy the existing file or regenerate the image
                    if os.path.exists(publisher.logo.path):
                        # Copy the existing file
                        try:
                            import shutil
                            os.makedirs(publishers_dir, exist_ok=True)
                            shutil.copy2(publisher.logo.path, new_path)
                            self.stdout.write(self.style.SUCCESS(f'      Copied existing image to new path'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'      Error copying file: {str(e)}'))
                            # If copy fails, we'll regenerate below
                    
                    # If the file doesn't exist or copy failed, regenerate the image
                    if not os.path.exists(new_path):
                        self.stdout.write(f'      Regenerating image...')
                        success = self.regenerate_publisher_logo(publisher, new_path, fallback)
                        if not success:
                            self.stdout.write(self.style.ERROR(f'      Failed to regenerate image'))
                            continue
                    
                    # Update the database record
                    relative_path = os.path.join('publishers', new_filename)
                    publisher.logo = relative_path
                    publisher.save(update_fields=['logo'])
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'      Successfully updated publisher logo path'))
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} duplicate publisher logo filenames'))
    
    def regenerate_book_cover(self, book, output_path, fallback):
        """Regenerate a book cover image"""
        try:
            # Generate the prompt
            authors = ", ".join([author.name for author in book.authors.all()])
            if not authors:
                authors = "Unknown Author"
            
            prompt = f"A professional book cover for '{book.title}' by {authors}. High quality, detailed, publishing industry standard."
            
            # Generate the image using flux_wrapper.py
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            cmd = [
                "python", flux_wrapper_path,
                "--prompt", prompt,
                "--output", output_path
            ]
            
            # Add fallback flag if requested
            if fallback:
                cmd.append("--fallback")
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            return success
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error regenerating book cover: {str(e)}'))
            return False
    
    def regenerate_author_photo(self, author, output_path, fallback):
        """Regenerate an author photo"""
        try:
            # Generate the prompt
            prompt = f"A professional portrait photograph of author {author.name}. High quality, detailed, professional headshot."
            
            # Generate the image using flux_wrapper.py
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            cmd = [
                "python", flux_wrapper_path,
                "--prompt", prompt,
                "--output", output_path
            ]
            
            # Add fallback flag if requested
            if fallback:
                cmd.append("--fallback")
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            return success
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error regenerating author photo: {str(e)}'))
            return False
    
    def regenerate_publisher_logo(self, publisher, output_path, fallback):
        """Regenerate a publisher logo"""
        try:
            # Generate the prompt
            prompt = f"A professional logo for publishing company '{publisher.name}'. Clean, corporate design, minimalist, high quality."
            
            # Generate the image using flux_wrapper.py
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            cmd = [
                "python", flux_wrapper_path,
                "--prompt", prompt,
                "--output", output_path
            ]
            
            # Add fallback flag if requested
            if fallback:
                cmd.append("--fallback")
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            return success
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error regenerating publisher logo: {str(e)}'))
            return False

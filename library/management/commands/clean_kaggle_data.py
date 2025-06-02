import os
import re
import sqlite3
import subprocess
import random
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Thoroughly clean Kaggle data and generate missing images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip image generation'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of images to generate in one batch'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_images = options['skip_images']
        batch_size = options['batch_size']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        # First, fix the data directly using SQL to avoid Django ORM issues
        self.fix_data_with_sql(dry_run)
        
        if not skip_images:
            self.generate_missing_images(dry_run, batch_size)
    
    def is_csv_data(self, text):
        """Check if text looks like CSV data with multiple fields"""
        if not text:
            return False
        # Look for patterns like: field1;"field2";field3
        return ';' in text and ('"' in text or text.count(';') >= 2)
    
    def extract_field(self, text, field_index=1):
        """Extract a specific field from CSV-like data"""
        if not text or not self.is_csv_data(text):
            return text
            
        # Split by semicolons
        parts = text.split(';')
        
        # If we have enough parts and the requested field exists
        if len(parts) > field_index:
            # Remove quotes if present
            field = parts[field_index].strip('"\'')
            return field
            
        return text
    
    def extract_first_field(self, text):
        """Extract the first field from CSV-like data"""
        if not text or not self.is_csv_data(text):
            return text
            
        # Try to extract the first field before the first semicolon
        parts = text.split(';', 1)
        if len(parts) > 0:
            # Remove quotes if present
            first_part = parts[0].strip('"\'')
            # If it's an ISBN or numeric ID, try the second field
            if first_part.isdigit() or (len(first_part) == 10 and first_part.replace('-', '').isdigit()):
                if len(parts) > 1:
                    second_parts = parts[1].split(';', 1)
                    if len(second_parts) > 0:
                        return second_parts[0].strip('"\'')
            return first_part
            
        return text
    
    def fix_data_with_sql(self, dry_run):
        """Fix all mangled data directly in the database using SQL"""
        self.stdout.write('Fixing data directly in the database...')
        
        # Connect to the database
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fix book titles
        self.stdout.write('Fixing book titles...')
        cursor.execute('SELECT id, title FROM library_book')
        books = cursor.fetchall()
        
        fixed_titles = 0
        fixed_isbns = 0
        
        for book_id, title in books:
            if self.is_csv_data(title):
                old_title = title
                new_title = self.extract_first_field(old_title)
                
                self.stdout.write(f'  Found mangled title: {old_title[:50]}...')
                self.stdout.write(f'  Will fix to: {new_title}')
                
                if not dry_run:
                    cursor.execute('UPDATE library_book SET title = ? WHERE id = ?', (new_title, book_id))
                    fixed_titles += 1
        
        # Fix ISBN fields
        self.stdout.write('Fixing ISBN fields...')
        cursor.execute('SELECT id, isbn FROM library_book')
        books = cursor.fetchall()
        
        for book_id, isbn in books:
            if isbn and self.is_csv_data(isbn):
                old_isbn = isbn
                # Extract just the ISBN part (first field)
                new_isbn = old_isbn.split(';')[0].strip('"\'')
                
                self.stdout.write(f'  Found mangled ISBN: {old_isbn[:50]}...')
                self.stdout.write(f'  Will fix to: {new_isbn}')
                
                if not dry_run:
                    cursor.execute('UPDATE library_book SET isbn = ? WHERE id = ?', (new_isbn, book_id))
                    fixed_isbns += 1
        
        # Fix author names
        self.stdout.write('Fixing author names...')
        cursor.execute('SELECT id, name FROM library_author')
        authors = cursor.fetchall()
        
        fixed_authors = 0
        
        for author_id, name in authors:
            if self.is_csv_data(name):
                old_name = name
                new_name = self.extract_first_field(old_name)
                
                self.stdout.write(f'  Found mangled author name: {old_name[:50]}...')
                self.stdout.write(f'  Will fix to: {new_name}')
                
                if not dry_run:
                    cursor.execute('UPDATE library_author SET name = ? WHERE id = ?', (new_name, author_id))
                    fixed_authors += 1
        
        # Fix publisher names
        self.stdout.write('Fixing publisher names...')
        cursor.execute('SELECT id, name FROM library_publisher')
        publishers = cursor.fetchall()
        
        fixed_publishers = 0
        
        for publisher_id, name in publishers:
            if self.is_csv_data(name):
                old_name = name
                new_name = self.extract_first_field(old_name)
                
                self.stdout.write(f'  Found mangled publisher name: {old_name[:50]}...')
                self.stdout.write(f'  Will fix to: {new_name}')
                
                if not dry_run:
                    cursor.execute('UPDATE library_publisher SET name = ? WHERE id = ?', (new_name, publisher_id))
                    fixed_publishers += 1
        
        # Fix book descriptions
        self.stdout.write('Fixing book descriptions...')
        cursor.execute('SELECT id, description FROM library_book')
        books = cursor.fetchall()
        
        fixed_descriptions = 0
        
        for book_id, description in books:
            if description and self.is_csv_data(description):
                old_description = description
                new_description = self.extract_first_field(old_description)
                
                self.stdout.write(f'  Found mangled description: {old_description[:50]}...')
                self.stdout.write(f'  Will fix to: {new_description[:50]}...')
                
                if not dry_run:
                    cursor.execute('UPDATE library_book SET description = ? WHERE id = ?', (new_description, book_id))
                    fixed_descriptions += 1
        
        # Extract author from CSV data and connect to books
        if not dry_run:
            self.stdout.write('Extracting authors from CSV data and connecting to books...')
            cursor.execute('SELECT id, title FROM library_book')
            books = cursor.fetchall()
            
            connected_authors = 0
            
            for book_id, title in books:
                if self.is_csv_data(title):
                    # Try to extract author name from the CSV data
                    parts = title.split(';')
                    if len(parts) >= 3:  # Format is typically ISBN;Title;Author;Year;Publisher
                        author_name = parts[2].strip('"\'')
                        
                        if author_name:
                            # Check if this author exists
                            cursor.execute('SELECT id FROM library_author WHERE name = ?', (author_name,))
                            author = cursor.fetchone()
                            
                            if author:
                                author_id = author[0]
                                
                                # Check if the relationship already exists
                                cursor.execute(
                                    'SELECT COUNT(*) FROM library_book_authors WHERE book_id = ? AND author_id = ?', 
                                    (book_id, author_id)
                                )
                                exists = cursor.fetchone()[0] > 0
                                
                                if not exists:
                                    cursor.execute(
                                        'INSERT INTO library_book_authors (book_id, author_id) VALUES (?, ?)',
                                        (book_id, author_id)
                                    )
                                    connected_authors += 1
                                    self.stdout.write(f'  Connected author "{author_name}" to book ID {book_id}')
        
        # Commit changes if not in dry run mode
        if not dry_run:
            conn.commit()
        
        conn.close()
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_titles} book titles'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_isbns} ISBN fields'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_authors} author names'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_publishers} publisher names'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_descriptions} book descriptions'))
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Connected {connected_authors} authors to books'))
    
    def generate_missing_images(self, dry_run, batch_size):
        """Generate missing images for books, authors, and publishers"""
        self.stdout.write('Checking for missing images...')
        
        # Check for books without covers
        books_without_covers = Book.objects.filter(cover__isnull=True) | Book.objects.filter(cover='')
        self.stdout.write(f'Found {books_without_covers.count()} books without covers')
        
        # Check for authors without photos
        authors_without_photos = Author.objects.filter(photo__isnull=True) | Author.objects.filter(photo='')
        self.stdout.write(f'Found {authors_without_photos.count()} authors without photos')
        
        # Check for publishers without logos
        publishers_without_logos = Publisher.objects.filter(logo__isnull=True) | Publisher.objects.filter(logo='')
        self.stdout.write(f'Found {publishers_without_logos.count()} publishers without logos')
        
        if dry_run:
            return
        
        # Generate book covers in batches
        self.stdout.write('Generating book covers...')
        for i, book in enumerate(books_without_covers):
            if i % batch_size == 0 and i > 0:
                self.stdout.write(f'Processed {i} books so far, pausing briefly...')
                import time
                time.sleep(2)  # Brief pause between batches
                
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
                
                # Generate the image using flux_wrapper.py
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
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
                        self.stdout.write(self.style.ERROR(f'    Error: {result.stderr}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating cover for book {book.id}: {str(e)}'))
        
        # Generate author photos in batches
        self.stdout.write('Generating author photos...')
        for i, author in enumerate(authors_without_photos):
            if i % batch_size == 0 and i > 0:
                self.stdout.write(f'Processed {i} authors so far, pausing briefly...')
                import time
                time.sleep(2)  # Brief pause between batches
                
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
                
                # Generate the image using flux_wrapper.py
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
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
                        self.stdout.write(self.style.ERROR(f'    Error: {result.stderr}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating photo for author {author.id}: {str(e)}'))
        
        # Generate publisher logos in batches
        self.stdout.write('Generating publisher logos...')
        for i, publisher in enumerate(publishers_without_logos):
            if i % batch_size == 0 and i > 0:
                self.stdout.write(f'Processed {i} publishers so far, pausing briefly...')
                import time
                time.sleep(2)  # Brief pause between batches
                
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
                
                # Generate the image using flux_wrapper.py
                flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
                cmd = [
                    "python", flux_wrapper_path,
                    "--prompt", prompt,
                    "--output", output_path
                ]
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
                        self.stdout.write(self.style.ERROR(f'    Error: {result.stderr}'))
            
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

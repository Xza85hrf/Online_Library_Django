import os
import re
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Fix data imported from Kaggle dataset and generate missing images'

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

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_images = options['skip_images']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        self.fix_book_titles(dry_run)
        self.fix_author_names(dry_run)
        self.fix_publisher_names(dry_run)
        
        if not skip_images:
            self.generate_missing_images(dry_run)
    
    def is_csv_data(self, text):
        """Check if text looks like CSV data with multiple fields"""
        if not text:
            return False
        # Look for patterns like: field1;"field2";field3
        return ';' in text and '"' in text and text.count(';') >= 2
    
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
    
    def fix_book_titles(self, dry_run):
        """Fix mangled book titles from Kaggle import"""
        self.stdout.write('Checking for mangled book titles...')
        
        fixed_count = 0
        with transaction.atomic():
            for book in Book.objects.all():
                if self.is_csv_data(book.title):
                    old_title = book.title
                    new_title = self.extract_first_field(old_title)
                    
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
    
    def fix_author_names(self, dry_run):
        """Fix mangled author names from Kaggle import"""
        self.stdout.write('Checking for mangled author names...')
        
        fixed_count = 0
        with transaction.atomic():
            for author in Author.objects.all():
                if self.is_csv_data(author.name):
                    old_name = author.name
                    new_name = self.extract_first_field(old_name)
                    
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
    
    def fix_publisher_names(self, dry_run):
        """Fix mangled publisher names from Kaggle import"""
        self.stdout.write('Checking for mangled publisher names...')
        
        fixed_count = 0
        with transaction.atomic():
            for publisher in Publisher.objects.all():
                if self.is_csv_data(publisher.name):
                    old_name = publisher.name
                    new_name = self.extract_first_field(old_name)
                    
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
    
    def generate_missing_images(self, dry_run):
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
        
        # Generate book covers
        for book in books_without_covers:
            try:
                # Create a filename for the cover
                filename = f"{book.id}_{book.title.replace(' ', '_')[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                covers_dir = os.path.join(media_root, 'covers')
                os.makedirs(covers_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(covers_dir, filename)
                
                # Generate the prompt
                authors = ", ".join([author.name for author in book.authors.all()])
                prompt = f"A professional book cover for '{book.title}' by {authors}. High quality, detailed, publishing industry standard."
                
                self.stdout.write(f'  Generating cover for book: {book.title}')
                
                # Generate the image
                success = generate_image(prompt, output_path)
                
                if success and os.path.exists(output_path):
                    # Update the book model with the new cover
                    relative_path = os.path.join('covers', filename)
                    book.cover = relative_path
                    book.save(update_fields=['cover'])
                    self.stdout.write(self.style.SUCCESS(f'    Successfully generated cover for book: {book.title}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to generate cover for book: {book.title}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating cover for book {book.id}: {str(e)}'))
        
        # Generate author photos
        for author in authors_without_photos:
            try:
                # Create a filename for the portrait
                filename = f"{author.id}_{author.name.replace(' ', '_')[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                authors_dir = os.path.join(media_root, 'authors')
                os.makedirs(authors_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(authors_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional portrait photograph of author {author.name}. High quality, detailed, professional headshot."
                
                self.stdout.write(f'  Generating photo for author: {author.name}')
                
                # Generate the image
                success = generate_image(prompt, output_path)
                
                if success and os.path.exists(output_path):
                    # Update the author model with the new photo
                    relative_path = os.path.join('authors', filename)
                    author.photo = relative_path
                    author.save(update_fields=['photo'])
                    self.stdout.write(self.style.SUCCESS(f'    Successfully generated photo for author: {author.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to generate photo for author: {author.name}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating photo for author {author.id}: {str(e)}'))
        
        # Generate publisher logos
        for publisher in publishers_without_logos:
            try:
                # Create a filename for the logo
                filename = f"{publisher.id}_{publisher.name.replace(' ', '_')[:30]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                publishers_dir = os.path.join(media_root, 'publishers')
                os.makedirs(publishers_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(publishers_dir, filename)
                
                # Generate the prompt
                prompt = f"A professional logo for publishing company '{publisher.name}'. Clean, corporate design, minimalist, high quality."
                
                self.stdout.write(f'  Generating logo for publisher: {publisher.name}')
                
                # Generate the image
                success = generate_image(prompt, output_path)
                
                if success and os.path.exists(output_path):
                    # Update the publisher model with the new logo
                    relative_path = os.path.join('publishers', filename)
                    publisher.logo = relative_path
                    publisher.save(update_fields=['logo'])
                    self.stdout.write(self.style.SUCCESS(f'    Successfully generated logo for publisher: {publisher.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'    Failed to generate logo for publisher: {publisher.name}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Error generating logo for publisher {publisher.id}: {str(e)}'))

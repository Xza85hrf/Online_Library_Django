import os
import re
from django.core.management.base import BaseCommand
from django.db.models import Q
from library.models import Book, Author, Publisher
from django.conf import settings

class Command(BaseCommand):
    help = 'Reset image paths for Kaggle-imported data to trigger regeneration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without making changes'
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Reset all image paths regardless of whether they appear to be from Kaggle'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_all = options['force_all']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        self.reset_book_covers(dry_run, force_all)
        self.reset_author_photos(dry_run, force_all)
        self.reset_publisher_logos(dry_run, force_all)
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Image paths reset completed! Run generate_missing_images to regenerate them.'))
        
    def is_likely_kaggle_item(self, name):
        """Check if an item name appears to be from Kaggle dataset"""
        # Look for patterns that indicate Kaggle data
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
    
    def check_image_exists(self, image_field):
        """Check if an image file actually exists"""
        if not image_field or not image_field.name:
            return False
            
        # Check if the file exists on disk
        if hasattr(image_field, 'path'):
            return os.path.exists(image_field.path)
        return False
    
    def reset_book_covers(self, dry_run, force_all):
        """Reset book cover paths for Kaggle-imported books"""
        self.stdout.write('Checking for books that need cover reset...')
        
        if force_all:
            # Reset all books
            books_to_reset = Book.objects.all()
        else:
            # Find books that appear to be from Kaggle or have invalid image paths
            kaggle_books = []
            for book in Book.objects.all():
                # Check if it's a Kaggle import or if the image doesn't exist
                if self.is_likely_kaggle_item(book.title) or (book.cover and not self.check_image_exists(book.cover)):
                    kaggle_books.append(book.id)
            
            books_to_reset = Book.objects.filter(id__in=kaggle_books)
        
        count = books_to_reset.count()
        self.stdout.write(f'Found {count} books to reset')
        
        reset_count = 0
        for book in books_to_reset:
            if book.cover:
                self.stdout.write(f'  Resetting cover for book: {book.title} (current path: {book.cover})')
                if not dry_run:
                    book.cover = None
                    book.save(update_fields=['cover'])
                    reset_count += 1
            else:
                self.stdout.write(f'  Book already has no cover: {book.title}')
        
        self.stdout.write(self.style.SUCCESS(f'Reset {reset_count} book covers'))
    
    def reset_author_photos(self, dry_run, force_all):
        """Reset author photo paths for Kaggle-imported authors"""
        self.stdout.write('Checking for authors that need photo reset...')
        
        if force_all:
            # Reset all authors
            authors_to_reset = Author.objects.all()
        else:
            # Find authors that appear to be from Kaggle or have invalid image paths
            kaggle_authors = []
            for author in Author.objects.all():
                # Check if it's a Kaggle import or if the image doesn't exist
                if self.is_likely_kaggle_item(author.name) or (author.photo and not self.check_image_exists(author.photo)):
                    kaggle_authors.append(author.id)
            
            authors_to_reset = Author.objects.filter(id__in=kaggle_authors)
        
        count = authors_to_reset.count()
        self.stdout.write(f'Found {count} authors to reset')
        
        reset_count = 0
        for author in authors_to_reset:
            if author.photo:
                self.stdout.write(f'  Resetting photo for author: {author.name} (current path: {author.photo})')
                if not dry_run:
                    author.photo = None
                    author.save(update_fields=['photo'])
                    reset_count += 1
            else:
                self.stdout.write(f'  Author already has no photo: {author.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Reset {reset_count} author photos'))
    
    def reset_publisher_logos(self, dry_run, force_all):
        """Reset publisher logo paths for Kaggle-imported publishers"""
        self.stdout.write('Checking for publishers that need logo reset...')
        
        if force_all:
            # Reset all publishers
            publishers_to_reset = Publisher.objects.all()
        else:
            # Find publishers that appear to be from Kaggle or have invalid image paths
            kaggle_publishers = []
            for publisher in Publisher.objects.all():
                # Check if it's a Kaggle import or if the image doesn't exist
                if self.is_likely_kaggle_item(publisher.name) or (publisher.logo and not self.check_image_exists(publisher.logo)):
                    kaggle_publishers.append(publisher.id)
            
            publishers_to_reset = Publisher.objects.filter(id__in=kaggle_publishers)
        
        count = publishers_to_reset.count()
        self.stdout.write(f'Found {count} publishers to reset')
        
        reset_count = 0
        for publisher in publishers_to_reset:
            if publisher.logo:
                self.stdout.write(f'  Resetting logo for publisher: {publisher.name} (current path: {publisher.logo})')
                if not dry_run:
                    publisher.logo = None
                    publisher.save(update_fields=['logo'])
                    reset_count += 1
            else:
                self.stdout.write(f'  Publisher already has no logo: {publisher.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Reset {reset_count} publisher logos'))

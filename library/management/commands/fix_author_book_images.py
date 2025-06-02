from django.core.management.base import BaseCommand
from django.db.models import Q
from library.models import Author, Book
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix author book thumbnails and regenerate missing images'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting author book image fix...'))
        
        # Fix author photos
        self.fix_author_photos()
        
        # Regenerate missing book covers
        self.regenerate_book_covers()
        
        self.stdout.write(self.style.SUCCESS('Author book image fix completed!'))
    
    def fix_author_photos(self):
        """Fix author photo paths and regenerate missing photos"""
        # Get all authors
        authors = Author.objects.all()
        
        fixed_count = 0
        regenerated_count = 0
        
        for author in authors:
            if author.photo and author.photo.name:
                # Check if the file exists
                full_path = os.path.join(settings.MEDIA_ROOT, author.photo.name)
                if not os.path.exists(full_path):
                    self.stdout.write(self.style.WARNING(
                        f'Author photo not found at {full_path} for author: {author.name}. Will trigger regeneration.'
                    ))
                    # Clear the photo field to trigger regeneration
                    author.photo = None
                    author.save()
                    regenerated_count += 1
                else:
                    self.stdout.write(f'Author photo exists for: {author.name}')
                    fixed_count += 1
            else:
                self.stdout.write(f'Author has no photo, will trigger regeneration: {author.name}')
                # Save to trigger the signal for image generation
                author.save()
                regenerated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Fixed {fixed_count} author photos and triggered regeneration for {regenerated_count} authors'
        ))
    
    def regenerate_book_covers(self):
        """Regenerate missing book covers"""
        # Get all books
        books = Book.objects.all()
        
        fixed_count = 0
        regenerated_count = 0
        
        for book in books:
            if book.cover and book.cover.name:
                # Check if the file exists
                full_path = os.path.join(settings.MEDIA_ROOT, book.cover.name)
                if not os.path.exists(full_path):
                    self.stdout.write(self.style.WARNING(
                        f'Book cover not found at {full_path} for book: {book.title}. Will trigger regeneration.'
                    ))
                    # Clear the cover field to trigger regeneration
                    book.cover = None
                    book.save()
                    regenerated_count += 1
                else:
                    self.stdout.write(f'Book cover exists for: {book.title}')
                    fixed_count += 1
            else:
                self.stdout.write(f'Book has no cover, will trigger regeneration: {book.title}')
                # Save to trigger the signal for image generation
                book.save()
                regenerated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Fixed {fixed_count} book covers and triggered regeneration for {regenerated_count} books'
        ))

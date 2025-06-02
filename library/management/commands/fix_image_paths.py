from django.core.management.base import BaseCommand
from django.db.models import Q
from library.models import Book, Author, Publisher
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix image paths in the database to match the actual file locations'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting image path fix...'))
        
        # Fix book covers
        self.fix_book_covers()
        
        # Fix author photos
        self.fix_author_photos()
        
        # Fix publisher logos
        self.fix_publisher_logos()
        
        self.stdout.write(self.style.SUCCESS('Image path fix completed!'))
    
    def fix_book_covers(self):
        """Fix book cover paths from book_covers/ to covers/"""
        books_with_wrong_path = Book.objects.filter(
            Q(cover__startswith='book_covers/') | 
            Q(cover='')
        )
        
        fixed_count = 0
        for book in books_with_wrong_path:
            if book.cover and book.cover.name and book.cover.name.startswith('book_covers/'):
                # Extract filename from path
                filename = os.path.basename(book.cover.name)
                # Create new path
                new_path = f'covers/{filename}'
                
                # Check if the file exists in the new location
                full_path = os.path.join(settings.MEDIA_ROOT, new_path)
                if os.path.exists(full_path):
                    # Update the path in the database
                    book.cover = new_path
                    book.save(update_fields=['cover'])
                    fixed_count += 1
                    self.stdout.write(f'Fixed cover path for book: {book.title}')
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Cover file not found at {full_path} for book: {book.title}. Will trigger regeneration.'
                    ))
                    # Clear the cover field to trigger regeneration
                    book.cover = None
                    book.save(update_fields=['cover'])
            elif not book.cover:
                self.stdout.write(f'Book has no cover, will trigger regeneration: {book.title}')
                # Save to trigger the signal for image generation
                book.save()
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} book cover paths'))
    
    def fix_author_photos(self):
        """Fix any issues with author photos"""
        authors_without_photos = Author.objects.filter(photo='')
        
        for author in authors_without_photos:
            self.stdout.write(f'Author has no photo, will trigger regeneration: {author.name}')
            # Save to trigger the signal for image generation
            author.save()
        
        self.stdout.write(self.style.SUCCESS(f'Processed {authors_without_photos.count()} authors without photos'))
    
    def fix_publisher_logos(self):
        """Fix any issues with publisher logos"""
        publishers_without_logos = Publisher.objects.filter(logo='')
        
        for publisher in publishers_without_logos:
            self.stdout.write(f'Publisher has no logo, will trigger regeneration: {publisher.name}')
            # Save to trigger the signal for image generation
            publisher.save()
        
        self.stdout.write(self.style.SUCCESS(f'Processed {publishers_without_logos.count()} publishers without logos'))

import os
import re
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Fix specific books with incorrect titles or missing Flux AI images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        # List of books to fix with their correct titles
        books_to_fix = [
            {
                'search_title': "What If?: The World's Foremost Military Historians Imagine What Might Have Been",
                'new_title': "What If?: The World's Foremost Military Historians Imagine What Might Have Been",
                'regenerate_image': True
            },
            {
                'search_title': "0425176428",
                'new_title': "Sharpe's Prey: Richard Sharpe and the Expedition to Copenhagen, 1807",
                'regenerate_image': True
            },
            {
                'search_title': "074322678X",
                'new_title': "The Da Vinci Code",
                'regenerate_image': True
            },
            {
                'search_title': "080652121X",
                'new_title': "The Lovely Bones",
                'regenerate_image': True
            }
        ]
        
        fixed_count = 0
        
        for book_info in books_to_fix:
            search_title = book_info['search_title']
            new_title = book_info['new_title']
            regenerate_image = book_info['regenerate_image']
            
            self.stdout.write(f'Looking for book with title: "{search_title}"')
            
            # Find the book by title
            books = Book.objects.filter(title=search_title)
            
            if not books.exists():
                self.stdout.write(self.style.WARNING(f'  No book found with title: "{search_title}"'))
                continue
            
            for book in books:
                self.stdout.write(f'  Found book ID {book.id}: "{book.title}"')
                
                # Update the title if needed
                if book.title != new_title:
                    self.stdout.write(f'  Updating title from "{book.title}" to "{new_title}"')
                    
                    if not dry_run:
                        book.title = new_title
                        book.save(update_fields=['title'])
                        self.stdout.write(self.style.SUCCESS(f'    Updated title successfully'))
                
                # Regenerate the image if requested
                if regenerate_image:
                    self.stdout.write(f'  Regenerating image for book ID {book.id}: "{book.title}"')
                    
                    if not dry_run:
                        success = self.regenerate_book_cover(book)
                        if success:
                            self.stdout.write(self.style.SUCCESS(f'    Successfully regenerated image'))
                            fixed_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'    Failed to regenerate image'))
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully fixed {fixed_count} books'))
        else:
            self.stdout.write('No books were fixed')
    
    def regenerate_book_cover(self, book):
        """Regenerate a book cover using Flux AI"""
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
            
            # Create a detailed prompt for better image generation
            prompt = f"A professional book cover for '{book.title}' by {authors}. High quality, detailed, publishing industry standard, book cover art, professional design, vibrant colors."
            
            self.stdout.write(f'    Generating cover with prompt: {prompt}')
            
            # Generate the image using flux_wrapper.py
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            
            # Check if flux_wrapper.py exists
            if not os.path.exists(flux_wrapper_path):
                self.stdout.write(self.style.ERROR(f'    Flux wrapper not found at {flux_wrapper_path}'))
                return False
            
            cmd = [
                "python", flux_wrapper_path,
                "--prompt", prompt,
                "--output", output_path
            ]
            
            self.stdout.write(f'    Running command: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if success:
                # Update the book model with the new cover
                relative_path = os.path.join('covers', filename)
                book.cover = relative_path
                book.save(update_fields=['cover'])
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    Failed to generate cover: {result.stderr[:200]}'))
                return False
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error generating cover: {str(e)}'))
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

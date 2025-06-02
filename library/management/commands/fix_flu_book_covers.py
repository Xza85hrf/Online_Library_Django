import os
import re
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from library.models import Book

class Command(BaseCommand):
    help = 'Fix specific broken book covers for books with "Flu" in the title'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--fallback',
            action='store_true',
            help='Force fallback to basic image generation'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fallback = options['fallback']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        # List of book IDs to fix (as mentioned by the user)
        book_ids = [13, 18, 26, 33, 38, 43]
        
        self.fix_specific_book_covers(book_ids, dry_run, fallback)
        
        self.stdout.write(self.style.SUCCESS('Flu book cover fix completed!'))
    
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
    
    def fix_specific_book_covers(self, book_ids, dry_run, fallback):
        """Fix covers for specific books by ID"""
        self.stdout.write('Fixing covers for specific books...')
        
        fixed_count = 0
        for book_id in book_ids:
            try:
                book = Book.objects.get(id=book_id)
                self.stdout.write(f'Processing book ID {book_id}: {book.title}')
                
                # Create a more unique filename using book ID and full title
                # Ensure we include more of the title to make it unique
                safe_title = self.sanitize_filename(book.title)
                # Use more of the title to ensure uniqueness
                filename = f"{book_id}_Flu_{book_id}_{safe_title[:50]}.jpg"
                
                # Define the media path
                media_root = settings.MEDIA_ROOT
                covers_dir = os.path.join(media_root, 'covers')
                os.makedirs(covers_dir, exist_ok=True)
                
                # Full path to save the image
                output_path = os.path.join(covers_dir, filename)
                
                # Show current and new paths
                current_path = book.cover.name if book.cover else 'None'
                self.stdout.write(f'  Current path: {current_path}')
                self.stdout.write(f'  New path: covers/{filename}')
                
                if not dry_run:
                    # Generate the prompt
                    authors = ", ".join([author.name for author in book.authors.all()])
                    if not authors:
                        authors = "Unknown Author"
                    
                    prompt = f"A professional book cover for '{book.title}' by {authors}. High quality, detailed, publishing industry standard."
                    
                    self.stdout.write(f'  Regenerating cover for book: {book.title}')
                    
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
                    
                    self.stdout.write(f'    Running command: {" ".join(cmd)}')
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    success = result.returncode == 0 and os.path.exists(output_path)
                    
                    if success and os.path.exists(output_path):
                        # Update the book model with the new cover
                        relative_path = os.path.join('covers', filename)
                        book.cover = relative_path
                        book.save(update_fields=['cover'])
                        fixed_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Successfully regenerated cover for book: {book.title}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'    Failed to regenerate cover for book: {book.title}'))
                        if result.stderr:
                            self.stdout.write(f'    Error: {result.stderr[:200]}...')
            
            except Book.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Book with ID {book_id} not found'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing book ID {book_id}: {str(e)}'))
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} book covers'))
        else:
            self.stdout.write('No book covers were fixed')

import os
import re
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from library.models import Book

class Command(BaseCommand):
    help = 'Regenerate high-quality covers for specific books with Flux AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retry-count',
            type=int,
            default=3,
            help='Number of times to retry generation if it fails'
        )
        parser.add_argument(
            '--pause-seconds',
            type=int,
            default=5,
            help='Seconds to pause between generation attempts'
        )

    def handle(self, *args, **options):
        retry_count = options['retry_count']
        pause_seconds = options['pause_seconds']
        
        # List of book IDs to fix (as mentioned by the user)
        book_ids = [13, 18, 26, 33, 38, 43]
        
        self.regenerate_book_covers(book_ids, retry_count, pause_seconds)
        
        self.stdout.write(self.style.SUCCESS('Book cover regeneration completed!'))
    
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
    
    def regenerate_book_covers(self, book_ids, retry_count, pause_seconds):
        """Regenerate covers for specific books using Flux AI"""
        self.stdout.write('Regenerating covers for specific books...')
        
        # Check if Flux AI is available
        flux_available = self.check_flux_availability()
        if not flux_available:
            self.stdout.write(self.style.ERROR('Flux AI is not available. Cannot generate high-quality images.'))
            return
        
        success_count = 0
        for book_id in book_ids:
            try:
                book = Book.objects.get(id=book_id)
                self.stdout.write(f'Processing book ID {book_id}: {book.title}')
                
                # Create a unique filename
                safe_title = self.sanitize_filename(book.title)
                filename = f"{book_id}_Flu_AI_{safe_title[:40]}.jpg"
                
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
                
                # Generate the prompt
                authors = ", ".join([author.name for author in book.authors.all()])
                if not authors:
                    authors = "Unknown Author"
                
                # Create a detailed prompt for better image generation
                prompt = self.create_detailed_prompt(book.title, authors)
                
                self.stdout.write(f'  Regenerating cover with Flux AI for book: {book.title}')
                
                # Try multiple times if needed
                success = False
                for attempt in range(retry_count):
                    if attempt > 0:
                        self.stdout.write(f'    Retry attempt {attempt+1}/{retry_count}')
                        time.sleep(pause_seconds)
                    
                    # Generate the image using direct_flux_generator.py (not flux_wrapper.py)
                    # This bypasses the wrapper and calls the Flux AI model directly
                    direct_flux_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'direct_flux_generator.py')
                    
                    if os.path.exists(direct_flux_path):
                        # Set environment variables for better CUDA memory management
                        env = os.environ.copy()
                        env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
                        env["CUDA_VISIBLE_DEVICES"] = "0"
                        
                        cmd = [
                            "conda", "run", "-n", "flux", "python", direct_flux_path,
                            "--prompt", prompt,
                            "--output", output_path
                        ]
                        
                        self.stdout.write(f'    Running direct Flux AI generation')
                        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                        success = result.returncode == 0 and os.path.exists(output_path)
                        
                        if success:
                            # Update the book model with the new cover
                            relative_path = os.path.join('covers', filename)
                            book.cover = relative_path
                            book.save(update_fields=['cover'])
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS(f'    Successfully generated high-quality cover'))
                            break
                        else:
                            self.stdout.write(self.style.WARNING(f'    Direct Flux AI generation failed, trying fallback...'))
                    else:
                        self.stdout.write(self.style.WARNING(f'    Direct Flux generator not found at {direct_flux_path}'))
                    
                    # If direct generation failed, try the wrapper with fallback disabled
                    flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
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
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f'    Successfully generated cover'))
                        break
                
                if not success:
                    self.stdout.write(self.style.ERROR(f'    Failed to generate cover after {retry_count} attempts'))
            
            except Book.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Book with ID {book_id} not found'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing book ID {book_id}: {str(e)}'))
            
            # Pause between books to avoid overwhelming the GPU
            if book_id != book_ids[-1]:  # Don't pause after the last book
                self.stdout.write(f'  Pausing for {pause_seconds} seconds before next book...')
                time.sleep(pause_seconds)
        
        if success_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully regenerated {success_count} book covers'))
        else:
            self.stdout.write(self.style.ERROR('No book covers were successfully regenerated'))
    
    def check_flux_availability(self):
        """Check if Flux AI is available"""
        try:
            # Check if direct_flux_generator.py exists
            direct_flux_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'direct_flux_generator.py')
            flux_wrapper_path = os.path.join(settings.BASE_DIR, 'library', 'ai_utils', 'flux_wrapper.py')
            
            if os.path.exists(direct_flux_path) or os.path.exists(flux_wrapper_path):
                return True
            
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking Flux availability: {str(e)}'))
            return False
    
    def create_detailed_prompt(self, title, authors):
        """Create a detailed prompt for better image generation"""
        # Base prompt
        base_prompt = f"A professional book cover for '{title}' by {authors}."
        
        # Add details based on the book title
        if "Flu" in title:
            return f"{base_prompt} The cover should depict a dramatic medical theme with imagery related to the 1918 influenza pandemic. Include subtle virus imagery, historical elements, and a somber, scientific aesthetic. Use a color palette of blues, grays, and reds. High quality, detailed, publishing industry standard."
        else:
            return f"{base_prompt} High quality, detailed, publishing industry standard."

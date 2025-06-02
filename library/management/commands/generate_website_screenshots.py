from django.core.management.base import BaseCommand
from django.urls import reverse
from django.conf import settings
import os
import time
from pathlib import Path
import subprocess
import sys

class Command(BaseCommand):
    help = 'Generate screenshots of all main pages of the website for documentation purposes'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', type=str, default='http://127.0.0.1:8000',
                            help='Base URL of the website')
        parser.add_argument('--output-dir', type=str, default=None,
                            help='Output directory for screenshots (default: project_root/screenshots)')
        parser.add_argument('--delay', type=float, default=1.0,
                            help='Delay in seconds between page loads')
        parser.add_argument('--width', type=int, default=1280,
                            help='Screenshot width in pixels')
        parser.add_argument('--height', type=int, default=800,
                            help='Screenshot height in pixels')
        parser.add_argument('--full-page', action='store_true',
                            help='Capture full page height')

    def handle(self, *args, **options):
        base_url = options['base_url']
        delay = options['delay']
        width = options['width']
        height = options['height']
        full_page = options['full_page']
        
        # Set up output directory
        if options['output_dir']:
            output_dir = Path(options['output_dir'])
        else:
            output_dir = Path(settings.BASE_DIR) / 'screenshots'
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        self.stdout.write(f"Screenshots will be saved to: {output_dir}")
        
        # Define pages to capture
        pages = [
            # Main pages
            {'url': '/', 'name': '01_home'},
            {'url': '/books/', 'name': '02_books_list'},
            {'url': '/authors/', 'name': '03_authors_list'},
            {'url': '/publishers/', 'name': '04_publishers_list'},
            
            # Detail pages (need to get actual IDs)
            {'url': '/books/1/', 'name': '05_book_detail'},
            {'url': '/authors/1/', 'name': '06_author_detail'},
            {'url': '/publishers/1/', 'name': '07_publisher_detail'},
            
            # Filtered views
            {'url': '/books/?genre=fiction', 'name': '08_books_fiction'},
            {'url': '/books/?genre=fantasy', 'name': '09_books_fantasy'},
            {'url': '/books/?availability=available', 'name': '10_books_available'},
            
            # Information pages
            {'url': '/about/', 'name': '11_about'},
            {'url': '/events/', 'name': '12_events'},
            {'url': '/digital-library/', 'name': '13_digital_library'},
            {'url': '/how-to-borrow/', 'name': '14_how_to_borrow'},
            {'url': '/rules/', 'name': '15_rules'},
            {'url': '/opening-hours/', 'name': '16_opening_hours'},
        ]
        
        # Check if playwright is installed
        try:
            import playwright
        except ImportError:
            self.stdout.write(self.style.WARNING(
                "Playwright not found. Installing playwright and dependencies..."
            ))
            subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
            subprocess.run([sys.executable, "-m", "playwright", "install"])
        
        # Import playwright after ensuring it's installed
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={'width': width, 'height': height})
            page = context.new_page()
            
            for page_info in pages:
                url = f"{base_url}{page_info['url']}"
                filename = f"{page_info['name']}.png"
                output_path = output_dir / filename
                
                self.stdout.write(f"Capturing {url} as {filename}")
                
                # Navigate to the page
                page.goto(url)
                
                # Wait for page to load
                page.wait_for_load_state('networkidle')
                time.sleep(delay)  # Additional delay for any animations
                
                # Take screenshot
                if full_page:
                    page.screenshot(path=str(output_path), full_page=True)
                else:
                    page.screenshot(path=str(output_path))
                
                self.stdout.write(self.style.SUCCESS(f"Saved screenshot to {output_path}"))
            
            # Additional dynamic pages - find actual IDs from the page
            # Books with different genres
            self.stdout.write("Finding additional book IDs for genre examples...")
            page.goto(f"{base_url}/books/")
            book_ids = page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('.book-card a'));
                return links.slice(0, 5).map(link => {
                    const href = link.getAttribute('href');
                    const match = href.match(/\\/books\\/(\\d+)\\//);
                    return match ? match[1] : null;
                }).filter(id => id !== null);
            }""")
            
            # Take screenshots of some specific book details
            for i, book_id in enumerate(book_ids):
                url = f"/books/{book_id}/"
                filename = f"17_book_detail_{i+1}.png"
                output_path = output_dir / filename
                
                self.stdout.write(f"Capturing {base_url}{url} as {filename}")
                page.goto(f"{base_url}{url}")
                page.wait_for_load_state('networkidle')
                time.sleep(delay)
                
                if full_page:
                    page.screenshot(path=str(output_path), full_page=True)
                else:
                    page.screenshot(path=str(output_path))
                
                self.stdout.write(self.style.SUCCESS(f"Saved screenshot to {output_path}"))
            
            # Close browser
            browser.close()
        
        # Create a README.md file in the screenshots directory
        readme_path = output_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("# Library Website Screenshots\n\n")
            f.write("These screenshots showcase the Library Website interface without requiring you to run the project.\n\n")
            f.write("## Main Pages\n\n")
            
            # Add screenshots to the README
            for page_info in pages:
                filename = f"{page_info['name']}.png"
                page_name = page_info['name'].split('_', 1)[1].replace('_', ' ').title()
                f.write(f"### {page_name}\n\n")
                f.write(f"![{page_name}](./{filename})\n\n")
            
            # Add book detail screenshots
            f.write("## Additional Book Details\n\n")
            for i in range(len(book_ids)):
                filename = f"17_book_detail_{i+1}.png"
                f.write(f"### Book Detail Example {i+1}\n\n")
                f.write(f"![Book Detail {i+1}](./{filename})\n\n")
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully generated {len(pages) + len(book_ids)} screenshots in {output_dir}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"README.md created at {readme_path}"
        ))

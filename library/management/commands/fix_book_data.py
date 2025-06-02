import os
import re
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from library.models import Book, Author, Publisher
from django.conf import settings
from pathlib import Path
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Fixes book data issues including categories, duplicate authors, and improper descriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--fix-categories',
            action='store_true',
            help='Fix missing book categories',
        )
        parser.add_argument(
            '--fix-authors',
            action='store_true',
            help='Fix duplicate authors',
        )
        parser.add_argument(
            '--fix-descriptions',
            action='store_true',
            help='Fix improper book descriptions',
        )
        parser.add_argument(
            '--create-category-model',
            action='store_true',
            help='Create Category model and migrate genres to categories',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Fix all issues (categories, authors, descriptions, create category model)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_categories = options['fix_categories'] or options['fix_all']
        fix_authors = options['fix_authors'] or options['fix_all']
        fix_descriptions = options['fix_descriptions'] or options['fix_all']
        create_category_model = options['create_category_model'] or options['fix_all']

        if not any([fix_categories, fix_authors, fix_descriptions, create_category_model]):
            self.stdout.write(self.style.WARNING(
                'No fix options specified. Use --fix-categories, --fix-authors, --fix-descriptions, --create-category-model, or --fix-all'
            ))
            return

        # Load book data corrections
        corrections = self.load_book_corrections()

        # Start transaction
        with transaction.atomic():
            if create_category_model:
                self.create_categories_from_genres(dry_run)
            
            if fix_categories:
                self.fix_book_categories(dry_run, corrections)
            
            if fix_authors:
                self.fix_duplicate_authors(dry_run, corrections)
            
            if fix_descriptions:
                self.fix_book_descriptions(dry_run, corrections)

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run completed. No changes were made.'))
        else:
            self.stdout.write(self.style.SUCCESS('Book data fixes completed successfully.'))

    def load_book_corrections(self):
        """Load book corrections from JSON file, or create default corrections if file doesn't exist"""
        corrections_path = Path(settings.BASE_DIR) / 'library' / 'data' / 'book_corrections.json'
        
        # Default corrections for common books
        default_corrections = {
            # Harry Potter series
            "9780747532743": {
                "title": "Harry Potter i Kamień Filozoficzny",
                "author": "J.K. Rowling",
                "categories": ["Fantasy", "Literatura młodzieżowa", "Przygodowe"],
                "description": "Harry Potter, chłopiec, który w swoje jedenaste urodziny dowiaduje się, że jest osieroconym synem dwóch potężnych czarodziejów i posiada wyjątkowe magiczne moce. Rozpoczyna naukę w Szkole Magii i Czarodziejstwa w Hogwarcie, gdzie odkrywa prawdę o swojej przeszłości i stawia czoła niebezpieczeństwom czarodziejskiego świata."
            },
            "9780747538486": {
                "title": "Harry Potter i Komnata Tajemnic",
                "author": "J.K. Rowling",
                "categories": ["Fantasy", "Literatura młodzieżowa", "Przygodowe"],
                "description": "Harry Potter powraca do Hogwartu na drugi rok nauki, tylko po to, by odkryć, że uczniowie są petryfikowani przez nieznaną siłę. Razem z przyjaciółmi musi rozwiązać zagadkę Komnaty Tajemnic i powstrzymać potwora, który w niej mieszka."
            },
            # The Da Vinci Code
            "074322678X": {
                "title": "Kod Leonarda da Vinci",
                "author": "Dan Brown",
                "categories": ["Thriller", "Sensacja", "Tajemnica"],
                "description": "Robert Langdon, profesor symboliki z Harvardu, zostaje wezwany do Luwru, gdzie znaleziono ciało kustosza. Obok zwłok znajduje się zagadkowy szyfr. Langdon i kryptolog Sophie Neveu muszą rozwiązać serię zagadek, które prowadzą do odkrycia tajemnicy pilnie strzeżonej przez tajne stowarzyszenie od dwóch tysięcy lat."
            },
            # Add more books as needed
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(corrections_path), exist_ok=True)
        
        # If file doesn't exist, create it with default corrections
        if not os.path.exists(corrections_path):
            with open(corrections_path, 'w', encoding='utf-8') as f:
                json.dump(default_corrections, f, ensure_ascii=False, indent=4)
            self.stdout.write(f"Created default book corrections file at {corrections_path}")
            return default_corrections
        
        # Load existing corrections
        try:
            with open(corrections_path, 'r', encoding='utf-8') as f:
                corrections = json.load(f)
            self.stdout.write(f"Loaded book corrections from {corrections_path}")
            return corrections
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading book corrections: {e}"))
            return default_corrections

    def fix_book_categories(self, dry_run, corrections):
        """Fix missing book categories by updating the genres JSONField"""
        self.stdout.write("Fixing book categories...")
        
        # Define common categories/genres
        common_categories = [
            "Fantasy", "Literatura młodzieżowa", "Przygodowe", "Thriller", 
            "Sensacja", "Tajemnica", "Science Fiction", "Romans", "Horror",
            "Literatura piękna", "Biografia", "Historia", "Kryminał"
        ]
        
        # Fix books without genres
        books_without_genres = Book.objects.filter(genres__isnull=True)
        books_with_empty_genres = Book.objects.exclude(genres__isnull=True).filter(genres={})  # Empty JSON object
        books_to_fix = list(books_without_genres) + list(books_with_empty_genres)
        
        self.stdout.write(f"Found {len(books_to_fix)} books without genres")
        
        for book in books_to_fix:
            # Check if we have corrections for this book
            book_correction = None
            if book.isbn and book.isbn in corrections:
                book_correction = corrections[book.isbn]
            
            if book_correction and 'categories' in book_correction:
                category_names = book_correction['categories']
                if dry_run:
                    self.stdout.write(f"Would assign genres {', '.join(category_names)} to book: {book.title}")
                else:
                    book.genres = category_names
                    book.save()
                    self.stdout.write(f"Assigned genres {', '.join(category_names)} to book: {book.title}")
            else:
                # Assign default categories based on book title or description
                assigned_categories = self.guess_categories(book)
                if assigned_categories:
                    if dry_run:
                        self.stdout.write(f"Would assign guessed genres {', '.join(assigned_categories)} to book: {book.title}")
                    else:
                        book.genres = assigned_categories
                        book.save()
                        self.stdout.write(f"Assigned guessed genres {', '.join(assigned_categories)} to book: {book.title}")
                else:
                    # Assign a default genre if we can't guess
                    if dry_run:
                        self.stdout.write(f"Would assign default genre 'Literatura piękna' to book: {book.title}")
                    else:
                        book.genres = ["Literatura piękna"]
                        book.save()
                        self.stdout.write(f"Assigned default genre 'Literatura piękna' to book: {book.title}")

    def guess_categories(self, book):
        """Guess book categories based on title and description"""
        title = book.title.lower() if book.title else ""
        description = book.description.lower() if book.description else ""
        
        categories = []
        
        # Fantasy keywords
        fantasy_keywords = ["magic", "wizard", "dragon", "spell", "hogwarts", "potter", "fantasy", 
                           "magia", "czarodziej", "smok", "zaklęcie", "fantastyka"]
        
        # Thriller/Mystery keywords
        thriller_keywords = ["murder", "mystery", "crime", "detective", "thriller", "secret", "code",
                            "morderstwo", "tajemnica", "zbrodnia", "detektyw", "kod", "sekret"]
        
        # Science Fiction keywords
        scifi_keywords = ["space", "alien", "future", "robot", "technology", "science fiction", 
                         "kosmos", "kosmita", "przyszłość", "robot", "technologia"]
        
        # Romance keywords
        romance_keywords = ["love", "romance", "relationship", "passion", 
                           "miłość", "romans", "związek", "namiętność"]
        
        # Check for fantasy
        if any(keyword in title or keyword in description for keyword in fantasy_keywords):
            categories.append("Fantasy")
            categories.append("Literatura młodzieżowa")
        
        # Check for thriller/mystery
        if any(keyword in title or keyword in description for keyword in thriller_keywords):
            categories.append("Thriller")
            categories.append("Tajemnica")
        
        # Check for science fiction
        if any(keyword in title or keyword in description for keyword in scifi_keywords):
            categories.append("Science Fiction")
        
        # Check for romance
        if any(keyword in title or keyword in description for keyword in romance_keywords):
            categories.append("Romans")
        
        return list(set(categories))  # Remove duplicates

    def fix_duplicate_authors(self, dry_run, corrections):
        """Fix duplicate authors in books"""
        self.stdout.write("Fixing duplicate authors...")
        
        try:
            # Get all books
            self.stdout.write("Fetching books...")
            books = Book.objects.prefetch_related('authors')
            self.stdout.write(f"Found {books.count()} books")
            books_fixed = 0
            
            # Common author corrections for books without ISBN
            common_author_corrections = {
                "The Da Vinci Code": "Dan Brown",
                "Angels & Demons": "Dan Brown",
                "Inferno": "Dan Brown",
                "The Lost Symbol": "Dan Brown",
                "Harry Potter": "J.K. Rowling",
                "Zmierzch": "Stephenie Meyer",
                "Twilight": "Stephenie Meyer",
                "New Moon": "Stephenie Meyer",
                "Eclipse": "Stephenie Meyer",
                "Breaking Dawn": "Stephenie Meyer",
                "The Hunger Games": "Suzanne Collins",
                "Catching Fire": "Suzanne Collins",
                "Mockingjay": "Suzanne Collins",
                "The Fault in Our Stars": "John Green",
                "Looking for Alaska": "John Green",
                "Paper Towns": "John Green",
                "The Hobbit": "J.R.R. Tolkien",
                "The Lord of the Rings": "J.R.R. Tolkien",
                "The Silmarillion": "J.R.R. Tolkien",
                "A Game of Thrones": "George R.R. Martin",
                "A Clash of Kings": "George R.R. Martin",
                "A Storm of Swords": "George R.R. Martin",
                "A Feast for Crows": "George R.R. Martin",
                "A Dance with Dragons": "George R.R. Martin",
                "The Great Gatsby": "F. Scott Fitzgerald",
                "To Kill a Mockingbird": "Harper Lee",
                "1984": "George Orwell",
                "Animal Farm": "George Orwell",
                "Pride and Prejudice": "Jane Austen",
                "Sense and Sensibility": "Jane Austen",
                "Emma": "Jane Austen",
                "Persuasion": "Jane Austen",
                "Northanger Abbey": "Jane Austen",
                "Mansfield Park": "Jane Austen",
                "Flu": "Gina Kolata",
                "Flu: The Story": "Gina Kolata",
                "Classical Mythology": "Mark P. O. Morford",
                "Clara Callan": "Richard Bruce Wright",
                "Decision in Normandy": "Carlo D'Este",
                "The Lovely Bones": "Alice Sebold",
                "The Middle Stories": "Sheila Heti",
                "Jane Doe": "Victoria Helen Stone",
                "The Witchfinder": "Loren D. Estleman",
                "More Cunning Than Man": "Robert Hendrickson",
                "Goodbye to the Buttermilk Sky": "Julia Oliver",
                "The Testament": "John Grisham",
                "Beloved": "Toni Morrison"
            }
            
            # Count books with Unknown Author
            unknown_author_count = 0
            for book in books:
                if book.authors.filter(name__icontains="Unknown Author").exists():
                    unknown_author_count += 1
            self.stdout.write(f"Found {unknown_author_count} books with Unknown Author")
            
            # Process books in smaller batches to avoid memory issues
            batch_size = 10
            total_books = books.count()
            for i in range(0, total_books, batch_size):
                batch = books[i:i+batch_size]
                self.stdout.write(f"Processing batch {i//batch_size + 1}/{(total_books + batch_size - 1)//batch_size}...")
                
                for book in batch:
                    self.stdout.write(f"Processing book: {book.title}")
                    # Check for duplicate authors
                    author_ids = set()
                    duplicate_authors = []
                    
                    for author in book.authors.all():
                        if author.id in author_ids:
                            duplicate_authors.append(author)
                        else:
                            author_ids.add(author.id)
                    
                    if duplicate_authors:
                        if dry_run:
                            self.stdout.write(f"Would remove {len(duplicate_authors)} duplicate authors from book: {book.title}")
                        else:
                            for author in duplicate_authors:
                                book.authors.remove(author)
                                self.stdout.write(f"Removed duplicate author {author.name} from book: {book.title}")
                            books_fixed += 1
                    
                    # Check for "Unknown Author" and replace if we have corrections
                    unknown_authors = book.authors.filter(name__icontains="Unknown Author")
                    if unknown_authors.exists():
                        correct_author_name = None
                        
                        # Try to find author in corrections by ISBN
                        if book.isbn and book.isbn in corrections and 'author' in corrections[book.isbn]:
                            correct_author_name = corrections[book.isbn]['author']
                        else:
                            # Try to match by title pattern
                            for title_pattern, author_name in common_author_corrections.items():
                                if title_pattern.lower() in book.title.lower():
                                    correct_author_name = author_name
                                    break
                            
                            # If still no match, try exact title match
                            if not correct_author_name and book.title in common_author_corrections:
                                correct_author_name = common_author_corrections[book.title]
                        
                        if correct_author_name:
                            if dry_run:
                                self.stdout.write(f"Would replace Unknown Author with {correct_author_name} for book: {book.title}")
                            else:
                                # Remove unknown authors
                                for unknown_author in unknown_authors:
                                    book.authors.remove(unknown_author)
                                
                                # Add correct author
                                correct_author, created = Author.objects.get_or_create(name=correct_author_name)
                                book.authors.add(correct_author)
                                self.stdout.write(f"Replaced Unknown Author with {correct_author_name} for book: {book.title}")
                                books_fixed += 1
            
            self.stdout.write(f"{'Would fix' if dry_run else 'Fixed'} authors for {books_fixed} books")
            return books_fixed
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fixing duplicate authors: {e}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            return 0

    def fix_book_descriptions(self, dry_run, corrections):
        """Fix improper book descriptions"""
        self.stdout.write("Fixing book descriptions...")
        
        # Find books with ISBN as description or "A book titled [ISBN]"
        isbn_pattern = re.compile(r'^(\d{10}|\d{13})$|^A book titled (\d{10}|\d{13})$')
        books_with_isbn_desc = []
        
        for book in Book.objects.all():
            if book.description and isbn_pattern.match(book.description.strip()):
                books_with_isbn_desc.append(book)
        
        self.stdout.write(f"Found {len(books_with_isbn_desc)} books with ISBN as description")
        books_fixed = 0
        
        for book in books_with_isbn_desc:
            # Check if we have corrections for this book
            if book.isbn and book.isbn in corrections and 'description' in corrections[book.isbn]:
                correct_description = corrections[book.isbn]['description']
                correct_title = corrections[book.isbn].get('title', book.title)
                
                if dry_run:
                    self.stdout.write(f"Would update description for book: {book.title}")
                    if book.title != correct_title:
                        self.stdout.write(f"Would update title from '{book.title}' to '{correct_title}'")
                else:
                    # Update description
                    old_description = book.description
                    book.description = correct_description
                    
                    # Update title if needed
                    if book.title != correct_title:
                        old_title = book.title
                        book.title = correct_title
                        self.stdout.write(f"Updated title from '{old_title}' to '{correct_title}'")
                    
                    book.save()
                    self.stdout.write(f"Updated description for book: {book.title}")
                    books_fixed += 1
            else:
                # Generate a generic description if no correction is available
                if dry_run:
                    self.stdout.write(f"Would generate generic description for book: {book.title}")
                else:
                    # Create a simple description based on the title
                    generic_description = f"Książka '{book.title}' wydana przez {book.publisher.name if book.publisher else 'nieznanego wydawcę'}."
                    book.description = generic_description
                    book.save()
                    self.stdout.write(f"Generated generic description for book: {book.title}")
                    books_fixed += 1
        
        self.stdout.write(f"{'Would fix' if dry_run else 'Fixed'} descriptions for {books_fixed} books")
        
    def create_categories_from_genres(self, dry_run):
        """Create Category model and migrate genres to categories"""
        self.stdout.write("Creating Category model and migrating genres to categories...")
        
        # Check if Category model already exists in the app
        try:
            from library.models import Category
            self.stdout.write("Category model already exists.")
            category_model_exists = True
        except ImportError:
            category_model_exists = False
            self.stdout.write("Category model does not exist yet.")
        
        if not category_model_exists:
            if dry_run:
                self.stdout.write("Would create Category model (requires manual migration)")
                self.stdout.write("\nTo create the Category model, add the following to library/models.py:\n")
                self.stdout.write("""
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'
""")
                self.stdout.write("\nThen add a ManyToMany relationship to the Book model:\n")
                self.stdout.write("""    categories = models.ManyToManyField('Category', related_name='books', blank=True)""")
                self.stdout.write("\nThen run migrations:\n")
                self.stdout.write("python manage.py makemigrations")
                self.stdout.write("python manage.py migrate")
                return
        
        # Get all unique genres from books
        all_genres = set()
        for book in Book.objects.exclude(genres__isnull=True).exclude(genres={}):
            if isinstance(book.genres, list):
                all_genres.update(book.genres)
            elif isinstance(book.genres, dict):
                all_genres.update(book.genres.keys())
        
        self.stdout.write(f"Found {len(all_genres)} unique genres")
        
        # Polish translation mapping for common genres
        # This will ensure categories are created with Polish names
        polish_genre_mapping = {
            'Adventure': 'Przygodowe',
            'Business': 'Biznes',
            'Dystopian': 'Dystopia',
            'Thriller': 'Thriller',
            'Biography': 'Biografia',
            'Horror': 'Horror',
            'Non-Fiction': 'Literatura faktu',
            'Self-Help': 'Poradniki',
            'Mystery': 'Kryminał',
            'Young Adult': 'Literatura młodzieżowa',
            'Romance': 'Romans',
            'Drama': 'Dramat',
            'Science Fiction': 'Science Fiction',
            'Classic': 'Klasyka',
            'Fiction': 'Literatura piękna',
            'Fantasy': 'Fantastyka',
            'Crime': 'Kryminał',
            'Epic': 'Epika',
            'Science': 'Nauka',
            'Poetry': 'Poezja',
            'Classics': 'Klasyka',
            "Children's": 'Literatura dziecięca'
        }
        
        # Create categories from genres
        from library.models import Category
        categories_created = 0
        categories_map = {}
        
        for genre in all_genres:
            if not genre:  # Skip empty genres
                continue
            
            # Translate genre to Polish if available
            polish_genre = polish_genre_mapping.get(genre, genre)
            
            slug = slugify(polish_genre)
            if not slug:  # Skip if slugify produces an empty string
                continue
                
            if dry_run:
                self.stdout.write(f"Would create category: {polish_genre} (slug: {slug})")
            else:
                category, created = Category.objects.get_or_create(
                    slug=slug,
                    defaults={'name': polish_genre}
                )
                # Map both English and Polish versions to the same category
                categories_map[genre] = category
                categories_map[polish_genre] = category
                
                if created:
                    categories_created += 1
                    self.stdout.write(f"Created category: {polish_genre}")
        
        # Associate books with categories based on their genres
        books_updated = 0
        for book in Book.objects.exclude(genres__isnull=True).exclude(genres={}):
            book_genres = []
            if isinstance(book.genres, list):
                book_genres = book.genres
            elif isinstance(book.genres, dict):
                book_genres = list(book.genres.keys())
            
            if not book_genres:
                continue
            
            if dry_run:
                polish_genres = [polish_genre_mapping.get(g, g) for g in book_genres]
                self.stdout.write(f"Would associate book '{book.title}' with categories: {', '.join(polish_genres)}")
            else:
                for genre in book_genres:
                    if genre in categories_map:
                        book.categories.add(categories_map[genre])
                books_updated += 1
                self.stdout.write(f"Associated book '{book.title}' with categories")
        
        if dry_run:
            self.stdout.write(f"Would create {len(all_genres)} categories and update {len(Book.objects.exclude(genres__isnull=True).exclude(genres={}))} books")
        else:
            self.stdout.write(f"Created {categories_created} categories and updated {books_updated} books")

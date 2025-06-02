from django.core.management.base import BaseCommand
from library.models import Book
from django.db import transaction
import json

class Command(BaseCommand):
    help = 'Fix book genres to match the category list in the filter'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Define genre translations for Polish (copied from views.py)
        genre_translations = {
            'fiction': 'Fikcja',
            'nonfiction': 'Literatura faktu',
            'scifi': 'Science Fiction',
            'mystery': 'Kryminał',
            'biography': 'Biografia',
            'fantasy': 'Fantastyka',
            'romance': 'Romans',
            'thriller': 'Thriller',
            'horror': 'Horror',
            'history': 'Historia',
            'poetry': 'Poezja',
            'drama': 'Dramat',
            'comedy': 'Komedia',
            'adventure': 'Przygodowa',
            'children': 'Dla dzieci',
            'young_adult': 'Młodzieżowa',
            'science': 'Naukowa',
            'travel': 'Podróżnicza',
            'cooking': 'Kulinarna',
            'art': 'Sztuka',
            'music': 'Muzyka',
            'sports': 'Sport',
            'education': 'Edukacja',
            'philosophy': 'Filozofia',
            'psychology': 'Psychologia',
            'religion': 'Religia',
            'politics': 'Polityka',
            'business': 'Biznes',
            'health': 'Zdrowie',
            'self_help': 'Poradniki',
            'comics': 'Komiksy',
            'manga': 'Manga',
            'other': 'Inne'
        }
        
        # Get all books
        books = Book.objects.all()
        self.stdout.write(f"Found {books.count()} books")
        
        # First, let's see what genres we have
        all_genres = set()
        for book in books:
            if book.genres:
                if isinstance(book.genres, list):
                    all_genres.update(book.genres)
                elif isinstance(book.genres, str):
                    all_genres.update(book.genres.split(','))
                elif isinstance(book.genres, dict):
                    all_genres.update(book.genres.keys())
        
        self.stdout.write(f"Found {len(all_genres)} unique genres: {sorted(all_genres)}")
        
        # Create a mapping from existing genres to standardized genres
        genre_mapping = {
            # Fiction categories
            'fiction': 'fiction',
            'novel': 'fiction',
            'novels': 'fiction',
            'literature': 'fiction',
            
            # Non-fiction
            'non-fiction': 'nonfiction',
            'nonfiction': 'nonfiction',
            
            # Sci-fi
            'sci-fi': 'scifi',
            'science fiction': 'scifi',
            'scifi': 'scifi',
            
            # Mystery
            'mystery': 'mystery',
            'detective': 'mystery',
            'crime': 'mystery',
            
            # Biography
            'biography': 'biography',
            'autobiography': 'biography',
            'memoir': 'biography',
            'memoirs': 'biography',
            
            # Fantasy
            'fantasy': 'fantasy',
            
            # Romance
            'romance': 'romance',
            'love': 'romance',
            
            # Thriller
            'thriller': 'thriller',
            'suspense': 'thriller',
            
            # Horror
            'horror': 'horror',
            
            # History
            'history': 'history',
            'historical': 'history',
            
            # Poetry
            'poetry': 'poetry',
            'poems': 'poetry',
            
            # Drama
            'drama': 'drama',
            'plays': 'drama',
            
            # Comedy
            'comedy': 'comedy',
            'humor': 'comedy',
            'humour': 'comedy',
            
            # Adventure
            'adventure': 'adventure',
            
            # Children's
            'children': 'children',
            'children\'s': 'children',
            'kids': 'children',
            
            # Young Adult
            'young adult': 'young_adult',
            'ya': 'young_adult',
            'teen': 'young_adult',
            
            # Science
            'science': 'science',
            'academic': 'science',
            'research': 'science',
            
            # Travel
            'travel': 'travel',
            
            # Cooking
            'cooking': 'cooking',
            'food': 'cooking',
            'recipes': 'cooking',
            'culinary': 'cooking',
            
            # Art
            'art': 'art',
            
            # Music
            'music': 'music',
            
            # Sports
            'sports': 'sports',
            'sport': 'sports',
            
            # Education
            'education': 'education',
            'educational': 'education',
            'textbook': 'education',
            'academic': 'education',
            
            # Philosophy
            'philosophy': 'philosophy',
            'philosophical': 'philosophy',
            
            # Psychology
            'psychology': 'psychology',
            'psychological': 'psychology',
            
            # Religion
            'religion': 'religion',
            'religious': 'religion',
            'spiritual': 'religion',
            
            # Politics
            'politics': 'politics',
            'political': 'politics',
            
            # Business
            'business': 'business',
            'economics': 'business',
            'finance': 'business',
            'management': 'business',
            
            # Health
            'health': 'health',
            'medical': 'health',
            'wellness': 'health',
            
            # Self-help
            'self-help': 'self_help',
            'self help': 'self_help',
            'personal development': 'self_help',
            'self-improvement': 'self_help',
            
            # Comics
            'comics': 'comics',
            'comic': 'comics',
            'graphic novel': 'comics',
            'graphic novels': 'comics',
            
            # Manga
            'manga': 'manga',
            'anime': 'manga',
            
            # Other (fallback)
            'other': 'other'
        }
        
        # Count how many books have genres
        books_with_genres = 0
        books_without_genres = 0
        
        for book in books:
            if book.genres:
                books_with_genres += 1
            else:
                books_without_genres += 1
        
        self.stdout.write(f"Books with genres: {books_with_genres}")
        self.stdout.write(f"Books without genres: {books_without_genres}")
        
        # Now let's fix the genres
        books_updated = 0
        
        with transaction.atomic():
            for book in books:
                original_genres = book.genres
                
                # Skip if no genres
                if not book.genres:
                    continue
                
                # Convert to standardized format
                standardized_genres = []
                
                if isinstance(book.genres, list):
                    for genre in book.genres:
                        genre_lower = genre.lower() if isinstance(genre, str) else str(genre).lower()
                        if genre_lower in genre_mapping:
                            standardized_genres.append(genre_mapping[genre_lower])
                        else:
                            # If we don't have a mapping, keep the original
                            standardized_genres.append('other')
                
                elif isinstance(book.genres, str):
                    for genre in book.genres.split(','):
                        genre_lower = genre.strip().lower()
                        if genre_lower in genre_mapping:
                            standardized_genres.append(genre_mapping[genre_lower])
                        else:
                            standardized_genres.append('other')
                
                elif isinstance(book.genres, dict):
                    for genre in book.genres.keys():
                        genre_lower = genre.lower()
                        if genre_lower in genre_mapping:
                            standardized_genres.append(genre_mapping[genre_lower])
                        else:
                            standardized_genres.append('other')
                
                # Remove duplicates
                standardized_genres = list(set(standardized_genres))
                
                # If no genres were mapped, add 'other'
                if not standardized_genres:
                    standardized_genres = ['other']
                
                # Update the book if genres changed
                if standardized_genres != original_genres:
                    if not dry_run:
                        book.genres = standardized_genres
                        book.save()
                    books_updated += 1
                    self.stdout.write(f"Updated genres for '{book.title}': {original_genres} -> {standardized_genres}")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run completed. {books_updated} books would be updated."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated genres for {books_updated} books."))

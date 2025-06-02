import os
import csv
import random
import re
from datetime import datetime, timedelta
import pandas as pd
import kagglehub
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Import books data from Kaggle dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit the number of books to import'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        self.stdout.write(self.style.SUCCESS(f'Starting import of up to {limit} books from Kaggle dataset'))
        
        try:
            # Download the dataset
            self.stdout.write('Downloading Kaggle dataset...')
            dataset_path = kagglehub.dataset_download("saurabhbagchi/books-dataset")
            self.stdout.write(self.style.SUCCESS(f'Dataset downloaded to: {dataset_path}'))
            
            # Process the dataset
            books_csv_path = os.path.join(dataset_path, 'books_data', 'books.csv')
            
            if not os.path.exists(books_csv_path):
                self.stdout.write(self.style.ERROR(f'Books CSV file not found at {books_csv_path}'))
                return
            
            # Read the CSV file using pandas with error handling for encoding
            try:
                # Try different encodings
                encodings = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
                
                for encoding in encodings:
                    try:
                        self.stdout.write(f'Trying to read CSV with {encoding} encoding...')
                        df = pd.read_csv(books_csv_path, encoding=encoding, on_bad_lines='skip')
                        self.stdout.write(self.style.SUCCESS(f'Successfully read CSV with {encoding} encoding'))
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise Exception('Failed to read CSV with any of the attempted encodings')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error reading CSV: {str(e)}'))
                return
            self.stdout.write(self.style.SUCCESS(f'Loaded {len(df)} books from CSV'))
            
            # Print column names for debugging
            self.stdout.write(f'Dataset columns: {list(df.columns)}')
            
            # Create column mapping for flexibility
            column_mapping = {
                'title': 'title',
                'authors': 'authors',
                'publisher': 'publisher',
                'isbn': 'isbn',
                'isbn13': 'isbn13',
                'average_rating': 'average_rating',
                'publication_date': 'publication_date',
                'publication_year': 'publication_year',  # Fallback
                'language_code': 'language_code',
                'num_pages': 'num_pages',
                'ratings_count': 'ratings_count',
                'description': 'description',
                # Add more mappings as needed
            }
            
            # Update mappings based on actual columns
            for actual_col in df.columns:
                # Check for close matches
                for expected_col, mapped_col in column_mapping.items():
                    if expected_col.lower() in actual_col.lower() or actual_col.lower() in expected_col.lower():
                        column_mapping[expected_col] = actual_col
            
            self.stdout.write(f'Column mapping: {column_mapping}')
            
            # Limit the number of books to import
            if limit > 0:
                df = df.head(limit)
                self.stdout.write(f'Limited to {len(df)} books')
            
            # Start importing data
            with transaction.atomic():
                books_imported = 0
                authors_created = 0
                publishers_created = 0
                
                # Create a dictionary to track created authors and publishers
                author_dict = {}
                publisher_dict = {}
                
                for _, row in df.iterrows():
                    # Get values using column mapping
                    def get_value(field, default=None):
                        mapped_col = column_mapping.get(field, field)
                        if mapped_col in row and not pd.isna(row[mapped_col]):
                            return row[mapped_col]
                        return default
                    
                    # Process author
                    author_name = get_value('authors', 'Unknown Author')
                    if author_name not in author_dict:
                        # Create a sanitized version of the author name for use in filenames
                        sanitized_name = self._sanitize_filename(author_name)
                        
                        # Disable AI signal processing temporarily to avoid filename issues
                        with transaction.atomic():
                            # Temporarily disable signals
                            from django.db.models.signals import post_save
                            from library.ai_signals import generate_author_portrait
                            post_save.disconnect(generate_author_portrait, sender=Author)
                            
                            # Create author
                            author = Author.objects.create(
                                name=author_name,
                                bio=f"Author of {get_value('title', 'unknown book')}",
                                birth_date=self._generate_random_date(1900, 1990)
                            )
                            
                            # Reconnect signals
                            post_save.connect(generate_author_portrait, sender=Author)
                        
                        author_dict[author_name] = author
                        authors_created += 1
                    else:
                        author = author_dict[author_name]
                    
                    # Process publisher
                    publisher_name = get_value('publisher', 'Unknown Publisher')
                    if publisher_name not in publisher_dict:
                        # Create a sanitized version of the publisher name for use in URLs and filenames
                        sanitized_name = self._sanitize_filename(publisher_name)
                        
                        # Disable AI signal processing temporarily to avoid filename issues
                        with transaction.atomic():
                            # Temporarily disable signals
                            from django.db.models.signals import post_save
                            from library.ai_signals import generate_publisher_logo
                            post_save.disconnect(generate_publisher_logo, sender=Publisher)
                            
                            # Create publisher
                            publisher = Publisher.objects.create(
                                name=publisher_name,
                                description=f"Publisher of {get_value('title', 'unknown book')}",
                                founded_date=self._generate_random_date(1800, 1990),
                                website=f"https://www.{slugify(sanitized_name)}.com"
                            )
                            
                            # Reconnect signals
                            post_save.connect(generate_publisher_logo, sender=Publisher)
                        
                        publisher_dict[publisher_name] = publisher
                        publishers_created += 1
                    else:
                        publisher = publisher_dict[publisher_name]
                    
                    # Process book
                    # Try both ISBN and ISBN13 fields
                    isbn = str(get_value('isbn13') or get_value('isbn', ''))[:13]  # Limit to 13 chars
                    
                    # Get language code or default to English
                    language_code = get_value('language_code', 'en')
                    
                    # Get publication date
                    pub_date = get_value('publication_date')
                    pub_year = get_value('publication_year')
                    
                    # Create a sanitized version of the book title for use in filenames
                    book_title = get_value('title', 'Unknown Title')
                    sanitized_title = self._sanitize_filename(book_title)
                    
                    # Disable AI signal processing temporarily to avoid filename issues
                    with transaction.atomic():
                        # Temporarily disable signals
                        from django.db.models.signals import post_save
                        from library.ai_signals import generate_book_cover
                        post_save.disconnect(generate_book_cover, sender=Book)
                        
                        # Create the book
                        book = Book.objects.create(
                            title=book_title,
                            publisher=publisher,
                            description=get_value('description', '') or f"A book titled {book_title}",
                            publication_date=self._parse_date_or_year(pub_date, pub_year),
                            isbn=isbn,
                            pages=get_value('num_pages', random.randint(100, 500)),
                            language=language_code[:2] if language_code else 'en',  # Extract main language code
                            genres=self._generate_random_genres(),
                            total_copies=random.randint(1, 10),
                            available_copies=random.randint(0, 5)
                        )
                        
                        # Add author to the book
                        book.authors.add(author)
                        
                        # Reconnect signals
                        post_save.connect(generate_book_cover, sender=Book)
                    
                    # Add average rating if available
                    avg_rating = get_value('average_rating')
                    if avg_rating:
                        try:
                            book.avg_rating = float(avg_rating)
                        except (ValueError, TypeError):
                            pass
                    
                    books_imported += 1
                    
                    if books_imported % 10 == 0:
                        self.stdout.write(f'Imported {books_imported} books...')
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully imported {books_imported} books, '
                    f'created {authors_created} authors and {publishers_created} publishers'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing books: {str(e)}'))
    
    def _generate_random_date(self, start_year, end_year):
        """Generate a random date between start_year and end_year"""
        start_date = datetime(start_year, 1, 1).date()
        end_date = datetime(end_year, 12, 31).date()
        days_between = (end_date - start_date).days
        random_days = random.randint(0, days_between)
        return start_date + timedelta(days=random_days)
    
    def _parse_date_or_year(self, date_str, year=None):
        """Parse date string or year into a date object"""
        # Try to parse date string first
        if date_str and not pd.isna(date_str):
            date_formats = ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y']
            for date_format in date_formats:
                try:
                    return datetime.strptime(str(date_str), date_format).date()
                except ValueError:
                    continue
        
        # Fall back to year
        if year and not pd.isna(year):
            try:
                year = int(year)
                return datetime(year, random.randint(1, 12), random.randint(1, 28)).date()
            except (ValueError, TypeError):
                pass
        
        # Default to random date
        return self._generate_random_date(1950, 2020)
        
    def _parse_year(self, year):
        """Convert year to date object (legacy method)"""
        return self._parse_date_or_year(None, year)
    
    def _sanitize_filename(self, filename):
        """Sanitize a string to be safe for filenames"""
        if not filename:
            return "unknown"
            
        # Replace problematic characters with underscores
        # Remove characters that are invalid in filenames (Windows restrictions)
        invalid_chars = r'[<>:"\/|?*\\]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Truncate to a reasonable length to avoid path length issues
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + '...'
            
        return sanitized
    
    def _generate_random_genres(self):
        """Generate a list of random genres"""
        all_genres = [
            "Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery", 
            "Thriller", "Romance", "Horror", "Biography", "History", 
            "Science", "Self-Help", "Business", "Children's", "Young Adult",
            "Poetry", "Drama", "Classics", "Adventure", "Dystopian"
        ]
        
        num_genres = random.randint(1, 3)
        return random.sample(all_genres, num_genres)

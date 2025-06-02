import os
from django.core.management.base import BaseCommand
from django.db.models import Count
from library.models import Book, BookLoan, BookReservation, Review

class Command(BaseCommand):
    help = 'Find and remove duplicate book entries in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be removed without making changes'
        )
        parser.add_argument(
            '--keep-newest',
            action='store_true',
            help='Keep the newest duplicate (by ID) instead of the oldest'
        )
        parser.add_argument(
            '--specific-titles',
            action='store_true',
            help='Only check for duplicates of specific titles mentioned in the code'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep_newest = options['keep_newest']
        specific_titles = options['specific_titles']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))
        
        if specific_titles:
            self.find_specific_duplicates(dry_run, keep_newest)
        else:
            self.find_all_duplicates(dry_run, keep_newest)
    
    def find_specific_duplicates(self, dry_run, keep_newest):
        """Find duplicates of specific titles"""
        self.stdout.write('Checking for duplicates of specific titles...')
        
        # List of specific titles to check
        specific_titles = [
            "What If?: The World's Foremost Military Historians Imagine What Might Have Been",
            "0425176428"  # This appears to be an ISBN used as a title
        ]
        
        total_removed = 0
        
        for title in specific_titles:
            self.stdout.write(f'\nChecking for duplicates of: "{title}"')
            
            # Find books with this title
            books = Book.objects.filter(title=title).order_by('id')
            count = books.count()
            
            if count <= 1:
                self.stdout.write(f'  No duplicates found (only {count} book with this title)')
                continue
            
            self.stdout.write(f'  Found {count} books with this title:')
            
            # Display all books with this title
            for i, book in enumerate(books):
                authors = ", ".join([author.name for author in book.authors.all()])
                publisher = book.publisher.name if book.publisher else "Unknown Publisher"
                self.stdout.write(f'    {i+1}. Book ID {book.id}: "{book.title}" by {authors} (Publisher: {publisher})')
                
                # Show related data
                loan_count = BookLoan.objects.filter(book=book).count()
                reservation_count = BookReservation.objects.filter(book=book).count()
                review_count = Review.objects.filter(book=book).count()
                
                self.stdout.write(f'       - Has {loan_count} loans, {reservation_count} reservations, {review_count} reviews')
                self.stdout.write(f'       - Cover image: {book.cover.name if book.cover else "None"}')
            
            # Determine which book to keep
            if keep_newest:
                keep_book = books.last()
                remove_books = books.exclude(id=keep_book.id)
            else:
                keep_book = books.first()
                remove_books = books.exclude(id=keep_book.id)
            
            self.stdout.write(f'  Will keep Book ID {keep_book.id} and remove {remove_books.count()} duplicates')
            
            if not dry_run:
                # Process each book to be removed
                for book in remove_books:
                    # Transfer related data to the book we're keeping
                    self.transfer_related_data(book, keep_book)
                    
                    # Delete the duplicate book
                    book_id = book.id
                    book.delete()
                    self.stdout.write(self.style.SUCCESS(f'  Removed duplicate Book ID {book_id}'))
                    total_removed += 1
        
        if total_removed > 0:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully removed {total_removed} duplicate books'))
        else:
            self.stdout.write('\nNo duplicate books were removed')
    
    def find_all_duplicates(self, dry_run, keep_newest):
        """Find all duplicate books based on title"""
        self.stdout.write('Checking for all duplicate book titles...')
        
        # Find titles that appear more than once
        duplicate_titles = Book.objects.values('title').annotate(
            count=Count('title')
        ).filter(count__gt=1).order_by('-count')
        
        if not duplicate_titles:
            self.stdout.write('No duplicate book titles found')
            return
        
        self.stdout.write(f'Found {len(duplicate_titles)} titles with duplicates:')
        
        total_removed = 0
        
        for dup in duplicate_titles:
            title = dup['title']
            count = dup['count']
            
            self.stdout.write(f'\nTitle: "{title}" appears {count} times')
            
            # Get all books with this title
            books = Book.objects.filter(title=title).order_by('id')
            
            # Display all books with this title
            for i, book in enumerate(books):
                authors = ", ".join([author.name for author in book.authors.all()])
                publisher = book.publisher.name if book.publisher else "Unknown Publisher"
                self.stdout.write(f'  {i+1}. Book ID {book.id}: "{book.title}" by {authors} (Publisher: {publisher})')
                
                # Show related data
                loan_count = BookLoan.objects.filter(book=book).count()
                reservation_count = BookReservation.objects.filter(book=book).count()
                review_count = Review.objects.filter(book=book).count()
                
                self.stdout.write(f'     - Has {loan_count} loans, {reservation_count} reservations, {review_count} reviews')
                self.stdout.write(f'     - Cover image: {book.cover.name if book.cover else "None"}')
            
            # Determine which book to keep
            if keep_newest:
                keep_book = books.last()
                remove_books = books.exclude(id=keep_book.id)
            else:
                keep_book = books.first()
                remove_books = books.exclude(id=keep_book.id)
            
            self.stdout.write(f'  Will keep Book ID {keep_book.id} and remove {remove_books.count()} duplicates')
            
            if not dry_run:
                # Process each book to be removed
                for book in remove_books:
                    # Transfer related data to the book we're keeping
                    self.transfer_related_data(book, keep_book)
                    
                    # Delete the duplicate book
                    book_id = book.id
                    book.delete()
                    self.stdout.write(self.style.SUCCESS(f'  Removed duplicate Book ID {book_id}'))
                    total_removed += 1
        
        if total_removed > 0:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully removed {total_removed} duplicate books'))
        else:
            self.stdout.write('\nNo duplicate books were removed')
    
    def transfer_related_data(self, source_book, target_book):
        """Transfer related data from source book to target book before deletion"""
        # Transfer loans
        loans = BookLoan.objects.filter(book=source_book)
        for loan in loans:
            self.stdout.write(f'    Transferring loan ID {loan.id} to Book ID {target_book.id}')
            loan.book = target_book
            loan.save()
        
        # Transfer reservations
        reservations = BookReservation.objects.filter(book=source_book)
        for reservation in reservations:
            self.stdout.write(f'    Transferring reservation ID {reservation.id} to Book ID {target_book.id}')
            reservation.book = target_book
            reservation.save()
        
        # Transfer reviews
        reviews = Review.objects.filter(book=source_book)
        for review in reviews:
            self.stdout.write(f'    Transferring review ID {review.id} to Book ID {target_book.id}')
            # Check if this user already has a review for the target book
            existing_review = Review.objects.filter(book=target_book, user=review.user).first()
            if existing_review:
                self.stdout.write(f'      User already has a review for target book, keeping the higher-rated one')
                if review.rating > existing_review.rating:
                    existing_review.rating = review.rating
                    existing_review.title = review.title
                    existing_review.content = review.content
                    existing_review.save()
            else:
                review.book = target_book
                review.save()
        
        # If target book has no cover but source book does, transfer the cover
        if not target_book.cover and source_book.cover:
            self.stdout.write(f'    Transferring cover image from Book ID {source_book.id} to Book ID {target_book.id}')
            target_book.cover = source_book.cover
            target_book.save()

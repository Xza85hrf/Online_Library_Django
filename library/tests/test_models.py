"""
Unit tests for library models.
Tests the functionality of all models in the library application.
"""
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import timedelta
import os
import tempfile
import shutil

from library.models import (
    Book, Author, Publisher, BookLoan, BookReservation,
    Review, LateFee, LibrarySettings
)

User = get_user_model()

class AuthorModelTests(TestCase):
    """Tests for the Author model."""
    
    def setUp(self):
        """Set up test data."""
        self.author = Author.objects.create(
            name="Jan Kowalski",
            bio="Polski pisarz fantasy.",
            birth_date=timezone.now().date() - timedelta(days=365*40)
        )
    
    def test_author_creation(self):
        """Test that an author can be created with basic fields."""
        self.assertEqual(self.author.name, "Jan Kowalski")
        self.assertEqual(self.author.bio, "Polski pisarz fantasy.")
        self.assertIsNotNone(self.author.birth_date)
    
    def test_author_str_representation(self):
        """Test the string representation of an author."""
        self.assertEqual(str(self.author), "Jan Kowalski")
    
    def test_author_get_absolute_url(self):
        """Test the get_absolute_url method."""
        url = self.author.get_absolute_url()
        self.assertEqual(url, f'/authors/{self.author.id}/')

class PublisherModelTests(TestCase):
    """Tests for the Publisher model."""
    
    def setUp(self):
        """Set up test data."""
        self.publisher = Publisher.objects.create(
            name="Wydawnictwo Literackie",
            description="Polskie wydawnictwo z tradycjami.",
            founded_date=timezone.now().date() - timedelta(days=365*30)
        )
    
    def test_publisher_creation(self):
        """Test that a publisher can be created with basic fields."""
        self.assertEqual(self.publisher.name, "Wydawnictwo Literackie")
        self.assertEqual(self.publisher.description, "Polskie wydawnictwo z tradycjami.")
        self.assertIsNotNone(self.publisher.founded_date)
    
    def test_publisher_str_representation(self):
        """Test the string representation of a publisher."""
        self.assertEqual(str(self.publisher), "Wydawnictwo Literackie")
    
    def test_publisher_get_absolute_url(self):
        """Test the get_absolute_url method."""
        url = self.publisher.get_absolute_url()
        self.assertEqual(url, f'/publishers/{self.publisher.id}/')

class BookModelTests(TestCase):
    """Tests for the Book model."""
    
    def setUp(self):
        """Set up test data."""
        self.author = Author.objects.create(name="Anna Nowak")
        self.publisher = Publisher.objects.create(name="Nowa Era")
        
        self.book = Book.objects.create(
            title="Przygody w Krainie Czarów",
            publisher=self.publisher,
            description="Fascynująca opowieść o przygodach w magicznej krainie.",
            publication_date=timezone.now().date() - timedelta(days=365),
            isbn="9788374321234",
            pages=320,
            language="polski",
            genres=["fantasy", "przygodowe"],
            available_copies=5,
            total_copies=10
        )
        self.book.authors.add(self.author)
        
        # Create a user for reviews
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        
        # Create some reviews
        self.review1 = Review.objects.create(
            book=self.book,
            user=self.user,
            rating=5,
            title="Wspaniała książka",
            content="Najlepsza książka jaką czytałem w tym roku!",
            status='approved'
        )
        
        self.review2 = Review.objects.create(
            book=self.book,
            user=User.objects.create_user(email='user2@example.com', password='pass'),
            rating=3,
            title="Przeciętna",
            content="Nic specjalnego, ale można przeczytać.",
            status='approved'
        )
        
        self.review3 = Review.objects.create(
            book=self.book,
            user=User.objects.create_user(email='user3@example.com', password='pass'),
            rating=4,
            title="Dobra lektura",
            content="Polecam na długie wieczory.",
            status='pending'  # This one is pending, shouldn't count in averages
        )
    
    def test_book_creation(self):
        """Test that a book can be created with basic fields."""
        self.assertEqual(self.book.title, "Przygody w Krainie Czarów")
        self.assertEqual(self.book.publisher.name, "Nowa Era")
        self.assertEqual(self.book.authors.first().name, "Anna Nowak")
        self.assertEqual(self.book.isbn, "9788374321234")
        self.assertEqual(self.book.language, "polski")
        self.assertEqual(self.book.genres, ["fantasy", "przygodowe"])
        self.assertEqual(self.book.available_copies, 5)
        self.assertEqual(self.book.total_copies, 10)
    
    def test_book_str_representation(self):
        """Test the string representation of a book."""
        self.assertEqual(str(self.book), "Przygody w Krainie Czarów")
    
    def test_book_get_absolute_url(self):
        """Test the get_absolute_url method."""
        url = self.book.get_absolute_url()
        self.assertEqual(url, f'/books/{self.book.id}/')
    
    def test_is_available_property(self):
        """Test the is_available property."""
        self.assertTrue(self.book.is_available)
        
        # Set available copies to 0
        self.book.available_copies = 0
        self.book.save()
        
        # Refresh from database
        self.book.refresh_from_db()
        self.assertFalse(self.book.is_available)
    
    def test_average_rating_property(self):
        """Test the average_rating property."""
        # Should only count approved reviews (review1 and review2)
        expected_avg = (5 + 3) / 2
        self.assertEqual(self.book.average_rating, expected_avg)
    
    def test_review_count_property(self):
        """Test the review_count property."""
        # Should only count approved reviews
        self.assertEqual(self.book.review_count, 2)
    
    def test_rating_distribution_property(self):
        """Test the rating_distribution property."""
        expected_distribution = {1: 0, 2: 0, 3: 1, 4: 0, 5: 1}
        self.assertEqual(self.book.rating_distribution, expected_distribution)

class BookLoanModelTests(TestCase):
    """Tests for the BookLoan model."""
    
    def setUp(self):
        """Set up test data."""
        # Create library settings
        LibrarySettings.objects.create(
            late_fee_daily_rate=Decimal('1.00'),
            max_loan_days=14
        )
        
        self.user = User.objects.create_user(email='borrower@example.com', password='pass')
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        self.book = Book.objects.create(
            title="Test Book",
            publisher=self.publisher,
            available_copies=5,
            total_copies=10
        )
        self.book.authors.add(self.author)
        
        # Create a current loan
        self.current_loan = BookLoan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.now().date() + timedelta(days=7),
            status='borrowed'
        )
        
        # Create an overdue loan
        self.overdue_loan = BookLoan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.now().date() - timedelta(days=3),
            status='borrowed'
        )
        
        # Create a returned loan
        self.returned_loan = BookLoan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.now().date() - timedelta(days=10),
            return_date=timezone.now().date() - timedelta(days=2),
            status='returned'
        )
    
    def test_loan_creation(self):
        """Test that a loan can be created with basic fields."""
        self.assertEqual(self.current_loan.book.title, "Test Book")
        self.assertEqual(self.current_loan.user.username, "borrower")
        self.assertEqual(self.current_loan.status, "borrowed")
        self.assertIsNone(self.current_loan.return_date)
    
    def test_loan_str_representation(self):
        """Test the string representation of a loan."""
        expected = f"Test Book - borrower"
        self.assertEqual(str(self.current_loan), expected)
    
    def test_is_overdue_property(self):
        """Test the is_overdue property."""
        self.assertFalse(self.current_loan.is_overdue)
        self.assertTrue(self.overdue_loan.is_overdue)
        self.assertTrue(self.returned_loan.is_overdue)  # Returned late
    
    def test_days_overdue_property(self):
        """Test the days_overdue property."""
        self.assertEqual(self.current_loan.days_overdue, 0)
        self.assertEqual(self.overdue_loan.days_overdue, 3)
        self.assertEqual(self.returned_loan.days_overdue, 8)  # 10 days loan, returned after 8 days
    
    def test_calculated_late_fee_property(self):
        """Test the calculated_late_fee property."""
        self.assertEqual(self.current_loan.calculated_late_fee, Decimal('0.00'))
        self.assertEqual(self.overdue_loan.calculated_late_fee, Decimal('3.00'))  # 3 days * 1.00
        self.assertEqual(self.returned_loan.calculated_late_fee, Decimal('8.00'))  # 8 days * 1.00
    
    def test_save_method_updates_status(self):
        """Test that the save method updates the status to 'overdue' when appropriate."""
        # Initially borrowed
        self.assertEqual(self.overdue_loan.status, "borrowed")
        
        # Save should update to overdue
        self.overdue_loan.save()
        self.assertEqual(self.overdue_loan.status, "overdue")
    
    def test_save_method_creates_late_fee(self):
        """Test that the save method creates a LateFee record for overdue loans."""
        # Initially no late fee
        self.assertFalse(LateFee.objects.filter(loan=self.overdue_loan).exists())
        
        # Save should create a late fee
        self.overdue_loan.save()
        
        # Check that a late fee was created
        self.assertTrue(LateFee.objects.filter(loan=self.overdue_loan).exists())
        late_fee = LateFee.objects.get(loan=self.overdue_loan)
        self.assertEqual(late_fee.amount, Decimal('3.00'))
        self.assertEqual(late_fee.days_overdue, 3)

class BookReservationModelTests(TestCase):
    """Tests for the BookReservation model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email='reserver@example.com', password='pass')
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        self.book = Book.objects.create(
            title="Reserved Book",
            publisher=self.publisher,
            available_copies=0,  # No copies available
            total_copies=5
        )
        self.book.authors.add(self.author)
        
        # Create a pending reservation
        self.pending_reservation = BookReservation.objects.create(
            book=self.book,
            user=self.user,
            expiry_date=timezone.now().date() + timedelta(days=3),
            status='pending'
        )
        
        # Create an expired reservation
        self.expired_reservation = BookReservation.objects.create(
            book=self.book,
            user=self.user,
            expiry_date=timezone.now().date() - timedelta(days=1),
            status='expired'
        )
    
    def test_reservation_creation(self):
        """Test that a reservation can be created with basic fields."""
        self.assertEqual(self.pending_reservation.book.title, "Reserved Book")
        self.assertEqual(self.pending_reservation.user.username, "reserver")
        self.assertEqual(self.pending_reservation.status, "pending")
    
    def test_reservation_str_representation(self):
        """Test the string representation of a reservation."""
        expected = f"Reserved Book - reserver"
        self.assertEqual(str(self.pending_reservation), expected)

class LibrarySettingsModelTests(TestCase):
    """Tests for the LibrarySettings model."""
    
    def setUp(self):
        """Set up test data."""
        # Clear any existing settings
        LibrarySettings.objects.all().delete()
        
        # Create settings
        self.settings = LibrarySettings.objects.create(
            late_fee_daily_rate=Decimal('0.75'),
            max_loan_days=21,
            max_renewals=3,
            max_books_per_user=7,
            reservation_expiry_days=5
        )
    
    def test_settings_creation(self):
        """Test that settings can be created with custom values."""
        self.assertEqual(self.settings.late_fee_daily_rate, Decimal('0.75'))
        self.assertEqual(self.settings.max_loan_days, 21)
        self.assertEqual(self.settings.max_renewals, 3)
        self.assertEqual(self.settings.max_books_per_user, 7)
        self.assertEqual(self.settings.reservation_expiry_days, 5)
    
    def test_get_settings_method(self):
        """Test the get_settings class method."""
        # Clear all settings
        LibrarySettings.objects.all().delete()
        
        # Should create default settings
        settings = LibrarySettings.get_settings()
        
        # Check default values
        self.assertEqual(settings.late_fee_daily_rate, Decimal('0.50'))
        self.assertEqual(settings.max_loan_days, 14)
        
        # Create custom settings
        custom_settings = LibrarySettings.objects.create(
            late_fee_daily_rate=Decimal('1.00'),
            max_loan_days=30
        )
        
        # Should return the existing settings
        retrieved_settings = LibrarySettings.get_settings()
        self.assertEqual(retrieved_settings.id, custom_settings.id)
        self.assertEqual(retrieved_settings.late_fee_daily_rate, Decimal('1.00'))

class LateFeeModelTests(TestCase):
    """Tests for the LateFee model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email='fee_user@example.com', password='pass')
        self.staff_user = User.objects.create_user(
            email='staff_user@example.com', 
            password='pass',
            is_staff=True
        )
        
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        self.book = Book.objects.create(
            title="Late Book",
            publisher=self.publisher,
            available_copies=1,
            total_copies=1
        )
        self.book.authors.add(self.author)
        
        self.loan = BookLoan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.now().date() - timedelta(days=5),
            status='overdue'
        )
        
        self.late_fee = LateFee.objects.create(
            loan=self.loan,
            amount=Decimal('5.00'),
            days_overdue=5,
            payment_status='pending'
        )
    
    def test_late_fee_creation(self):
        """Test that a late fee can be created with basic fields."""
        self.assertEqual(self.late_fee.loan, self.loan)
        self.assertEqual(self.late_fee.amount, Decimal('5.00'))
        self.assertEqual(self.late_fee.days_overdue, 5)
        self.assertEqual(self.late_fee.payment_status, 'pending')
    
    def test_late_fee_str_representation(self):
        """Test the string representation of a late fee."""
        expected = f"Late fee of 5.00 for Late Book - fee_user"
        self.assertEqual(str(self.late_fee), expected)
    
    def test_mark_as_paid_method(self):
        """Test the mark_as_paid method."""
        self.late_fee.mark_as_paid()
        
        # Check that the status was updated
        self.assertEqual(self.late_fee.payment_status, 'paid')
        self.assertIsNotNone(self.late_fee.payment_date)
        
        # Check that the loan's late_fee_paid flag was updated
        self.loan.refresh_from_db()
        self.assertTrue(self.loan.late_fee_paid)
    
    def test_waive_fee_method(self):
        """Test the waive_fee method."""
        reason = "Customer loyalty discount"
        self.late_fee.waive_fee(self.staff_user, reason)
        
        # Check that the status was updated
        self.assertEqual(self.late_fee.payment_status, 'waived')
        self.assertEqual(self.late_fee.waived_by, self.staff_user)
        self.assertEqual(self.late_fee.waived_reason, reason)
        
        # Check that the loan's late_fee_paid flag was updated
        self.loan.refresh_from_db()
        self.assertTrue(self.loan.late_fee_paid)

class ReviewModelTests(TestCase):
    """Tests for the Review model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email='reviewer@example.com', password='pass')
        self.author = Author.objects.create(name="Review Author")
        self.publisher = Publisher.objects.create(name="Review Publisher")
        
        self.book = Book.objects.create(
            title="Book to Review",
            publisher=self.publisher,
            available_copies=3,
            total_copies=3
        )
        self.book.authors.add(self.author)
        
        self.review = Review.objects.create(
            book=self.book,
            user=self.user,
            rating=4,
            title="Good read",
            content="I enjoyed this book very much.",
            status='pending'
        )
    
    def test_review_creation(self):
        """Test that a review can be created with basic fields."""
        self.assertEqual(self.review.book, self.book)
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.title, "Good read")
        self.assertEqual(self.review.content, "I enjoyed this book very much.")
        self.assertEqual(self.review.status, 'pending')
    
    def test_review_str_representation(self):
        """Test the string representation of a review."""
        expected = f"Review of Book to Review by reviewer"
        self.assertEqual(str(self.review), expected)
    
    def test_get_absolute_url(self):
        """Test the get_absolute_url method."""
        url = self.review.get_absolute_url()
        self.assertEqual(url, f'/books/{self.book.id}/')
    
    def test_is_approved_property(self):
        """Test the is_approved property."""
        self.assertFalse(self.review.is_approved)
        
        # Change status to approved
        self.review.status = 'approved'
        self.review.save()
        
        self.assertTrue(self.review.is_approved)

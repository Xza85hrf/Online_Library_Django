"""
End-to-end tests for the library application.
Tests the complete flow of borrowing, returning, and reviewing books.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from unittest.mock import patch

from library.models import (
    Book, Author, Publisher, BookLoan, BookReservation,
    Review, LateFee, LibrarySettings
)

User = get_user_model()

class LibraryE2ETests(TestCase):
    """End-to-end tests for the library application."""
    
    def setUp(self):
        """Set up test data."""
        # Create library settings
        LibrarySettings.objects.create(
            late_fee_daily_rate=1.00,
            max_loan_days=14,
            max_renewals=2,
            max_books_per_user=5,
            reservation_expiry_days=3
        )
        
        # Create users
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='password123'
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='password123',
            is_staff=True
        )
        
        # Create authors
        self.author1 = Author.objects.create(
            name="Jan Kowalski",
            bio="Polski pisarz fantasy."
        )
        
        self.author2 = Author.objects.create(
            name="Anna Nowak",
            bio="Polska autorka kryminałów."
        )
        
        # Create publishers
        self.publisher1 = Publisher.objects.create(
            name="Wydawnictwo Literackie",
            description="Polskie wydawnictwo z tradycjami."
        )
        
        self.publisher2 = Publisher.objects.create(
            name="Nowa Era",
            description="Nowoczesne wydawnictwo edukacyjne."
        )
        
        # Create books
        self.book1 = Book.objects.create(
            title="Przygody w Krainie Czarów",
            publisher=self.publisher1,
            description="Fascynująca opowieść o przygodach w magicznej krainie.",
            publication_date=timezone.now().date() - timedelta(days=365),
            isbn="9788374321234",
            pages=320,
            language="polski",
            genres=["fantasy", "przygodowe"],
            available_copies=2,
            total_copies=3
        )
        self.book1.authors.add(self.author1)
        
        self.book2 = Book.objects.create(
            title="Zbrodnia w Mieście",
            publisher=self.publisher2,
            description="Wciągający kryminał osadzony w polskim mieście.",
            publication_date=timezone.now().date() - timedelta(days=180),
            isbn="9788374325678",
            pages=280,
            language="polski",
            genres=["kryminał", "thriller"],
            available_copies=1,
            total_copies=2
        )
        self.book2.authors.add(self.author2)
        
        self.book3 = Book.objects.create(
            title="Poradnik Programisty",
            publisher=self.publisher2,
            description="Praktyczny przewodnik po programowaniu.",
            publication_date=timezone.now().date() - timedelta(days=90),
            isbn="9788374329012",
            pages=450,
            language="polski",
            genres=["edukacja", "informatyka"],
            available_copies=0,  # No available copies
            total_copies=1
        )
        self.book3.authors.add(self.author1)
        
        # Create a client
        self.client = Client()
    
    @patch('library.ai_signals.generate_with_flux')
    def test_complete_borrowing_flow(self, mock_generate):
        """Test the complete flow of borrowing and returning a book."""
        # Mock successful image generation
        mock_generate.return_value = True
        
        # Log in as a regular user
        self.client.login(email='user@example.com', password='password123')
        
        # 1. Browse the book list
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Przygody w Krainie Czarów")
        self.assertContains(response, "Zbrodnia w Mieście")
        
        # 2. View book details
        response = self.client.get(reverse('book_detail', kwargs={'pk': self.book1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Przygody w Krainie Czarów")
        self.assertContains(response, "Jan Kowalski")
        
        # 3. Borrow the book
        initial_available_copies = self.book1.available_copies
        response = self.client.post(reverse('borrow_book', kwargs={'pk': self.book1.pk}))
        self.assertRedirects(response, reverse('my_loans'))
        
        # Check that the book was borrowed
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.available_copies, initial_available_copies - 1)
        
        # Check that a loan was created
        loan = BookLoan.objects.filter(user=self.regular_user, book=self.book1).first()
        self.assertIsNotNone(loan)
        self.assertEqual(loan.status, 'borrowed')
        
        # 4. View my loans
        response = self.client.get(reverse('my_loans'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Przygody w Krainie Czarów")
        
        # 5. Return the book
        response = self.client.post(reverse('return_book', kwargs={'loan_id': loan.pk}))
        self.assertRedirects(response, reverse('my_loans'))
        
        # Check that the book was returned
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.available_copies, initial_available_copies)
        
        # Check that the loan status was updated
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'returned')
        
        # 6. Write a review for the book
        response = self.client.post(
            reverse('create_review', kwargs={'book_id': self.book1.pk}),
            {
                'rating': 5,
                'title': 'Wspaniała książka',
                'content': 'Jedna z najlepszych książek, jakie czytałem w tym roku!'
            }
        )
        self.assertRedirects(response, reverse('book_detail', kwargs={'pk': self.book1.pk}))
        
        # Check that the review was created
        review = Review.objects.filter(user=self.regular_user, book=self.book1).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        
        # 7. Try to reserve an unavailable book
        response = self.client.post(reverse('reserve_book', kwargs={'pk': self.book3.pk}))
        self.assertRedirects(response, reverse('my_reservations'))
        
        # Check that a reservation was created
        reservation = BookReservation.objects.filter(user=self.regular_user, book=self.book3).first()
        self.assertIsNotNone(reservation)
        self.assertEqual(reservation.status, 'pending')
    
    @patch('library.ai_signals.generate_with_flux')
    def test_late_fee_flow(self, mock_generate):
        """Test the flow of late fees and waiver requests."""
        # Mock successful image generation
        mock_generate.return_value = True
        
        # Create an overdue loan
        overdue_loan = BookLoan.objects.create(
            book=self.book2,
            user=self.regular_user,
            due_date=timezone.now().date() - timedelta(days=5),
            status='overdue'
        )
        
        # Update book available copies
        self.book2.available_copies -= 1
        self.book2.save()
        
        # Create a late fee
        late_fee = LateFee.objects.create(
            loan=overdue_loan,
            amount=5.00,
            days_overdue=5,
            payment_status='pending'
        )
        
        # Log in as a regular user
        self.client.login(email='user@example.com', password='password123')
        
        # 1. View my late fees
        response = self.client.get(reverse('my_late_fees'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zbrodnia w Mieście")
        self.assertContains(response, "5.00")
        
        # 2. Request a waiver
        response = self.client.post(
            reverse('request_fee_waiver', kwargs={'fee_id': late_fee.pk}),
            {
                'reason': 'Byłem chory i nie mogłem zwrócić książki na czas.'
            }
        )
        self.assertRedirects(response, reverse('my_late_fees'))
        
        # Check that the waiver request was saved
        late_fee.refresh_from_db()
        self.assertEqual(late_fee.waived_reason, 'Byłem chory i nie mogłem zwrócić książki na czas.')
        
        # Log out and log in as staff
        self.client.logout()
        self.client.login(email='staff@example.com', password='password123')
        
        # 3. View manage late fees
        response = self.client.get(reverse('manage_late_fees'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zbrodnia w Mieście")
        self.assertContains(response, "5.00")
        
        # 4. Process the waiver request (approve)
        response = self.client.post(
            reverse('process_waiver_request', kwargs={'fee_id': late_fee.pk}),
            {
                'action': 'approve'
            }
        )
        self.assertRedirects(response, reverse('manage_late_fees'))
        
        # Check that the late fee was waived
        late_fee.refresh_from_db()
        self.assertEqual(late_fee.payment_status, 'waived')
        self.assertEqual(late_fee.waived_by, self.staff_user)
        
        # Check that the loan's late_fee_paid flag was updated
        overdue_loan.refresh_from_db()
        self.assertTrue(overdue_loan.late_fee_paid)
    
    @patch('library.ai_signals.generate_with_flux')
    def test_reservation_to_loan_flow(self, mock_generate):
        """Test the flow from reservation to loan when a book becomes available."""
        # Mock successful image generation
        mock_generate.return_value = True
        
        # Create a reservation
        reservation = BookReservation.objects.create(
            book=self.book3,
            user=self.regular_user,
            expiry_date=timezone.now().date() + timedelta(days=3),
            status='pending'
        )
        
        # Log in as a regular user
        self.client.login(email='user@example.com', password='password123')
        
        # 1. View my reservations
        response = self.client.get(reverse('my_reservations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Poradnik Programisty")
        
        # 2. Simulate book becoming available
        self.book3.available_copies = 1
        self.book3.save()
        
        # 3. Borrow the reserved book
        response = self.client.post(reverse('borrow_book', kwargs={'pk': self.book3.pk}))
        self.assertRedirects(response, reverse('my_loans'))
        
        # Check that the book was borrowed
        self.book3.refresh_from_db()
        self.assertEqual(self.book3.available_copies, 0)
        
        # Check that a loan was created
        loan = BookLoan.objects.filter(user=self.regular_user, book=self.book3).first()
        self.assertIsNotNone(loan)
        self.assertEqual(loan.status, 'borrowed')
        
        # Check that the reservation was fulfilled
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'fulfilled')

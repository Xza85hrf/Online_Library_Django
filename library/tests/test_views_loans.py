"""
Tests for loan and reservation related views in the library application.
Tests the borrow_book, return_book, reserve_book, cancel_reservation, my_loans, and my_reservations views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from library.models import Book, Author, Publisher, BookLoan, BookReservation, LibrarySettings

User = get_user_model()

class BookLoanViewTests(TestCase):
    """Tests for book loan related views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create library settings
        LibrarySettings.objects.create(
            late_fee_daily_rate=1.00,
            max_loan_days=14,
            max_renewals=2,
            max_books_per_user=3
        )
        
        # Create a user
        self.user = User.objects.create_user(
            email='borrower@example.com',
            password='password123'
        )
        
        # Create an author and publisher
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create some books
        self.available_book = Book.objects.create(
            title="Available Book",
            publisher=self.publisher,
            available_copies=2,
            total_copies=3
        )
        self.available_book.authors.add(self.author)
        
        self.unavailable_book = Book.objects.create(
            title="Unavailable Book",
            publisher=self.publisher,
            available_copies=0,
            total_copies=1
        )
        self.unavailable_book.authors.add(self.author)
        
        # Create an existing loan
        self.existing_loan = BookLoan.objects.create(
            book=self.available_book,
            user=self.user,
            due_date=timezone.now().date() + timedelta(days=7),
            status='borrowed'
        )
    
    def test_borrow_book_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('borrow_book', kwargs={'pk': self.available_book.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/books/{self.available_book.pk}/borrow/'
        )
    
    def test_borrow_book_view_authenticated(self):
        """Test that authenticated users can borrow available books."""
        self.client.login(email='borrower@example.com', password='password123')
        
        # Borrow a book that's available
        response = self.client.post(
            reverse('borrow_book', kwargs={'pk': self.available_book.pk})
        )
        
        # Should redirect to my_loans
        self.assertRedirects(response, reverse('my_loans'))
        
        # Check that a new loan was created
        self.assertEqual(BookLoan.objects.filter(user=self.user).count(), 2)
        
        # Check that available_copies was decremented
        self.available_book.refresh_from_db()
        self.assertEqual(self.available_book.available_copies, 1)
    
    def test_borrow_book_view_unavailable(self):
        """Test that users can't borrow unavailable books."""
        self.client.login(email='borrower@example.com', password='password123')
        
        # Try to borrow a book that's unavailable
        response = self.client.post(
            reverse('library:borrow_book', kwargs={'pk': self.unavailable_book.pk})
        )
        
        # Should redirect to book detail with error message
        self.assertRedirects(
            response, 
            reverse('book_detail', kwargs={'pk': self.unavailable_book.pk})
        )
        
        # Check that no new loan was created
        self.assertEqual(BookLoan.objects.filter(user=self.user).count(), 1)
    
    def test_return_book_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('return_book', kwargs={'loan_id': self.existing_loan.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/loans/{self.existing_loan.pk}/return/'
        )
    
    def test_return_book_view_authenticated(self):
        """Test that authenticated users can return borrowed books."""
        self.client.login(email='borrower@example.com', password='password123')
        
        # Return a borrowed book
        response = self.client.post(
            reverse('return_book', kwargs={'loan_id': self.existing_loan.pk})
        )
        
        # Should redirect to my_loans
        self.assertRedirects(response, reverse('my_loans'))
        
        # Check that the loan status was updated
        self.existing_loan.refresh_from_db()
        self.assertEqual(self.existing_loan.status, 'returned')
        self.assertIsNotNone(self.existing_loan.return_date)
        
        # Check that available_copies was incremented
        self.available_book.refresh_from_db()
        self.assertEqual(self.available_book.available_copies, 3)
    
    def test_return_book_view_wrong_user(self):
        """Test that users can't return books borrowed by others."""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='password123'
        )
        
        # Log in as the other user
        self.client.login(email='other@example.com', password='password123')
        
        # Try to return a book borrowed by the first user
        response = self.client.post(
            reverse('return_book', kwargs={'loan_id': self.existing_loan.pk})
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Check that the loan status was not updated
        self.existing_loan.refresh_from_db()
        self.assertEqual(self.existing_loan.status, 'borrowed')
        self.assertIsNone(self.existing_loan.return_date)
    
    def test_my_loans_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('my_loans'))
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/my-loans/'
        )
    
    def test_my_loans_view_authenticated(self):
        """Test that authenticated users can see their loans."""
        self.client.login(email='borrower@example.com', password='password123')
        
        response = self.client.get(reverse('my_loans'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'loans/my_loans.html')
        
        # Check context
        self.assertIn('active_loans', response.context)
        self.assertIn('past_loans', response.context)
        
        # Check that the existing loan is in active_loans
        self.assertEqual(len(response.context['active_loans']), 1)
        self.assertEqual(response.context['active_loans'][0], self.existing_loan)
        
        # Check that past_loans is empty
        self.assertEqual(len(response.context['past_loans']), 0)
        
        # Return the loan
        self.existing_loan.status = 'returned'
        self.existing_loan.return_date = timezone.now().date()
        self.existing_loan.save()
        
        # Check the view again
        response = self.client.get(reverse('my_loans'))
        
        # Now active_loans should be empty and past_loans should have the loan
        self.assertEqual(len(response.context['active_loans']), 0)
        self.assertEqual(len(response.context['past_loans']), 1)
        self.assertEqual(response.context['past_loans'][0], self.existing_loan)

class BookReservationViewTests(TestCase):
    """Tests for book reservation related views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create library settings
        LibrarySettings.objects.create(
            reservation_expiry_days=3
        )
        
        # Create a user
        self.user = User.objects.create_user(
            email='reserver@example.com',
            password='password123'
        )
        
        # Create an author and publisher
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create some books
        self.unavailable_book = Book.objects.create(
            title="Unavailable Book",
            publisher=self.publisher,
            available_copies=0,
            total_copies=1
        )
        self.unavailable_book.authors.add(self.author)
        
        self.available_book = Book.objects.create(
            title="Available Book",
            publisher=self.publisher,
            available_copies=1,
            total_copies=1
        )
        self.available_book.authors.add(self.author)
        
        # Create an existing reservation
        self.existing_reservation = BookReservation.objects.create(
            book=self.unavailable_book,
            user=self.user,
            expiry_date=timezone.now().date() + timedelta(days=3),
            status='pending'
        )
    
    def test_reserve_book_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('reserve_book', kwargs={'pk': self.unavailable_book.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/books/{self.unavailable_book.pk}/reserve/'
        )
    
    def test_reserve_book_view_authenticated_unavailable(self):
        """Test that authenticated users can reserve unavailable books."""
        self.client.login(username='reserver', password='password123')
        
        # Create another user to reserve a different book
        other_user = User.objects.create_user(
            username='other_reserver',
            email='other@example.com',
            password='password123'
        )
        self.client.logout()
        self.client.login(username='other_reserver', password='password123')
        
        # Reserve an unavailable book
        response = self.client.post(
            reverse('reserve_book', kwargs={'pk': self.unavailable_book.pk})
        )
        
        # Should redirect to my_reservations
        self.assertRedirects(response, reverse('my_reservations'))
        
        # Check that a new reservation was created
        self.assertEqual(BookReservation.objects.filter(user=other_user).count(), 1)
    
    def test_reserve_book_view_authenticated_available(self):
        """Test that users can't reserve available books."""
        self.client.login(username='reserver', password='password123')
        
        # Try to reserve an available book
        response = self.client.post(
            reverse('library:reserve_book', kwargs={'pk': self.available_book.pk})
        )
        
        # Should redirect to book detail with error message
        self.assertRedirects(
            response, 
            reverse('library:book_detail', kwargs={'pk': self.available_book.pk})
        )
        
        # Check that no new reservation was created
        self.assertEqual(BookReservation.objects.filter(
            user=self.user, 
            book=self.available_book
        ).count(), 0)
    
    def test_reserve_book_view_already_reserved(self):
        """Test that users can't reserve books they've already reserved."""
        self.client.login(username='reserver', password='password123')
        
        # Try to reserve a book already reserved by this user
        response = self.client.post(
            reverse('reserve_book', kwargs={'pk': self.unavailable_book.pk})
        )
        
        # Should redirect to book detail with error message
        self.assertRedirects(
            response, 
            reverse('book_detail', kwargs={'pk': self.unavailable_book.pk})
        )
        
        # Check that no new reservation was created
        self.assertEqual(BookReservation.objects.filter(
            user=self.user, 
            book=self.unavailable_book
        ).count(), 1)
    
    def test_cancel_reservation_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('cancel_reservation', kwargs={'reservation_id': self.existing_reservation.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/reservations/{self.existing_reservation.pk}/cancel/'
        )
    
    def test_cancel_reservation_view_authenticated(self):
        """Test that authenticated users can cancel their reservations."""
        self.client.login(username='reserver', password='password123')
        
        # Cancel a reservation
        response = self.client.post(
            reverse('cancel_reservation', kwargs={'reservation_id': self.existing_reservation.pk})
        )
        
        # Should redirect to my_reservations
        self.assertRedirects(response, reverse('my_reservations'))
        
        # Check that the reservation status was updated
        self.existing_reservation.refresh_from_db()
        self.assertEqual(self.existing_reservation.status, 'cancelled')
    
    def test_cancel_reservation_view_wrong_user(self):
        """Test that users can't cancel reservations made by others."""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='password123'
        )
        
        # Log in as the other user
        self.client.login(email='other@example.com', password='password123')
        
        # Try to cancel a reservation made by the first user
        response = self.client.post(
            reverse('cancel_reservation', kwargs={'reservation_id': self.existing_reservation.pk})
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Check that the reservation status was not updated
        self.existing_reservation.refresh_from_db()
        self.assertEqual(self.existing_reservation.status, 'pending')
    
    def test_my_reservations_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('my_reservations'))
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/my-reservations/'
        )
    
    def test_my_reservations_view_authenticated(self):
        """Test that authenticated users can see their reservations."""
        self.client.login(username='reserver', password='password123')
        
        response = self.client.get(reverse('my_reservations'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'reservations/my_reservations.html')
        
        # Check context
        self.assertIn('active_reservations', response.context)
        self.assertIn('past_reservations', response.context)
        
        # Check that the existing reservation is in active_reservations
        self.assertEqual(len(response.context['active_reservations']), 1)
        self.assertEqual(response.context['active_reservations'][0], self.existing_reservation)
        
        # Check that past_reservations is empty
        self.assertEqual(len(response.context['past_reservations']), 0)
        
        # Cancel the reservation
        self.existing_reservation.status = 'cancelled'
        self.existing_reservation.save()
        
        # Check the view again
        response = self.client.get(reverse('my_reservations'))
        
        # Now active_reservations should be empty and past_reservations should have the reservation
        self.assertEqual(len(response.context['active_reservations']), 0)
        self.assertEqual(len(response.context['past_reservations']), 1)
        self.assertEqual(response.context['past_reservations'][0], self.existing_reservation)

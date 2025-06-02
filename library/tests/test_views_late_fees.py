"""
Tests for late fee related views in the library application.
Tests the my_late_fees, pay_late_fee, request_fee_waiver, manage_late_fees, and process_waiver_request views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from library.models import Book, Author, Publisher, BookLoan, LateFee, LibrarySettings

User = get_user_model()

class LateFeeViewsTests(TestCase):
    """Tests for late fee related views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create library settings
        LibrarySettings.objects.create(
            late_fee_daily_rate=Decimal('1.00'),
            max_loan_days=14
        )
        
        # Create a regular user
        self.user = User.objects.create_user(
            email='borrower@example.com',
            password='password123'
        )
        
        # Create a staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='password123',
            is_staff=True
        )
        
        # Create an author and publisher
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create a book
        self.book = Book.objects.create(
            title="Overdue Book",
            publisher=self.publisher,
            available_copies=0,  # All copies are borrowed
            total_copies=1
        )
        self.book.authors.add(self.author)
        
        # Create an overdue loan
        self.overdue_loan = BookLoan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.now().date() - timedelta(days=5),
            status='overdue'
        )
        
        # Create a late fee
        self.late_fee = LateFee.objects.create(
            loan=self.overdue_loan,
            amount=Decimal('5.00'),
            days_overdue=5,
            payment_status='pending'
        )
    
    def test_my_late_fees_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('my_late_fees'))
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/my-late-fees/'
        )
    
    def test_my_late_fees_view_authenticated(self):
        """Test that authenticated users can see their late fees."""
        self.client.login(email='borrower@example.com', password='password123')
        
        response = self.client.get(reverse('my_late_fees'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'late_fees/my_late_fees.html')
        
        # Check context
        self.assertIn('pending_fees', response.context)
        self.assertIn('paid_fees', response.context)
        self.assertIn('waived_fees', response.context)
        
        # Check that the late fee is in pending_fees
        self.assertEqual(len(response.context['pending_fees']), 1)
        self.assertEqual(response.context['pending_fees'][0], self.late_fee)
        
        # Check that paid_fees and waived_fees are empty
        self.assertEqual(len(response.context['paid_fees']), 0)
        self.assertEqual(len(response.context['waived_fees']), 0)
    
    def test_pay_late_fee_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('pay_late_fee', kwargs={'fee_id': self.late_fee.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/late-fees/{self.late_fee.pk}/pay/'
        )
    
    def test_pay_late_fee_view_authenticated(self):
        """Test that authenticated users can pay their late fees."""
        self.client.login(email='borrower@example.com', password='password123')
        
        # Pay the late fee
        response = self.client.post(
            reverse('pay_late_fee', kwargs={'fee_id': self.late_fee.pk})
        )
        
        # Should redirect to my_late_fees
        self.assertRedirects(response, reverse('my_late_fees'))
        
        # Check that the late fee status was updated
        self.late_fee.refresh_from_db()
        self.assertEqual(self.late_fee.payment_status, 'paid')
        self.assertIsNotNone(self.late_fee.payment_date)
        
        # Check that the loan's late_fee_paid flag was updated
        self.overdue_loan.refresh_from_db()
        self.assertTrue(self.overdue_loan.late_fee_paid)
    
    def test_pay_late_fee_view_wrong_user(self):
        """Test that users can't pay late fees for other users' loans."""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='password123'
        )
        
        # Log in as the other user
        self.client.login(email='other@example.com', password='password123')
        
        # Try to pay a late fee for a loan by the first user
        response = self.client.post(
            reverse('pay_late_fee', kwargs={'fee_id': self.late_fee.pk})
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Check that the late fee status was not updated
        self.late_fee.refresh_from_db()
        self.assertEqual(self.late_fee.payment_status, 'pending')
    
    def test_request_fee_waiver_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('request_fee_waiver', kwargs={'fee_id': self.late_fee.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/late-fees/{self.late_fee.pk}/request-waiver/'
        )
    
    def test_request_fee_waiver_view_authenticated_get(self):
        """Test that authenticated users can access the waiver request form."""
        self.client.login(email='borrower@example.com', password='password123')
        
        response = self.client.get(
            reverse('request_fee_waiver', kwargs={'fee_id': self.late_fee.pk})
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'late_fees/waiver_request_form.html')
        
        # Check context
        self.assertIn('fee', response.context)
        self.assertEqual(response.context['fee'], self.late_fee)
    
    def test_request_fee_waiver_view_authenticated_post(self):
        """Test that authenticated users can request waivers for their late fees."""
        self.client.login(email='borrower@example.com', password='password123')
        
        # Request a waiver
        response = self.client.post(
            reverse('request_fee_waiver', kwargs={'fee_id': self.late_fee.pk}),
            {
                'reason': 'I was sick and couldn\'t return the book on time.'
            }
        )
        
        # Should redirect to my_late_fees
        self.assertRedirects(response, reverse('my_late_fees'))
        
        # Check that the waiver request was saved
        self.late_fee.refresh_from_db()
        self.assertEqual(self.late_fee.waived_reason, 'I was sick and couldn\'t return the book on time.')
    
    def test_request_fee_waiver_view_wrong_user(self):
        """Test that users can't request waivers for other users' late fees."""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='password123'
        )
        
        # Log in as the other user
        self.client.login(email='other@example.com', password='password123')
        
        # Try to request a waiver for a late fee for a loan by the first user
        response = self.client.get(
            reverse('request_fee_waiver', kwargs={'fee_id': self.late_fee.pk})
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_manage_late_fees_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('manage_late_fees'))
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/admin/late-fees/'
        )
    
    def test_manage_late_fees_view_non_staff(self):
        """Test that non-staff users can't access the manage late fees view."""
        self.client.login(email='borrower@example.com', password='password123')
        
        response = self.client.get(reverse('manage_late_fees'))
        
        # Should redirect to login (or home)
        self.assertEqual(response.status_code, 302)
    
    def test_manage_late_fees_view_staff(self):
        """Test that staff users can access the manage late fees view."""
        self.client.login(email='staff@example.com', password='password123')
        
        response = self.client.get(reverse('manage_late_fees'))
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'late_fees/manage_late_fees.html')
        
        # Check context
        self.assertIn('pending_fees', response.context)
        self.assertIn('paid_fees', response.context)
        self.assertIn('waived_fees', response.context)
        self.assertIn('waiver_requests', response.context)
        
        # Check that the late fee is in pending_fees
        self.assertEqual(len(response.context['pending_fees']), 1)
        self.assertEqual(response.context['pending_fees'][0], self.late_fee)
    
    def test_process_waiver_request_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('process_waiver_request', kwargs={'fee_id': self.late_fee.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/admin/late-fees/{self.late_fee.pk}/process-waiver/'
        )
    
    def test_process_waiver_request_view_non_staff(self):
        """Test that non-staff users can't access the process waiver request view."""
        self.client.login(email='borrower@example.com', password='password123')
        
        response = self.client.get(
            reverse('process_waiver_request', kwargs={'fee_id': self.late_fee.pk})
        )
        
        # Should redirect to login (or home)
        self.assertEqual(response.status_code, 302)
    
    def test_process_waiver_request_view_staff_get(self):
        """Test that staff users can access the process waiver request form."""
        # Add a waiver reason to the late fee
        self.late_fee.waived_reason = 'I was sick and couldn\'t return the book on time.'
        self.late_fee.save()
        
        self.client.login(email='staff@example.com', password='password123')
        
        response = self.client.get(
            reverse('process_waiver_request', kwargs={'fee_id': self.late_fee.pk})
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'late_fees/process_waiver_form.html')
        
        # Check context
        self.assertIn('fee', response.context)
        self.assertEqual(response.context['fee'], self.late_fee)
    
    def test_process_waiver_request_view_staff_post_approve(self):
        """Test that staff users can approve waiver requests."""
        # Add a waiver reason to the late fee
        self.late_fee.waived_reason = 'I was sick and couldn\'t return the book on time.'
        self.late_fee.save()
        
        self.client.login(email='staff@example.com', password='password123')
        
        # Approve the waiver request
        response = self.client.post(
            reverse('process_waiver_request', kwargs={'fee_id': self.late_fee.pk}),
            {
                'action': 'approve'
            }
        )
        
        # Should redirect to manage_late_fees
        self.assertRedirects(response, reverse('manage_late_fees'))
        
        # Check that the late fee status was updated
        self.late_fee.refresh_from_db()
        self.assertEqual(self.late_fee.payment_status, 'waived')
        self.assertEqual(self.late_fee.waived_by, self.staff_user)
        
        # Check that the loan's late_fee_paid flag was updated
        self.overdue_loan.refresh_from_db()
        self.assertTrue(self.overdue_loan.late_fee_paid)
    
    def test_process_waiver_request_view_staff_post_reject(self):
        """Test that staff users can reject waiver requests."""
        # Add a waiver reason to the late fee
        self.late_fee.waived_reason = 'I was sick and couldn\'t return the book on time.'
        self.late_fee.save()
        
        self.client.login(email='staff@example.com', password='password123')
        
        # Reject the waiver request
        response = self.client.post(
            reverse('process_waiver_request', kwargs={'fee_id': self.late_fee.pk}),
            {
                'action': 'reject'
            }
        )
        
        # Should redirect to manage_late_fees
        self.assertRedirects(response, reverse('manage_late_fees'))
        
        # Check that the late fee status was not updated
        self.late_fee.refresh_from_db()
        self.assertEqual(self.late_fee.payment_status, 'pending')
        self.assertIsNone(self.late_fee.waived_by)
        
        # Check that the loan's late_fee_paid flag was not updated
        self.overdue_loan.refresh_from_db()
        self.assertFalse(self.overdue_loan.late_fee_paid)

"""
Tests for review related views in the library application.
Tests the create_review, edit_review, and delete_review views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from library.models import Book, Author, Publisher, Review
from library.forms import ReviewForm

User = get_user_model()

class ReviewViewsTests(TestCase):
    """Tests for review related views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create a user
        self.user = User.objects.create_user(
            email='reviewer@example.com',
            password='password123'
        )
        
        # Create another user
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='password123'
        )
        
        # Create an author and publisher
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create a book
        self.book = Book.objects.create(
            title="Book to Review",
            publisher=self.publisher,
            available_copies=2,
            total_copies=3
        )
        self.book.authors.add(self.author)
        
        # Create a review by the user
        self.review = Review.objects.create(
            book=self.book,
            user=self.user,
            rating=4,
            title="Good book",
            content="I enjoyed reading this book.",
            status='approved'
        )
        
        # Create a review by the other user
        self.other_review = Review.objects.create(
            book=self.book,
            user=self.other_user,
            rating=2,
            title="Not great",
            content="I didn't enjoy this book much.",
            status='approved'
        )
    
    def test_create_review_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('create_review', kwargs={'book_id': self.book.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/books/{self.book.pk}/review/create/'
        )
    
    def test_create_review_view_authenticated_get(self):
        """Test that authenticated users can access the create review form."""
        # Create a new user who hasn't reviewed yet
        new_user = User.objects.create_user(
            email='new@example.com',
            password='password123'
        )
        
        self.client.login(email='new@example.com', password='password123')
        
        response = self.client.get(
            reverse('create_review', kwargs={'book_id': self.book.pk})
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'reviews/review_form.html')
        
        # Check context
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ReviewForm)
        self.assertIn('book', response.context)
        self.assertEqual(response.context['book'], self.book)
    
    def test_create_review_view_authenticated_post(self):
        """Test that authenticated users can create reviews."""
        # Create a new user who hasn't reviewed yet
        new_user = User.objects.create_user(
            email='new@example.com',
            password='password123'
        )
        
        self.client.login(email='new@example.com', password='password123')
        
        # Submit a review
        response = self.client.post(
            reverse('create_review', kwargs={'book_id': self.book.pk}),
            {
                'rating': 5,
                'title': 'Excellent book',
                'content': 'One of the best books I have read.'
            }
        )
        
        # Should redirect to book detail
        self.assertRedirects(
            response, 
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        
        # Check that a new review was created
        self.assertTrue(Review.objects.filter(
            book=self.book,
            user=new_user,
            rating=5,
            title='Excellent book'
        ).exists())
    
    def test_create_review_view_already_reviewed(self):
        """Test that users can't create multiple reviews for the same book."""
        self.client.login(email='reviewer@example.com', password='password123')
        
        # Try to create another review for the same book
        response = self.client.post(
            reverse('create_review', kwargs={'book_id': self.book.pk}),
            {
                'rating': 3,
                'title': 'Changed my mind',
                'content': 'On second thought, it was just okay.'
            }
        )
        
        # Should redirect to book detail with error message
        self.assertRedirects(
            response, 
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        
        # Check that no new review was created
        self.assertEqual(Review.objects.filter(
            book=self.book,
            user=self.user
        ).count(), 1)
    
    def test_edit_review_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('edit_review', kwargs={'review_id': self.review.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/reviews/{self.review.pk}/edit/'
        )
    
    def test_edit_review_view_authenticated_get(self):
        """Test that authenticated users can access the edit review form."""
        self.client.login(email='reviewer@example.com', password='password123')
        
        response = self.client.get(
            reverse('edit_review', kwargs={'review_id': self.review.pk})
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'reviews/review_form.html')
        
        # Check context
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ReviewForm)
        self.assertIn('review', response.context)
        self.assertEqual(response.context['review'], self.review)
    
    def test_edit_review_view_authenticated_post(self):
        """Test that authenticated users can edit their reviews."""
        self.client.login(email='reviewer@example.com', password='password123')
        
        # Edit the review
        response = self.client.post(
            reverse('edit_review', kwargs={'review_id': self.review.pk}),
            {
                'rating': 3,
                'title': 'Changed my mind',
                'content': 'On second thought, it was just okay.'
            }
        )
        
        # Should redirect to book detail
        self.assertRedirects(
            response, 
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        
        # Check that the review was updated
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)
        self.assertEqual(self.review.title, 'Changed my mind')
        self.assertEqual(self.review.content, 'On second thought, it was just okay.')
        self.assertEqual(self.review.status, 'pending')  # Should be reset to pending
    
    def test_edit_review_view_wrong_user(self):
        """Test that users can't edit reviews made by others."""
        self.client.login(email='other@example.com', password='password123')
        
        # Try to edit a review made by another user
        response = self.client.get(
            reverse('edit_review', kwargs={'review_id': self.review.pk})
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_delete_review_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(
            reverse('delete_review', kwargs={'review_id': self.review.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/reviews/{self.review.pk}/delete/'
        )
    
    def test_delete_review_view_authenticated_get(self):
        """Test that authenticated users can access the delete review confirmation."""
        self.client.login(email='reviewer@example.com', password='password123')
        
        response = self.client.get(
            reverse('delete_review', kwargs={'review_id': self.review.pk})
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check template
        self.assertTemplateUsed(response, 'reviews/review_confirm_delete.html')
        
        # Check context
        self.assertIn('review', response.context)
        self.assertEqual(response.context['review'], self.review)
    
    def test_delete_review_view_authenticated_post(self):
        """Test that authenticated users can delete their reviews."""
        self.client.login(email='reviewer@example.com', password='password123')
        
        # Delete the review
        response = self.client.post(
            reverse('delete_review', kwargs={'review_id': self.review.pk})
        )
        
        # Should redirect to book detail
        self.assertRedirects(
            response, 
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        
        # Check that the review was deleted
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())
    
    def test_delete_review_view_wrong_user(self):
        """Test that users can't delete reviews made by others."""
        self.client.login(email='other@example.com', password='password123')
        
        # Try to delete a review made by another user
        response = self.client.get(
            reverse('delete_review', kwargs={'review_id': self.review.pk})
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

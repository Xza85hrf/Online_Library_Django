"""
Tests for forms in the library application.
Tests the ReviewForm and any other forms used in the application.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from library.models import Book, Author, Publisher, Review
from library.forms import ReviewForm

User = get_user_model()

class ReviewFormTests(TestCase):
    """Tests for the ReviewForm."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='password123'
        )
        
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        self.book = Book.objects.create(
            title="Test Book",
            publisher=self.publisher
        )
        self.book.authors.add(self.author)
    
    def test_review_form_valid_data(self):
        """Test that the form is valid with valid data."""
        form_data = {
            'rating': 4,
            'title': 'Good book',
            'content': 'I enjoyed reading this book.'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_review_form_invalid_rating(self):
        """Test that the form is invalid with an invalid rating."""
        # Rating too high
        form_data = {
            'rating': 6,  # Invalid: should be 1-5
            'title': 'Good book',
            'content': 'I enjoyed reading this book.'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        
        # Rating too low
        form_data = {
            'rating': 0,  # Invalid: should be 1-5
            'title': 'Good book',
            'content': 'I enjoyed reading this book.'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
    
    def test_review_form_missing_content(self):
        """Test that the form is invalid with missing content."""
        form_data = {
            'rating': 4,
            'title': 'Good book',
            # Missing content
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)
    
    def test_review_form_missing_rating(self):
        """Test that the form is invalid with missing rating."""
        form_data = {
            # Missing rating
            'title': 'Good book',
            'content': 'I enjoyed reading this book.'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
    
    def test_review_form_optional_title(self):
        """Test that the title field is optional."""
        form_data = {
            'rating': 4,
            # No title
            'content': 'I enjoyed reading this book.'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_review_form_with_user_and_book(self):
        """Test that the form correctly sets user and book when provided."""
        form_data = {
            'rating': 4,
            'title': 'Good book',
            'content': 'I enjoyed reading this book.'
        }
        form = ReviewForm(data=form_data, user=self.user, book=self.book)
        self.assertTrue(form.is_valid())
        
        # Save the form
        review = form.save()
        
        # Check that user and book were set correctly
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.book, self.book)
    
    def test_review_form_widgets(self):
        """Test that the form has the correct widgets."""
        form = ReviewForm()
        
        # Check that rating uses RadioSelect widget
        self.assertEqual(form.fields['rating'].widget.__class__.__name__, 'RadioSelect')
        
        # Check that title uses TextInput widget
        self.assertEqual(form.fields['title'].widget.__class__.__name__, 'TextInput')
        
        # Check that content uses Textarea widget
        self.assertEqual(form.fields['content'].widget.__class__.__name__, 'Textarea')
    
    def test_review_form_help_texts(self):
        """Test that the form has the correct help texts."""
        form = ReviewForm()
        
        # Check help texts
        self.assertEqual(form.fields['rating'].help_text, _('Rate this book from 1 to 5 stars'))
        self.assertEqual(form.fields['title'].help_text, _('Give your review a title (optional)'))
        self.assertEqual(form.fields['content'].help_text, _('Share your thoughts about this book'))
    
    def test_review_form_labels(self):
        """Test that the form has the correct labels."""
        form = ReviewForm()
        
        # Check labels
        self.assertEqual(form.fields['rating'].label, _('Your Rating'))
        self.assertEqual(form.fields['title'].label, _('Review Title'))
        self.assertEqual(form.fields['content'].label, _('Your Review'))

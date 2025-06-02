"""
Tests for basic views in the library application.
Tests the home, book_list, book_detail, author_list, author_detail, publisher_list, and publisher_detail views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from library.models import Book, Author, Publisher, Review

User = get_user_model()

class HomeViewTests(TestCase):
    """Tests for the home view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create some authors
        self.author1 = Author.objects.create(name="Author One")
        self.author2 = Author.objects.create(name="Author Two")
        
        # Create a publisher
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create some books
        for i in range(10):
            book = Book.objects.create(
                title=f"Book {i}",
                publisher=self.publisher,
                publication_date=timezone.now().date() - timedelta(days=i*30),
                available_copies=i % 3 + 1,
                total_copies=i % 3 + 2
            )
            book.authors.add(self.author1 if i % 2 == 0 else self.author2)
    
    def test_home_view_status_code(self):
        """Test that the home view returns a 200 status code."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_view_template(self):
        """Test that the home view uses the correct template."""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home.html')
    
    def test_home_view_context(self):
        """Test that the home view provides the correct context."""
        response = self.client.get(reverse('home'))
        
        # Check that featured_books and popular_authors are in the context
        self.assertIn('featured_books', response.context)
        self.assertIn('popular_authors', response.context)
        
        # Check that we have the expected number of featured books (6)
        self.assertEqual(len(response.context['featured_books']), 6)
        
        # Check that we have the expected number of popular authors (4 or less)
        self.assertLessEqual(len(response.context['popular_authors']), 4)

class BookListViewTests(TestCase):
    """Tests for the book_list view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create some authors
        self.author1 = Author.objects.create(name="Fantasy Author")
        self.author2 = Author.objects.create(name="Science Author")
        
        # Create some publishers
        self.publisher1 = Publisher.objects.create(name="Fantasy Publisher")
        self.publisher2 = Publisher.objects.create(name="Science Publisher")
        
        # Create some books with different genres
        # Fantasy books
        for i in range(5):
            Book.objects.create(
                title=f"Fantasy Book {i}",
                publisher=self.publisher1,
                language="polski",
                genres=["fantasy", "adventure"],
                available_copies=1,
                total_copies=2
            ).authors.add(self.author1)
        
        # Science books
        for i in range(3):
            Book.objects.create(
                title=f"Science Book {i}",
                publisher=self.publisher2,
                language="english",
                genres=["science", "education"],
                available_copies=0,  # Unavailable
                total_copies=1
            ).authors.add(self.author2)
    
    def test_book_list_view_status_code(self):
        """Test that the book_list view returns a 200 status code."""
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_book_list_view_template(self):
        """Test that the book_list view uses the correct template."""
        response = self.client.get(reverse('book_list'))
        self.assertTemplateUsed(response, 'books/book_list.html')
    
    def test_book_list_view_context(self):
        """Test that the book_list view provides the correct context."""
        response = self.client.get(reverse('book_list'))
        
        # Check that books are in the context
        self.assertIn('books', response.context)
        
        # Check that we have all books (8)
        self.assertEqual(len(response.context['books']), 8)
        
        # Check that genre_choices are in the context
        self.assertIn('genre_choices', response.context)
    
    def test_book_list_view_with_query(self):
        """Test that the book_list view filters by query."""
        response = self.client.get(reverse('library:book_list') + '?q=Fantasy')
        
        # Check that we only have fantasy books (5)
        self.assertEqual(len(response.context['books']), 5)
        
        # Check that the first book title contains 'Fantasy'
        self.assertIn('Fantasy', response.context['books'][0].title)
    
    def test_book_list_view_with_author_filter(self):
        """Test that the book_list view filters by author."""
        response = self.client.get(
            reverse('library:book_list') + f'?author={self.author2.id}'
        )
        
        # Check that we only have science books (3)
        self.assertEqual(len(response.context['books']), 3)
        
        # Check that the first book title contains 'Science'
        self.assertIn('Science', response.context['books'][0].title)
    
    def test_book_list_view_with_publisher_filter(self):
        """Test that the book_list view filters by publisher."""
        response = self.client.get(
            reverse('library:book_list') + f'?publisher={self.publisher1.id}'
        )
        
        # Check that we only have fantasy books (5)
        self.assertEqual(len(response.context['books']), 5)
    
    def test_book_list_view_with_language_filter(self):
        """Test that the book_list view filters by language."""
        response = self.client.get(
            reverse('library:book_list') + '?language=english'
        )
        
        # Check that we only have english books (3)
        self.assertEqual(len(response.context['books']), 3)
    
    def test_book_list_view_with_availability_filter(self):
        """Test that the book_list view filters by availability."""
        # Test available books
        response = self.client.get(
            reverse('library:book_list') + '?availability=available'
        )
        self.assertEqual(len(response.context['books']), 5)  # Fantasy books
        
        # Test unavailable books
        response = self.client.get(
            reverse('library:book_list') + '?availability=unavailable'
        )
        self.assertEqual(len(response.context['books']), 3)  # Science books

class BookDetailViewTests(TestCase):
    """Tests for the book_detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create an author and publisher
        self.author = Author.objects.create(name="Test Author")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create a book
        self.book = Book.objects.create(
            title="Test Book",
            publisher=self.publisher,
            description="A test book description.",
            isbn="1234567890123",
            pages=200,
            language="polski",
            genres=["fantasy", "adventure"],
            available_copies=2,
            total_copies=3
        )
        self.book.authors.add(self.author)
        
        # Create a user for reviews
        self.user = User.objects.create_user(
            email='reviewer@example.com',
            password='password123'
        )
        
        # Create some reviews
        Review.objects.create(
            book=self.book,
            user=self.user,
            rating=5,
            title="Great book",
            content="I loved this book!",
            status='approved'
        )
        
        # Create another user and review
        other_user = User.objects.create_user(
            username='other_reviewer',
            email='other@example.com',
            password='password123'
        )
        
        Review.objects.create(
            book=self.book,
            user=other_user,
            rating=3,
            title="It was okay",
            content="Not bad, but not great either.",
            status='approved'
        )
        
        # Create a pending review
        Review.objects.create(
            book=self.book,
            user=User.objects.create_user(username='pending_user', password='pass'),
            rating=1,
            title="Terrible",
            content="I hated it.",
            status='pending'  # This one shouldn't show up
        )
    
    def test_book_detail_view_status_code(self):
        """Test that the book_detail view returns a 200 status code."""
        response = self.client.get(
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_book_detail_view_template(self):
        """Test that the book_detail view uses the correct template."""
        response = self.client.get(
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        self.assertTemplateUsed(response, 'books/book_detail_main.html')
    
    def test_book_detail_view_context(self):
        """Test that the book_detail view provides the correct context."""
        response = self.client.get(
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        
        # Check that book is in the context
        self.assertIn('book', response.context)
        self.assertEqual(response.context['book'], self.book)
        
        # Check that reviews are in the context
        self.assertIn('reviews', response.context)
        
        # Check that we only have approved reviews (2)
        self.assertEqual(len(response.context['reviews']), 2)
        
        # Check that review_form is in the context
        self.assertIn('review_form', response.context)
    
    def test_book_detail_view_with_authenticated_user(self):
        """Test the book_detail view with an authenticated user."""
        self.client.login(email='reviewer@example.com', password='password123')
        
        response = self.client.get(
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        
        # Check that user_has_reviewed is True
        self.assertIn('user_has_reviewed', response.context)
        self.assertTrue(response.context['user_has_reviewed'])
        
        # Check that user_review is in the context
        self.assertIn('user_review', response.context)
        self.assertIsNotNone(response.context['user_review'])
    
    def test_book_detail_view_with_unauthenticated_user(self):
        """Test the book_detail view with an unauthenticated user."""
        response = self.client.get(
            reverse('book_detail', kwargs={'pk': self.book.pk})
        )
        
        # Check that user_has_reviewed is False
        self.assertIn('user_has_reviewed', response.context)
        self.assertFalse(response.context['user_has_reviewed'])
        
        # Check that user_review is None
        self.assertIn('user_review', response.context)
        self.assertIsNone(response.context['user_review'])

class AuthorListViewTests(TestCase):
    """Tests for the author_list view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create some authors
        for i in range(15):
            author = Author.objects.create(
                name=f"Author {chr(65 + i)}",  # A, B, C, ...
                bio=f"Bio for Author {chr(65 + i)}"
            )
            
            # Create some books for each author
            for j in range(i % 5 + 1):  # 1-5 books per author
                book = Book.objects.create(
                    title=f"Book {j} by Author {chr(65 + i)}",
                    description=f"Description for Book {j}"
                )
                book.authors.add(author)
    
    def test_author_list_view_status_code(self):
        """Test that the author_list view returns a 200 status code."""
        response = self.client.get(reverse('author_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_author_list_view_template(self):
        """Test that the author_list view uses the correct template."""
        response = self.client.get(reverse('author_list'))
        self.assertTemplateUsed(response, 'authors/author_list.html')
    
    def test_author_list_view_context(self):
        """Test that the author_list view provides the correct context."""
        response = self.client.get(reverse('author_list'))
        
        # Check that authors are in the context
        self.assertIn('authors', response.context)
        
        # Check that we have all authors (15)
        self.assertEqual(len(response.context['authors']), 15)
    
    def test_author_list_view_with_query(self):
        """Test that the author_list view filters by query."""
        response = self.client.get(reverse('library:author_list') + '?q=Author A')
        
        # Check that we only have authors with 'A' in their name
        for author in response.context['authors']:
            self.assertIn('A', author.name)
    
    def test_author_list_view_with_letter_filter(self):
        """Test that the author_list view filters by starting letter."""
        response = self.client.get(reverse('library:author_list') + '?letter=A')
        
        # Check that we only have authors starting with 'A'
        for author in response.context['authors']:
            self.assertTrue(author.name.startswith('A'))
    
    def test_author_list_view_with_sorting(self):
        """Test that the author_list view sorts correctly."""
        # Test name ascending
        response = self.client.get(reverse('library:author_list') + '?sort=name_asc')
        authors = list(response.context['authors'])
        for i in range(len(authors) - 1):
            self.assertLessEqual(authors[i].name, authors[i + 1].name)
        
        # Test name descending
        response = self.client.get(reverse('library:author_list') + '?sort=name_desc')
        authors = list(response.context['authors'])
        for i in range(len(authors) - 1):
            self.assertGreaterEqual(authors[i].name, authors[i + 1].name)

class AuthorDetailViewTests(TestCase):
    """Tests for the author_detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create an author
        self.author = Author.objects.create(
            name="Test Author",
            bio="This is a test author bio.",
            birth_date=timezone.now().date() - timedelta(days=365*40)
        )
        
        # Create some books for this author
        for i in range(5):
            book = Book.objects.create(
                title=f"Book {i} by Test Author",
                description=f"Description for Book {i}",
                publication_date=timezone.now().date() - timedelta(days=i*100)
            )
            book.authors.add(self.author)
    
    def test_author_detail_view_status_code(self):
        """Test that the author_detail view returns a 200 status code."""
        response = self.client.get(
            reverse('author_detail', kwargs={'pk': self.author.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_author_detail_view_template(self):
        """Test that the author_detail view uses the correct template."""
        response = self.client.get(
            reverse('author_detail', kwargs={'pk': self.author.pk})
        )
        self.assertTemplateUsed(response, 'authors/author_detail.html')
    
    def test_author_detail_view_context(self):
        """Test that the author_detail view provides the correct context."""
        response = self.client.get(
            reverse('author_detail', kwargs={'pk': self.author.pk})
        )
        
        # Check that author is in the context
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.author)
        
        # Check that books are in the context
        self.assertIn('books', response.context)
        
        # Check that we have all books by this author (5)
        self.assertEqual(len(response.context['books']), 5)

class PublisherListViewTests(TestCase):
    """Tests for the publisher_list view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create some publishers
        for i in range(10):
            Publisher.objects.create(
                name=f"Publisher {i}",
                description=f"Description for Publisher {i}"
            )
    
    def test_publisher_list_view_status_code(self):
        """Test that the publisher_list view returns a 200 status code."""
        response = self.client.get(reverse('publisher_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_publisher_list_view_template(self):
        """Test that the publisher_list view uses the correct template."""
        response = self.client.get(reverse('publisher_list'))
        self.assertTemplateUsed(response, 'publishers/publisher_list.html')
    
    def test_publisher_list_view_context(self):
        """Test that the publisher_list view provides the correct context."""
        response = self.client.get(reverse('publisher_list'))
        
        # Check that publishers are in the context
        self.assertIn('publishers', response.context)
        
        # Check that we have all publishers (10)
        self.assertEqual(len(response.context['publishers']), 10)
    
    def test_publisher_list_view_with_query(self):
        """Test that the publisher_list view filters by query."""
        response = self.client.get(reverse('library:publisher_list') + '?q=Publisher 1')
        
        # Check that we only have publishers with '1' in their name
        for publisher in response.context['publishers']:
            self.assertIn('1', publisher.name)

class PublisherDetailViewTests(TestCase):
    """Tests for the publisher_detail view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create a publisher
        self.publisher = Publisher.objects.create(
            name="Test Publisher",
            description="This is a test publisher description.",
            founded_date=timezone.now().date() - timedelta(days=365*20)
        )
        
        # Create some books for this publisher
        for i in range(5):
            Book.objects.create(
                title=f"Book {i} by Test Publisher",
                description=f"Description for Book {i}",
                publisher=self.publisher,
                publication_date=timezone.now().date() - timedelta(days=i*100)
            )
    
    def test_publisher_detail_view_status_code(self):
        """Test that the publisher_detail view returns a 200 status code."""
        response = self.client.get(
            reverse('publisher_detail', kwargs={'pk': self.publisher.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_publisher_detail_view_template(self):
        """Test that the publisher_detail view uses the correct template."""
        response = self.client.get(
            reverse('publisher_detail', kwargs={'pk': self.publisher.pk})
        )
        self.assertTemplateUsed(response, 'publishers/publisher_detail.html')
    
    def test_publisher_detail_view_context(self):
        """Test that the publisher_detail view provides the correct context."""
        response = self.client.get(
            reverse('publisher_detail', kwargs={'pk': self.publisher.pk})
        )
        
        # Check that publisher is in the context
        self.assertIn('publisher', response.context)
        self.assertEqual(response.context['publisher'], self.publisher)
        
        # Check that books are in the context
        self.assertIn('books', response.context)
        
        # Check that we have all books by this publisher (5)
        self.assertEqual(len(response.context['books']), 5)

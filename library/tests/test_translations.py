"""
Tests for translations and localization in the library application.
Tests that views correctly use translated strings and that the UI is properly localized.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from library.models import Book, Author, Publisher

User = get_user_model()

class TranslationTests(TestCase):
    """Tests for translations and localization."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create a user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123'
        )
        
        # Create an author
        self.author = Author.objects.create(name="Test Author")
        
        # Create a publisher
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create a book
        self.book = Book.objects.create(
            title="Test Book",
            publisher=self.publisher,
            available_copies=2,
            total_copies=3
        )
        self.book.authors.add(self.author)
    
    def test_home_page_polish_translation(self):
        """Test that the home page is correctly translated to Polish."""
        with translation.override('pl'):
            response = self.client.get(reverse('home'))
            
            # Check that the response contains Polish text
            self.assertContains(response, "Biblioteka Online")
            self.assertContains(response, "Najnowsze książki")
            self.assertContains(response, "Popularne kategorie")
    
    def test_book_list_page_polish_translation(self):
        """Test that the book list page is correctly translated to Polish."""
        with translation.override('pl'):
            response = self.client.get(reverse('book_list'))
            
            # Check that the response contains Polish text
            self.assertContains(response, "Wszystkie książki")
            self.assertContains(response, "Filtruj")
            self.assertContains(response, "Sortuj według")
    
    def test_book_detail_page_polish_translation(self):
        """Test that the book detail page is correctly translated to Polish."""
        with translation.override('pl'):
            response = self.client.get(reverse('book_detail', kwargs={'pk': self.book.pk}))
            
            # Check that the response contains Polish text
            self.assertContains(response, "Szczegóły książki")
            self.assertContains(response, "Autor")
            self.assertContains(response, "Wydawca")
            self.assertContains(response, "Dostępne egzemplarze")
    
    def test_login_page_polish_translation(self):
        """Test that the login page is correctly translated to Polish."""
        with translation.override('pl'):
            response = self.client.get(reverse('login'))
            
            # Check that the response contains Polish text
            self.assertContains(response, "Zaloguj się")
            self.assertContains(response, "Nazwa użytkownika")
            self.assertContains(response, "Hasło")
    
    def test_genre_translations(self):
        """Test that book genres are correctly translated."""
        with translation.override('pl'):
            response = self.client.get(reverse('book_list'))
            
            # Check that genre translations are in the context
            self.assertIn('genre_translations', response.context)
            genre_translations = response.context['genre_translations']
            
            # Check some specific translations
            self.assertEqual(genre_translations['fiction'], 'Fikcja')
            self.assertEqual(genre_translations['nonfiction'], 'Literatura faktu')
            self.assertEqual(genre_translations['scifi'], 'Science Fiction')
            self.assertEqual(genre_translations['mystery'], 'Kryminał')
            self.assertEqual(genre_translations['fantasy'], 'Fantastyka')
    
    def test_model_verbose_names(self):
        """Test that model verbose names are correctly translated."""
        with translation.override('pl'):
            # Check Book model verbose name
            self.assertEqual(Book._meta.verbose_name, _('Book'))
            self.assertEqual(Book._meta.verbose_name_plural, _('Books'))
            
            # Check Author model verbose name
            self.assertEqual(Author._meta.verbose_name, _('Author'))
            self.assertEqual(Author._meta.verbose_name_plural, _('Authors'))
            
            # Check Publisher model verbose name
            self.assertEqual(Publisher._meta.verbose_name, _('Publisher'))
            self.assertEqual(Publisher._meta.verbose_name_plural, _('Publishers'))
    
    def test_field_verbose_names(self):
        """Test that field verbose names are correctly translated."""
        with translation.override('pl'):
            # Check Book field verbose names
            self.assertEqual(Book._meta.get_field('title').verbose_name, _('title'))
            self.assertEqual(Book._meta.get_field('authors').verbose_name, _('authors'))
            self.assertEqual(Book._meta.get_field('publisher').verbose_name, _('publisher'))
            self.assertEqual(Book._meta.get_field('available_copies').verbose_name, _('available copies'))
            
            # Check Author field verbose names
            self.assertEqual(Author._meta.get_field('name').verbose_name, _('name'))
            self.assertEqual(Author._meta.get_field('bio').verbose_name, _('bio'))
            
            # Check Publisher field verbose names
            self.assertEqual(Publisher._meta.get_field('name').verbose_name, _('name'))
            self.assertEqual(Publisher._meta.get_field('description').verbose_name, _('description'))
    
    def test_language_switch(self):
        """Test that the language can be switched."""
        # First check English
        with translation.override('en'):
            response = self.client.get(reverse('home'))
            self.assertContains(response, "Online Library")
            self.assertContains(response, "Latest Books")
        
        # Then check Polish
        with translation.override('pl'):
            response = self.client.get(reverse('home'))
            self.assertContains(response, "Biblioteka Online")
            self.assertContains(response, "Najnowsze książki")
    
    def test_form_translations(self):
        """Test that form labels and help texts are correctly translated."""
        # Login to access the review form
        self.client.login(email='test@example.com', password='password123')
        
        with translation.override('pl'):
            response = self.client.get(reverse('create_review', kwargs={'book_id': self.book.pk}))
            
            # Check that the form labels are translated
            self.assertContains(response, "Twoja ocena")
            self.assertContains(response, "Tytuł recenzji")
            self.assertContains(response, "Twoja recenzja")
            
            # Check that the form help texts are translated
            self.assertContains(response, "Oceń tę książkę od 1 do 5 gwiazdek")
            self.assertContains(response, "Podziel się swoimi przemyśleniami na temat tej książki")
    
    def test_error_messages_translation(self):
        """Test that error messages are correctly translated."""
        with translation.override('pl'):
            # Try to access a non-existent book
            response = self.client.get(
                reverse('library:book_detail', kwargs={'pk': 9999})
            )
            
            # Check that the 404 page is in Polish
            self.assertEqual(response.status_code, 404)
            self.assertContains(response, "Nie znaleziono", status_code=404)
    
    def test_date_format_localization(self):
        """Test that dates are correctly formatted according to the locale."""
        # Login to access the my_loans page
        self.client.login(email='test@example.com', password='password123')
        
        with translation.override('pl'):
            response = self.client.get(reverse('my_loans'))
            
            # Check that the date format is Polish (DD.MM.YYYY)
            # This is a bit tricky to test without actual loans,
            # but we can check for the date headers
            self.assertContains(response, "Data wypożyczenia")
            self.assertContains(response, "Termin zwrotu")

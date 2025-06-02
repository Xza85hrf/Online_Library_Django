"""
Tests for AI image generation signals in the library application.
Tests the signal handlers that generate book covers, author portraits, and publisher logos.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil

from library.models import Book, Author, Publisher
from library.ai_signals import (
    generate_book_cover, generate_author_portrait, generate_publisher_logo,
    generate_with_flux
)

class AISignalsTestCase(TestCase):
    """Base test case for AI signals with temporary media directory."""
    
    def setUp(self):
        """Set up test data and temporary media directory."""
        # Create a temporary directory for media files
        self.temp_media_dir = tempfile.mkdtemp()
        self.old_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self.temp_media_dir
        
        # Create directories for images
        os.makedirs(os.path.join(self.temp_media_dir, 'covers'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_media_dir, 'authors'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_media_dir, 'publishers'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_media_dir, 'profile_pics'), exist_ok=True)
    
    def tearDown(self):
        """Clean up temporary media directory."""
        settings.MEDIA_ROOT = self.old_media_root
        shutil.rmtree(self.temp_media_dir)

class GenerateWithFluxTests(AISignalsTestCase):
    """Tests for the generate_with_flux function."""
    
    @patch('library.ai_signals.subprocess.run')
    @patch('library.ai_signals.os.path.exists')
    def test_generate_with_flux_success(self, mock_exists, mock_run):
        """Test successful image generation with Flux AI."""
        # Mock the existence of the flux wrapper
        mock_exists.return_value = True
        
        # Mock successful subprocess run
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Image generated successfully"
        mock_run.return_value = mock_process
        
        # Call the function
        output_path = os.path.join(self.temp_media_dir, 'test_image.jpg')
        result = generate_with_flux("Test prompt", output_path)
        
        # Check that the function returned True
        self.assertTrue(result)
        
        # Check that subprocess.run was called with the correct arguments
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertIn("--prompt", cmd)
        self.assertIn("Test prompt", cmd)
        self.assertIn("--output", cmd)
        self.assertIn(output_path, cmd)
    
    @patch('library.ai_signals.subprocess.run')
    @patch('library.ai_signals.os.path.exists')
    def test_generate_with_flux_failure(self, mock_exists, mock_run):
        """Test failed image generation with Flux AI."""
        # Mock the existence of the flux wrapper
        mock_exists.return_value = True
        
        # Mock failed subprocess run
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Error generating image"
        mock_run.return_value = mock_process
        
        # Call the function
        output_path = os.path.join(self.temp_media_dir, 'test_image.jpg')
        result = generate_with_flux("Test prompt", output_path)
        
        # Check that the function returned False
        self.assertFalse(result)
    
    @patch('library.ai_signals.os.path.exists')
    def test_generate_with_flux_wrapper_not_found(self, mock_exists):
        """Test behavior when Flux AI wrapper is not found."""
        # Mock the non-existence of the flux wrapper
        mock_exists.return_value = False
        
        # Call the function
        output_path = os.path.join(self.temp_media_dir, 'test_image.jpg')
        result = generate_with_flux("Test prompt", output_path)
        
        # Check that the function returned False
        self.assertFalse(result)

class BookCoverSignalTests(AISignalsTestCase):
    """Tests for the generate_book_cover signal handler."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create an author
        self.author = Author.objects.create(name="Test Author")
        
        # Create a publisher
        self.publisher = Publisher.objects.create(name="Test Publisher")
    
    @patch('library.ai_signals.generate_with_flux')
    def test_generate_book_cover_signal(self, mock_generate):
        """Test that the signal generates a book cover for a new book."""
        # Mock successful image generation
        mock_generate.return_value = True
        
        # Create a test image file
        with open(os.path.join(self.temp_media_dir, 'test_cover.jpg'), 'wb') as f:
            f.write(b'test image content')
        
        # Create a book without a cover
        book = Book.objects.create(
            title="Test Book",
            publisher=self.publisher
        )
        book.authors.add(self.author)
        
        # The signal should have been triggered automatically
        
        # Check that generate_with_flux was called
        mock_generate.assert_called_once()
        
        # Check that the prompt contains the book title and author name
        args, kwargs = mock_generate.call_args
        prompt, output_path = args
        self.assertIn("Test Book", prompt)
        self.assertIn("Test Author", prompt)
        
        # Check that the prompt includes professional book cover keywords
        self.assertIn("professional book cover", prompt.lower())
        
        # Check that the output path is in the covers directory
        self.assertIn('covers', output_path)
    
    @patch('library.ai_signals.generate_with_flux')
    def test_generate_book_cover_signal_with_existing_cover(self, mock_generate):
        """Test that the signal doesn't generate a cover if one already exists."""
        # Create a book with a cover
        book = Book.objects.create(
            title="Test Book with Cover",
            publisher=self.publisher,
            cover="covers/existing_cover.jpg"
        )
        book.authors.add(self.author)
        
        # Check that generate_with_flux was not called
        mock_generate.assert_not_called()
    
    @patch('library.ai_signals.generate_with_flux')
    def test_generate_book_cover_signal_no_authors(self, mock_generate):
        """Test that the signal doesn't generate a cover if the book has no authors."""
        # Create a book without authors
        book = Book.objects.create(
            title="Test Book No Authors",
            publisher=self.publisher
        )
        
        # Check that generate_with_flux was not called
        mock_generate.assert_not_called()

class AuthorPortraitSignalTests(AISignalsTestCase):
    """Tests for the generate_author_portrait signal handler."""
    
    @patch('library.ai_signals.generate_with_flux')
    def test_generate_author_portrait_signal(self, mock_generate):
        """Test that the signal generates a portrait for a new author."""
        # Mock successful image generation
        mock_generate.return_value = True
        
        # Create a test image file
        with open(os.path.join(self.temp_media_dir, 'test_portrait.jpg'), 'wb') as f:
            f.write(b'test image content')
        
        # Create an author without a photo
        author = Author.objects.create(
            name="New Author"
        )
        
        # The signal should have been triggered automatically
        
        # Check that generate_with_flux was called
        mock_generate.assert_called_once()
        
        # Check that the prompt contains the author name
        args, kwargs = mock_generate.call_args
        prompt, output_path = args
        self.assertIn("New Author", prompt)
        
        # Check that the prompt includes portrait keywords
        self.assertIn("portrait", prompt.lower())
        self.assertIn("professional", prompt.lower())
        
        # Check that the output path is in the authors directory
        self.assertIn('authors', output_path)
    
    @patch('library.ai_signals.generate_with_flux')
    def test_generate_author_portrait_signal_with_existing_photo(self, mock_generate):
        """Test that the signal doesn't generate a portrait if one already exists."""
        # Create an author with a photo
        author = Author.objects.create(
            name="Author with Photo",
            photo="authors/existing_photo.jpg"
        )
        
        # Check that generate_with_flux was not called
        mock_generate.assert_not_called()

class PublisherLogoSignalTests(AISignalsTestCase):
    """Tests for the generate_publisher_logo signal handler."""
    
    @patch('library.ai_signals.generate_with_flux')
    def test_generate_publisher_logo_signal(self, mock_generate):
        """Test that the signal generates a logo for a new publisher."""
        # Mock successful image generation
        mock_generate.return_value = True
        
        # Create a test image file
        with open(os.path.join(self.temp_media_dir, 'test_logo.jpg'), 'wb') as f:
            f.write(b'test image content')
        
        # Create a publisher without a logo
        publisher = Publisher.objects.create(
            name="New Publisher"
        )
        
        # The signal should have been triggered automatically
        
        # Check that generate_with_flux was called
        mock_generate.assert_called_once()
        
        # Check that the prompt contains the publisher name
        args, kwargs = mock_generate.call_args
        prompt, output_path = args
        self.assertIn("New Publisher", prompt)
        
        # Check that the prompt includes logo keywords
        self.assertIn("logo", prompt.lower())
        self.assertIn("professional", prompt.lower())
        
        # Check that the output path is in the publishers directory
        self.assertIn('publishers', output_path)
    
    @patch('library.ai_signals.generate_with_flux')
    def test_generate_publisher_logo_signal_with_existing_logo(self, mock_generate):
        """Test that the signal doesn't generate a logo if one already exists."""
        # Create a publisher with a logo
        publisher = Publisher.objects.create(
            name="Publisher with Logo",
            logo="publishers/existing_logo.jpg"
        )
        
        # Check that generate_with_flux was not called
        mock_generate.assert_not_called()

class ImagePathTests(TestCase):
    """Tests for correct image paths in the database.
    
    These tests ensure that images are saved to the correct directories as specified in the project:
    - Book covers: media/covers/
    - Author photos: media/authors/
    - Publisher logos: media/publishers/
    """
    
    def test_book_cover_path(self):
        """Test that book covers are saved to the correct path."""
        # Create a book with a cover
        author = Author.objects.create(name="Test Author")
        publisher = Publisher.objects.create(name="Test Publisher")
        
        # Create a simple uploaded file for the cover
        cover_content = b'test cover image content'
        cover_file = SimpleUploadedFile(
            name='test_cover.jpg',
            content=cover_content,
            content_type='image/jpeg'
        )
        
        book = Book.objects.create(
            title="Test Book",
            publisher=publisher,
            cover=cover_file
        )
        book.authors.add(author)
        
        # Check that the cover path starts with 'covers/'
        self.assertTrue(book.cover.name.startswith('covers/'))
    
    def test_author_photo_path(self):
        """Test that author photos are saved to the correct path."""
        # Create a simple uploaded file for the photo
        photo_content = b'test photo image content'
        photo_file = SimpleUploadedFile(
            name='test_photo.jpg',
            content=photo_content,
            content_type='image/jpeg'
        )
        
        author = Author.objects.create(
            name="Test Author",
            photo=photo_file
        )
        
        # Check that the photo path starts with 'authors/'
        self.assertTrue(author.photo.name.startswith('authors/'))
    
    def test_publisher_logo_path(self):
        """Test that publisher logos are saved to the correct path."""
        # Create a simple uploaded file for the logo
        logo_content = b'test logo image content'
        logo_file = SimpleUploadedFile(
            name='test_logo.jpg',
            content=logo_content,
            content_type='image/jpeg'
        )
        
        publisher = Publisher.objects.create(
            name="Test Publisher",
            logo=logo_file
        )
        
        # Check that the logo path starts with 'publishers/'
        self.assertTrue(publisher.logo.name.startswith('publishers/'))

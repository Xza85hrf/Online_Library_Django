"""
Tests for user profile image generation functionality.
Tests the automatic generation of profile pictures for users.
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

from accounts.models import CustomUser, UserProfile

class UserProfileImageTests(TestCase):
    """Tests for user profile image generation."""
    
    def setUp(self):
        """Set up test data and temporary media directory."""
        # Create a temporary directory for media files
        self.temp_media_dir = tempfile.mkdtemp()
        self.old_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self.temp_media_dir
        
        # Create directories for images
        os.makedirs(os.path.join(self.temp_media_dir, 'profile_pics'), exist_ok=True)
    
    def tearDown(self):
        """Clean up temporary media directory."""
        settings.MEDIA_ROOT = self.old_media_root
        shutil.rmtree(self.temp_media_dir)
    
    @patch('accounts.models.generate_profile_image', return_value=True)
    def test_profile_image_generation_on_user_creation(self, mock_generate):
        """Test that a profile image is generated when a new user is created."""
        # Create a test user
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='password123'
        )
        
        # Check that the profile was created
        self.assertTrue(hasattr(user, 'profile'))
        
        # Check that generate_profile_image was called
        mock_generate.assert_called_once()
        
        # Check that the user email was used in the function call
        args, kwargs = mock_generate.call_args
        self.assertEqual(args[0], user)
    
    def test_profile_image_path(self):
        """Test that profile images are saved to the correct path."""
        # Create a simple uploaded file for the profile image
        image_content = b'test profile image content'
        image_file = SimpleUploadedFile(
            name='test_profile.jpg',
            content=image_content,
            content_type='image/jpeg'
        )
        
        # Create a user
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='password123'
        )
        
        # Update the profile with an image
        profile = user.profile
        profile.profile_image = image_file
        profile.save()
        
        # Check that the profile image path starts with 'profile_pics/'
        self.assertTrue(profile.profile_image.name.startswith('profile_pics/'))

class UserProfileUIImageTests(TestCase):
    """Tests for UI-related image generation."""
    
    def setUp(self):
        """Set up test data."""
        # Create a temporary directory for media files
        self.temp_media_dir = tempfile.mkdtemp()
        self.old_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self.temp_media_dir
        
        # Create directories for images
        os.makedirs(os.path.join(self.temp_media_dir, 'ui_images'), exist_ok=True)
    
    def tearDown(self):
        """Clean up temporary media directory."""
        settings.MEDIA_ROOT = self.old_media_root
        shutil.rmtree(self.temp_media_dir)
    
    @patch('library.ui_images.generate_ui_image')
    def test_ui_image_generation(self, mock_generate):
        """Test generation of UI images for the library."""
        # Mock successful image generation
        mock_generate.return_value = True
        
        # Import the function that generates UI images
        from library.ui_images import generate_library_ui_images
        
        # Call the function to generate UI images
        result = generate_library_ui_images()
        
        # Check that the function was called for each required UI image
        expected_calls = [
            'library-hero',
            'book-reading',
            'book-borrowing',
            'library-community',
            'digital-library'
        ]
        
        # Check that generate_ui_image was called the expected number of times
        self.assertEqual(mock_generate.call_count, len(expected_calls))
        
        # Check that each expected image was generated
        for call_args, image_name in zip(mock_generate.call_args_list, expected_calls):
            args, kwargs = call_args
            self.assertIn(image_name, args[0])  # Check that the image name is in the prompt
            self.assertIn('ui_images', args[1])  # Check that the output path is in the ui_images directory

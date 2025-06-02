"""
Custom test runner for the library project.
This helps resolve import issues with test modules.
"""
import os
import sys
from django.test.runner import DiscoverRunner


class LibraryTestRunner(DiscoverRunner):
    """
    Custom test runner that modifies the Python path to handle test imports correctly.
    """
    def setup_test_environment(self, **kwargs):
        # Add the project root to the Python path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Call the parent setup method
        super().setup_test_environment(**kwargs)
    
    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        """
        Build the test suite with custom handling for test modules.
        """
        if not test_labels:
            test_labels = ['library']
        
        return super().build_suite(test_labels, extra_tests, **kwargs)

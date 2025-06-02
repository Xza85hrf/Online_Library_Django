import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
import re
from pathlib import Path


class Command(BaseCommand):
    help = 'Cleans up template files across the project, removing duplicates and ensuring consistent naming'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Create backups of files before removing them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        create_backup = options['backup']
        
        # Define the templates directory
        templates_dir = Path(settings.BASE_DIR) / 'templates'
        backup_dir = templates_dir / 'backup'
        
        # Create backup directory if needed
        if create_backup and not dry_run:
            backup_dir.mkdir(exist_ok=True)
            self.stdout.write(self.style.SUCCESS(f"Created backup directory at {backup_dir}"))
        
        # Define cleanup tasks for different template directories
        cleanup_tasks = [
            self.cleanup_books_templates(templates_dir, backup_dir, dry_run, create_backup),
            self.cleanup_test_templates(templates_dir, backup_dir, dry_run, create_backup),
            self.cleanup_duplicate_templates(templates_dir, backup_dir, dry_run, create_backup)
        ]
        
        # Calculate total removed count
        removed_count = sum(cleanup_tasks)
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run completed. Would remove {removed_count} files."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Cleanup completed. Removed {removed_count} files."))
    
    def cleanup_books_templates(self, templates_dir, backup_dir, dry_run, create_backup):
        """Clean up templates in the books directory"""
        books_dir = templates_dir / 'books'
        books_backup_dir = backup_dir / 'books'
        removed_count = 0
        
        # Create backup directory if needed
        if create_backup and not dry_run:
            books_backup_dir.mkdir(exist_ok=True)
        
        # Files to keep (essential templates)
        essential_files = [
            'book_list.html',
            'book_detail.html',
            'book_detail_main.html',
            'book_detail_tabs.html',
            'author_list.html',
            'author_detail.html',
            'publisher_list.html',
            'publisher_detail.html',
            'my_loans.html',
            'my_reservations.html',
            'review_form.html',
            'review_confirm_delete.html',
            'reviews_section.html',
        ]
        
        # Files to remove (duplicates, unused files, or files with inconsistent naming)
        files_to_remove = [
            'author_list.html.new',
            'book_detail_fixed.html',
            'book_detail_tabs_fixed.html',
            'book_detail_tabs_new.html',
            'publisher_list.html.new',
            'book_detail_actions.html',
        ]
        
        # Check if any essential files are missing
        for file in essential_files:
            file_path = books_dir / file
            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f"Essential file {file} is missing!"))
        
        # Process files to remove
        for file in files_to_remove:
            file_path = books_dir / file
            if file_path.exists():
                if create_backup and not dry_run:
                    backup_path = books_backup_dir / file
                    shutil.copy2(file_path, backup_path)
                    self.stdout.write(f"Backed up {file} to {books_backup_dir}")
                
                if dry_run:
                    self.stdout.write(f"Would remove: {file}")
                else:
                    file_path.unlink()
                    self.stdout.write(f"Removed: {file}")
                removed_count += 1
        
        # Check for any other potential duplicates or inconsistent naming
        pattern = re.compile(r'(.+)\.html\.(new|old|bak|fixed)$')
        
        for file in books_dir.iterdir():
            if not file.is_file():
                continue
                
            match = pattern.match(file.name)
            if match and file.name not in files_to_remove:
                if dry_run:
                    self.stdout.write(f"Would remove additional file with inconsistent naming: {file.name}")
                else:
                    if create_backup:
                        backup_path = books_backup_dir / file.name
                        shutil.copy2(file, backup_path)
                        self.stdout.write(f"Backed up {file.name} to {books_backup_dir}")
                    
                    file.unlink()
                    self.stdout.write(f"Removed additional file with inconsistent naming: {file.name}")
                    removed_count += 1
                    
        return removed_count
    
    def cleanup_test_templates(self, templates_dir, backup_dir, dry_run, create_backup):
        """Clean up test templates that should be in the books directory"""
        removed_count = 0
        test_images_path = templates_dir / 'test_images.html'
        
        # Check if test_images.html exists in the root templates directory
        if test_images_path.exists():
            # The view is looking for this file in books/ directory
            books_test_images_path = templates_dir / 'books' / 'test_images.html'
            
            if dry_run:
                self.stdout.write(f"Would move: test_images.html from templates/ to templates/books/")
            else:
                if create_backup:
                    backup_path = backup_dir / 'test_images.html'
                    shutil.copy2(test_images_path, backup_path)
                    self.stdout.write(f"Backed up test_images.html to {backup_dir}")
                
                # Create the file in the books directory if it doesn't exist
                if not books_test_images_path.exists():
                    shutil.copy2(test_images_path, books_test_images_path)
                    self.stdout.write(f"Copied test_images.html to templates/books/")
                
                # Remove the original file
                test_images_path.unlink()
                self.stdout.write(f"Removed test_images.html from templates/ root")
                removed_count += 1
                
        return removed_count
    
    def cleanup_duplicate_templates(self, templates_dir, backup_dir, dry_run, create_backup):
        """Find and clean up duplicate templates across all template directories"""
        removed_count = 0
        pattern = re.compile(r'(.+)\.(new|old|bak|fixed)$')
        
        # Recursively search for duplicate templates
        for root, dirs, files in os.walk(templates_dir):
            root_path = Path(root)
            
            # Skip the backup directory
            if 'backup' in root_path.parts or 'books_backup' in root_path.parts:
                continue
                
            for file in files:
                match = pattern.match(file)
                if match:
                    file_path = root_path / file
                    relative_path = file_path.relative_to(templates_dir)
                    
                    if dry_run:
                        self.stdout.write(f"Would remove duplicate template: {relative_path}")
                    else:
                        if create_backup:
                            # Create necessary backup directories
                            backup_file_dir = backup_dir / relative_path.parent
                            backup_file_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Backup the file
                            backup_file_path = backup_dir / relative_path
                            shutil.copy2(file_path, backup_file_path)
                            self.stdout.write(f"Backed up {relative_path} to {backup_file_path}")
                        
                        # Remove the duplicate file
                        file_path.unlink()
                        self.stdout.write(f"Removed duplicate template: {relative_path}")
                        removed_count += 1
        
        return removed_count
        


import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Fix mangled data imported from Kaggle dataset (titles only, no image generation)'

    def handle(self, *args, **options):
        self.fix_book_titles()
        self.fix_author_names()
        self.fix_publisher_names()
    
    def is_csv_data(self, text):
        """Check if text looks like CSV data with multiple fields"""
        if not text:
            return False
        # Look for patterns like: field1;"field2";field3
        return ';' in text and '"' in text and text.count(';') >= 2
    
    def extract_first_field(self, text):
        """Extract the first field from CSV-like data"""
        if not text or not self.is_csv_data(text):
            return text
            
        # Try to extract the first field before the first semicolon
        parts = text.split(';', 1)
        if len(parts) > 0:
            # Remove quotes if present
            first_part = parts[0].strip('"\'')
            # If it's an ISBN or numeric ID, try the second field
            if first_part.isdigit() or (len(first_part) == 10 and first_part.replace('-', '').isdigit()):
                if len(parts) > 1:
                    second_parts = parts[1].split(';', 1)
                    if len(second_parts) > 0:
                        return second_parts[0].strip('"\'')
            return first_part
            
        return text
    
    def fix_book_titles(self):
        """Fix mangled book titles from Kaggle import"""
        self.stdout.write('Checking for mangled book titles...')
        
        fixed_count = 0
        with transaction.atomic():
            for book in Book.objects.all():
                if self.is_csv_data(book.title):
                    old_title = book.title
                    new_title = self.extract_first_field(old_title)
                    
                    self.stdout.write(f'  Found mangled title: {old_title[:50]}...')
                    self.stdout.write(f'  Will fix to: {new_title}')
                    
                    book.title = new_title
                    book.save(update_fields=['title'])
                    fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} book titles'))
        else:
            self.stdout.write('No mangled book titles found')
    
    def fix_author_names(self):
        """Fix mangled author names from Kaggle import"""
        self.stdout.write('Checking for mangled author names...')
        
        fixed_count = 0
        with transaction.atomic():
            for author in Author.objects.all():
                if self.is_csv_data(author.name):
                    old_name = author.name
                    new_name = self.extract_first_field(old_name)
                    
                    self.stdout.write(f'  Found mangled author name: {old_name[:50]}...')
                    self.stdout.write(f'  Will fix to: {new_name}')
                    
                    author.name = new_name
                    author.save(update_fields=['name'])
                    fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} author names'))
        else:
            self.stdout.write('No mangled author names found')
    
    def fix_publisher_names(self):
        """Fix mangled publisher names from Kaggle import"""
        self.stdout.write('Checking for mangled publisher names...')
        
        fixed_count = 0
        with transaction.atomic():
            for publisher in Publisher.objects.all():
                if self.is_csv_data(publisher.name):
                    old_name = publisher.name
                    new_name = self.extract_first_field(old_name)
                    
                    self.stdout.write(f'  Found mangled publisher name: {old_name[:50]}...')
                    self.stdout.write(f'  Will fix to: {new_name}')
                    
                    publisher.name = new_name
                    publisher.save(update_fields=['name'])
                    fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} publisher names'))
        else:
            self.stdout.write('No mangled publisher names found')

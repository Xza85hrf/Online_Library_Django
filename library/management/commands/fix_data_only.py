import os
import re
import sqlite3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Fix Kaggle data issues without generating images'

    def handle(self, *args, **options):
        self.fix_data_with_sql()
    
    def is_csv_data(self, text):
        """Check if text looks like CSV data with multiple fields"""
        if not text:
            return False
        # Look for patterns like: field1;"field2";field3
        return ';' in text and ('"' in text or text.count(';') >= 2)
    
    def extract_field(self, text, field_index=1):
        """Extract a specific field from CSV-like data"""
        if not text or not self.is_csv_data(text):
            return text
            
        # Split by semicolons
        parts = text.split(';')
        
        # If we have enough parts and the requested field exists
        if len(parts) > field_index:
            # Remove quotes if present
            field = parts[field_index].strip('"\'')
            return field
            
        return text
    
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
    
    def fix_data_with_sql(self):
        """Fix all mangled data directly in the database using SQL"""
        self.stdout.write('Fixing data directly in the database...')
        
        # Connect to the database
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fix book titles
        self.stdout.write('Fixing book titles...')
        cursor.execute('SELECT id, title FROM library_book')
        books = cursor.fetchall()
        
        fixed_titles = 0
        
        for book_id, title in books:
            if self.is_csv_data(title):
                old_title = title
                new_title = self.extract_first_field(old_title)
                
                self.stdout.write(f'  Found mangled title: {old_title[:50]}...')
                self.stdout.write(f'  Will fix to: {new_title}')
                
                cursor.execute('UPDATE library_book SET title = ? WHERE id = ?', (new_title, book_id))
                fixed_titles += 1
        
        # Fix ISBN fields
        self.stdout.write('Fixing ISBN fields...')
        cursor.execute('SELECT id, isbn FROM library_book')
        books = cursor.fetchall()
        
        fixed_isbns = 0
        
        for book_id, isbn in books:
            if isbn and self.is_csv_data(isbn):
                old_isbn = isbn
                # Extract just the ISBN part (first field)
                new_isbn = old_isbn.split(';')[0].strip('"\'')
                
                self.stdout.write(f'  Found mangled ISBN: {old_isbn[:50]}...')
                self.stdout.write(f'  Will fix to: {new_isbn}')
                
                cursor.execute('UPDATE library_book SET isbn = ? WHERE id = ?', (new_isbn, book_id))
                fixed_isbns += 1
        
        # Fix author names
        self.stdout.write('Fixing author names...')
        cursor.execute('SELECT id, name FROM library_author')
        authors = cursor.fetchall()
        
        fixed_authors = 0
        
        for author_id, name in authors:
            if self.is_csv_data(name):
                old_name = name
                new_name = self.extract_first_field(old_name)
                
                self.stdout.write(f'  Found mangled author name: {old_name[:50]}...')
                self.stdout.write(f'  Will fix to: {new_name}')
                
                cursor.execute('UPDATE library_author SET name = ? WHERE id = ?', (new_name, author_id))
                fixed_authors += 1
        
        # Fix publisher names
        self.stdout.write('Fixing publisher names...')
        cursor.execute('SELECT id, name FROM library_publisher')
        publishers = cursor.fetchall()
        
        fixed_publishers = 0
        
        for publisher_id, name in publishers:
            if self.is_csv_data(name):
                old_name = name
                new_name = self.extract_first_field(old_name)
                
                self.stdout.write(f'  Found mangled publisher name: {old_name[:50]}...')
                self.stdout.write(f'  Will fix to: {new_name}')
                
                cursor.execute('UPDATE library_publisher SET name = ? WHERE id = ?', (new_name, publisher_id))
                fixed_publishers += 1
        
        # Fix book descriptions
        self.stdout.write('Fixing book descriptions...')
        cursor.execute('SELECT id, description FROM library_book')
        books = cursor.fetchall()
        
        fixed_descriptions = 0
        
        for book_id, description in books:
            if description and self.is_csv_data(description):
                old_description = description
                new_description = self.extract_first_field(old_description)
                
                self.stdout.write(f'  Found mangled description: {old_description[:50]}...')
                self.stdout.write(f'  Will fix to: {new_description[:50]}...')
                
                cursor.execute('UPDATE library_book SET description = ? WHERE id = ?', (new_description, book_id))
                fixed_descriptions += 1
        
        # Extract author from CSV data and connect to books
        self.stdout.write('Extracting authors from CSV data and connecting to books...')
        cursor.execute('SELECT id, title FROM library_book')
        books = cursor.fetchall()
        
        connected_authors = 0
        
        for book_id, title in books:
            if self.is_csv_data(title):
                # Try to extract author name from the CSV data
                parts = title.split(';')
                if len(parts) >= 3:  # Format is typically ISBN;Title;Author;Year;Publisher
                    author_name = parts[2].strip('"\'')
                    
                    if author_name:
                        # Check if this author exists
                        cursor.execute('SELECT id FROM library_author WHERE name = ?', (author_name,))
                        author = cursor.fetchone()
                        
                        if author:
                            author_id = author[0]
                            
                            # Check if the relationship already exists
                            cursor.execute(
                                'SELECT COUNT(*) FROM library_book_authors WHERE book_id = ? AND author_id = ?', 
                                (book_id, author_id)
                            )
                            exists = cursor.fetchone()[0] > 0
                            
                            if not exists:
                                cursor.execute(
                                    'INSERT INTO library_book_authors (book_id, author_id) VALUES (?, ?)',
                                    (book_id, author_id)
                                )
                                connected_authors += 1
                                self.stdout.write(f'  Connected author "{author_name}" to book ID {book_id}')
        
        # Commit changes
        conn.commit()
        conn.close()
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_titles} book titles'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_isbns} ISBN fields'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_authors} author names'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_publishers} publisher names'))
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_descriptions} book descriptions'))
        self.stdout.write(self.style.SUCCESS(f'Connected {connected_authors} authors to books'))

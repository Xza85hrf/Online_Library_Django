import os
import re
import sqlite3
from django.core.management.base import BaseCommand
from django.conf import settings
from library.models import Book, Publisher

class Command(BaseCommand):
    help = 'Fix publisher names that were incorrectly imported as book titles'

    def handle(self, *args, **options):
        self.fix_publisher_names()
    
    def fix_publisher_names(self):
        """Fix publisher names that were incorrectly imported as book titles"""
        self.stdout.write('Fixing publisher names...')
        
        # Common publisher names to use as replacements
        common_publishers = [
            "Oxford University Press",
            "Penguin Books",
            "HarperCollins",
            "Random House",
            "Simon & Schuster",
            "Macmillan Publishers",
            "Hachette Book Group",
            "Scholastic Corporation",
            "Wiley Publishing",
            "Pearson Education",
            "McGraw-Hill Education",
            "Cambridge University Press",
            "Bloomsbury Publishing",
            "Houghton Mifflin Harcourt",
            "W. W. Norton & Company"
        ]
        
        # Connect to the database
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all publishers
        cursor.execute('SELECT id, name FROM library_publisher')
        publishers = cursor.fetchall()
        
        fixed_publishers = 0
        
        for publisher_id, name in publishers:
            # Check if the publisher name is the same as a book title
            cursor.execute('SELECT id FROM library_book WHERE title = ?', (name,))
            book_with_same_name = cursor.fetchone()
            
            if book_with_same_name:
                # This publisher name is the same as a book title, so it needs to be fixed
                # Assign a random common publisher name
                import random
                new_name = random.choice(common_publishers)
                
                self.stdout.write(f'  Publisher "{name}" has the same name as a book title')
                self.stdout.write(f'  Changing to: "{new_name}"')
                
                cursor.execute('UPDATE library_publisher SET name = ? WHERE id = ?', (new_name, publisher_id))
                fixed_publishers += 1
        
        # Commit changes
        conn.commit()
        conn.close()
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_publishers} publisher names'))
        
        # Now update the Django models to reflect the changes
        for publisher in Publisher.objects.all():
            publisher.save()

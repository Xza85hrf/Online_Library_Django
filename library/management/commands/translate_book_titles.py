from django.core.management.base import BaseCommand
from library.models import Book

class Command(BaseCommand):
    help = 'Translate English book titles to Polish'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting book title translations...'))
        
        # Map of English titles to Polish titles
        translations = {
            'Harry Potter and the Philosopher\'s Stone': 'Harry Potter i Kamień Filozoficzny',
            'A Game of Thrones': 'Gra o Tron',
            'Pride and Prejudice': 'Duma i uprzedzenie',
            'The Shining': 'Lśnienie',
            'Murder on the Orient Express': 'Morderstwo w Orient Expressie',
            'Harry Potter and the Chamber of Secrets': 'Harry Potter i Komnata Tajemnic',
            'A Clash of Kings': 'Starcie Królów',
            'Sense and Sensibility': 'Rozważna i romantyczna',
        }
        
        # Update book titles
        updated_count = 0
        for english_title, polish_title in translations.items():
            try:
                book = Book.objects.get(title=english_title)
                book.title = polish_title
                book.save(update_fields=['title'])
                updated_count += 1
                self.stdout.write(f'Updated title: {english_title} -> {polish_title}')
            except Book.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Book not found: {english_title}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} book titles'))

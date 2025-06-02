from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from library.models import Author, Publisher, Book
import random
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates sample data for the library app'

    def handle(self, *args, **kwargs):
        # Create authors
        authors = [
            {
                'name': 'J.K. Rowling',
                'bio': 'Joanne Rowling, znana pod pseudonimem J. K. Rowling, jest brytyjską autorką i filantropką. Jest najbardziej znana jako autorka serii fantasy Harry Potter.',
                'birth_date': '1965-07-31',
            },
            {
                'name': 'George R.R. Martin',
                'bio': 'George Raymond Richard Martin, znany również jako GRRM, jest amerykańskim powieściopisarzem, scenarzystą i producentem telewizyjnym. Jest autorem serii epickich powieści fantasy Pieśń Lodu i Ognia.',
                'birth_date': '1948-09-20',
            },
            {
                'name': 'Jane Austen',
                'bio': 'Jane Austen była angielską powieściopisarką znaną głównie z sześciu głównych powieści, które interpretują, krytykują i komentują brytyjską szlachtę ziemską końca XVIII wieku.',
                'birth_date': '1775-12-16',
            },
            {
                'name': 'Stephen King',
                'bio': 'Stephen Edwin King jest amerykańskim autorem powieści grozy, fikcji nadprzyrodzonej, thrillerów, kryminałów, science-fiction i fantasy.',
                'birth_date': '1947-09-21',
            },
            {
                'name': 'Agatha Christie',
                'bio': 'Dame Agatha Mary Clarissa Christie, Lady Mallowan, DBE była angielską pisarką znaną z 66 powieści kryminalnych i 14 zbiorów opowiadań.',
                'birth_date': '1890-09-15',
            },
        ]

        author_objects = []
        for author_data in authors:
            author, created = Author.objects.get_or_create(
                name=author_data['name'],
                defaults={
                    'bio': author_data['bio'],
                    'birth_date': author_data['birth_date'],
                }
            )
            author_objects.append(author)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created author: {author.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Author already exists: {author.name}'))

        # Create publishers
        publishers = [
            {
                'name': 'Bloomsbury Publishing',
                'description': 'Bloomsbury Publishing to wiodące niezależne wydawnictwo założone w 1986 roku.',
                'website': 'https://www.bloomsbury.com',
                'founded_date': '1986-01-01',
            },
            {
                'name': 'Penguin Random House',
                'description': 'Penguin Random House to amerykański międzynarodowy konglomerat wydawniczy utworzony w 2013 roku.',
                'website': 'https://www.penguinrandomhouse.com',
                'founded_date': '2013-07-01',
            },
            {
                'name': 'HarperCollins',
                'description': 'HarperCollins Publishers LLC jest jednym z największych wydawnictw na świecie i należy do pięciu największych anglojęzycznych firm wydawniczych.',
                'website': 'https://www.harpercollins.com',
                'founded_date': '1989-01-01',
            },
        ]

        publisher_objects = []
        for publisher_data in publishers:
            publisher, created = Publisher.objects.get_or_create(
                name=publisher_data['name'],
                defaults={
                    'description': publisher_data['description'],
                    'website': publisher_data['website'],
                    'founded_date': publisher_data['founded_date'],
                }
            )
            publisher_objects.append(publisher)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created publisher: {publisher.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Publisher already exists: {publisher.name}'))

        # Create books
        books = [
            {
                'title': 'Harry Potter and the Philosopher\'s Stone',
                'authors': ['J.K. Rowling'],
                'publisher': 'Bloomsbury Publishing',
                'description': 'Harry Potter, chłopiec, który w swoje jedenaste urodziny dowiaduje się, że jest osieroconym synem dwóch potężnych czarodziejów i posiada wyjątkowe magiczne moce.',
                'publication_date': '1997-06-26',
                'isbn': '9780747532743',
                'pages': 223,
                'language': 'English',
                'genres': ['Fantasy', 'Young Adult'],
                'available_copies': 5,
                'total_copies': 10,
            },
            {
                'title': 'A Game of Thrones',
                'authors': ['George R.R. Martin'],
                'publisher': 'HarperCollins',
                'description': 'Pierwsza powieść z serii Pieśń Lodu i Ognia, cyklu powieści fantasy autorstwa amerykańskiego pisarza George R. R. Martina.',
                'publication_date': '1996-08-01',
                'isbn': '9780553103540',
                'pages': 694,
                'language': 'English',
                'genres': ['Fantasy', 'Epic'],
                'available_copies': 3,
                'total_copies': 7,
            },
            {
                'title': 'Pride and Prejudice',
                'authors': ['Jane Austen'],
                'publisher': 'Penguin Random House',
                'description': 'Duma i uprzedzenie śledzi rozwój postaci Elizabeth Bennet, dynamicznej protagonistki książki, która uczy się o konsekwencjach pochopnych osądów.',
                'publication_date': '1813-01-28',
                'isbn': '9780141439518',
                'pages': 432,
                'language': 'English',
                'genres': ['Classic', 'Romance'],
                'available_copies': 2,
                'total_copies': 5,
            },
            {
                'title': 'The Shining',
                'authors': ['Stephen King'],
                'publisher': 'Penguin Random House',
                'description': 'Lśnienie koncentruje się na życiu Jacka Torrancea, zmagającego się pisarza i wychodzącego z alkoholizmu, który przyjmuje posadę dozorcy poza sezonem w zabytkowym hotelu Overlook.',
                'publication_date': '1977-01-28',
                'isbn': '9780307743657',
                'pages': 447,
                'language': 'English',
                'genres': ['Horror', 'Thriller'],
                'available_copies': 1,
                'total_copies': 3,
            },
            {
                'title': 'Murder on the Orient Express',
                'authors': ['Agatha Christie'],
                'publisher': 'HarperCollins',
                'description': 'Morderstwo w Orient Expressie to powieść kryminalna angielskiej pisarki Agathy Christie z udziałem belgijskiego detektywa Herkulesa Poirot.',
                'publication_date': '1934-01-01',
                'isbn': '9780062693662',
                'pages': 256,
                'language': 'English',
                'genres': ['Mystery', 'Crime'],
                'available_copies': 4,
                'total_copies': 6,
            },
            {
                'title': 'Harry Potter and the Chamber of Secrets',
                'authors': ['J.K. Rowling'],
                'publisher': 'Bloomsbury Publishing',
                'description': 'Druga powieść z serii Harry Potter, napisana przez J.K. Rowling.',
                'publication_date': '1998-07-02',
                'isbn': '9780747538486',
                'pages': 251,
                'language': 'English',
                'genres': ['Fantasy', 'Young Adult'],
                'available_copies': 2,
                'total_copies': 5,
            },
            {
                'title': 'A Clash of Kings',
                'authors': ['George R.R. Martin'],
                'publisher': 'HarperCollins',
                'description': 'Starcie Królów to druga powieść z cyklu Pieśń Lodu i Ognia, epickiej serii fantasy amerykańskiego autora George R. R. Martina.',
                'publication_date': '1998-11-16',
                'isbn': '9780553108033',
                'pages': 761,
                'language': 'English',
                'genres': ['Fantasy', 'Epic'],
                'available_copies': 1,
                'total_copies': 4,
            },
            {
                'title': 'Sense and Sensibility',
                'authors': ['Jane Austen'],
                'publisher': 'Penguin Random House',
                'description': 'Rozważna i romantyczna to powieść Jane Austen, opublikowana w 1811 roku. Została wydana anonimowo; na stronie tytułowej, gdzie mogłoby znajdować się nazwisko autora, widnieje napis "Autorstwa Pewnej Damy".',
                'publication_date': '1811-10-30',
                'isbn': '9780141439662',
                'pages': 409,
                'language': 'English',
                'genres': ['Classic', 'Romance'],
                'available_copies': 3,
                'total_copies': 5,
            },
        ]

        for book_data in books:
            # Get authors
            book_authors = []
            for author_name in book_data['authors']:
                try:
                    author = Author.objects.get(name=author_name)
                    book_authors.append(author)
                except Author.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Author not found: {author_name}'))
                    continue

            # Get publisher
            try:
                publisher = Publisher.objects.get(name=book_data['publisher'])
            except Publisher.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Publisher not found: {book_data["publisher"]}'))
                continue

            # Create or get book
            book, created = Book.objects.get_or_create(
                title=book_data['title'],
                defaults={
                    'publisher': publisher,
                    'description': book_data['description'],
                    'publication_date': book_data['publication_date'],
                    'isbn': book_data['isbn'],
                    'pages': book_data['pages'],
                    'language': book_data['language'],
                    'genres': book_data['genres'],
                    'available_copies': book_data['available_copies'],
                    'total_copies': book_data['total_copies'],
                }
            )

            # Add authors to book
            for author in book_authors:
                book.authors.add(author)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created book: {book.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Book already exists: {book.title}'))

        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))

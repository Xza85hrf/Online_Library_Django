from django.core.management.base import BaseCommand
from library.models import Book, Author, Publisher

class Command(BaseCommand):
    help = 'Update database records with Polish translations'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting translation updates...'))
        
        # Update author biographies
        self.update_author_bios()
        
        # Update book descriptions
        self.update_book_descriptions()
        
        # Update publisher descriptions
        self.update_publisher_descriptions()
        
        self.stdout.write(self.style.SUCCESS('Translation updates completed!'))
    
    def update_author_bios(self):
        """Update author biographies to Polish"""
        translations = {
            'J.K. Rowling': 'Joanne Rowling, znana pod pseudonimem J. K. Rowling, jest brytyjską autorką i filantropką. Jest najbardziej znana jako autorka serii fantasy Harry Potter.',
            'George R.R. Martin': 'George Raymond Richard Martin, znany również jako GRRM, jest amerykańskim powieściopisarzem, scenarzystą i producentem telewizyjnym. Jest autorem serii epickich powieści fantasy Pieśń Lodu i Ognia.',
            'Jane Austen': 'Jane Austen była angielską powieściopisarką znaną głównie z sześciu głównych powieści, które interpretują, krytykują i komentują brytyjską szlachtę ziemską końca XVIII wieku.',
            'Stephen King': 'Stephen Edwin King jest amerykańskim autorem powieści grozy, fikcji nadprzyrodzonej, thrillerów, kryminałów, science-fiction i fantasy.',
            'Agatha Christie': 'Dame Agatha Mary Clarissa Christie, Lady Mallowan, DBE była angielską pisarką znaną z 66 powieści kryminalnych i 14 zbiorów opowiadań.',
        }
        
        updated_count = 0
        for author_name, bio in translations.items():
            try:
                author = Author.objects.get(name=author_name)
                author.bio = bio
                author.save(update_fields=['bio'])
                updated_count += 1
                self.stdout.write(f'Updated biography for author: {author.name}')
            except Author.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Author not found: {author_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} author biographies'))
    
    def update_book_descriptions(self):
        """Update book descriptions to Polish"""
        translations = {
            'Harry Potter and the Philosopher\'s Stone': 'Harry Potter, chłopiec, który w swoje jedenaste urodziny dowiaduje się, że jest osieroconym synem dwóch potężnych czarodziejów i posiada wyjątkowe magiczne moce.',
            'A Game of Thrones': 'Pierwsza powieść z serii Pieśń Lodu i Ognia, cyklu powieści fantasy autorstwa amerykańskiego pisarza George R. R. Martina.',
            'Pride and Prejudice': 'Duma i uprzedzenie śledzi rozwój postaci Elizabeth Bennet, dynamicznej protagonistki książki, która uczy się o konsekwencjach pochopnych osądów.',
            'The Shining': 'Lśnienie koncentruje się na życiu Jacka Torrancea, zmagającego się pisarza i wychodzącego z alkoholizmu, który przyjmuje posadę dozorcy poza sezonem w zabytkowym hotelu Overlook.',
            'Murder on the Orient Express': 'Morderstwo w Orient Expressie to powieść kryminalna angielskiej pisarki Agathy Christie z udziałem belgijskiego detektywa Herkulesa Poirot.',
            'Harry Potter and the Chamber of Secrets': 'Druga powieść z serii Harry Potter, napisana przez J.K. Rowling.',
            'A Clash of Kings': 'Starcie Królów to druga powieść z cyklu Pieśń Lodu i Ognia, epickiej serii fantasy amerykańskiego autora George R. R. Martina.',
            'Sense and Sensibility': 'Rozważna i romantyczna to powieść Jane Austen, opublikowana w 1811 roku. Została wydana anonimowo; na stronie tytułowej, gdzie mogłoby znajdować się nazwisko autora, widnieje napis "Autorstwa Pewnej Damy".',
        }
        
        updated_count = 0
        for book_title, description in translations.items():
            try:
                book = Book.objects.get(title=book_title)
                book.description = description
                book.save(update_fields=['description'])
                updated_count += 1
                self.stdout.write(f'Updated description for book: {book.title}')
            except Book.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Book not found: {book_title}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} book descriptions'))
    
    def update_publisher_descriptions(self):
        """Update publisher descriptions to Polish"""
        translations = {
            'Bloomsbury Publishing': 'Bloomsbury Publishing to wiodące niezależne wydawnictwo założone w 1986 roku.',
            'Penguin Random House': 'Penguin Random House to amerykański międzynarodowy konglomerat wydawniczy utworzony w 2013 roku.',
            'HarperCollins': 'HarperCollins Publishers LLC jest jednym z największych wydawnictw na świecie i należy do pięciu największych anglojęzycznych firm wydawniczych.',
        }
        
        updated_count = 0
        for publisher_name, description in translations.items():
            try:
                publisher = Publisher.objects.get(name=publisher_name)
                publisher.description = description
                publisher.save(update_fields=['description'])
                updated_count += 1
                self.stdout.write(f'Updated description for publisher: {publisher.name}')
            except Publisher.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Publisher not found: {publisher_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} publisher descriptions'))

import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from library.models import Book, Review
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Generate random reviews for books in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-reviews',
            type=int,
            default=3,
            help='Minimum number of reviews per book'
        )
        parser.add_argument(
            '--max-reviews',
            type=int,
            default=10,
            help='Maximum number of reviews per book'
        )
        parser.add_argument(
            '--book-limit',
            type=int,
            default=0,
            help='Limit the number of books to generate reviews for (0 = all books)'
        )

    def handle(self, *args, **options):
        min_reviews = options['min_reviews']
        max_reviews = options['max_reviews']
        book_limit = options['book_limit']
        
        # Get all books
        books = Book.objects.all()
        if book_limit > 0:
            books = books[:book_limit]
        
        # Get all users or create a test user if none exist
        users = list(CustomUser.objects.all())
        if not users:
            self.stdout.write('No users found. Creating a test user...')
            user = CustomUser.objects.create_user(
                username='reviewer',
                email='reviewer@example.com',
                password='reviewpass123'
            )
            users = [user]
        
        # Review titles and content templates
        review_titles = [
            "Świetna książka!", "Warto przeczytać", "Polecam", "Niesamowita lektura",
            "Rozczarowanie", "Nie polecam", "Przeciętna", "Mogło być lepiej",
            "Fascynująca historia", "Wciągająca fabuła", "Ciekawa pozycja", "Nudna lektura",
            "Zaskakujące zakończenie", "Rewelacyjna", "Słaba", "Mieszane uczucia"
        ]
        
        positive_content_templates = [
            "Świetna książka! {title} to jedna z najlepszych pozycji, jakie czytałem/am w ostatnim czasie.",
            "Polecam {title}. Autor świetnie przedstawił historię, która wciąga od pierwszej strony.",
            "Książka {title} to prawdziwa perełka w swoim gatunku. Nie mogłem/am się oderwać.",
            "Fantastyczna lektura! {title} to książka, do której na pewno wrócę.",
            "Bardzo dobrze napisana książka. {title} to pozycja obowiązkowa dla miłośników gatunku."
        ]
        
        neutral_content_templates = [
            "Książka {title} jest całkiem niezła, choć spodziewałem/am się czegoś więcej.",
            "{title} to przeciętna lektura. Ma swoje mocne strony, ale również sporo niedociągnięć.",
            "Mieszane uczucia po przeczytaniu {title}. Niektóre wątki były interesujące, inne mniej.",
            "Książka {title} jest OK, ale nie powala. Można przeczytać, ale bez większych oczekiwań.",
            "Średnia książka. {title} ma potencjał, ale nie został on w pełni wykorzystany."
        ]
        
        negative_content_templates = [
            "Niestety, {title} to rozczarowanie. Nie polecam tej książki.",
            "Słaba książka. {title} nie spełniła moich oczekiwań pod żadnym względem.",
            "Zmarnowany czas na czytanie {title}. Fabuła jest przewidywalna i nudna.",
            "Nie polecam książki {title}. Autor nie poradził sobie z tematem.",
            "Bardzo słaba pozycja. {title} to książka, do której na pewno nie wrócę."
        ]
        
        reviews_created = 0
        
        with transaction.atomic():
            for book in books:
                # Determine number of reviews for this book
                num_reviews = random.randint(min_reviews, max_reviews)
                
                # Get existing reviews for this book to avoid duplicates
                existing_user_reviews = set(Review.objects.filter(book=book).values_list('user_id', flat=True))
                
                # Create reviews
                for _ in range(num_reviews):
                    # Select a random user who hasn't reviewed this book yet
                    available_users = [user for user in users if user.id not in existing_user_reviews]
                    if not available_users:
                        self.stdout.write(f'No more available users for book: {book.title}')
                        break
                    
                    user = random.choice(available_users)
                    existing_user_reviews.add(user.id)
                    
                    # Generate rating and appropriate content
                    rating = random.randint(1, 5)
                    title = random.choice(review_titles)
                    
                    if rating >= 4:
                        content = random.choice(positive_content_templates).format(title=book.title)
                    elif rating >= 3:
                        content = random.choice(neutral_content_templates).format(title=book.title)
                    else:
                        content = random.choice(negative_content_templates).format(title=book.title)
                    
                    # Create the review
                    review = Review.objects.create(
                        book=book,
                        user=user,
                        rating=rating,
                        title=title,
                        content=content,
                        created_at=timezone.now() - timezone.timedelta(days=random.randint(1, 365)),
                        status='approved'  # Auto-approve for demo purposes
                    )
                    
                    reviews_created += 1
                    
                self.stdout.write(f'Created {num_reviews} reviews for book: {book.title}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {reviews_created} reviews for {books.count()} books'))

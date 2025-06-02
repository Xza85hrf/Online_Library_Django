from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Avg, Sum
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseForbidden
from datetime import timedelta
from decimal import Decimal
from .models import Book, Author, Publisher, BookLoan, BookReservation, Review, LateFee, LibrarySettings
from .forms import ReviewForm, BookForm, AuthorForm, PublisherForm

def home(request):
    featured_books = Book.objects.all().order_by('-id')[:6]  # Get the latest books
    
    # Explicitly select author fields and prefetch related books for better performance
    popular_authors = Author.objects.all().prefetch_related('books')[:4]
    
    # Print author names to debug
    print("Popular authors:", [author.name for author in popular_authors])
    
    context = {
        'featured_books': featured_books,
        'popular_authors': popular_authors,
        'title': 'Online Library - Home',
    }
    return render(request, 'home.html', context)

def book_list(request):
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    genre = request.GET.get('genre', '')
    author_id = request.GET.get('author', '')
    publisher_id = request.GET.get('publisher', '')
    availability = request.GET.get('availability', '')
    language = request.GET.get('language', '')
    sort = request.GET.get('sort', '')
    
    # Start with all books
    books = Book.objects.all()
    
    # Apply filters if provided
    if query:
        books = books.filter(
            Q(title__icontains=query) | 
            Q(authors__name__icontains=query) | 
            Q(isbn__icontains=query)
        ).distinct()
    
    # Handle genre filtering differently since JSONField contains lookup isn't supported in SQLite
    if genre:
        # Filter books that have the genre in their genres field
        # This is a workaround since we can't use the contains lookup
        filtered_books = []
        for book in books:
            if book.genres:
                # Check if genres is a list or a string
                if isinstance(book.genres, list) and genre in book.genres:
                    filtered_books.append(book.id)
                # If genres is a string, check if it contains the genre
                elif isinstance(book.genres, str) and genre in book.genres.split(','):
                    filtered_books.append(book.id)
                # If genres is a dict, check if genre is a key
                elif isinstance(book.genres, dict) and genre in book.genres:
                    filtered_books.append(book.id)
        books = books.filter(id__in=filtered_books)
    
    if author_id:
        books = books.filter(authors__id=author_id)
    
    if publisher_id:
        books = books.filter(publisher__id=publisher_id)
    
    if language:
        books = books.filter(language__iexact=language)
    
    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'unavailable':
        books = books.filter(available_copies=0)
    
    # Define genre translations for Polish
    genre_translations = {
        'fiction': 'Fikcja',
        'nonfiction': 'Literatura faktu',
        'scifi': 'Science Fiction',
        'mystery': 'Kryminał',
        'biography': 'Biografia',
        'fantasy': 'Fantastyka',
        'romance': 'Romans',
        'thriller': 'Thriller',
        'horror': 'Horror',
        'history': 'Historia',
        'poetry': 'Poezja',
        'drama': 'Dramat',
        'comedy': 'Komedia',
        'adventure': 'Przygodowa',
        'children': 'Dla dzieci',
        'young_adult': 'Młodzieżowa',
        'science': 'Naukowa',
        'travel': 'Podróżnicza',
        'cooking': 'Kulinarna',
        'art': 'Sztuka',
        'music': 'Muzyka',
        'sports': 'Sport',
        'education': 'Edukacja',
        'philosophy': 'Filozofia',
        'psychology': 'Psychologia',
        'religion': 'Religia',
        'politics': 'Polityka',
        'business': 'Biznes',
        'health': 'Zdrowie',
        'self_help': 'Poradniki',
        'comics': 'Komiksy',
        'manga': 'Manga',
        'other': 'Inne'
    }
    
    # Create genre choices for the template
    genre_choices = [(key, value) for key, value in genre_translations.items()]
    
    # Apply sorting
    if sort == 'title_asc':
        books = books.order_by('title')
    elif sort == 'title_desc':
        books = books.order_by('-title')
    elif sort == 'date_asc':
        books = books.order_by('publication_date')
    elif sort == 'date_desc':
        books = books.order_by('-publication_date')
    
    # Use the translated genre choices created earlier
    
    context = {
        'books': books,
        'title': 'Wszystkie książki',
        'query': query,
        'genre': genre,
        'genre_choices': genre_choices,
        'author_id': author_id,
        'publisher_id': publisher_id,
        'availability': availability,
        'language': language,
        'sort': sort,
        'genre_translations': genre_translations,
    }
    return render(request, 'books/book_list.html', context)

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Get approved reviews for this book
    reviews = book.reviews.filter(status='approved').order_by('-created_at')
    
    # Check if the user has already reviewed this book
    user_has_reviewed = False
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(book=book, user=request.user).first()
        user_has_reviewed = user_review is not None
    
    # Create a review form for the user
    review_form = ReviewForm()
    
    context = {
        'book': book,
        'related_books': Book.objects.filter(authors__in=book.authors.all()).exclude(pk=book.pk).distinct()[:4],
        'reviews': reviews,
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
        'user_review': user_review,
    }
    return render(request, 'books/book_detail_main.html', context)

def author_list(request):
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    letter = request.GET.get('letter', '')
    sort_by = request.GET.get('sort', 'name_asc')
    per_page = int(request.GET.get('per_page', 12))
    
    # Start with all authors
    authors = Author.objects.all()
    
    # Apply filters if provided
    if query:
        authors = authors.filter(name__icontains=query)
    
    if letter:
        authors = authors.filter(name__istartswith=letter)
    
    # Apply sorting
    if sort_by == 'name_asc':
        authors = authors.order_by('name')
    elif sort_by == 'name_desc':
        authors = authors.order_by('-name')
    elif sort_by == 'books_asc':
        authors = sorted(authors, key=lambda a: a.books.count())
    elif sort_by == 'books_desc':
        authors = sorted(authors, key=lambda a: -a.books.count())
    
    context = {
        'authors': authors,
        'title': 'All Authors',
        'query': query,
        'current_letter': letter,
        'sort_by': sort_by,
        'per_page': per_page,
    }
    return render(request, 'books/author_list.html', context)

def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    context = {
        'author': author,
        'books': author.books.all(),
        'related_authors': Author.objects.exclude(pk=author.pk)[:4],
    }
    return render(request, 'books/author_detail.html', context)

def publisher_list(request):
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    letter = request.GET.get('letter', '')
    sort_by = request.GET.get('sort', 'name_asc')
    per_page = int(request.GET.get('per_page', 12))
    
    # Start with all publishers
    publishers = Publisher.objects.all()
    
    # Apply filters if provided
    if query:
        publishers = publishers.filter(name__icontains=query)
    
    if letter:
        publishers = publishers.filter(name__istartswith=letter)
    
    # Apply sorting
    if sort_by == 'name_asc':
        publishers = publishers.order_by('name')
    elif sort_by == 'name_desc':
        publishers = publishers.order_by('-name')
    elif sort_by == 'books_asc':
        publishers = sorted(publishers, key=lambda p: p.books.count())
    elif sort_by == 'books_desc':
        publishers = sorted(publishers, key=lambda p: -p.books.count())
    
    # Add some featured publishers for the bottom section
    featured_publishers = Publisher.objects.all().order_by('?')[:4] if publishers.exists() else []
    
    context = {
        'publishers': publishers,
        'title': 'All Publishers',
        'query': query,
        'current_letter': letter,
        'sort_by': sort_by,
        'per_page': per_page,
        'featured_publishers': featured_publishers,
    }
    return render(request, 'books/publisher_list.html', context)


def book_detail(request, pk):
    book = get_object_or_404(Book, id=pk)
    context = {
        'book': book,
        'title': book.title,
    }
    return render(request, 'books/book_detail.html', context)

def publisher_detail(request, pk):
    publisher = get_object_or_404(Publisher, pk=pk)
    context = {
        'publisher': publisher,
        'books': publisher.books.all(),
        'related_publishers': Publisher.objects.exclude(pk=publisher.pk)[:4],
    }
    return render(request, 'books/publisher_detail.html', context)


@login_required
def borrow_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Check if book is available
    if book.available_copies <= 0:
        messages.error(request, f'Przepraszamy, książka "{book.title}" jest obecnie niedostępna.')
        return redirect('library:book_detail', pk=book.pk)
    
    # Check if user already has an active loan for this book
    existing_loan = BookLoan.objects.filter(
        book=book,
        user=request.user,
        status__in=['borrowed', 'overdue']
    ).first()
    
    if existing_loan:
        messages.warning(request, f'Już wypożyczyłeś tę książkę. Termin zwrotu: {existing_loan.due_date}.')
        return redirect('library:book_detail', pk=book.pk)
    
    # Check if user has reached their borrowing limit
    active_loans_count = BookLoan.objects.filter(
        user=request.user,
        status__in=['borrowed', 'overdue']
    ).count()
    
    # Default limit is 5 books, can be customized based on user role
    if active_loans_count >= 5:  # This could be user.profile.book_limit if implemented
        messages.error(request, 'Osiągnąłeś limit wypożyczeń. Zwróć niektóre książki, aby wypożyczyć więcej.')
        return redirect('library:book_detail', pk=book.pk)
    
    # Create new loan
    due_date = timezone.now().date() + timedelta(days=14)  # 2 weeks loan period
    loan = BookLoan.objects.create(
        book=book,
        user=request.user,
        due_date=due_date,
        status='borrowed'
    )
    
    # Update book availability
    book.available_copies -= 1
    book.save()
    
    messages.success(request, f'Pomyślnie wypożyczono "{book.title}". Termin zwrotu: {due_date}.')
    return redirect('library:my_loans')


@login_required
def return_book(request, loan_id):
    loan = get_object_or_404(BookLoan, id=loan_id, user=request.user)
    
    if loan.status in ['returned', 'lost']:
        messages.warning(request, 'Ta książka została już zwrócona lub oznaczona jako zgubiona.')
        return redirect('library:my_loans')
    
    # Update loan status
    loan.status = 'returned'
    loan.return_date = timezone.now().date()
    loan.save()
    
    # Update book availability
    book = loan.book
    book.available_copies += 1
    book.save()
    
    messages.success(request, f'Pomyślnie zwrócono "{book.title}".')
    
    # Check if there are pending reservations for this book
    pending_reservation = BookReservation.objects.filter(
        book=book,
        status='pending'
    ).order_by('reservation_date').first()
    
    if pending_reservation:
        messages.info(request, f'Książka ma oczekującą rezerwację od {pending_reservation.user.username}.')
    
    return redirect('library:my_loans')


@login_required
def reserve_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # Check if user already has an active reservation for this book
    existing_reservation = BookReservation.objects.filter(
        book=book,
        user=request.user,
        status='pending'
    ).first()
    
    if existing_reservation:
        messages.warning(request, f'Już zarezerwowałeś tę książkę. Data wygaśnięcia rezerwacji: {existing_reservation.expiry_date}.')
        return redirect('library:book_detail', pk=book.pk)
    
    # Check if user already has an active loan for this book
    existing_loan = BookLoan.objects.filter(
        book=book,
        user=request.user,
        status__in=['borrowed', 'overdue']
    ).first()
    
    if existing_loan:
        messages.warning(request, f'Już wypożyczyłeś tę książkę. Termin zwrotu: {existing_loan.due_date}.')
        return redirect('library:book_detail', pk=book.pk)
    
    # Create new reservation (valid for 7 days)
    expiry_date = timezone.now().date() + timedelta(days=7)
    reservation = BookReservation.objects.create(
        book=book,
        user=request.user,
        expiry_date=expiry_date,
        status='pending'
    )
    
    messages.success(request, f'Pomyślnie zarezerwowano "{book.title}". Rezerwacja ważna do: {expiry_date}.')
    return redirect('library:my_reservations')


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(BookReservation, id=reservation_id, user=request.user)
    
    if reservation.status != 'pending':
        messages.warning(request, 'Ta rezerwacja została już zrealizowana, anulowana lub wygasła.')
        return redirect('library:my_reservations')
    
    # Update reservation status
    reservation.status = 'cancelled'
    reservation.save()
    
    messages.success(request, f'Pomyślnie anulowano rezerwację książki "{reservation.book.title}".')
    return redirect('library:my_reservations')


@login_required
def my_loans(request):
    # Get active loans
    active_loans = BookLoan.objects.filter(
        user=request.user,
        status__in=['borrowed', 'overdue']
    ).order_by('due_date')
    
    # Get past loans
    past_loans = BookLoan.objects.filter(
        user=request.user,
        status='returned'
    ).order_by('-return_date')
    
    context = {
        'active_loans': active_loans,
        'past_loans': past_loans,
        'title': 'Moje wypożyczenia',
    }
    return render(request, 'books/my_loans.html', context)


@login_required
def my_reservations(request):
    # Get all reservations for the current user
    reservations = BookReservation.objects.filter(user=request.user)
    
    # Filter by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    # Group reservations by status for easier display
    pending_reservations = reservations.filter(status='pending')
    fulfilled_reservations = reservations.filter(status='fulfilled')
    cancelled_reservations = reservations.filter(status='cancelled')
    expired_reservations = reservations.filter(status='expired')
    
    context = {
        'reservations': reservations,
        'pending_reservations': pending_reservations,
        'fulfilled_reservations': fulfilled_reservations,
        'cancelled_reservations': cancelled_reservations,
        'expired_reservations': expired_reservations,
        'status_filter': status_filter,
    }
    return render(request, 'books/my_reservations.html', context)


@login_required
def create_review(request, book_id):
    """Create a new review for a book."""
    book = get_object_or_404(Book, pk=book_id)
    
    # Check if the user has already reviewed this book
    existing_review = Review.objects.filter(book=book, user=request.user).first()
    if existing_review:
        messages.warning(request, _('You have already reviewed this book. You can edit your existing review.'))
        return redirect('library:edit_review', review_id=existing_review.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, user=request.user, book=book)
        if form.is_valid():
            review = form.save()
            messages.success(request, _('Your review has been submitted and is pending approval.'))
            return redirect('library:book_detail', pk=book.id)
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'book': book,
        'title': _('Review') + f' {book.title}',
    }
    return render(request, 'books/review_form.html', context)


@login_required
def edit_review(request, review_id):
    """Edit an existing review."""
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    book = review.book
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            # Reset status to pending for moderation
            review = form.save(commit=False)
            review.status = 'pending'
            review.save()
            messages.success(request, _('Your review has been updated and is pending approval.'))
            return redirect('library:book_detail', pk=book.id)
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'form': form,
        'book': book,
        'review': review,
        'title': _('Edit Review') + f' - {book.title}',
    }
    return render(request, 'books/review_form.html', context)


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    
    # Check if the user is the owner of the review
    if review.user != request.user and not request.user.is_staff:
        messages.error(request, _('You do not have permission to delete this review.'))
        return redirect('library:book_detail', pk=review.book.id)
    
    if request.method == 'POST':
        book_id = review.book.id
        review.delete()
        messages.success(request, _('Your review has been deleted.'))
        return redirect('library:book_detail', pk=book_id)
    
    return render(request, 'books/review_confirm_delete.html', {'review': review})


# Late Fee Management Views

@login_required
def my_late_fees(request):
    """View for users to see their own late fees."""
    # Get all late fees for the user's loans
    late_fees = LateFee.objects.filter(loan__user=request.user).select_related('loan', 'loan__book')
    
    # Calculate total amount due
    total_pending = late_fees.filter(payment_status='pending').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'late_fees': late_fees,
        'total_pending': total_pending,
        'title': 'My Late Fees',
    }
    return render(request, 'fees/my_late_fees.html', context)


@login_required
def pay_late_fee(request, fee_id):
    """View for users to pay a late fee."""
    late_fee = get_object_or_404(LateFee, pk=fee_id)
    
    # Ensure the user owns this late fee
    if late_fee.loan.user != request.user:
        messages.error(request, _('You do not have permission to pay this late fee.'))
        return redirect('library:my_late_fees')
    
    # Ensure the fee is still pending
    if late_fee.payment_status != 'pending':
        messages.warning(request, _('This late fee has already been processed.'))
        return redirect('library:my_late_fees')
    
    if request.method == 'POST':
        # In a real application, this would integrate with a payment gateway
        # For now, we'll just mark it as paid
        late_fee.mark_as_paid()
        messages.success(request, _('Your payment of {:.2f} PLN has been processed successfully.').format(late_fee.amount))
        return redirect('library:my_late_fees')
    
    return render(request, 'fees/pay_late_fee.html', {'late_fee': late_fee})


@login_required
def request_fee_waiver(request, fee_id):
    """View for users to request a waiver for a late fee."""
    late_fee = get_object_or_404(LateFee, pk=fee_id)
    
    # Ensure the user owns this late fee
    if late_fee.loan.user != request.user:
        messages.error(request, _('You do not have permission to request a waiver for this late fee.'))
        return redirect('library:my_late_fees')
    
    # Ensure the fee is still pending
    if late_fee.payment_status != 'pending':
        messages.warning(request, _('This late fee has already been processed.'))
        return redirect('library:my_late_fees')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        if not reason:
            messages.error(request, _('Please provide a reason for your waiver request.'))
            return render(request, 'fees/request_waiver.html', {'late_fee': late_fee})
        
        # Store the waiver request and notify staff (in a real app, this would send an email)
        late_fee.waived_reason = f"WAIVER REQUESTED: {reason}"
        late_fee.save()
        
        messages.success(request, _('Your waiver request has been submitted and is pending review.'))
        return redirect('library:my_late_fees')
    
    return render(request, 'fees/request_waiver.html', {'late_fee': late_fee})


# Staff views for managing late fees

def is_staff(user):
    return user.is_staff


@user_passes_test(is_staff)
def manage_late_fees(request):
    """Admin view to manage all late fees."""
    late_fees = LateFee.objects.all().select_related('loan', 'loan__book', 'loan__user')
    
    # Filter by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter:
        late_fees = late_fees.filter(payment_status=status_filter)
    
    # Calculate totals
    total_pending = late_fees.filter(payment_status='pending').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_paid = late_fees.filter(payment_status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_waived = late_fees.filter(payment_status='waived').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'late_fees': late_fees,
        'total_pending': total_pending,
        'total_paid': total_paid,
        'total_waived': total_waived,
        'status_filter': status_filter,
        'title': 'Manage Late Fees',
    }
    return render(request, 'fees/manage_late_fees.html', context)


@user_passes_test(is_staff)
def process_waiver_request(request, fee_id):
    """Admin view to process a waiver request."""
    late_fee = get_object_or_404(LateFee, pk=fee_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            late_fee.waive_fee(request.user, f"Approved: {late_fee.waived_reason}")
            messages.success(request, _('Waiver request approved for {:.2f} PLN.').format(late_fee.amount))
        elif action == 'reject':
            # Reset the waiver reason and keep the fee pending
            original_reason = late_fee.waived_reason.replace("WAIVER REQUESTED: ", "")
            late_fee.waived_reason = f"REJECTED: {original_reason}"
            late_fee.save()
            messages.warning(request, _('Waiver request rejected for {:.2f} PLN.').format(late_fee.amount))
        
        return redirect('library:manage_late_fees')
    
    return render(request, 'fees/process_waiver.html', {'late_fee': late_fee})


@user_passes_test(is_staff)
def library_settings(request):
    """Admin view to manage library settings."""
    settings = LibrarySettings.get_settings()
    
    if request.method == 'POST':
        # Update settings
        try:
            settings.late_fee_daily_rate = Decimal(request.POST.get('late_fee_daily_rate', '0.50'))
            settings.max_loan_days = int(request.POST.get('max_loan_days', '14'))
            settings.max_renewals = int(request.POST.get('max_renewals', '2'))
            settings.max_books_per_user = int(request.POST.get('max_books_per_user', '5'))
            settings.reservation_expiry_days = int(request.POST.get('reservation_expiry_days', '3'))
            settings.save()
            
            messages.success(request, _('Library settings updated successfully.'))
        except (ValueError, TypeError) as e:
            messages.error(request, _('Error updating settings: {}').format(str(e)))
    
    return render(request, 'library/settings.html', {'settings': settings})


def test_images(request):
    """Test view to check if images are being served correctly."""
    return render(request, 'books/test_images.html')


# Library Information Pages

def about(request):
    """About page with information about the library."""
    return render(request, 'library/about.html', {'title': 'O bibliotece'})

def events(request):
    """Page with information about library events."""
    return render(request, 'library/events.html', {'title': 'Wydarzenia'})

def digital_library(request):
    """Page with information about digital resources."""
    return render(request, 'library/digital_library.html', {'title': 'Biblioteka Cyfrowa'})

def how_to_borrow(request):
    """Page with instructions on how to borrow books."""
    return render(request, 'library/how_to_borrow.html', {'title': 'Jak wypożyczyć'})

def rules(request):
    """Page with library rules and regulations."""
    return render(request, 'library/rules.html', {'title': 'Regulamin'})

def opening_hours(request):
    """Page with library opening hours."""
    return render(request, 'library/opening_hours.html', {'title': 'Godziny otwarcia'})


# Librarian Management Views

def is_librarian_or_admin(user):
    """Check if the user is a librarian or administrator."""
    return user.is_authenticated and hasattr(user, 'profile') and (user.profile.role in ['admin', 'librarian'] or user.is_staff)


@user_passes_test(is_librarian_or_admin)
def librarian_dashboard(request):
    """Dashboard for librarians to manage books, authors, and publishers."""
    recent_books = Book.objects.all().order_by('-id')[:5]
    recent_authors = Author.objects.all().order_by('-id')[:5]
    recent_publishers = Publisher.objects.all().order_by('-id')[:5]
    active_loans = BookLoan.objects.filter(status='borrowed').order_by('-loan_date')[:10]
    pending_reservations = BookReservation.objects.filter(status='pending').order_by('-reservation_date')[:10]
    
    context = {
        'recent_books': recent_books,
        'recent_authors': recent_authors,
        'recent_publishers': recent_publishers,
        'active_loans': active_loans,
        'pending_reservations': pending_reservations,
        'title': 'Panel Bibliotekarza',
    }
    return render(request, 'library/librarian/dashboard.html', context)


# Author management views
@user_passes_test(is_librarian_or_admin)
def author_create(request):
    """View for librarians to add a new author."""
    if request.method == 'POST':
        form = AuthorForm(request.POST, request.FILES)
        if form.is_valid():
            author = form.save()
            messages.success(request, f'Autor "{author.name}" został dodany pomyślnie.')
            return redirect('author_detail', pk=author.pk)
    else:
        form = AuthorForm()
    
    return render(request, 'library/librarian/author_form.html', {
        'form': form,
        'title': 'Dodaj nowego autora',
    })


@user_passes_test(is_librarian_or_admin)
def author_update(request, pk):
    """View for librarians to edit an existing author."""
    author = get_object_or_404(Author, pk=pk)
    
    if request.method == 'POST':
        form = AuthorForm(request.POST, request.FILES, instance=author)
        if form.is_valid():
            author = form.save()
            messages.success(request, f'Autor "{author.name}" został zaktualizowany pomyślnie.')
            return redirect('author_detail', pk=author.pk)
    else:
        form = AuthorForm(instance=author)
    
    return render(request, 'library/librarian/author_form.html', {
        'form': form,
        'author': author,
        'title': f'Edytuj autora: {author.name}',
    })


@user_passes_test(is_librarian_or_admin)
def author_delete(request, pk):
    """View for librarians to delete an author."""
    author = get_object_or_404(Author, pk=pk)
    
    if request.method == 'POST':
        name = author.name
        author.delete()
        messages.success(request, f'Autor "{name}" został usunięty pomyślnie.')
        return redirect('author_list')
    
    return render(request, 'library/librarian/author_confirm_delete.html', {
        'author': author,
        'title': f'Usuń autora: {author.name}',
    })


# Publisher management views
@user_passes_test(is_librarian_or_admin)
def publisher_create(request):
    """View for librarians to add a new publisher."""
    if request.method == 'POST':
        form = PublisherForm(request.POST, request.FILES)
        if form.is_valid():
            publisher = form.save()
            messages.success(request, f'Wydawnictwo "{publisher.name}" zostało dodane pomyślnie.')
            return redirect('publisher_detail', pk=publisher.pk)
    else:
        form = PublisherForm()
    
    return render(request, 'library/librarian/publisher_form.html', {
        'form': form,
        'title': 'Dodaj nowe wydawnictwo',
    })


@user_passes_test(is_librarian_or_admin)
def publisher_update(request, pk):
    """View for librarians to edit an existing publisher."""
    publisher = get_object_or_404(Publisher, pk=pk)
    
    if request.method == 'POST':
        form = PublisherForm(request.POST, request.FILES, instance=publisher)
        if form.is_valid():
            publisher = form.save()
            messages.success(request, f'Wydawnictwo "{publisher.name}" zostało zaktualizowane pomyślnie.')
            return redirect('publisher_detail', pk=publisher.pk)
    else:
        form = PublisherForm(instance=publisher)
    
    return render(request, 'library/librarian/publisher_form.html', {
        'form': form,
        'publisher': publisher,
        'title': f'Edytuj wydawnictwo: {publisher.name}',
    })


@user_passes_test(is_librarian_or_admin)
def publisher_delete(request, pk):
    """View for librarians to delete a publisher."""
    publisher = get_object_or_404(Publisher, pk=pk)
    
    if request.method == 'POST':
        name = publisher.name
        publisher.delete()
        messages.success(request, f'Wydawnictwo "{name}" zostało usunięte pomyślnie.')
        return redirect('publisher_list')
    
    return render(request, 'library/librarian/publisher_confirm_delete.html', {
        'publisher': publisher,
        'title': f'Usuń wydawnictwo: {publisher.name}',
    })


# Book management views
@user_passes_test(is_librarian_or_admin)
def book_create(request):
    """View for librarians to add a new book."""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Książka "{book.title}" została dodana pomyślnie.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()
    
    return render(request, 'library/librarian/book_form.html', {
        'form': form,
        'title': 'Dodaj nową książkę',
    })


@user_passes_test(is_librarian_or_admin)
def book_update(request, pk):
    """View for librarians to edit an existing book."""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Książka "{book.title}" została zaktualizowana pomyślnie.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    
    return render(request, 'library/librarian/book_form.html', {
        'form': form,
        'book': book,
        'title': f'Edytuj książkę: {book.title}',
    })


@user_passes_test(is_librarian_or_admin)
def book_delete(request, pk):
    """View for librarians to delete a book."""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Książka "{title}" została usunięta pomyślnie.')
        return redirect('book_list')
    
    return render(request, 'library/librarian/book_confirm_delete.html', {
        'book': book,
        'title': f'Usuń książkę: {book.title}',
    })

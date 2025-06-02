from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.utils.text import slugify
from accounts.models import CustomUser

class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='authors/', blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    social_media = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('library:author_detail', args=[str(self.id)])

class Publisher(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='publishers/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    founded_date = models.DateField(blank=True, null=True)
    contact_info = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('library:publisher_detail', args=[str(self.id)])


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = 'Categories'

class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, related_name='books')
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)
    description = models.TextField(blank=True)
    publication_date = models.DateField(blank=True, null=True)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    pages = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    genres = models.JSONField(blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name='books', blank=True)
    available_copies = models.PositiveIntegerField(default=0)
    total_copies = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('library:book_detail', args=[str(self.id)])
    
    @property
    def is_available(self):
        return self.available_copies > 0
    
    @property
    def average_rating(self):
        """Calculate the average rating for approved reviews."""
        approved_reviews = self.reviews.filter(status='approved')
        if not approved_reviews.exists():
            return 0
        total_rating = sum(review.rating for review in approved_reviews)
        return round(total_rating / approved_reviews.count(), 1)
    
    @property
    def review_count(self):
        """Return the count of approved reviews."""
        return self.reviews.filter(status='approved').count()
    
    @property
    def rating_distribution(self):
        """Return the distribution of ratings as a dictionary."""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        approved_reviews = self.reviews.filter(status='approved')
        
        for review in approved_reviews:
            distribution[review.rating] += 1
            
        return distribution

class BookLoan(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='book_loans')
    loan_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='borrowed')
    late_fee_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.book.title} - {self.user.username}"
    
    @property
    def is_overdue(self):
        if self.return_date:
            return self.return_date > self.due_date
        return timezone.now().date() > self.due_date
    
    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        
        if self.return_date:
            return (self.return_date - self.due_date).days
        
        return (timezone.now().date() - self.due_date).days
    
    @property
    def calculated_late_fee(self):
        """Calculate the late fee based on days overdue and daily rate."""
        if not self.is_overdue:
            return Decimal('0.00')
        
        # Get the library settings for late fee rate
        from library.models import LibrarySettings
        settings = LibrarySettings.get_settings()
        daily_rate = settings.late_fee_daily_rate
        
        return Decimal(self.days_overdue) * daily_rate
    
    def save(self, *args, **kwargs):
        # Update status to 'overdue' if past due date and not returned
        if self.is_overdue and not self.return_date and self.status != 'lost':
            self.status = 'overdue'
        
        super().save(*args, **kwargs)
        
        # Create or update late fee record if overdue
        if self.is_overdue and not self.late_fee_paid:
            LateFee.objects.update_or_create(
                loan=self,
                defaults={
                    'amount': self.calculated_late_fee,
                    'days_overdue': self.days_overdue
                }
            )

class BookReservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='book_reservations')
    reservation_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.book.title} - {self.user.username}"


class LibrarySettings(models.Model):
    """Global settings for the library system."""
    late_fee_daily_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.50'),
        help_text=_('Daily late fee rate in PLN')
    )
    max_loan_days = models.PositiveIntegerField(
        default=14,
        help_text=_('Maximum number of days for a book loan')
    )
    max_renewals = models.PositiveIntegerField(
        default=2,
        help_text=_('Maximum number of times a loan can be renewed')
    )
    max_books_per_user = models.PositiveIntegerField(
        default=5,
        help_text=_('Maximum number of books a user can borrow at once')
    )
    reservation_expiry_days = models.PositiveIntegerField(
        default=3,
        help_text=_('Number of days until a reservation expires')
    )
    
    class Meta:
        verbose_name = _('Library Settings')
        verbose_name_plural = _('Library Settings')
    
    @classmethod
    def get_settings(cls):
        """Get the library settings, creating default settings if none exist."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class LateFee(models.Model):
    """Model for tracking late fees for overdue books."""
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('waived', _('Waived')),
    ]
    
    loan = models.OneToOneField(BookLoan, on_delete=models.CASCADE, related_name='late_fee')
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    days_overdue = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(blank=True, null=True)
    waived_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='waived_fees'
    )
    waived_reason = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Late Fee')
        verbose_name_plural = _('Late Fees')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.loan.book.title} - {self.amount} PLN - {self.loan.user.username}"
    
    def mark_as_paid(self):
        """Mark the late fee as paid."""
        self.payment_status = 'paid'
        self.payment_date = timezone.now()
        self.save()
        
        # Update the loan record
        self.loan.late_fee_paid = True
        self.loan.save()
    
    def waive_fee(self, waived_by, reason=''):
        """Waive the late fee."""
        self.payment_status = 'waived'
        self.waived_by = waived_by
        self.waived_reason = reason
        self.save()
        
        # Update the loan record
        self.loan.late_fee_paid = True
        self.loan.save()


class Review(models.Model):
    """Model for book reviews and ratings."""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='book_reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 to 5 stars')
    )
    title = models.CharField(max_length=100, blank=True)
    content = models.TextField(help_text=_('Your review of the book'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        ordering = ['-created_at']
        # Ensure a user can only review a book once
        unique_together = ['book', 'user']
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
    
    def __str__(self):
        return f"{self.book.title} - {self.rating}/5 - {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('library:book_detail', args=[str(self.book.id)]) + '#reviews'
    
    @property
    def is_approved(self):
        return self.status == 'approved'

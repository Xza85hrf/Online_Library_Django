from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model that uses email as the unique identifier."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """Extended user profile model with additional information."""
    ADMIN = 'admin'
    LIBRARIAN = 'librarian'
    READER = 'reader'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (LIBRARIAN, 'Bibliotekarz'),
        (READER, 'Czytelnik'),
    ]
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default=READER,
        verbose_name='Rola'
    )
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name='Numer telefonu'
    )
    address = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Adres'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        verbose_name='Zdjęcie profilowe'
    )
    date_of_birth = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Data urodzenia'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data utworzenia'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Data aktualizacji'
    )
    
    class Meta:
        verbose_name = 'Profil użytkownika'
        verbose_name_plural = 'Profile użytkowników'
    
    @property
    def book_limit(self):
        """Returns the maximum number of books this user can borrow."""
        if self.role == self.ADMIN:
            return 15
        elif self.role == self.LIBRARIAN:
            return 10
        return 5  # Default for READER
    
    def active_borrowings_count(self):
        """Returns the number of active book borrowings."""
        from library.models import BookLoan
        return BookLoan.objects.filter(user=self.user, status='borrowed').count()
    
    def can_borrow_more_books(self):
        """Checks if the user can borrow more books."""
        return self.active_borrowings_count() < self.book_limit
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} ({self.get_role_display()})"


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile whenever a new CustomUser is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile whenever the CustomUser is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()

"""
Forms for the library application.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Review, Book, Author, Publisher


class ReviewForm(forms.ModelForm):
    """Form for creating and editing book reviews."""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'content']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
                attrs={'class': 'rating-input'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Review Title (optional)')
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Write your review here...')
            }),
        }
        help_texts = {
            'rating': _('Rate this book from 1 to 5 stars'),
            'title': _('Give your review a title (optional)'),
            'content': _('Share your thoughts about this book'),
        }
        labels = {
            'rating': _('Your Rating'),
            'title': _('Review Title'),
            'content': _('Your Review'),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.book = kwargs.pop('book', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        review = super().save(commit=False)
        if self.user:
            review.user = self.user
        if self.book:
            review.book = self.book
        
        if commit:
            review.save()
        
        return review


class AuthorForm(forms.ModelForm):
    """Form for creating and editing authors."""
    
    class Meta:
        model = Author
        fields = ['name', 'bio', 'photo', 'birth_date', 'website', 'social_media']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'social_media': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        help_texts = {
            'social_media': _('Enter social media links in JSON format, e.g., {"twitter": "https://twitter.com/username"}'),
        }


class PublisherForm(forms.ModelForm):
    """Form for creating and editing publishers."""
    
    class Meta:
        model = Publisher
        fields = ['name', 'description', 'logo', 'website', 'founded_date', 'contact_info']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'founded_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contact_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        help_texts = {
            'contact_info': _('Enter contact information in JSON format, e.g., {"email": "info@publisher.com", "phone": "+1234567890"}'),
        }


class BookForm(forms.ModelForm):
    """Form for creating and editing books."""
    
    class Meta:
        model = Book
        fields = ['title', 'authors', 'publisher', 'cover', 'description', 'publication_date', 
                 'isbn', 'pages', 'language', 'genres', 'available_copies', 'total_copies']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'authors': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'publisher': forms.Select(attrs={'class': 'form-select'}),
            'cover': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'pages': forms.NumberInput(attrs={'class': 'form-control'}),
            'language': forms.TextInput(attrs={'class': 'form-control'}),
            'genres': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'genres': _('Enter genres in JSON format, e.g., ["fiction", "mystery", "thriller"]'),
        }

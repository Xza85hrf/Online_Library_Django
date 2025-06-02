from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

CustomUser = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """A form for creating new users with email as the unique identifier."""
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')})
    )
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')})
    )
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')})
    )
    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')}),
        help_text=_('Your password must contain at least 8 characters.')
    )
    password2 = forms.CharField(
        label=_('Password confirmation'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirm Password')}),
        help_text=_('Enter the same password as before, for verification.')
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')


class CustomUserChangeForm(UserChangeForm):
    """A form for updating users."""
    password = None  # Remove the password field from the form

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserProfileForm(forms.ModelForm):
    """A form for updating user profile information."""
    class Meta:
        model = UserProfile
        fields = ('phone_number', 'address', 'date_of_birth', 'profile_picture')
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'placeholder': 'YYYY-MM-DD'
                },
                format='%Y-%m-%d'
            ),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'date_of_birth': 'Format: YYYY-MM-DD',
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """A form for changing a user's password."""
    old_password = forms.CharField(
        label=_('Current Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Current Password')}),
    )
    new_password1 = forms.CharField(
        label=_('New Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('New Password')}),
        help_text=_('Your password must contain at least 8 characters.')
    )
    new_password2 = forms.CharField(
        label=_('New Password Confirmation'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirm New Password')}),
    )

    class Meta:
        model = CustomUser
        fields = ('old_password', 'new_password1', 'new_password2')

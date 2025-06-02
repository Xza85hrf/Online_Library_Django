from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, TemplateView, UpdateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import UserProfile, CustomUser
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm,
    UserProfileForm, CustomPasswordChangeForm
)


class RegisterView(CreateView):
    """View for user registration."""
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Registration successful! You can now log in.')
        )
        return response


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(BaseLoginView):
    """View for user login."""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        # Call the parent's form_valid to perform the login
        response = super().form_valid(form)
        messages.success(self.request, _('Successfully logged in!'))
        return response

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url or reverse_lazy('library:home')


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(BaseLogoutView):
    """View for user logout."""
    template_name = 'accounts/logged_out.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Custom dispatch to handle both GET and POST requests without CSRF verification
        logout(request)
        messages.success(request, _('Wylogowano pomyślnie!'))
        return render(request, self.template_name, {})


class ProfileView(LoginRequiredMixin, TemplateView):
    """View for displaying user profile."""
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = CustomUserChangeForm(instance=self.request.user)
        context['profile_form'] = UserProfileForm(instance=self.request.user.profile)
        context['password_form'] = CustomPasswordChangeForm(user=self.request.user)
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating user profile."""
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'user_form' not in context:
            context['user_form'] = self.get_form()
        if 'profile_form' not in context:
            context['profile_form'] = UserProfileForm(instance=self.request.user.profile)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_form = self.get_form()
        profile_form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Profile updated successfully!'))
            return self.form_valid(user_form)
        else:
            # Add both forms to the context when validation fails
            return self.render_to_response(
                self.get_context_data(
                    form=user_form,
                    user_form=user_form,
                    profile_form=profile_form
                )
            )


class ChangePasswordView(LoginRequiredMixin, FormView):
    """View for changing user password."""
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, _('Your password was successfully updated!'))
        return super().form_valid(form)


@login_required
def delete_account(request):
    """View for deleting user account."""
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, _('Your account has been deleted successfully.'))
        return redirect('library:home')
    return redirect('accounts:profile')

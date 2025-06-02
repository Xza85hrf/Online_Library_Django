"""
Notification system for the library application.
Handles email notifications and in-app notifications for various events.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta

from .models import BookLoan, BookReservation


def send_email_notification(subject, template_name, context, recipient_list):
    """
    Send an email notification using a template.
    
    Args:
        subject (str): Email subject
        template_name (str): Path to the email template
        context (dict): Context data for the template
        recipient_list (list): List of recipient email addresses
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    html_message = render_to_string(f'emails/{template_name}.html', context)
    plain_message = strip_tags(html_message)
    
    return send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=False,
    )


def send_due_date_reminder():
    """
    Send reminder emails for books due in the next 3 days.
    This function is intended to be run daily via a scheduled task.
    """
    # Find loans due in the next 3 days
    today = timezone.now().date()
    reminder_date = today + timedelta(days=3)
    
    upcoming_due_loans = BookLoan.objects.filter(
        status='borrowed',
        due_date=reminder_date,
        return_date__isnull=True
    )
    
    for loan in upcoming_due_loans:
        context = {
            'user': loan.user,
            'book': loan.book,
            'due_date': loan.due_date,
        }
        
        send_email_notification(
            subject='Reminder: Book Due Soon',
            template_name='due_date_reminder',
            context=context,
            recipient_list=[loan.user.email]
        )


def send_overdue_notification():
    """
    Send notifications for overdue books.
    This function is intended to be run daily via a scheduled task.
    """
    today = timezone.now().date()
    
    overdue_loans = BookLoan.objects.filter(
        status='borrowed',
        due_date__lt=today,
        return_date__isnull=True
    )
    
    for loan in overdue_loans:
        # Update status to overdue if not already
        if loan.status != 'overdue':
            loan.status = 'overdue'
            loan.save()
        
        days_overdue = (today - loan.due_date).days
        
        context = {
            'user': loan.user,
            'book': loan.book,
            'due_date': loan.due_date,
            'days_overdue': days_overdue,
        }
        
        send_email_notification(
            subject='Book Overdue Notice',
            template_name='overdue_notification',
            context=context,
            recipient_list=[loan.user.email]
        )


def send_reservation_confirmation(reservation):
    """
    Send a confirmation email when a book is reserved.
    
    Args:
        reservation (BookReservation): The reservation object
    """
    context = {
        'user': reservation.user,
        'book': reservation.book,
        'reservation_date': reservation.reservation_date,
        'expiry_date': reservation.expiry_date,
    }
    
    send_email_notification(
        subject='Book Reservation Confirmation',
        template_name='reservation_confirmation',
        context=context,
        recipient_list=[reservation.user.email]
    )


def send_reservation_available_notification(reservation):
    """
    Send a notification when a reserved book becomes available.
    
    Args:
        reservation (BookReservation): The reservation object
    """
    context = {
        'user': reservation.user,
        'book': reservation.book,
        'reservation_date': reservation.reservation_date,
        'expiry_date': reservation.expiry_date,
    }
    
    send_email_notification(
        subject='Your Reserved Book is Now Available',
        template_name='reservation_available',
        context=context,
        recipient_list=[reservation.user.email]
    )


def send_loan_confirmation(loan):
    """
    Send a confirmation email when a book is borrowed.
    
    Args:
        loan (BookLoan): The loan object
    """
    context = {
        'user': loan.user,
        'book': loan.book,
        'loan_date': loan.loan_date,
        'due_date': loan.due_date,
    }
    
    send_email_notification(
        subject='Book Loan Confirmation',
        template_name='loan_confirmation',
        context=context,
        recipient_list=[loan.user.email]
    )


def send_return_confirmation(loan):
    """
    Send a confirmation email when a book is returned.
    
    Args:
        loan (BookLoan): The loan object
    """
    context = {
        'user': loan.user,
        'book': loan.book,
        'loan_date': loan.loan_date,
        'return_date': loan.return_date,
    }
    
    send_email_notification(
        subject='Book Return Confirmation',
        template_name='return_confirmation',
        context=context,
        recipient_list=[loan.user.email]
    )

"""
Signal handlers for the library app.
These signals automatically trigger notifications when certain events occur.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import BookLoan, BookReservation, Book
from .notifications import (
    send_loan_confirmation,
    send_return_confirmation,
    send_reservation_confirmation,
    send_reservation_available_notification
)


@receiver(post_save, sender=BookLoan)
def handle_book_loan_signals(sender, instance, created, **kwargs):
    """
    Handle signals for BookLoan model.
    Sends notifications when a book is borrowed or returned.
    Updates book availability when loan status changes.
    """
    # If this is a new loan, send confirmation and update book availability
    if created:
        # Send loan confirmation email
        send_loan_confirmation(instance)
        
        # Update book availability
        book = instance.book
        if book.available_copies > 0:
            book.available_copies -= 1
            book.save()
    
    # If a book is returned (status changed to 'returned' and return_date is set)
    elif instance.status == 'returned' and instance.return_date:
        # Check if this is a newly returned book (by comparing with pre_save instance)
        old_instance = getattr(instance, '_pre_save_instance', None)
        is_newly_returned = (
            old_instance and 
            (old_instance.status != 'returned' or not old_instance.return_date)
        )
        
        if is_newly_returned:
            # Send return confirmation email
            send_return_confirmation(instance)
            
            # Update book availability
            book = instance.book
            book.available_copies += 1
            book.save()
            
            # Check if there are pending reservations for this book
            pending_reservations = BookReservation.objects.filter(
                book=book,
                status='pending'
            ).order_by('reservation_date')
            
            if pending_reservations.exists():
                # Get the oldest reservation
                oldest_reservation = pending_reservations.first()
                oldest_reservation.status = 'fulfilled'
                oldest_reservation.save()
                
                # Notify the user that their reserved book is available
                send_reservation_available_notification(oldest_reservation)


@receiver(pre_save, sender=BookLoan)
def store_pre_save_book_loan(sender, instance, **kwargs):
    """
    Store the pre-save state of BookLoan instances.
    This is used to detect changes in the post_save signal.
    """
    if instance.pk:
        try:
            instance._pre_save_instance = BookLoan.objects.get(pk=instance.pk)
        except BookLoan.DoesNotExist:
            pass


@receiver(post_save, sender=BookReservation)
def handle_book_reservation_signals(sender, instance, created, **kwargs):
    """
    Handle signals for BookReservation model.
    Sends notifications when a book is reserved.
    """
    if created:
        # Send reservation confirmation email
        send_reservation_confirmation(instance)
        
        # If the book is available, immediately fulfill the reservation
        book = instance.book
        if book.available_copies > 0 and instance.status == 'pending':
            instance.status = 'fulfilled'
            instance.save()
            
            # Notify the user that their reserved book is available
            send_reservation_available_notification(instance)

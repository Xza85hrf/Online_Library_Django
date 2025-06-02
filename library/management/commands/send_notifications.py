"""
Management command to send scheduled notifications.
This command can be run via a cron job or similar scheduler to send notifications on a regular basis.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from library.models import BookLoan, BookReservation
from library.notifications import send_due_date_reminder, send_overdue_notification


class Command(BaseCommand):
    help = 'Send scheduled notifications for due dates and overdue books'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['due', 'overdue', 'all'],
            default='all',
            help='Type of notifications to send: due, overdue, or all'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without actually sending emails'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        dry_run = options['dry_run']
        
        if notification_type in ['due', 'all']:
            self.send_due_date_reminders(dry_run)
        
        if notification_type in ['overdue', 'all']:
            self.send_overdue_notifications(dry_run)
        
        self.check_expired_reservations(dry_run)

    def send_due_date_reminders(self, dry_run=False):
        """Send reminders for books due in the next 3 days."""
        count = 0
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: Due date reminders'))
        
        # Logic moved to the notifications module
        send_due_date_reminder()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {count} due date reminders')
        )

    def send_overdue_notifications(self, dry_run=False):
        """Send notifications for overdue books."""
        count = 0
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: Overdue notifications'))
        
        # Logic moved to the notifications module
        send_overdue_notification()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {count} overdue notifications')
        )

    def check_expired_reservations(self, dry_run=False):
        """Check for and handle expired reservations."""
        today = timezone.now().date()
        
        # Find expired reservations
        expired_reservations = BookReservation.objects.filter(
            Q(status='pending') | Q(status='fulfilled'),
            expiry_date__lt=today
        )
        
        count = expired_reservations.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would expire {count} reservations')
            )
            return
        
        # Update status to expired
        expired_reservations.update(status='expired')
        
        # For each expired fulfilled reservation, make the book available again
        for reservation in expired_reservations.filter(status='fulfilled'):
            book = reservation.book
            book.available_copies += 1
            book.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully expired {count} reservations')
        )

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from library.models import Book, Author, Publisher, BookLoan, BookReservation, Review, LateFee

User = get_user_model()

class Report(models.Model):
    """Model for storing generated reports."""
    REPORT_TYPES = [
        ('loan_history', _('Loan History')),
        ('popular_books', _('Popular Books')),
        ('user_activity', _('User Activity')),
        ('overdue_books', _('Overdue Books')),
        ('revenue', _('Revenue')),
        ('inventory', _('Inventory')),
        ('custom', _('Custom')),
    ]
    
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    results = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True, null=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
    
    def __str__(self):
        return self.title
    
    def run_report(self):
        """Execute the report based on its type and parameters."""
        if self.report_type == 'loan_history':
            self.results = self.generate_loan_history_report()
        elif self.report_type == 'popular_books':
            self.results = self.generate_popular_books_report()
        elif self.report_type == 'user_activity':
            self.results = self.generate_user_activity_report()
        elif self.report_type == 'overdue_books':
            self.results = self.generate_overdue_books_report()
        elif self.report_type == 'revenue':
            self.results = self.generate_revenue_report()
        elif self.report_type == 'inventory':
            self.results = self.generate_inventory_report()
        elif self.report_type == 'custom':
            self.results = self.generate_custom_report()
        
        self.last_run = timezone.now()
        self.save()
        return self.results
    
    def generate_loan_history_report(self):
        """Generate a report on loan history."""
        start_date = self.parameters.get('start_date')
        end_date = self.parameters.get('end_date')
        user_id = self.parameters.get('user_id')
        
        loans_query = BookLoan.objects.all()
        
        if start_date:
            loans_query = loans_query.filter(loan_date__gte=start_date)
        if end_date:
            loans_query = loans_query.filter(loan_date__lte=end_date)
        if user_id:
            loans_query = loans_query.filter(user_id=user_id)
        
        loans = loans_query.values(
            'id', 'book__title', 'user__email', 'loan_date', 'due_date', 
            'return_date', 'status'
        )
        
        return {
            'total_loans': loans.count(),
            'loans': list(loans),
            'parameters': self.parameters,
        }
    
    def generate_popular_books_report(self):
        """Generate a report on the most popular books."""
        time_period = self.parameters.get('time_period', '30')
        limit = self.parameters.get('limit', 10)
        
        # Convert time_period to days
        days = int(time_period)
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get books with the most loans in the time period
        popular_books = Book.objects.filter(
            loans__loan_date__gte=start_date
        ).annotate(
            loan_count=models.Count('loans')
        ).order_by('-loan_count')[:limit]
        
        # Get books with the highest ratings
        top_rated_books = Book.objects.annotate(
            avg_rating=models.Avg('reviews__rating')
        ).filter(
            avg_rating__isnull=False
        ).order_by('-avg_rating')[:limit]
        
        return {
            'most_borrowed': list(popular_books.values('id', 'title', 'loan_count')),
            'top_rated': list(top_rated_books.values('id', 'title', 'avg_rating')),
            'parameters': self.parameters,
        }
    
    def generate_user_activity_report(self):
        """Generate a report on user activity."""
        time_period = self.parameters.get('time_period', '30')
        limit = self.parameters.get('limit', 10)
        
        # Convert time_period to days
        days = int(time_period)
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get users with the most loans
        active_users = User.objects.filter(
            book_loans__loan_date__gte=start_date
        ).annotate(
            loan_count=models.Count('book_loans')
        ).order_by('-loan_count')[:limit]
        
        # Get users with the most reviews
        reviewing_users = User.objects.filter(
            book_reviews__created_at__gte=start_date
        ).annotate(
            review_count=models.Count('book_reviews')
        ).order_by('-review_count')[:limit]
        
        return {
            'most_active_borrowers': list(active_users.values('id', 'email', 'loan_count')),
            'most_active_reviewers': list(reviewing_users.values('id', 'email', 'review_count')),
            'parameters': self.parameters,
        }
    
    def generate_overdue_books_report(self):
        """Generate a report on overdue books."""
        # Get all overdue loans
        overdue_loans = BookLoan.objects.filter(
            status='overdue'
        ).select_related('book', 'user')
        
        # Group by days overdue
        days_overdue_groups = {
            '1-7 days': 0,
            '8-14 days': 0,
            '15-30 days': 0,
            'Over 30 days': 0
        }
        
        loans_data = []
        for loan in overdue_loans:
            days_overdue = loan.days_overdue
            
            if days_overdue <= 7:
                days_overdue_groups['1-7 days'] += 1
            elif days_overdue <= 14:
                days_overdue_groups['8-14 days'] += 1
            elif days_overdue <= 30:
                days_overdue_groups['15-30 days'] += 1
            else:
                days_overdue_groups['Over 30 days'] += 1
            
            loans_data.append({
                'id': loan.id,
                'book_title': loan.book.title,
                'user_email': loan.user.email,
                'due_date': loan.due_date.isoformat(),
                'days_overdue': days_overdue,
                'late_fee': str(loan.calculated_late_fee) if hasattr(loan, 'calculated_late_fee') else '0.00'
            })
        
        return {
            'total_overdue': overdue_loans.count(),
            'days_overdue_groups': days_overdue_groups,
            'overdue_loans': loans_data,
            'parameters': self.parameters,
        }
    
    def generate_revenue_report(self):
        """Generate a report on revenue from late fees."""
        start_date = self.parameters.get('start_date')
        end_date = self.parameters.get('end_date')
        
        late_fees_query = LateFee.objects.all()
        
        if start_date:
            late_fees_query = late_fees_query.filter(created_at__gte=start_date)
        if end_date:
            late_fees_query = late_fees_query.filter(created_at__lte=end_date)
        
        # Get total amounts by status
        total_pending = late_fees_query.filter(payment_status='pending').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_paid = late_fees_query.filter(payment_status='paid').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_waived = late_fees_query.filter(payment_status='waived').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Get monthly breakdown
        monthly_data = late_fees_query.filter(payment_status='paid').annotate(
            month=models.functions.TruncMonth('payment_date')
        ).values('month').annotate(
            total=models.Sum('amount')
        ).order_by('month')
        
        return {
            'total_pending': float(total_pending),
            'total_paid': float(total_paid),
            'total_waived': float(total_waived),
            'total_revenue': float(total_paid),
            'monthly_breakdown': list(monthly_data),
            'parameters': self.parameters,
        }
    
    def generate_inventory_report(self):
        """Generate a report on book inventory."""
        # Get total books and copies
        total_books = Book.objects.count()
        total_copies = Book.objects.aggregate(total=models.Sum('total_copies'))['total'] or 0
        available_copies = Book.objects.aggregate(available=models.Sum('available_copies'))['available'] or 0
        
        # Get books with low availability
        low_availability = Book.objects.filter(
            available_copies__lt=models.F('total_copies') * 0.2
        ).values('id', 'title', 'available_copies', 'total_copies')
        
        # Get books by publisher
        by_publisher = Publisher.objects.annotate(
            book_count=models.Count('books')
        ).values('id', 'name', 'book_count')
        
        # Get books by author
        by_author = Author.objects.annotate(
            book_count=models.Count('books')
        ).values('id', 'name', 'book_count')
        
        return {
            'total_books': total_books,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'low_availability': list(low_availability),
            'by_publisher': list(by_publisher),
            'by_author': list(by_author),
            'parameters': self.parameters,
        }
    
    def generate_custom_report(self):
        """Generate a custom report based on SQL query or other parameters."""
        # This would be implemented based on specific requirements
        # For now, return a placeholder
        return {
            'message': 'Custom report functionality not implemented yet',
            'parameters': self.parameters,
        }


class ReportExport(models.Model):
    """Model for storing exported reports."""
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    file = models.FileField(upload_to='reports/')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Report Export')
        verbose_name_plural = _('Report Exports')
    
    def __str__(self):
        return f"{self.report.title} - {self.format} - {self.created_at.strftime('%Y-%m-%d')}"


class Dashboard(models.Model):
    """Model for storing dashboard configurations."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    layout = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dashboards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = _('Dashboard')
        verbose_name_plural = _('Dashboards')
    
    def __str__(self):
        return self.title


class DashboardWidget(models.Model):
    """Model for storing dashboard widgets."""
    WIDGET_TYPES = [
        ('chart', _('Chart')),
        ('counter', _('Counter')),
        ('table', _('Table')),
        ('list', _('List')),
        ('custom', _('Custom')),
    ]
    
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    data_source = models.CharField(max_length=255)
    parameters = models.JSONField(default=dict, blank=True)
    position = models.PositiveIntegerField(default=0)
    size = models.CharField(max_length=20, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
        verbose_name = _('Dashboard Widget')
        verbose_name_plural = _('Dashboard Widgets')
    
    def __str__(self):
        return self.title

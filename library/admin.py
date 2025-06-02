from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Author, Publisher, Book, BookLoan, BookReservation, Review, LibrarySettings, LateFee

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'birth_date')
    search_fields = ('name',)

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'founded_date')
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'publication_date', 'available_copies', 'total_copies')
    list_filter = ('publication_date', 'language')
    search_fields = ('title', 'isbn')
    filter_horizontal = ('authors',)

@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'loan_date', 'due_date', 'return_date', 'status', 'is_overdue_display', 'days_overdue_display', 'late_fee_display')
    list_filter = ('status', 'loan_date', 'due_date', 'late_fee_paid')
    search_fields = ('book__title', 'user__email')
    readonly_fields = ('is_overdue_display', 'days_overdue_display', 'calculated_late_fee_display')
    fieldsets = (
        (None, {
            'fields': ('book', 'user', 'loan_date', 'due_date', 'return_date', 'status')
        }),
        ('Late Fee Information', {
            'fields': ('late_fee_paid', 'is_overdue_display', 'days_overdue_display', 'calculated_late_fee_display'),
            'classes': ('collapse',),
        }),
    )
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_overdue_display.short_description = 'Overdue'
    
    def days_overdue_display(self, obj):
        if obj.days_overdue > 0:
            return format_html('<span style="color: red;">{} days</span>', obj.days_overdue)
        return '0 days'
    days_overdue_display.short_description = 'Days Overdue'
    
    def calculated_late_fee_display(self, obj):
        if obj.calculated_late_fee > 0:
            return format_html('<span style="color: red;">{:.2f} PLN</span>', obj.calculated_late_fee)
        return '0.00 PLN'
    calculated_late_fee_display.short_description = 'Calculated Late Fee'
    
    def late_fee_display(self, obj):
        if hasattr(obj, 'late_fee'):
            if obj.late_fee.payment_status == 'paid':
                return format_html('<span style="color: green;">{:.2f} PLN (Paid)</span>', obj.late_fee.amount)
            elif obj.late_fee.payment_status == 'waived':
                return format_html('<span style="color: blue;">{:.2f} PLN (Waived)</span>', obj.late_fee.amount)
            else:
                fee_url = reverse('admin:library_latefee_change', args=[obj.late_fee.id])
                return format_html('<a href="{}" style="color: red;">{:.2f} PLN (Pending)</a>', fee_url, obj.late_fee.amount)
        elif obj.is_overdue:
            return format_html('<span style="color: orange;">{:.2f} PLN (Calculating)</span>', obj.calculated_late_fee)
        return '-'
    late_fee_display.short_description = 'Late Fee'

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'reservation_date', 'expiry_date', 'status')
    list_filter = ('status', 'reservation_date', 'expiry_date')
    search_fields = ('book__title', 'user__email')

@admin.register(LibrarySettings)
class LibrarySettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'late_fee_daily_rate', 'max_loan_days', 'max_renewals', 'max_books_per_user')
    fieldsets = (
        ('Late Fee Settings', {
            'fields': ('late_fee_daily_rate',)
        }),
        ('Loan Settings', {
            'fields': ('max_loan_days', 'max_renewals', 'max_books_per_user')
        }),
        ('Reservation Settings', {
            'fields': ('reservation_expiry_days',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return not LibrarySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the settings object
        return False


@admin.register(LateFee)
class LateFeeAdmin(admin.ModelAdmin):
    list_display = ('loan_book_title', 'loan_user', 'amount', 'days_overdue', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('loan__book__title', 'loan__user__email')
    readonly_fields = ('loan', 'amount', 'days_overdue', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('loan', 'amount', 'days_overdue', 'payment_status')
        }),
        ('Payment Information', {
            'fields': ('payment_date',),
            'classes': ('collapse',),
        }),
        ('Waiver Information', {
            'fields': ('waived_by', 'waived_reason'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    actions = ['mark_as_paid', 'waive_fees']
    
    def loan_book_title(self, obj):
        return obj.loan.book.title
    loan_book_title.short_description = 'Book'
    
    def loan_user(self, obj):
        return obj.loan.user
    loan_user.short_description = 'User'
    
    def mark_as_paid(self, request, queryset):
        for fee in queryset:
            fee.mark_as_paid()
        self.message_user(request, f'{queryset.count()} late fees have been marked as paid.')
    mark_as_paid.short_description = "Mark selected fees as paid"
    
    def waive_fees(self, request, queryset):
        for fee in queryset:
            fee.waive_fee(request.user, "Waived by administrator")
        self.message_user(request, f'{queryset.count()} late fees have been waived.')
    waive_fees.short_description = "Waive selected fees"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'title', 'created_at', 'status')
    list_filter = ('status', 'rating', 'created_at')
    search_fields = ('book__title', 'user__email', 'title', 'content')
    actions = ['approve_reviews', 'reject_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} reviews have been approved.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} reviews have been rejected.')
    reject_reviews.short_description = "Reject selected reviews"

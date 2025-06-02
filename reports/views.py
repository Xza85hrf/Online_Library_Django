from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Avg, F, Q
from django.core.paginator import Paginator
from django.conf import settings

import csv
import json
import datetime
import io
import xlsxwriter

from .models import Report, ReportExport, Dashboard, DashboardWidget
from library.models import Book, Author, Publisher, BookLoan, BookReservation, Review, LateFee


def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def reports_dashboard(request):
    """Main dashboard for reports and analytics."""
    # Get default dashboard or first available
    dashboard = Dashboard.objects.filter(is_default=True).first() or Dashboard.objects.first()
    
    # Get recent reports
    recent_reports = Report.objects.all()[:5]
    
    # Get quick stats
    total_books = Book.objects.count()
    total_loans = BookLoan.objects.count()
    active_loans = BookLoan.objects.filter(return_date__isnull=True).count()
    overdue_loans = BookLoan.objects.filter(return_date__isnull=True, due_date__lt=timezone.now().date()).count()
    
    context = {
        'dashboard': dashboard,
        'recent_reports': recent_reports,
        'total_books': total_books,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def report_list(request):
    """List all available reports."""
    reports = Report.objects.all()
    
    # Filter by type if provided
    report_type = request.GET.get('type')
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'report_types': dict(Report.REPORT_TYPES),
        'selected_type': report_type,
    }
    
    return render(request, 'reports/report_list.html', context)


@login_required
@user_passes_test(is_staff)
def report_detail(request, pk):
    """View a specific report and its results."""
    report = get_object_or_404(Report, pk=pk)
    
    # Run the report if requested
    if request.method == 'POST' and 'run_report' in request.POST:
        report.run_report()
        messages.success(request, _('Report has been executed successfully.'))
        return redirect('report_detail', pk=report.pk)
    
    # Get exports
    exports = report.exports.all().order_by('-created_at')
    
    context = {
        'report': report,
        'exports': exports,
    }
    
    return render(request, 'reports/report_detail.html', context)


@login_required
@user_passes_test(is_staff)
def create_report(request):
    """Create a new report."""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        
        if not report_type or not title:
            messages.error(request, _('Please provide a title and report type.'))
            return redirect('create_report')
        
        # Create the report
        report = Report.objects.create(
            title=title,
            report_type=report_type,
            description=description,
            created_by=request.user,
            parameters={},  # Empty parameters for now
        )
        
        messages.success(request, _('Report has been created successfully.'))
        return redirect('report_parameters', pk=report.pk)
    
    context = {
        'report_types': Report.REPORT_TYPES,
    }
    
    return render(request, 'reports/create_report.html', context)


@login_required
@user_passes_test(is_staff)
def report_parameters(request, pk):
    """Set parameters for a report."""
    report = get_object_or_404(Report, pk=pk)
    
    if request.method == 'POST':
        # Process parameters based on report type
        parameters = {}
        
        if report.report_type == 'loan_history':
            parameters['start_date'] = request.POST.get('start_date')
            parameters['end_date'] = request.POST.get('end_date')
            parameters['user_id'] = request.POST.get('user_id')
        
        elif report.report_type == 'popular_books':
            parameters['time_period'] = request.POST.get('time_period', '30')
            parameters['limit'] = request.POST.get('limit', '10')
        
        elif report.report_type == 'user_activity':
            parameters['time_period'] = request.POST.get('time_period', '30')
            parameters['limit'] = request.POST.get('limit', '10')
        
        elif report.report_type == 'revenue':
            parameters['start_date'] = request.POST.get('start_date')
            parameters['end_date'] = request.POST.get('end_date')
        
        # Save parameters
        report.parameters = parameters
        report.save()
        
        # Run the report if requested
        if 'run_report' in request.POST:
            report.run_report()
            messages.success(request, _('Report has been executed with the new parameters.'))
        else:
            messages.success(request, _('Report parameters have been updated.'))
        
        return redirect('report_detail', pk=report.pk)
    
    context = {
        'report': report,
    }
    
    # Add context based on report type
    if report.report_type == 'loan_history':
        from accounts.models import CustomUser
        context['users'] = CustomUser.objects.all()
    
    return render(request, f'reports/parameters/{report.report_type}.html', context)


@login_required
@user_passes_test(is_staff)
def export_report(request, pk):
    """Export a report in various formats."""
    report = get_object_or_404(Report, pk=pk)
    
    # Make sure the report has results
    if not report.results:
        messages.error(request, _('The report has no results to export. Please run the report first.'))
        return redirect('report_detail', pk=report.pk)
    
    export_format = request.GET.get('format', 'csv')
    
    # Generate filename
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{report.title.replace(' ', '_')}_{timestamp}"
    
    # Export based on format
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write headers and data based on report type
        if report.report_type == 'loan_history':
            writer.writerow(['ID', 'Book Title', 'User Email', 'Loan Date', 'Due Date', 'Return Date', 'Status'])
            for loan in report.results.get('loans', []):
                writer.writerow([
                    loan.get('id'),
                    loan.get('book__title'),
                    loan.get('user__email'),
                    loan.get('loan_date'),
                    loan.get('due_date'),
                    loan.get('return_date'),
                    loan.get('status'),
                ])
        
        elif report.report_type == 'overdue_books':
            writer.writerow(['ID', 'Book Title', 'User Email', 'Due Date', 'Days Overdue', 'Late Fee'])
            for loan in report.results.get('overdue_loans', []):
                writer.writerow([
                    loan.get('id'),
                    loan.get('book_title'),
                    loan.get('user_email'),
                    loan.get('due_date'),
                    loan.get('days_overdue'),
                    loan.get('late_fee'),
                ])
        
        # Save the export record
        export = ReportExport.objects.create(
            report=report,
            format='csv',
            created_by=request.user,
        )
        
        return response
    
    elif export_format == 'excel':
        # Create an in-memory output file for the Excel workbook
        output = io.BytesIO()
        
        # Create Excel file
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Add headers and data based on report type
        if report.report_type == 'loan_history':
            headers = ['ID', 'Book Title', 'User Email', 'Loan Date', 'Due Date', 'Return Date', 'Status']
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header)
            
            for row_num, loan in enumerate(report.results.get('loans', []), 1):
                worksheet.write(row_num, 0, loan.get('id'))
                worksheet.write(row_num, 1, loan.get('book__title'))
                worksheet.write(row_num, 2, loan.get('user__email'))
                worksheet.write(row_num, 3, str(loan.get('loan_date')))
                worksheet.write(row_num, 4, str(loan.get('due_date')))
                worksheet.write(row_num, 5, str(loan.get('return_date')) if loan.get('return_date') else '')
                worksheet.write(row_num, 6, loan.get('status'))
        
        elif report.report_type == 'overdue_books':
            headers = ['ID', 'Book Title', 'User Email', 'Due Date', 'Days Overdue', 'Late Fee']
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header)
            
            for row_num, loan in enumerate(report.results.get('overdue_loans', []), 1):
                worksheet.write(row_num, 0, loan.get('id'))
                worksheet.write(row_num, 1, loan.get('book_title'))
                worksheet.write(row_num, 2, loan.get('user_email'))
                worksheet.write(row_num, 3, loan.get('due_date'))
                worksheet.write(row_num, 4, loan.get('days_overdue'))
                worksheet.write(row_num, 5, loan.get('late_fee'))
        
        workbook.close()
        
        # Prepare response
        output.seek(0)
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        # Save the export record
        export = ReportExport.objects.create(
            report=report,
            format='excel',
            created_by=request.user,
        )
        
        return response
    
    elif export_format == 'json':
        response = HttpResponse(json.dumps(report.results, indent=4), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
        
        # Save the export record
        export = ReportExport.objects.create(
            report=report,
            format='json',
            created_by=request.user,
        )
        
        return response
    
    # Default fallback
    messages.error(request, _('Invalid export format selected.'))
    return redirect('report_detail', pk=report.pk)


@login_required
@user_passes_test(is_staff)
def dashboard_list(request):
    """List all available dashboards."""
    dashboards = Dashboard.objects.all()
    
    context = {
        'dashboards': dashboards,
    }
    
    return render(request, 'reports/dashboard_list.html', context)


@login_required
@user_passes_test(is_staff)
def dashboard_detail(request, pk):
    """View a specific dashboard."""
    dashboard = get_object_or_404(Dashboard, pk=pk)
    widgets = dashboard.widgets.all().order_by('position')
    
    context = {
        'dashboard': dashboard,
        'widgets': widgets,
    }
    
    return render(request, 'reports/dashboard_detail.html', context)


@login_required
@user_passes_test(is_staff)
def create_dashboard(request):
    """Create a new dashboard."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        is_default = request.POST.get('is_default') == 'on'
        
        if not title:
            messages.error(request, _('Please provide a title for the dashboard.'))
            return redirect('create_dashboard')
        
        # If this is set as default, unset other defaults
        if is_default:
            Dashboard.objects.filter(is_default=True).update(is_default=False)
        
        # Create the dashboard
        dashboard = Dashboard.objects.create(
            title=title,
            description=description,
            is_default=is_default,
            created_by=request.user,
            layout={},  # Empty layout for now
        )
        
        messages.success(request, _('Dashboard has been created successfully.'))
        return redirect('dashboard_detail', pk=dashboard.pk)
    
    return render(request, 'reports/create_dashboard.html')


@login_required
@user_passes_test(is_staff)
def add_widget(request, dashboard_pk):
    """Add a widget to a dashboard."""
    dashboard = get_object_or_404(Dashboard, pk=dashboard_pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        widget_type = request.POST.get('widget_type')
        data_source = request.POST.get('data_source')
        size = request.POST.get('size', 'medium')
        
        if not all([title, widget_type, data_source]):
            messages.error(request, _('Please fill in all required fields.'))
            return redirect('add_widget', dashboard_pk=dashboard.pk)
        
        # Get the next position
        position = dashboard.widgets.count() + 1
        
        # Create the widget
        widget = DashboardWidget.objects.create(
            dashboard=dashboard,
            title=title,
            widget_type=widget_type,
            data_source=data_source,
            position=position,
            size=size,
            parameters={},  # Empty parameters for now
        )
        
        messages.success(request, _('Widget has been added successfully.'))
        return redirect('dashboard_detail', pk=dashboard.pk)
    
    context = {
        'dashboard': dashboard,
        'widget_types': DashboardWidget.WIDGET_TYPES,
    }
    
    return render(request, 'reports/add_widget.html', context)


@login_required
@user_passes_test(is_staff)
@require_POST
def widget_data(request, widget_pk):
    """AJAX endpoint to get data for a specific widget."""
    widget = get_object_or_404(DashboardWidget, pk=widget_pk)
    
    # Process data source and return appropriate data
    data = {}
    
    if widget.data_source == 'recent_loans':
        loans = BookLoan.objects.all().order_by('-loan_date')[:10]
        data = {
            'loans': [
                {
                    'id': loan.id,
                    'book_title': loan.book.title,
                    'user_email': loan.user.email,
                    'loan_date': loan.loan_date.isoformat(),
                    'due_date': loan.due_date.isoformat(),
                }
                for loan in loans
            ]
        }
    
    elif widget.data_source == 'overdue_stats':
        # Group overdue loans by days overdue
        overdue_loans = BookLoan.objects.filter(return_date__isnull=True, due_date__lt=timezone.now().date())
        
        days_overdue_groups = {
            '1-7 days': 0,
            '8-14 days': 0,
            '15-30 days': 0,
            'Over 30 days': 0
        }
        
        for loan in overdue_loans:
            days_overdue = (timezone.now().date() - loan.due_date).days
            
            if days_overdue <= 7:
                days_overdue_groups['1-7 days'] += 1
            elif days_overdue <= 14:
                days_overdue_groups['8-14 days'] += 1
            elif days_overdue <= 30:
                days_overdue_groups['15-30 days'] += 1
            else:
                days_overdue_groups['Over 30 days'] += 1
        
        data = {
            'groups': days_overdue_groups,
            'total': overdue_loans.count(),
        }
    
    elif widget.data_source == 'popular_books':
        # Get books with the most loans in the last 30 days
        start_date = timezone.now() - datetime.timedelta(days=30)
        
        popular_books = Book.objects.filter(
            loans__loan_date__gte=start_date
        ).annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:5]
        
        data = {
            'books': [
                {
                    'title': book.title,
                    'loan_count': book.loan_count,
                }
                for book in popular_books
            ]
        }
    
    elif widget.data_source == 'revenue_stats':
        # Get revenue from late fees in the last 6 months
        start_date = timezone.now() - datetime.timedelta(days=180)
        
        # Get monthly breakdown
        monthly_data = LateFee.objects.filter(
            payment_status='paid',
            payment_date__gte=start_date
        ).annotate(
            month=models.functions.TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        data = {
            'monthly': [
                {
                    'month': item['month'].strftime('%b %Y'),
                    'total': float(item['total']),
                }
                for item in monthly_data
            ]
        }
    
    return JsonResponse(data)

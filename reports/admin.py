from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Report, ReportExport, Dashboard, DashboardWidget


class ReportExportInline(admin.TabularInline):
    model = ReportExport
    extra = 0
    readonly_fields = ['created_at', 'created_by']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'created_by', 'created_at', 'last_run', 'is_scheduled']
    list_filter = ['report_type', 'is_scheduled', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_run']
    fieldsets = [
        (None, {
            'fields': ['title', 'report_type', 'description']
        }),
        (_('Parameters'), {
            'fields': ['parameters'],
            'classes': ['collapse']
        }),
        (_('Results'), {
            'fields': ['results'],
            'classes': ['collapse']
        }),
        (_('Schedule'), {
            'fields': ['is_scheduled', 'schedule_frequency']
        }),
        (_('Metadata'), {
            'fields': ['created_by', 'created_at', 'updated_at', 'last_run'],
            'classes': ['collapse']
        }),
    ]
    inlines = [ReportExportInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['run_selected_reports']
    
    def run_selected_reports(self, request, queryset):
        for report in queryset:
            report.run_report()
        self.message_user(request, _(f"{queryset.count()} reports have been executed."))
    run_selected_reports.short_description = _('Run selected reports')


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ['report', 'format', 'created_at', 'created_by']
    list_filter = ['format', 'created_at']
    search_fields = ['report__title']
    readonly_fields = ['created_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 1
    fields = ['title', 'widget_type', 'data_source', 'position', 'size']


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_default', 'created_by', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['title', 'description', 'is_default']
        }),
        (_('Layout'), {
            'fields': ['layout'],
            'classes': ['collapse']
        }),
        (_('Metadata'), {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    inlines = [DashboardWidgetInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'dashboard', 'widget_type', 'position']
    list_filter = ['widget_type', 'dashboard']
    search_fields = ['title', 'dashboard__title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['dashboard', 'title', 'widget_type', 'data_source']
        }),
        (_('Display'), {
            'fields': ['position', 'size']
        }),
        (_('Configuration'), {
            'fields': ['parameters'],
            'classes': ['collapse']
        }),
        (_('Metadata'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard views
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('dashboards/', views.dashboard_list, name='dashboard_list'),
    path('dashboards/<int:pk>/', views.dashboard_detail, name='dashboard_detail'),
    path('dashboards/create/', views.create_dashboard, name='create_dashboard'),
    path('dashboards/<int:dashboard_pk>/add-widget/', views.add_widget, name='add_widget'),
    path('widgets/<int:widget_pk>/data/', views.widget_data, name='widget_data'),
    
    # Report views
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/create/', views.create_report, name='create_report'),
    path('reports/<int:pk>/parameters/', views.report_parameters, name='report_parameters'),
    path('reports/<int:pk>/export/', views.export_report, name='export_report'),
]

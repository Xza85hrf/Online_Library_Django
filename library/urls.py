from django.urls import path
from . import views

# Usunięto app_name = 'library', aby URL-e działały bez prefiksu

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('authors/', views.author_list, name='author_list'),
    path('authors/<int:pk>/', views.author_detail, name='author_detail'),
    path('publishers/', views.publisher_list, name='publisher_list'),
    path('publishers/<int:pk>/', views.publisher_detail, name='publisher_detail'),
    
    # Book borrowing and reservation system
    path('books/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('loans/<int:loan_id>/return/', views.return_book, name='return_book'),
    path('books/<int:pk>/reserve/', views.reserve_book, name='reserve_book'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    
    # User book management
    path('my-loans/', views.my_loans, name='my_loans'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    
    # Review system
    path('books/<int:book_id>/review/', views.create_review, name='create_review'),
    path('reviews/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    
    # Late fee management system
    path('my-late-fees/', views.my_late_fees, name='my_late_fees'),
    
    # Test images
    path('test-images/', views.test_images, name='test_images'),
    path('late-fees/<int:fee_id>/pay/', views.pay_late_fee, name='pay_late_fee'),
    path('late-fees/<int:fee_id>/request-waiver/', views.request_fee_waiver, name='request_fee_waiver'),
    
    # Staff late fee management
    path('admin/late-fees/', views.manage_late_fees, name='manage_late_fees'),
    path('admin/late-fees/<int:fee_id>/process-waiver/', views.process_waiver_request, name='process_waiver_request'),
    path('admin/library-settings/', views.library_settings, name='library_settings'),
    
    # Library information pages
    path('about/', views.about, name='about'),
    path('events/', views.events, name='events'),
    path('digital-library/', views.digital_library, name='digital_library'),
    path('how-to-borrow/', views.how_to_borrow, name='how_to_borrow'),
    path('rules/', views.rules, name='rules'),
    path('opening-hours/', views.opening_hours, name='opening_hours'),
    
    # Librarian management views
    path('librarian/', views.librarian_dashboard, name='librarian_dashboard'),
    
    # Author management
    path('librarian/authors/add/', views.author_create, name='author_create'),
    path('librarian/authors/<int:pk>/edit/', views.author_update, name='author_update'),
    path('librarian/authors/<int:pk>/delete/', views.author_delete, name='author_delete'),
    
    # Publisher management
    path('librarian/publishers/add/', views.publisher_create, name='publisher_create'),
    path('librarian/publishers/<int:pk>/edit/', views.publisher_update, name='publisher_update'),
    path('librarian/publishers/<int:pk>/delete/', views.publisher_delete, name='publisher_delete'),
    
    # Book management
    path('librarian/books/add/', views.book_create, name='book_create'),
    path('librarian/books/<int:pk>/edit/', views.book_update, name='book_update'),
    path('librarian/books/<int:pk>/delete/', views.book_delete, name='book_delete'),
]

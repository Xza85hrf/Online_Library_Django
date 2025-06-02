#!/usr/bin/env python
"""
Image Generation Script for Online Library Project

This script generates various images for the Online Library project:
- Book covers
- Author portraits
- Publisher logos
- Report charts and graphs

It uses Pillow for basic image manipulation and matplotlib for charts.
"""

import os
import random
import string
import django
# Set matplotlib to use Agg backend (non-GUI) to avoid Qt errors
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

# Import models after Django setup
from library.models import Book, Author, Publisher, BookLoan
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg, F, Q

User = get_user_model()

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
COVERS_DIR = os.path.join(MEDIA_DIR, 'covers')
AUTHOR_DIR = os.path.join(MEDIA_DIR, 'authors')
PUBLISHER_DIR = os.path.join(MEDIA_DIR, 'publishers')
CHART_DIR = os.path.join(MEDIA_DIR, 'charts')

# Create directories if they don't exist
for directory in [MEDIA_DIR, COVERS_DIR, AUTHOR_DIR, PUBLISHER_DIR, CHART_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Colors
COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
]

def random_color():
    """Return a random color from the COLORS list."""
    return random.choice(COLORS)

def generate_book_cover(book, output_path=None):
    """Generate a book cover image for a given book."""
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), random_color())
    draw = ImageDraw.Draw(image)
    
    # Add a decorative border
    border_width = 20
    draw.rectangle(
        [(border_width, border_width), (width - border_width, height - border_width)],
        outline=random_color(),
        width=5
    )
    
    # Add title
    font_size = 60
    try:
        font = ImageFont.truetype('arial.ttf', font_size)
    except IOError:
        # Fallback to default font if arial.ttf is not available
        font = ImageFont.load_default()
        font_size = 20
    
    title = book.title
    title_width = draw.textlength(title, font=font)
    
    # If title is too long, reduce font size
    while title_width > width - 100 and font_size > 30:
        font_size -= 5
        try:
            font = ImageFont.truetype('arial.ttf', font_size)
        except IOError:
            font = ImageFont.load_default()
        title_width = draw.textlength(title, font=font)
    
    # Draw title
    draw.text(
        (width // 2 - title_width // 2, height // 4),
        title,
        fill='white',
        font=font
    )
    
    # Add some decorative elements
    for _ in range(5):
        x1 = random.randint(50, width - 50)
        y1 = random.randint(height // 2, height - 100)
        size = random.randint(30, 100)
        draw.ellipse(
            [(x1, y1), (x1 + size, y1 + size)],
            fill=random_color(),
            outline=random_color()
        )
    
    # Save the image
    if output_path is None:
        # If book has an id, use it, otherwise generate a random filename
        if hasattr(book, 'id') and book.id:
            filename = f"{book.id}.png"
            output_path = os.path.join(COVERS_DIR, filename)
            
            # Update book model with image path if it's a real book object from the database
            if hasattr(book, 'cover_image') and hasattr(book, 'save'):
                relative_path = os.path.join('covers', filename)
                book.cover_image = relative_path
                book.save()
        else:
            output_path = os.path.join(COVERS_DIR, f"book_cover_{random.randint(1000, 9999)}.png")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the image
    image.save(output_path)
    
    return output_path

def generate_author_portrait(author, output_path=None):
    """Generate an author portrait for a given author."""
    width, height = 500, 600
    img = Image.new('RGB', (width, height), color=random_color())
    draw = ImageDraw.Draw(img)
    
    # Try to load font, use default if not available
    try:
        name_font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        name_font = ImageFont.load_default()
    
    # Draw author name
    name = author.name
    if len(name) > 30:
        name = name[:30] + "..."
    draw.text((width//2, height-50), name, fill="white", font=name_font, anchor="mm")
    
    # Draw a simple portrait silhouette
    head_size = 150
    head_x, head_y = width//2, height//3
    # Draw head
    draw.ellipse([(head_x-head_size//2, head_y-head_size//2), 
                 (head_x+head_size//2, head_y+head_size//2)], 
                 fill="white")
    # Draw body
    draw.rectangle([(width//2-head_size//3, head_y+head_size//2), 
                    (width//2+head_size//3, height-100)], 
                   fill="white")
    
    # Save the image
    if output_path is None:
        # If author has an id, use it, otherwise generate a random filename
        if hasattr(author, 'id') and author.id:
            filename = f"{author.id}_{author.name.replace(' ', '_')[:30]}.jpg"
            output_path = os.path.join(AUTHOR_DIR, filename)
            
            # Update author model with image path if it's a real author object from the database
            if hasattr(author, 'portrait') and hasattr(author, 'save'):
                relative_path = os.path.join('authors', filename)
                author.portrait = relative_path
                author.save()
        else:
            output_path = os.path.join(AUTHOR_DIR, f"author_portrait_{random.randint(1000, 9999)}.jpg")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the image
    img.save(output_path)
    
    return output_path

def generate_publisher_logo(publisher, output_path=None):
    """Generate a publisher logo for a given publisher."""
    width, height = 400, 400
    img = Image.new('RGB', (width, height), color=random_color())
    draw = ImageDraw.Draw(img)
    
    # Try to load font, use default if not available
    try:
        logo_font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        logo_font = ImageFont.load_default()
    
    # Draw publisher name
    name = publisher.name
    if len(name) > 20:
        name = name[:20] + "..."
    draw.text((width//2, height//2), name, fill="white", font=logo_font, anchor="mm")
    
    # Draw a simple logo design
    draw.rectangle([(50, 50), (width-50, height-50)], outline="white", width=5)
    
    # Save the image
    if output_path is None:
        # If publisher has an id, use it, otherwise generate a random filename
        if hasattr(publisher, 'id') and publisher.id:
            filename = f"{publisher.id}_{publisher.name.replace(' ', '_')[:30]}.jpg"
            output_path = os.path.join(PUBLISHER_DIR, filename)
            
            # Update publisher model with image path if it's a real publisher object from the database
            if hasattr(publisher, 'logo') and hasattr(publisher, 'save'):
                relative_path = os.path.join('publishers', filename)
                publisher.logo = relative_path
                publisher.save()
        else:
            output_path = os.path.join(PUBLISHER_DIR, f"publisher_logo_{random.randint(1000, 9999)}.jpg")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the image
    img.save(output_path)
    
    return output_path

def generate_loan_history_chart():
    """Generate a chart showing loan history over time."""
    # Get loan data for the last 12 months
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    # Prepare data
    months = []
    loan_counts = []
    
    for i in range(12):
        month_start = start_date + timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_name = month_start.strftime('%b')
        
        # Count loans in this month - using due_date instead of created_at
        count = BookLoan.objects.filter(
            due_date__gte=month_start,
            due_date__lt=month_end
        ).count()
        
        months.append(month_name)
        loan_counts.append(count)
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    plt.bar(months, loan_counts, color=COLORS[:len(months)])
    plt.title('Book Loans by Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Loans')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the chart
    filename = 'loan_history_chart.png'
    filepath = os.path.join(CHART_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    
    return filepath

def generate_popular_books_chart():
    """Generate a chart showing the most popular books."""
    # Get the top 10 most loaned books
    popular_books = Book.objects.annotate(
        loan_count=Count('loans')
    ).order_by('-loan_count')[:10]
    
    # Prepare data
    book_titles = []
    loan_counts = []
    
    for book in popular_books:
        title = book.title
        if len(title) > 20:
            title = title[:17] + "..."
        book_titles.append(title)
        loan_counts.append(book.loan_count)
    
    # Create the chart
    plt.figure(figsize=(12, 8))
    bars = plt.barh(book_titles, loan_counts, color=COLORS[:len(book_titles)])
    plt.title('Most Popular Books')
    plt.xlabel('Number of Loans')
    plt.ylabel('Book Title')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Add count labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.0f}', 
                ha='left', va='center')
    
    # Save the chart
    filename = 'popular_books_chart.png'
    filepath = os.path.join(CHART_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    
    return filepath

def generate_user_activity_chart():
    """Generate a chart showing user activity."""
    # Create default data in case there are no users or loans
    usernames = ['No active users']
    loan_counts = [0]
    
    try:
        # Get the top 10 most active users
        active_users = User.objects.annotate(
            loan_count=Count('book_loans')
        ).filter(loan_count__gt=0).order_by('-loan_count')[:10]
        
        # Check if we have any active users
        if active_users.exists():
            # Clear the default data
            usernames = []
            loan_counts = []
            
            # Add real user data
            for user in active_users:
                if user and user.username:  # Ensure user and username are not None
                    username = user.username
                    if len(username) > 15:
                        username = username[:12] + "..."
                    usernames.append(username)
                    loan_counts.append(user.loan_count)
    except Exception as e:
        print(f"  Warning: Could not get user activity data: {e}")
        # Keep using the default data
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    plt.bar(usernames, loan_counts, color=COLORS[:len(usernames)])
    plt.title('Most Active Users')
    plt.xlabel('Username')
    plt.ylabel('Number of Loans')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save the chart
    filename = 'user_activity_chart.png'
    filepath = os.path.join(CHART_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    
    return filepath

def generate_genre_distribution_chart():
    """Generate a chart showing book genre distribution."""
    # Get all books with non-null genres
    books_with_genres = Book.objects.exclude(genres__isnull=True)
    
    # Create a genre counter dictionary
    genre_counter = {}
    
    # Count occurrences of each genre across all books
    for book in books_with_genres:
        if book.genres:  # Check if genres is not None or empty
            for genre in book.genres:
                if genre in genre_counter:
                    genre_counter[genre] += 1
                else:
                    genre_counter[genre] = 1
    
    # Sort genres by count (descending)
    sorted_genres = sorted(genre_counter.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare data for chart (limit to top 10 if more than 10 genres)
    genre_names = []
    book_counts = []
    
    for genre, count in sorted_genres[:10]:  # Limit to top 10 genres
        genre_names.append(genre)
        book_counts.append(count)
    
    # Create the chart
    plt.figure(figsize=(10, 10))
    plt.pie(book_counts, labels=genre_names, autopct='%1.1f%%', 
            startangle=90, colors=COLORS[:len(genre_names)])
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Book Distribution by Genre')
    plt.tight_layout()
    
    # Save the chart
    filename = 'genre_distribution_chart.png'
    filepath = os.path.join(CHART_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    
    return filepath

def main():
    """Main function to generate all images."""
    print("Starting image generation for Online Library project...")
    
    # Generate book covers
    print("\nGenerating book covers...")
    books = Book.objects.all()
    for i, book in enumerate(books):
        filepath = generate_book_cover(book)
        print(f"  Generated cover for '{book.title}' ({i+1}/{len(books)})")
    
    # Generate author portraits
    print("\nGenerating author portraits...")
    authors = Author.objects.all()
    for i, author in enumerate(authors):
        filepath = generate_author_portrait(author)
        print(f"  Generated portrait for '{author.name}' ({i+1}/{len(authors)})")
    
    # Generate publisher logos
    print("\nGenerating publisher logos...")
    publishers = Publisher.objects.all()
    for i, publisher in enumerate(publishers):
        filepath = generate_publisher_logo(publisher)
        print(f"  Generated logo for '{publisher.name}' ({i+1}/{len(publishers)})")
    
    # Generate charts
    print("\nGenerating statistical charts...")
    
    try:
        filepath = generate_loan_history_chart()
        print(f"  Generated loan history chart: {filepath}")
    except Exception as e:
        print(f"  Error generating loan history chart: {e}")
    
    try:
        filepath = generate_popular_books_chart()
        print(f"  Generated popular books chart: {filepath}")
    except Exception as e:
        print(f"  Error generating popular books chart: {e}")
    
    try:
        filepath = generate_user_activity_chart()
        print(f"  Generated user activity chart: {filepath}")
    except Exception as e:
        print(f"  Error generating user activity chart: {e}")
    
    try:
        filepath = generate_genre_distribution_chart()
        print(f"  Generated genre distribution chart: {filepath}")
    except Exception as e:
        print(f"  Error generating genre distribution chart: {e}")
    
    print("\nImage generation complete!")

if __name__ == "__main__":
    main()

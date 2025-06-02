#!/usr/bin/env python
"""
Advanced Image Generation Script for Online Library Project

This script combines basic image generation with AI-powered image generation using the Flux model.
It generates various images for the Online Library project:
- Book covers (AI-generated)
- Author portraits (AI-generated)
- Publisher logos (AI-generated)
- Report charts and graphs (matplotlib-generated)

It uses Flux AI for realistic images and matplotlib for charts.
"""

import os
import random
import string
import django
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from pathlib import Path
import time
import json
import sys

# Define base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Skip torch import to avoid AMD GPU library issues
FLUX_AVAILABLE = False
print("Skipping Flux AI initialization due to potential GPU library issues.")

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

# Import models after Django setup
from library.models import Book, Author, Publisher, BookLoan
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg, F, Q

# Check if flux_wrapper.py exists
FLUX_WRAPPER_PATH = os.path.join(BASE_DIR, 'flux_wrapper.py')
if os.path.exists(FLUX_WRAPPER_PATH):
    FLUX_AVAILABLE = True
    print(f"Found Flux AI wrapper: {FLUX_WRAPPER_PATH}")
else:
    FLUX_AVAILABLE = False
    print(f"Flux AI wrapper not found: {FLUX_WRAPPER_PATH}")
    print("Using basic image generation only.")

# Function to generate images using the flux_wrapper.py script
def generate_with_flux(prompt, output_path, seed=None):
    """Generate an image using Flux AI through the flux_wrapper.py script."""
    try:
        import subprocess
        cmd = [
            "python", FLUX_WRAPPER_PATH,
            "--prompt", prompt,
            "--output", output_path
        ]
        
        # Add seed if provided
        if seed is not None:
            cmd.extend(["--seed", str(seed)])
            
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Command output: {result.stdout}")
        
        if result.returncode == 0:
            print(f"Successfully generated image at {output_path}")
            return True
        else:
            print(f"Error generating image: {result.stderr}")
            return False
    except Exception as e:
        print(f"Exception while generating with Flux: {e}")
        return False

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


class AdvancedImageGenerator:
    def __init__(self):
        """Initialize the AdvancedImageGenerator."""
        self.flux_available = FLUX_AVAILABLE
        print(f"Advanced Image Generator initialized. Flux AI available: {self.flux_available}")
    
    def generate_ai_image(self, prompt, output_path, seed=None):
        """Generate an image using Flux AI through subprocess."""
        if not self.flux_available:
            print("Flux AI not available. Skipping AI image generation.")
            return None
        
        # Use the subprocess approach to generate the image
        success = generate_with_flux(prompt, output_path, seed)
        
        if success and os.path.exists(output_path):
            print(f"Successfully generated AI image at: {output_path}")
            return output_path
        else:
            print(f"Failed to generate AI image at: {output_path}")
            return None
    
    def generate_book_cover(self, book):
        """Generate a book cover image for a given book."""
        filename = f"{book.id}_{book.title.replace(' ', '_')[:30]}.jpg"
        filepath = os.path.join(COVERS_DIR, filename)
        
        if self.flux_available:
            # Generate AI-powered book cover
            authors = ", ".join([author.name for author in book.authors.all()])
            prompt = f"A professional book cover for '{book.title}' by {authors}. High quality, detailed, publishing industry standard."
            
            if self.generate_ai_image(prompt, filepath):
                # Update book model with image path
                relative_path = os.path.join('covers', filename)
                book.cover_image = relative_path
                book.save()
                return filepath
        
        # Fallback to basic image generation
        width, height = 600, 900
        img = Image.new('RGB', (width, height), color=random_color())
        draw = ImageDraw.Draw(img)
        
        # Try to load font, use default if not available
        try:
            title_font = ImageFont.truetype("arial.ttf", 40)
            author_font = ImageFont.truetype("arial.ttf", 30)
        except IOError:
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Draw book title
        title = book.title
        if len(title) > 20:
            title = title[:20] + "..."
        draw.text((width//2, height//4), title, fill="white", font=title_font, anchor="mm")
        
        # Draw author name
        author_names = ", ".join([author.name for author in book.authors.all()])
        if len(author_names) > 30:
            author_names = author_names[:30] + "..."
        draw.text((width//2, height//3), author_names, fill="white", font=author_font, anchor="mm")
        
        # Draw a simple book design
        draw.rectangle([(50, 50), (width-50, height-50)], outline="white", width=5)
        
        # Save the image
        img.save(filepath)
        
        # Update book model with image path
        relative_path = os.path.join('covers', filename)
        book.cover_image = relative_path
        book.save()
        
        return filepath
    
    def generate_author_portrait(self, author):
        """Generate an author portrait for a given author."""
        filename = f"{author.id}_{author.name.replace(' ', '_')[:30]}.jpg"
        filepath = os.path.join(AUTHOR_DIR, filename)
        
        if self.flux_available:
            # Generate AI-powered author portrait
            prompt = f"A professional portrait photograph of author {author.name}. High quality, detailed, professional headshot."
            
            if self.generate_ai_image(prompt, filepath):
                # Update author model with image path
                relative_path = os.path.join('authors', filename)
                author.photo = relative_path
                author.save()
                return filepath
        
        # Fallback to basic image generation
        width, height = 500, 600
        img = Image.new('RGB', (width, height), color=random_color())
        draw = ImageDraw.Draw(img)
        
        # Try to load font, use default if not available
        try:
            name_font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            name_font = ImageFont.load_default()
        
        # Draw a simple portrait frame
        draw.ellipse([(100, 100), (width-100, height-200)], fill="white")
        
        # Draw author name
        name = author.name
        if len(name) > 25:
            name = name[:25] + "..."
        draw.text((width//2, height-100), name, fill="white", font=name_font, anchor="mm")
        
        # Save the image
        img.save(filepath)
        
        # Update author model with image path
        relative_path = os.path.join('authors', filename)
        author.photo = relative_path
        author.save()
        
        return filepath
    
    def generate_publisher_logo(self, publisher):
        """Generate a publisher logo for a given publisher."""
        filename = f"{publisher.id}_{publisher.name.replace(' ', '_')[:30]}.jpg"
        filepath = os.path.join(PUBLISHER_DIR, filename)
        
        if self.flux_available:
            # Generate AI-powered publisher logo
            prompt = f"A professional logo for publishing company '{publisher.name}'. Clean, corporate design, minimalist, high quality."
            
            if self.generate_ai_image(prompt, filepath):
                # Update publisher model with image path
                relative_path = os.path.join('publishers', filename)
                publisher.logo = relative_path
                publisher.save()
                return filepath
        
        # Fallback to basic image generation
        width, height = 400, 400
        img = Image.new('RGB', (width, height), color=random_color())
        draw = ImageDraw.Draw(img)
        
        # Try to load font, use default if not available
        try:
            name_font = ImageFont.truetype("arial.ttf", 30)
        except IOError:
            name_font = ImageFont.load_default()
        
        # Draw a simple logo
        draw.rectangle([(50, 50), (width-50, height-50)], fill="white")
        
        # Draw publisher name
        name = publisher.name
        if len(name) > 20:
            name = name[:20] + "..."
        draw.text((width//2, height//2), name, fill=random_color(), font=name_font, anchor="mm")
        
        # Save the image
        img.save(filepath)
        
        # Update publisher model with image path
        relative_path = os.path.join('publishers', filename)
        publisher.logo = relative_path
        publisher.save()
        
        return filepath


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
    print("Starting advanced image generation for Online Library project...")
    
    # Initialize the advanced image generator
    generator = AdvancedImageGenerator()
    
    # Generate book covers
    print("\nGenerating book covers...")
    books = Book.objects.all()
    for i, book in enumerate(books):
        filepath = generator.generate_book_cover(book)
        print(f"  Generated cover for '{book.title}' ({i+1}/{len(books)})")
    
    # Generate author portraits
    print("\nGenerating author portraits...")
    authors = Author.objects.all()
    for i, author in enumerate(authors):
        filepath = generator.generate_author_portrait(author)
        print(f"  Generated portrait for '{author.name}' ({i+1}/{len(authors)})")
    
    # Generate publisher logos
    print("\nGenerating publisher logos...")
    publishers = Publisher.objects.all()
    for i, publisher in enumerate(publishers):
        filepath = generator.generate_publisher_logo(publisher)
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

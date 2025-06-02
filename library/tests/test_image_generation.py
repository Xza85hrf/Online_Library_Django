#!/usr/bin/env python
"""
Test Image Generation Script

This script tests both the basic and advanced image generation capabilities
for the Online Library project.
"""

import os
import sys
import random
import argparse
from pathlib import Path

# Import our image generation modules
import generate_images as basic_generator
from advanced_image_generator import AdvancedImageGenerator

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test image generation for the Online Library project')
    parser.add_argument('--mode', choices=['basic', 'advanced', 'both'], default='both',
                        help='Which image generation mode to test')
    parser.add_argument('--output-dir', default='test_images',
                        help='Directory to save generated images')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Test prompts for different types of images
    test_prompts = {
        'book_cover': [
            "Fantasy book cover with a dragon and a castle",
            "Science fiction book cover with spaceships and alien planets",
            "Mystery novel cover with a silhouette in the fog"
        ],
        'author_portrait': [
            "Portrait of a distinguished male author with glasses and beard",
            "Portrait of a female author with short hair in a library setting",
            "Artistic portrait of a young writer with a notebook"
        ],
        'publisher_logo': [
            "Minimalist publishing house logo with book icon",
            "Elegant publisher logo with quill pen design",
            "Modern publishing company logo with abstract book shape"
        ]
    }
    
    # Test basic image generation if requested
    if args.mode in ['basic', 'both']:
        print("\n=== Testing Basic Image Generation ===")
        
        # Test book covers
        for i, prompt in enumerate(test_prompts['book_cover']):
            output_path = os.path.join(output_dir, f"basic_book_cover_{i+1}.png")
            print(f"Generating basic book cover {i+1} at {output_path}")
            # Create a mock book object with a title
            class MockBook:
                def __init__(self, title):
                    self.title = title
            mock_book = MockBook(f"Test Book {i+1}: {prompt[:30]}...")
            basic_generator.generate_book_cover(mock_book, output_path=output_path)
        
        # Test author portraits
        for i, prompt in enumerate(test_prompts['author_portrait']):
            output_path = os.path.join(output_dir, f"basic_author_portrait_{i+1}.png")
            print(f"Generating basic author portrait {i+1} at {output_path}")
            # Create a mock author object with a name
            class MockAuthor:
                def __init__(self, name):
                    self.name = name
            mock_author = MockAuthor(f"Author {i+1}")
            basic_generator.generate_author_portrait(mock_author, output_path=output_path)
        
        # Test publisher logos
        for i, prompt in enumerate(test_prompts['publisher_logo']):
            output_path = os.path.join(output_dir, f"basic_publisher_logo_{i+1}.png")
            print(f"Generating basic publisher logo {i+1} at {output_path}")
            # Create a mock publisher object with a name
            class MockPublisher:
                def __init__(self, name):
                    self.name = name
            mock_publisher = MockPublisher(f"Publisher {i+1}")
            basic_generator.generate_publisher_logo(mock_publisher, output_path=output_path)
    
    # Test advanced image generation if requested
    if args.mode in ['advanced', 'both']:
        print("\n=== Testing Advanced Image Generation ===")
        advanced_generator = AdvancedImageGenerator()
        
        # Test book covers
        for i, prompt in enumerate(test_prompts['book_cover']):
            output_path = os.path.join(output_dir, f"advanced_book_cover_{i+1}.png")
            print(f"Generating advanced book cover {i+1} at {output_path}")
            seed = random.randint(1, 1000000)
            advanced_generator.generate_ai_image(prompt, output_path, seed)
        
        # Test author portraits
        for i, prompt in enumerate(test_prompts['author_portrait']):
            output_path = os.path.join(output_dir, f"advanced_author_portrait_{i+1}.png")
            print(f"Generating advanced author portrait {i+1} at {output_path}")
            seed = random.randint(1, 1000000)
            advanced_generator.generate_ai_image(prompt, output_path, seed)
        
        # Test publisher logos
        for i, prompt in enumerate(test_prompts['publisher_logo']):
            output_path = os.path.join(output_dir, f"advanced_publisher_logo_{i+1}.png")
            print(f"Generating advanced publisher logo {i+1} at {output_path}")
            seed = random.randint(1, 1000000)
            advanced_generator.generate_ai_image(prompt, output_path, seed)
    
    print("\n=== Image Generation Testing Complete ===")
    print(f"Generated images can be found in the '{args.output_dir}' directory")

if __name__ == "__main__":
    main()

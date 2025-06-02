#!/usr/bin/env python
"""
Test a single image generation with Flux AI
"""

import os
from advanced_image_generator import AdvancedImageGenerator

def main():
    # Create output directory if it doesn't exist
    output_dir = "test_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test advanced image generation
    print("\n=== Testing Advanced Image Generation ===")
    advanced_generator = AdvancedImageGenerator()
    
    # Test a single book cover
    prompt = "Fantasy book cover with a dragon and a castle"
    output_path = os.path.join(output_dir, "advanced_book_cover_test.png")
    print(f"Generating advanced book cover at {output_path}")
    seed = 12345  # Fixed seed for reproducibility
    result = advanced_generator.generate_ai_image(prompt, output_path, seed)
    
    if result:
        print(f"Successfully generated image at: {output_path}")
    else:
        print(f"Failed to generate image")

if __name__ == "__main__":
    main()

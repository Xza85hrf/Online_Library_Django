#!/usr/bin/env python
"""
Flux AI Wrapper Script

This script serves as a wrapper to call the Flux AI image generation functionality
from the correct conda environment. It takes a prompt and output path as arguments
and generates an image using the Flux AI pipeline.

If the Flux AI environment is not properly set up, it will generate a basic image instead.
"""

import os
import sys
import subprocess
import argparse
from PIL import Image, ImageDraw, ImageFont
import random

# Fallback image generation function
def generate_basic_image(prompt, output_path, seed=None):
    """Generate a basic image with text when Flux AI is not available."""
    if seed is not None:
        random.seed(seed)
    
    # Create a colorful background
    width, height = 1024, 1024
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255),
        (128, 0, 0), (0, 128, 0), (0, 0, 128),
        (128, 128, 0), (128, 0, 128), (0, 128, 128)
    ]
    bg_color = random.choice(colors)
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Add some random shapes
    for _ in range(10):
        shape_type = random.choice(['circle', 'rectangle'])
        x1 = random.randint(0, width - 100)
        y1 = random.randint(0, height - 100)
        x2 = x1 + random.randint(50, 200)
        y2 = y1 + random.randint(50, 200)
        color = random.choice(colors)
        
        if shape_type == 'circle':
            draw.ellipse([(x1, y1), (x2, y2)], fill=color)
        else:
            draw.rectangle([(x1, y1), (x2, y2)], fill=color)
    
    # Add the prompt text
    try:
        font = ImageFont.truetype('arial.ttf', 30)
    except IOError:
        font = ImageFont.load_default()
    
    # Wrap text to fit the image width
    words = prompt.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        text_width = draw.textlength(test_line, font=font)
        if text_width < width - 40:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw text
    y_position = height // 2 - (len(lines) * 35) // 2
    for line in lines:
        text_width = draw.textlength(line, font=font)
        draw.text(
            (width // 2 - text_width // 2, y_position),
            line,
            fill=(255, 255, 255),
            font=font
        )
        y_position += 35
    
    # Add a note about fallback
    fallback_text = "[Fallback Image - Flux AI unavailable]"
    text_width = draw.textlength(fallback_text, font=font)
    draw.text(
        (width // 2 - text_width // 2, height - 50),
        fallback_text,
        fill=(255, 255, 255),
        font=font
    )
    
    # Save the image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    print(f"Generated fallback image at {output_path}")
    return True

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate images using Flux AI')
    parser.add_argument('--prompt', required=True, help='Text prompt for image generation')
    parser.add_argument('--output', required=True, help='Output path for the generated image')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--fallback', action='store_true', help='Force fallback to basic image generation')
    args = parser.parse_args()
    
    # If fallback is requested, generate a basic image
    if args.fallback:
        return generate_basic_image(args.prompt, args.output, args.seed)
    
    # Path to our direct flux generator script
    flux_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "direct_flux_generator.py")
    
    # Ensure the script exists
    if not os.path.exists(flux_script_path):
        print(f"Error: Direct Flux generator script not found at {flux_script_path}")
        print("Falling back to basic image generation...")
        return generate_basic_image(args.prompt, args.output, args.seed)
    
    try:
        # Construct the command to run our direct flux generator script
        # For Windows, we need to set environment variables differently
        env = os.environ.copy()
        env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        env["CUDA_VISIBLE_DEVICES"] = "0"
        
        cmd = [
            "conda", "run", "-n", "flux", "python", flux_script_path,
            "--prompt", args.prompt,
            "--output", args.output
        ]
        
        # Add seed if provided
        if args.seed is not None:
            cmd.extend(["--seed", str(args.seed)])
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        # Print the output
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            print("Falling back to basic image generation...")
            return generate_basic_image(args.prompt, args.output, args.seed)
        
        # Verify the output file was created
        if not os.path.exists(args.output):
            print(f"Error: Output file not created at {args.output}")
            print("Falling back to basic image generation...")
            return generate_basic_image(args.prompt, args.output, args.seed)
        
        print(f"Successfully generated image at {args.output}")
        return True
    except Exception as e:
        print(f"Error running Flux AI: {e}")
        print("Falling back to basic image generation...")
        return generate_basic_image(args.prompt, args.output, args.seed)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python
"""
Direct Flux AI Generator

This script provides a direct interface to the Flux AI pipeline for image generation.
It's designed to be run in the flux conda environment and handles the generation process
with proper error handling and resource management.
"""

import os
import sys
import argparse
from pathlib import Path

# Add Flux project path to sys.path
FLUX_PROJECT_PATH = r"K:\Self Projects\Flux_Ai\flux_pipeline"
if os.path.exists(FLUX_PROJECT_PATH):
    sys.path.append(FLUX_PROJECT_PATH)
else:
    print(f"Error: Flux AI project path not found at {FLUX_PROJECT_PATH}")
    sys.exit(1)

try:
    # Import Flux AI components
    from pipeline.flux_pipeline import FluxPipeline
    from core.seed_manager import SeedProfile
    print("Successfully imported Flux AI components")
except ImportError as e:
    print(f"Error importing Flux AI components: {e}")
    sys.exit(1)

def generate_image(prompt, output_path, seed=None):
    """Generate an image using the Flux AI pipeline.
    
    Args:
        prompt (str): Text prompt for image generation
        output_path (str): Path to save the generated image
        seed (int, optional): Random seed for reproducibility
        
    Returns:
        bool: True if image generation was successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize workspace
        workspace = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # Initialize pipeline with memory management
        pipeline = FluxPipeline(
            model_id="black-forest-labs/FLUX.1-schnell",
            memory_threshold=0.90,
            max_retries=3,
            enable_xformers=False,
            use_fast_tokenizer=True,
            workspace=workspace,
        )
        
        print("Initializing Flux AI pipeline...")
        
        # Load model
        if not pipeline.load_model():
            print("Failed to load Flux AI model")
            return False
        
        print("Model loaded successfully, generating image...")
        
        # Set up generation parameters with balanced quality and memory usage
        params = {
            "prompt": prompt,
            "num_inference_steps": 4,  # Standard quality setting
            "guidance_scale": 0.0,
            "height": 512,  # Reduced from 1024 to save memory
            "width": 512,   # Reduced from 1024 to save memory
            "seed_profile": SeedProfile.BALANCED,
            "output_path": output_path
        }
        
        # Add seed if provided
        if seed is not None:
            params["seed"] = seed
        
        # Generate image
        image, used_seed = pipeline.generate_image(**params)
        
        if image:
            print(f"Image generated successfully with seed {used_seed}")
            print(f"Saved to {output_path}")
            return True
        else:
            print("Failed to generate image")
            return False
            
    except Exception as e:
        print(f"Error during image generation: {e}")
        return False
    finally:
        # Clean up resources
        if 'pipeline' in locals() and pipeline is not None:
            if hasattr(pipeline, 'pipe') and pipeline.pipe is not None:
                del pipeline.pipe
        
        # Force garbage collection
        import gc
        import torch
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        gc.collect()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate images using Flux AI')
    parser.add_argument('--prompt', required=True, help='Text prompt for image generation')
    parser.add_argument('--output', required=True, help='Output path for the generated image')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    args = parser.parse_args()
    
    # Generate image
    success = generate_image(args.prompt, args.output, args.seed)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

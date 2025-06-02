"""
Interactive image generation using the FluxPipeline.

This script provides an interactive interface for generating images using the FluxPipeline. It allows users to input prompts, select seed profiles, and specify generation parameters. The script handles memory management, error handling, and performance logging.
"""

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import time
from datetime import datetime
from typing import Any, Dict
import json
import sys
import torch

from pathlib import Path
from config.env_config import setup_environment, ensure_environment
from pipeline.flux_pipeline import FluxPipeline
from core.seed_manager import SeedProfile
from utils.system_utils import setup_workspace, suppress_warnings
from config.logging_config import logger


class InteractiveGenerator:
    def __init__(self):
        """
        Initialize the InteractiveGenerator.

        This method sets up the environment, suppresses warnings, initializes the workspace, and creates an instance of the FluxPipeline.
        """
        # Setup environment and CUDA settings
        setup_environment()
        suppress_warnings()
        self.workspace = setup_workspace()

        # Set CUDA memory settings
        if torch.cuda.is_available():
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

        # Initialize pipeline
        self.pipeline = FluxPipeline(
            model_id="black-forest-labs/FLUX.1-schnell",
            memory_threshold=0.90,
            max_retries=3,
            enable_xformers=False,
            use_fast_tokenizer=True,
            workspace=self.workspace,
        )

        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)

    def get_user_input(self):
        """
        Get user input for image generation parameters.

        This method prompts the user to input a prompt, select a seed profile, and specify additional generation parameters such as the number of steps and guidance scale.

        Returns:
            A dictionary containing the user input parameters.
        """
        print("\n=== Image Generation Parameters ===")

        prompt = input("\nEnter your prompt (or 'quit' to exit): ")
        if prompt.lower() == "quit":
            return None

        print("\nSelect seed profile:")
        print("1. Conservative (stable results)")
        print("2. Balanced (default)")
        print("3. Experimental (unique results)")
        print("4. Full Range (maximum variation)")
        print("5. Use manual seed")

        profile_choice = input("Enter choice (1-5) [2]: ").strip() or "2"

        seed = None
        if profile_choice == "5":
            while True:
                try:
                    seed_input = input("Enter seed value (or press Enter for random): ")
                    if not seed_input:
                        break
                    seed = int(seed_input)
                    if seed < 0:
                        seed = abs(seed)
                        print(f"Converted negative seed to positive: {seed}")
                    break
                except ValueError:
                    print("Please enter a valid number or press Enter for random seed.")

        # Get additional parameters with validation
        try:
            steps = int(input("\nEnter number of steps (4-50) [4]: ") or "4")
            steps = max(4, min(50, steps))
        except ValueError:
            steps = 4
            print("Invalid steps value, using default: 4")

        try:
            guidance = float(
                input("\nEnter guidance scale (0.0-20.0) [0.0]: ") or "0.0"
            )
            guidance = max(0.0, min(20.0, guidance))
        except ValueError:
            guidance = 0.0
            print("Invalid guidance value, using default: 0.0")

        profile_map = {
            "1": SeedProfile.CONSERVATIVE,
            "2": SeedProfile.BALANCED,
            "3": SeedProfile.EXPERIMENTAL,
            "4": SeedProfile.FULL_RANGE,
            "5": SeedProfile.BALANCED,
        }

        return {
            "prompt": prompt,
            "profile": profile_map.get(profile_choice, SeedProfile.BALANCED),
            "manual_seed": seed,
            "num_inference_steps": steps,
            "guidance_scale": guidance,
        }

    def generate_with_memory_management(self, params):
        """
        Generate an image with enhanced memory management.

        This method handles memory cleanup before and after image generation, uses autocast for performance optimization, and logs performance metrics.

        Args:
            params: A dictionary containing the generation parameters.

        Returns:
            The generated image or None if generation fails.
        """
        try:
            # Pre-generation cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = (
                f"generation_{timestamp}_seed{params.get('manual_seed', 'random')}.png"
            )
            output_path = self.output_dir / output_filename

            # Performance tracking
            start_time = time.time()

            # Generate with proper autocast
            with torch.inference_mode(), torch.amp.autocast(
                device_type="cuda" if torch.cuda.is_available() else "cpu"
            ):
                image = self.pipeline.generate_image(
                    prompt=params["prompt"],
                    seed_profile=params["profile"],
                    seed=params["manual_seed"],
                    guidance_scale=params["guidance_scale"],
                    num_inference_steps=params["num_inference_steps"],
                    height=1024,
                    width=1024,
                    output_path=str(output_path),  # Add output path
                )

            if image:
                # Log success and performance metrics
                generation_time = time.time() - start_time
                logger.info(f"\nImage generated successfully! Saved to: {output_path}")
                logger.info(f"Generation time: {generation_time:.2f}s")

                # Save performance metrics
                self._log_generation_metrics(params, generation_time, output_path)

                if torch.cuda.is_available():
                    mem_allocated = torch.cuda.memory_allocated() / 1e9
                    mem_reserved = torch.cuda.memory_reserved() / 1e9
                    logger.debug(f"Memory allocated: {mem_allocated:.2f} GB")
                    logger.debug(f"Memory reserved: {mem_reserved:.2f} GB")
            else:
                logger.error("Failed to generate image.")

            return image

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

    def _log_generation_metrics(
        self, params: Dict[str, Any], generation_time: float, output_path: Path
    ):
        """
        Log generation metrics to performance.log.

        Args:
            params: A dictionary containing the generation parameters.
            generation_time: The time taken to generate the image.
            output_path: The path where the generated image is saved.
        """
        perf_log_path = self.workspace / "logs" / "performance.log"
        perf_log_path.parent.mkdir(parents=True, exist_ok=True)

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "prompt": params["prompt"],
            "seed_profile": params["profile"].value,
            "seed": params.get("manual_seed", "random"),
            "steps": params["num_inference_steps"],
            "guidance_scale": params["guidance_scale"],
            "generation_time": generation_time,
            "output_path": str(output_path),
            "cuda_available": torch.cuda.is_available(),
        }

        if torch.cuda.is_available():
            metrics.update(
                {
                    "gpu_memory_allocated": f"{torch.cuda.memory_allocated() / 1e9:.2f}GB",
                    "gpu_memory_reserved": f"{torch.cuda.memory_reserved() / 1e9:.2f}GB",
                    "gpu_name": torch.cuda.get_device_name(0),
                }
            )

        with open(perf_log_path, "a") as f:
            f.write(f"{json.dumps(metrics)}\n")

    def run(self):
        """
        Main run loop with enhanced error handling and memory management.

        This method continuously prompts the user for input, generates images, and handles errors gracefully.
        """
        print("\nWelcome to the Flux Image Generator!")
        print("=====================================")

        if not self.pipeline.load_model():
            logger.error("Failed to load model. Exiting.")
            return

        while True:
            try:
                # Get parameters from user
                params = self.get_user_input()
                if params is None:
                    break

                # Generate image
                image = self.generate_with_memory_management(params)

                # Ask to continue
                if (
                    input("\nGenerate another image? (y/n) [y]: ").lower().strip()
                    == "n"
                ):
                    break

            except KeyboardInterrupt:
                print("\nOperation interrupted by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if input("\nContinue anyway? (y/n) [y]: ").lower().strip() == "n":
                    break
            finally:
                # Ensure cleanup
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()

        print("\nThank you for using Flux Image Generator!")


if __name__ == "__main__":
    try:
        generator = InteractiveGenerator()
        generator.run()
    except KeyboardInterrupt:
        print("\nGeneration interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)

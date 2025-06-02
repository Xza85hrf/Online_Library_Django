"""AI Image Generation Pipeline with integrated resource management.

This module provides a comprehensive pipeline for AI image generation with:
- Integrated memory management for GPU and system resources
- Prompt processing and optimization
- Seed management for reproducible generation
- Automatic error handling and recovery
- Generation parameter optimization
- Output management and metadata tracking

The pipeline automatically handles:
- Model loading and optimization
- Memory pressure monitoring
- Device selection and configuration
- Error recovery and retries
- Resource cleanup

Example:
    Basic usage:
    ```python
    from pipeline.flux_pipeline import FluxPipeline
    from core.seed_manager import SeedProfile
    
    # Initialize pipeline
    pipeline = FluxPipeline()
    
    # Load model
    if pipeline.load_model():
        # Generate image
        image, seed = pipeline.generate_image(
            prompt="A modern minimalist logo",
            num_inference_steps=4,
            guidance_scale=0.0,
            height=1024,
            width=1024,
            seed_profile=SeedProfile.BALANCED,
            output_path="output/logo.png"
        )
        
        if image:
            print(f"Image generated successfully with seed {seed}")
    ```

Note:
    The pipeline automatically manages resources and handles errors,
    making it suitable for both interactive and automated use cases.
"""

import gc
import inspect
import json
import os
import torch
import transformers
from pathlib import Path
from typing import Optional, Any, Dict, Union
from datetime import datetime

from core.memory_manager import MemoryManager
from core.prompt_manager import PromptManager
from core.seed_manager import SeedManager, SeedProfile
from utils.system_utils import (
    suppress_stdout,
    safe_import_flux,
    get_unique_filename,
)
from config.logging_config import logger
from config.env_config import DEFAULT_MODEL_CONFIG, GENERATION_DEFAULTS


class FluxPipeline:
    """Advanced AI image generation pipeline with integrated management systems.
    
    This class provides a complete pipeline for AI image generation with:
    - Memory management and optimization
    - Prompt processing and validation
    - Seed management for reproducibility
    - Automatic error handling and recovery
    - Output management and metadata tracking
    
    Attributes:
        memory_manager (MemoryManager): Handles memory optimization
        prompt_manager (PromptManager): Processes and validates prompts
        seed_manager (SeedManager): Manages generation seeds
        model_id (str): Identifier for the generation model
        max_retries (int): Maximum retry attempts for generation
        enable_xformers (bool): Whether to use xformers optimization
        use_fast_tokenizer (bool): Whether to use fast tokenizer
        workspace (Path): Working directory for outputs
        output_dir (Path): Directory for generated images
        pipe: The underlying generation pipeline
        model_capabilities (Dict): Available model features
        generation_config (Dict): Generation parameters
    
    Example:
        ```python
        pipeline = FluxPipeline(
            model_id="black-forest-labs/FLUX.1-schnell",
            memory_threshold=0.90,
            max_retries=3
        )
        
        if pipeline.load_model():
            image, seed = pipeline.generate_image(
                prompt="A futuristic cityscape",
                num_inference_steps=4
            )
        ```
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_CONFIG["model_id"],
        memory_threshold: float = DEFAULT_MODEL_CONFIG["memory_threshold"],
        max_retries: int = DEFAULT_MODEL_CONFIG["max_retries"],
        enable_xformers: bool = DEFAULT_MODEL_CONFIG["enable_xformers"],
        use_fast_tokenizer: bool = DEFAULT_MODEL_CONFIG["use_fast_tokenizer"],
        max_prompt_tokens: int = DEFAULT_MODEL_CONFIG["max_prompt_tokens"],
        workspace: Optional[Path] = None,
    ):
        """Initialize the pipeline with specified configuration.
        
        Args:
            model_id (str, optional): Model identifier. Defaults to config value.
            memory_threshold (float, optional): Memory usage threshold. Defaults to 0.90.
            max_retries (int, optional): Maximum generation retries. Defaults to 3.
            enable_xformers (bool, optional): Use xformers optimization. Defaults to False.
            use_fast_tokenizer (bool, optional): Use fast tokenizer. Defaults to True.
            max_prompt_tokens (int, optional): Maximum prompt length. Defaults to 77.
            workspace (Optional[Path], optional): Working directory. Defaults to None.
        """
        # Initialize management systems
        self.memory_manager = MemoryManager(memory_threshold)
        self.prompt_manager = PromptManager(max_tokens=max_prompt_tokens)
        self.seed_manager = SeedManager()

        # Store configuration
        self.model_id = model_id
        self.max_retries = max_retries
        self.enable_xformers = enable_xformers
        self.use_fast_tokenizer = use_fast_tokenizer

        # Setup workspace directories
        self.workspace = workspace or Path.cwd()
        self.output_dir = self.workspace / "outputs" / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize pipeline components
        self.pipe = None
        self.model_capabilities = {}
        self.generation_config = self._initialize_generation_config()

    def _initialize_generation_config(self) -> Dict[str, Any]:
        """Initialize default generation configuration.
        
        Returns:
            Dict[str, Any]: Default generation parameters
        """
        return {
            "default_steps": GENERATION_DEFAULTS["default_steps"],
            "default_guidance": GENERATION_DEFAULTS["guidance_scale"],
            "min_height": 512,
            "min_width": 512,
            "max_height": 1024,
            "max_width": 1024,
            "supported_features": set(),
        }

    def load_model(self) -> bool:
        """Load and optimize the generation model.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        
        Example:
            ```python
            pipeline = FluxPipeline()
            if pipeline.load_model():
                print("Model loaded successfully")
            else:
                print("Failed to load model")
            ```
        """
        logger.info("Loading model with optimizations...")
        try:
            # Clear memory before loading
            self.memory_manager.cleanup()
            torch.cuda.empty_cache()
            gc.collect()

            # Import pipeline safely
            FluxPipeline, error = safe_import_flux()
            if error:
                logger.error(f"Failed to import FluxPipeline: {error}")
                return False

            # Configure logging
            transformers.logging.set_verbosity_error()

            # Configure model loading
            if torch.cuda.is_available():
                # GPU configuration
                load_config = {
                    "torch_dtype": torch.float16,
                    "use_safetensors": True,
                    "use_fast_tokenizer": self.use_fast_tokenizer,
                    "device_map": "balanced",
                }

                # Set memory optimization
                if "PYTORCH_CUDA_ALLOC_CONF" not in os.environ:
                    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

                logger.info("Loading model to GPU...")
                with suppress_stdout():
                    self.pipe = FluxPipeline.from_pretrained(
                        self.model_id, **load_config
                    )

                # Apply post-load optimizations
                if hasattr(self.pipe, "enable_attention_slicing"):
                    self.pipe.enable_attention_slicing("max")
                    logger.info("Enabled maximum attention slicing")

            else:
                # CPU fallback configuration
                load_config = {
                    "torch_dtype": torch.float32,
                    "use_safetensors": True,
                    "use_fast_tokenizer": self.use_fast_tokenizer,
                }

                logger.info("Loading model to CPU...")
                with suppress_stdout():
                    self.pipe = FluxPipeline.from_pretrained(
                        self.model_id, **load_config
                    )

            # Check model features
            self._check_model_capabilities()

            return True

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self._cleanup_after_error()
            return False

    def _check_model_capabilities(self):
        """Check and log available model features."""
        if self.pipe is None:
            return

        try:
            # Check available features
            self.model_capabilities = {
                "negative_prompt": hasattr(self.pipe, "negative_prompt"),
                "height_width": True,
                "guidance_scale": True,
                "num_inference_steps": True,
                "max_sequence_length": True,
                "generator": True,
                "attention_slicing": hasattr(self.pipe, "enable_attention_slicing"),
                "xformers": hasattr(
                    self.pipe, "enable_xformers_memory_efficient_attention"
                ),
                "cpu_offload": hasattr(self.pipe, "enable_model_cpu_offload"),
            }

            # Log capabilities
            logger.info("\nModel capabilities detected:")
            for feature, supported in self.model_capabilities.items():
                symbol = "[+]" if supported else "[-]"
                logger.info(f"  {feature}: {symbol}")

        except Exception as e:
            logger.warning(f"Error checking capabilities: {str(e)}")

    def _apply_optimizations(self):
        """Apply performance optimizations to the model."""
        if self.pipe is None:
            return

        try:
            # Clear memory before optimizing
            torch.cuda.empty_cache()
            gc.collect()

            if torch.cuda.is_available():
                # Configure attention optimization
                if hasattr(self.pipe, "enable_attention_slicing"):
                    chunk_size = self._get_optimal_chunk_size()
                    self.pipe.enable_attention_slicing(chunk_size)
                    logger.info(
                        f"Enabled attention slicing with chunk size {chunk_size}"
                    )

            # Check memory pressure
            if self.memory_manager.get_system_memory_info()["status"] == "critical":
                self._enable_memory_efficient_settings()

        except Exception as e:
            logger.warning(f"Error during optimization: {str(e)}")

    def _get_optimal_chunk_size(self) -> int:
        """Calculate optimal attention chunk size based on GPU memory.
        
        Returns:
            int: Optimal chunk size for attention slicing
        """
        try:
            if not torch.cuda.is_available():
                return 1

            # Get GPU memory capacity
            total_memory = torch.cuda.get_device_properties(0).total_memory
            # Scale chunk size based on available memory
            if total_memory >= 16 * (1024**3):  # 16GB or more
                return 2
            elif total_memory >= 8 * (1024**3):  # 8GB or more
                return 1
            else:
                return 1
        except:
            return 1

    def _enable_memory_efficient_settings(self):
        """Enable memory optimization settings."""
        try:
            if hasattr(self.pipe, "enable_model_cpu_offload"):
                # Reset device mapping
                if hasattr(self.pipe, "device_map"):
                    self.pipe.device_map = None
                if hasattr(self.pipe, "_hf_hook"):
                    self.pipe._hf_hook = None

                # Enable CPU offloading
                self.pipe.enable_model_cpu_offload()
                logger.info("Enabled CPU offloading for memory efficiency")

            # Additional GPU optimizations
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                if hasattr(torch.cuda, "memory_stats"):
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.reset_accumulated_memory_stats()

        except Exception as e:
            logger.warning(f"Error enabling memory efficient settings: {str(e)}")

    def _prepare_generation_params(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Prepare parameters for image generation.
        
        Args:
            prompt (str): Generation prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Dict[str, Any]: Prepared generation parameters
        """
        # Set base parameters
        params = {
            "prompt": prompt,
            "num_inference_steps": kwargs.get(
                "num_inference_steps", self.generation_config["default_steps"]
            ),
            "guidance_scale": kwargs.get(
                "guidance_scale", self.generation_config["default_guidance"]
            ),
            "height": kwargs.get("height", 1024),
            "width": kwargs.get("width", 1024),
        }

        # Add seed-based generator if provided
        if "seed" in kwargs:
            params["generator"] = torch.Generator(
                device=self.memory_manager.device
            ).manual_seed(kwargs["seed"])

        # Add negative prompt if supported
        if (
            self.model_capabilities.get("negative_prompt", False)
            and "negative_prompt" in kwargs
        ):
            processed_negative = self.prompt_manager.process_negative_prompt(
                kwargs["negative_prompt"]
            )
            if processed_negative:
                params["negative_prompt"] = processed_negative

        return params

    def generate_image(
        self,
        prompt: str,
        num_inference_steps: int = 4,
        guidance_scale: float = 0.0,
        height: int = 1024,
        width: int = 1024,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        seed_profile: Optional[SeedProfile] = None,
    ) -> Optional[tuple[Any, int]]:
        """Generate an image with the specified parameters.
        
        Args:
            prompt (str): Generation prompt
            num_inference_steps (int, optional): Number of generation steps. Defaults to 4.
            guidance_scale (float, optional): Guidance scale. Defaults to 0.0.
            height (int, optional): Image height. Defaults to 1024.
            width (int, optional): Image width. Defaults to 1024.
            seed (Optional[int], optional): Generation seed. Defaults to None.
            negative_prompt (Optional[str], optional): Negative prompt. Defaults to None.
            output_path (Optional[str], optional): Save path. Defaults to None.
            seed_profile (Optional[SeedProfile], optional): Seed profile. Defaults to None.
            
        Returns:
            Optional[tuple[Any, int]]: Generated image and used seed, or None if failed
        
        Example:
            ```python
            image, seed = pipeline.generate_image(
                prompt="A serene landscape",
                num_inference_steps=4,
                seed_profile=SeedProfile.BALANCED
            )
            if image:
                print(f"Generated with seed: {seed}")
            ```
        """
        if self.pipe is None:
            logger.error("Model not loaded. Please call load_model() first.")
            return None, None

        try:
            # Configure seed generation
            if seed_profile:
                self.seed_manager.set_profile(seed_profile)

            # Get generation seed
            if seed is not None:
                generation_seed = self.seed_manager._validate_seed(seed)
            else:
                generation_seed = self.seed_manager.generate_seed()

            # Process prompt
            processed_prompt = self.prompt_manager.process_prompt(prompt)
            if not processed_prompt:
                logger.error("Invalid or empty prompt after processing")
                return None, generation_seed

            # Setup generation parameters
            generation_params = {
                "prompt": processed_prompt,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "height": height,
                "width": width,
            }

            # Configure seed
            if generation_seed is not None:
                generation_params["generator"] = torch.Generator(
                    device=self.memory_manager.device
                ).manual_seed(generation_seed)

            # Add negative prompt
            if negative_prompt:
                processed_negative = self.prompt_manager.process_negative_prompt(
                    negative_prompt
                )
                if processed_negative:
                    generation_params["negative_prompt"] = processed_negative

            # Optimize memory
            self.memory_manager.optimize_memory_allocation()

            # Generation loop with retries
            for attempt in range(self.max_retries):
                try:
                    logger.info(
                        f"\nGeneration attempt {attempt + 1}/{self.max_retries}"
                    )
                    if generation_seed is not None:
                        logger.info(f"Using seed: {generation_seed}")

                    # Generate image
                    with torch.inference_mode():
                        with torch.amp.autocast(
                            "cuda" if torch.cuda.is_available() else "cpu"
                        ):
                            image = self.pipe(**generation_params).images[0]

                    # Save if path provided
                    if output_path:
                        output_path = Path(output_path)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        image.save(output_path)
                        logger.info(f"Image saved to {output_path}")

                    return image, generation_seed

                except RuntimeError as e:
                    if "out of memory" in str(e):
                        if attempt < self.max_retries - 1:
                            self._handle_oom_error()
                            continue
                    logger.error(
                        f"\nFailed after {self.max_retries} attempts: {str(e)}"
                    )
                    return None, generation_seed

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None, None
        finally:
            self.memory_manager.cleanup()

    def _handle_oom_error(self):
        """Handle out of memory errors during generation."""
        logger.warning("Handling out of memory error...")

        # Clear memory
        self.memory_manager.optimize_memory_allocation()
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

        # Configure memory growth
        if "PYTORCH_CUDA_ALLOC_CONF" not in os.environ:
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = (
                "expandable_segments:True,max_split_size_mb:512"
            )

        # Enable memory optimizations
        if hasattr(self.pipe, "enable_attention_slicing"):
            self.pipe.enable_attention_slicing("max")

    def _save_generation_output(
        self, image: Any, output_path: Path, params: Dict[str, Any]
    ):
        """Save generated image and metadata.
        
        Args:
            image (Any): Generated image
            output_path (Path): Save location
            params (Dict[str, Any]): Generation parameters
        """
        try:
            # Create output directory
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save image
            image.save(str(output_path), quality=95, optimize=True)

            # Save metadata
            metadata_path = output_path.with_suffix(".json")
            generation_info = {
                "timestamp": datetime.now().isoformat(),
                "prompt": params.get("prompt", ""),
                "seed": params.get("seed", "not_specified"),
                "num_inference_steps": params.get("num_inference_steps", 4),
                "guidance_scale": params.get("guidance_scale", 0.0),
                "height": params.get("height", 1024),
                "width": params.get("width", 1024),
                "negative_prompt": params.get("negative_prompt", None),
                "model_id": self.model_id,
                "device": str(self.memory_manager.device),
            }

            with open(metadata_path, "w") as f:
                json.dump(generation_info, f, indent=2)

            logger.info(f"Image saved to: {output_path}")
            logger.info(f"Metadata saved to: {metadata_path}")

        except Exception as e:
            logger.error(f"Error saving generation output: {str(e)}")

    def _cleanup_after_error(self):
        """Perform cleanup after error occurs."""
        try:
            if self.pipe is not None:
                # Move to CPU before deletion
                if hasattr(self.pipe, "to"):
                    self.pipe = self.pipe.to("cpu")
                del self.pipe
                self.pipe = None

            # Clear GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

            gc.collect()

        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")
        finally:
            self.memory_manager.cleanup()

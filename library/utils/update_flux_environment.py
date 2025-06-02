#!/usr/bin/env python
"""
Flux AI Environment Update Script

This script updates the Flux conda environment to ensure compatibility with the
required dependencies, particularly fixing the tokenizers version conflict.

Usage:
    python update_flux_environment.py

The script will:
1. Check if the flux conda environment exists
2. Update the tokenizers package to the required version
3. Verify the installation was successful
4. Provide detailed logs of the process
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flux_environment_update.log')
    ]
)
logger = logging.getLogger('flux_environment_updater')

def run_command(command, shell=False):
    """Run a command and return its output and return code.
    
    Args:
        command: Command to run (list or string)
        shell: Whether to run the command in a shell
        
    Returns:
        tuple: (stdout, stderr, return_code)
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            text=True
        )
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return "", str(e), 1

def check_conda_environment():
    """Check if the flux conda environment exists.
    
    Returns:
        bool: True if environment exists, False otherwise
    """
    logger.info("Checking if flux conda environment exists...")
    stdout, stderr, return_code = run_command(["conda", "env", "list"])
    
    if return_code != 0:
        logger.error(f"Error checking conda environments: {stderr}")
        return False
    
    if "flux" in stdout:
        logger.info("Flux conda environment found")
        return True
    else:
        logger.error("Flux conda environment not found")
        return False

def update_tokenizers():
    """Update the tokenizers package in the flux environment.
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    logger.info("Updating tokenizers package in flux environment...")
    
    # First try with pip
    cmd = ["conda", "run", "-n", "flux", "pip", "install", "tokenizers>=0.21,<0.22", "--force-reinstall"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.warning(f"Error updating tokenizers with pip: {stderr}")
        logger.info("Trying with conda install...")
        
        # Try with conda install
        cmd = ["conda", "install", "-n", "flux", "tokenizers>=0.21", "-c", "conda-forge", "-y"]
        stdout, stderr, return_code = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Error updating tokenizers with conda: {stderr}")
            return False
    
    logger.info("Tokenizers package updated successfully")
    return True

def update_transformers():
    """Update the transformers package in the flux environment.
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    logger.info("Updating transformers package in flux environment...")
    
    cmd = ["conda", "run", "-n", "flux", "pip", "install", "transformers", "--upgrade"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.warning(f"Error updating transformers: {stderr}")
        return False
    
    logger.info("Transformers package updated successfully")
    return True

def install_clip_dependencies():
    """Install CLIP model dependencies in the flux environment.
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    logger.info("Installing CLIP model dependencies...")
    
    # Install diffusers with all extras
    cmd = ["conda", "run", "-n", "flux", "pip", "install", "diffusers[torch]", "--upgrade"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.warning(f"Error installing diffusers: {stderr}")
        return False
    
    # Install transformers with CLIP support
    cmd = ["conda", "run", "-n", "flux", "pip", "install", "transformers[sentencepiece]", "--upgrade"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.warning(f"Error installing transformers with sentencepiece: {stderr}")
        return False
    
    # Install accelerate for better performance
    cmd = ["conda", "run", "-n", "flux", "pip", "install", "accelerate", "--upgrade"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.warning(f"Error installing accelerate: {stderr}")
        # Not critical, continue anyway
    
    logger.info("CLIP model dependencies installed successfully")
    return True

def verify_installation():
    """Verify that the required packages were installed correctly.
    
    Returns:
        bool: True if verification was successful, False otherwise
    """
    # Verify tokenizers installation
    logger.info("Verifying tokenizers installation...")
    
    cmd = ["conda", "run", "-n", "flux", "python", "-c", 
           "import tokenizers; print(f'Tokenizers version: {tokenizers.__version__}')"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"Error verifying tokenizers installation: {stderr}")
        return False
    
    if "Tokenizers version: " in stdout:
        version = stdout.strip().split("Tokenizers version: ")[1]
        logger.info(f"Tokenizers version {version} installed successfully")
        
        # Check if version meets requirements
        major, minor = map(int, version.split('.')[:2])
        if major == 0 and minor >= 21:
            logger.info("Tokenizers version meets requirements")
        else:
            logger.warning(f"Tokenizers version {version} does not meet requirements (>=0.21,<0.22)")
            return False
    else:
        logger.error("Could not determine tokenizers version")
        return False
    
    # Verify CLIP model availability
    logger.info("Verifying CLIP model availability...")
    
    cmd = ["conda", "run", "-n", "flux", "python", "-c", 
           "from transformers import CLIPTextModel; print('CLIP model available')"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"Error verifying CLIP model: {stderr}")
        return False
    
    if "CLIP model available" in stdout:
        logger.info("CLIP model is available")
    else:
        logger.error("CLIP model is not available")
        return False
    
    # Verify diffusers installation
    logger.info("Verifying diffusers installation...")
    
    cmd = ["conda", "run", "-n", "flux", "python", "-c", 
           "import diffusers; print(f'Diffusers version: {diffusers.__version__}')"]
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        logger.error(f"Error verifying diffusers installation: {stderr}")
        return False
    
    if "Diffusers version: " in stdout:
        version = stdout.strip().split("Diffusers version: ")[1]
        logger.info(f"Diffusers version {version} installed successfully")
    else:
        logger.error("Could not determine diffusers version")
        return False
    
    logger.info("All required packages verified successfully")
    return True

def main():
    """Main function to update the flux environment."""
    logger.info("Starting Flux environment update process...")
    
    # Check if flux environment exists
    if not check_conda_environment():
        logger.error("Cannot proceed without flux environment")
        return False
    
    # Update tokenizers package
    if not update_tokenizers():
        logger.error("Failed to update tokenizers package")
        return False
    
    # Update transformers package
    if not update_transformers():
        logger.warning("Failed to update transformers package, but continuing...")
    
    # Install CLIP dependencies
    if not install_clip_dependencies():
        logger.error("Failed to install CLIP dependencies")
        return False
    
    # Verify installation
    if not verify_installation():
        logger.error("Verification failed, required packages may not be properly installed")
        return False
    
    logger.info("Flux environment update completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nFlux environment updated successfully!")
        print("You can now use the advanced AI image generation without fallback.")
    else:
        print("\nFlux environment update failed.")
        print("Please check the logs for details and try again.")
    
    sys.exit(0 if success else 1)

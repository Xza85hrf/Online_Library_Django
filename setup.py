#!/usr/bin/env python
"""
Setup script for the Library Management System.
This script creates a virtual environment and installs all required dependencies.
"""
import os
import platform
import subprocess
import sys
from pathlib import Path

def create_venv():
    """Create a virtual environment if it doesn't exist."""
    if not Path("venv").exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        return True
    else:
        print("Virtual environment already exists.")
        return False

def activate_venv():
    """Return the activation command for the virtual environment."""
    if platform.system() == "Windows":
        return str(Path("venv") / "Scripts" / "activate.bat")
    else:
        return f"source {str(Path('venv') / 'bin' / 'activate')}"

def install_requirements():
    """Install requirements from requirements.txt."""
    print("Installing dependencies...")
    
    if platform.system() == "Windows":
        pip_path = str(Path("venv") / "Scripts" / "pip")
    else:
        pip_path = str(Path("venv") / "bin" / "pip")
    
    subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully!")

def main():
    """Main function to set up the environment."""
    print("=" * 50)
    print("Library Management System - Environment Setup")
    print("=" * 50)
    
    created = create_venv()
    
    # Print activation instructions
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate.bat"
    else:
        activate_cmd = "source venv/bin/activate"
    
    print(f"\nTo activate the environment manually, run: {activate_cmd}")
    
    # Install requirements if venv was just created or if forced
    if created or "--force" in sys.argv:
        if platform.system() == "Windows":
            # On Windows, we need to run a separate process with the activated environment
            subprocess.check_call(f"{activate_cmd} && pip install -r requirements.txt", shell=True)
        else:
            # On Unix, we can use source within a shell
            subprocess.check_call(f"{activate_cmd} && pip install -r requirements.txt", shell=True)
    
    print("\nSetup complete! You can now run the project using:")
    if platform.system() == "Windows":
        print("run_library.bat")
    else:
        print("python run_library.py")
    
    print("=" * 50)

if __name__ == "__main__":
    main()

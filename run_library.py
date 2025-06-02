#!/usr/bin/env python
"""
Library Management System Runner
This script provides an interactive menu to run various commands for the Library Management System.
"""
import os
import platform
import subprocess
import sys
from pathlib import Path

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def get_python_path():
    """Get the path to the Python executable in the virtual environment."""
    if platform.system() == "Windows":
        return str(Path("venv") / "Scripts" / "python")
    else:
        return str(Path("venv") / "bin" / "python")

def get_activate_cmd():
    """Get the command to activate the virtual environment."""
    if platform.system() == "Windows":
        return str(Path("venv") / "Scripts" / "activate.bat")
    else:
        return f"source {str(Path('venv') / 'bin' / 'activate')}"

def run_command(command, new_window=False):
    """Run a command in the virtual environment."""
    python_path = get_python_path()
    
    if new_window and platform.system() == "Windows":
        # For Windows, open a new command window
        full_cmd = f"start cmd /k \"{get_activate_cmd()} && {command}\""
        subprocess.call(full_cmd, shell=True)
    elif new_window and platform.system() == "Darwin":  # macOS
        # For macOS, open a new terminal window
        apple_script = f'tell application "Terminal" to do script "cd {os.getcwd()} && {get_activate_cmd()} && {command}"'
        subprocess.call(["osascript", "-e", apple_script])
    elif new_window and platform.system() == "Linux":
        # For Linux, try to detect the terminal
        if os.path.exists("/usr/bin/gnome-terminal"):
            subprocess.call(f"gnome-terminal -- bash -c \"cd {os.getcwd()} && {get_activate_cmd()} && {command}; exec bash\"", shell=True)
        elif os.path.exists("/usr/bin/xterm"):
            subprocess.call(f"xterm -e \"cd {os.getcwd()} && {get_activate_cmd()} && {command}; exec bash\"", shell=True)
        else:
            print("Could not detect terminal. Running in current window...")
            subprocess.call(f"{get_activate_cmd()} && {command}", shell=True)
    else:
        # Run in the current window
        subprocess.call(f"{get_activate_cmd()} && {command}", shell=True)

def check_venv():
    """Check if virtual environment exists and create it if it doesn't."""
    if not Path("venv").exists():
        print("Virtual environment not found. Setting up...")
        if platform.system() == "Windows":
            subprocess.call("setup_env.bat", shell=True)
        else:
            subprocess.call(["python", "setup.py"])
    else:
        print("Virtual environment found.")

def main_menu():
    """Display the main menu and handle user input."""
    while True:
        clear_screen()
        print("\nLibrary Management System")
        print("========================")
        print()
        print("1. Run development server")
        print("2. Setup database (migrate)")
        print("3. Create superuser")
        print("4. Collect static files")
        print("5. Run tests")
        print("6. Generate AI images (requires GPU)")
        print("7. Optimize library images")
        print("8. Exit")
        print()
        
        choice = input("Enter your choice (1-8): ")
        
        if choice == "1":
            print("Starting development server...")
            run_command("python manage.py runserver", new_window=True)
        elif choice == "2":
            print("Running migrations...")
            run_command("python manage.py makemigrations && python manage.py migrate")
            input("Press Enter to continue...")
        elif choice == "3":
            print("Creating superuser...")
            run_command("python manage.py createsuperuser")
            input("Press Enter to continue...")
        elif choice == "4":
            print("Collecting static files...")
            run_command("python manage.py collectstatic")
            input("Press Enter to continue...")
        elif choice == "5":
            print("Running tests...")
            run_command("python manage.py test")
            input("Press Enter to continue...")
        elif choice == "6":
            print("Generating AI images...")
            run_command("python manage.py generate_ai_images")
            input("Press Enter to continue...")
        elif choice == "7":
            print("Optimizing library images...")
            run_command("python manage.py optimize_library_images")
            input("Press Enter to continue...")
        elif choice == "8":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    print("=" * 50)
    print("Library Management System Launcher")
    print("=" * 50)
    
    check_venv()
    main_menu()

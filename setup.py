import os
import subprocess
import platform
import sys
from pathlib import Path

# Define color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Print ProtoNomia ASCII art
def print_banner():
    banner = f"""
{Colors.BLUE}██████╗ ██████╗  ██████╗ ████████╗ ██████╗ ███╗   ██╗ ██████╗ ███╗   ███╗██╗ █████╗ 
██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗████╗  ██║██╔═══██╗████╗ ████║██║██╔══██╗
██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║██╔██╗ ██║██║   ██║██╔████╔██║██║███████║
██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║██║╚██╗██║██║   ██║██║╚██╔╝██║██║██╔══██║
██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║ ╚████║╚██████╔╝██║ ╚═╝ ██║██║██║  ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝{Colors.ENDC}
                                                                                    
{Colors.GREEN}Cyberpunk Mars Economic Simulation{Colors.ENDC}
{Colors.BOLD}Setup Script{Colors.ENDC}
"""
    print(banner)

# Check if Python version is compatible
def check_python_version():
    print(f"{Colors.BLUE}[*] Checking Python version...{Colors.ENDC}")
    
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 9):
        print(f"{Colors.FAIL}[!] Python 3.9 or higher is required. You are using Python {major}.{minor}{Colors.ENDC}")
        return False
    
    print(f"{Colors.GREEN}[+] Python version {major}.{minor} is compatible{Colors.ENDC}")
    return True

# Check if required commands are available
def check_commands():
    print(f"{Colors.BLUE}[*] Checking required commands...{Colors.ENDC}")
    
    commands = ['pip', 'npm', 'ollama']
    missing = []
    
    for cmd in commands:
        try:
            subprocess.run([cmd, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            print(f"{Colors.GREEN}[+] {cmd} is installed{Colors.ENDC}")
        except FileNotFoundError:
            print(f"{Colors.WARNING}[!] {cmd} is not installed{Colors.ENDC}")
            missing.append(cmd)
    
    if missing:
        print(f"\n{Colors.FAIL}Missing required commands: {', '.join(missing)}{Colors.ENDC}")
        print("\nPlease install the missing dependencies:")
        if 'pip' in missing:
            print("  - pip: Install Python with pip (https://www.python.org/downloads/)")
        if 'npm' in missing:
            print("  - npm: Install Node.js with npm (https://nodejs.org/)")
        if 'ollama' in missing:
            print("  - ollama: Install Ollama (https://ollama.ai/)")
        return False
    
    return True

# Create virtual environment
def create_venv():
    print(f"{Colors.BLUE}[*] Creating virtual environment...{Colors.ENDC}")
    
    if os.path.exists('venv'):
        print(f"{Colors.WARNING}[!] Virtual environment already exists{Colors.ENDC}")
        return True
    
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print(f"{Colors.GREEN}[+] Virtual environment created successfully{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}[!] Failed to create virtual environment{Colors.ENDC}")
        return False

# Install Python dependencies
def install_python_deps():
    print(f"{Colors.BLUE}[*] Installing Python dependencies...{Colors.ENDC}")
    
    pip_cmd = 'venv/Scripts/pip' if platform.system() == 'Windows' else 'venv/bin/pip'
    
    try:
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        print(f"{Colors.GREEN}[+] Python dependencies installed successfully{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}[!] Failed to install Python dependencies{Colors.ENDC}")
        return False

# Setup the frontend
def setup_frontend():
    print(f"{Colors.BLUE}[*] Setting up frontend...{Colors.ENDC}")
    
    frontend_dir = Path('frontend/protonomia-ui')
    if not frontend_dir.exists():
        print(f"{Colors.WARNING}[!] Frontend directory not found{Colors.ENDC}")
        return False
    
    try:
        subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
        print(f"{Colors.GREEN}[+] Frontend dependencies installed successfully{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}[!] Failed to install frontend dependencies{Colors.ENDC}")
        return False

# Pull Ollama models
def pull_ollama_models():
    print(f"{Colors.BLUE}[*] Pulling Ollama models...{Colors.ENDC}")
    
    models = ['gemma:2b']
    success = True
    
    for model in models:
        try:
            print(f"Pulling {model}...")
            subprocess.run(['ollama', 'pull', model], check=True)
            print(f"{Colors.GREEN}[+] Successfully pulled {model}{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.FAIL}[!] Failed to pull {model}{Colors.ENDC}")
            success = False
    
    return success

# Create startup scripts
def create_startup_scripts():
    print(f"{Colors.BLUE}[*] Creating startup scripts...{Colors.ENDC}")
    
    # Backend startup script
    if platform.system() == 'Windows':
        with open('start_backend.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('call venv\\Scripts\\activate\n')
            f.write('cd api\n')
            f.write('uvicorn main:app --reload --host 0.0.0.0 --port 8000\n')
        
        with open('start_frontend.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('cd frontend\\protonomia-ui\n')
            f.write('npm run dev\n')
    else:
        with open('start_backend.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('source venv/bin/activate\n')
            f.write('cd api\n')
            f.write('uvicorn main:app --reload --host 0.0.0.0 --port 8000\n')
        
        with open('start_frontend.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('cd frontend/protonomia-ui\n')
            f.write('npm run dev\n')
        
        # Make scripts executable
        os.chmod('start_backend.sh', 0o755)
        os.chmod('start_frontend.sh', 0o755)
    
    print(f"{Colors.GREEN}[+] Startup scripts created successfully{Colors.ENDC}")
    return True

# Main setup function
def main():
    print_banner()
    
    print(f"{Colors.BOLD}Starting ProtoNomia setup...{Colors.ENDC}\n")
    
    if not check_python_version():
        return
    
    if not check_commands():
        return
    
    steps = [
        create_venv,
        install_python_deps,
        setup_frontend,
        pull_ollama_models,
        create_startup_scripts
    ]
    
    success = True
    for step in steps:
        if not step():
            success = False
            break
        print("")  # Add newline between steps
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}ProtoNomia setup completed successfully!{Colors.ENDC}")
        print("\nTo start the application:")
        
        if platform.system() == 'Windows':
            print("1. Run start_backend.bat")
            print("2. Run start_frontend.bat in another terminal")
        else:
            print("1. Run ./start_backend.sh")
            print("2. Run ./start_frontend.sh in another terminal")
        
        print("\nThen open http://localhost:3000 in your browser")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}ProtoNomia setup failed. Please check the errors above.{Colors.ENDC}")

if __name__ == "__main__":
    main()
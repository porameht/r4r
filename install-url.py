#!/usr/bin/env python3
"""
r4r - URL-based Installation Script
Can be executed directly from URL using: python3 <(curl -sSL URL)
"""

import os
import sys
import subprocess
import tempfile
import shutil
import platform
import urllib.request
import urllib.error
import json
from pathlib import Path

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def log_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.NC}")

def log_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

def log_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

def log_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")

def log_header(msg):
    print(f"{Colors.BLUE}🚀 {msg}{Colors.NC}")

def run_command(cmd, capture_output=True, text=True, check=True, **kwargs):
    """Run a command safely with error handling"""
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(cmd, capture_output=capture_output, text=text, check=check, **kwargs)
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            log_error(f"Command failed: {' '.join(cmd)}")
            if e.stderr:
                log_error(f"Error: {e.stderr.strip()}")
        raise
    except FileNotFoundError:
        log_error(f"Command not found: {cmd[0]}")
        raise

def check_python_version():
    """Check if Python version is adequate"""
    log_info("Checking Python version...")
    
    if sys.version_info < (3, 8):
        log_error(f"Python 3.8+ required. You have {sys.version}")
        log_info("Please upgrade Python from: https://www.python.org/downloads/")
        sys.exit(1)
    
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    log_success(f"Python {python_version} detected")
    return python_version

def check_internet_connectivity():
    """Check if we can reach PyPI"""
    log_info("Checking internet connectivity...")
    
    try:
        urllib.request.urlopen("https://pypi.org", timeout=5)
        log_success("Internet connectivity verified")
        return True
    except urllib.error.URLError:
        log_error("No internet connection or PyPI unreachable")
        return False

def detect_package_manager():
    """Detect available package managers"""
    log_info("Detecting package managers...")
    
    managers = {}
    
    # Check for uv
    try:
        result = run_command(["uv", "--version"])
        managers['uv'] = result.stdout.strip()
        log_success(f"uv detected: {managers['uv']}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for pip
    try:
        result = run_command([sys.executable, "-m", "pip", "--version"])
        managers['pip'] = result.stdout.strip()
        log_success(f"pip detected: {managers['pip']}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return managers

def install_uv():
    """Install uv package manager"""
    log_info("Installing uv package manager...")
    
    try:
        # Download and execute uv installer
        with urllib.request.urlopen("https://astral.sh/uv/install.sh") as response:
            install_script = response.read().decode('utf-8')
        
        # Execute the install script
        result = run_command(["sh", "-c", install_script], capture_output=False)
        
        # Try to add uv to PATH
        cargo_env = Path.home() / ".cargo" / "env"
        if cargo_env.exists():
            # Source cargo env to get uv in PATH
            cmd = f"source {cargo_env} && uv --version"
            result = run_command(["bash", "-c", cmd])
            log_success("uv installed successfully")
            return True
            
    except Exception as e:
        log_warning(f"Failed to install uv: {e}")
        return False

def install_r4r_with_uv():
    """Install r4r using uv"""
    log_info("Installing r4r using uv...")
    
    try:
        run_command(["uv", "tool", "install", "r4r"], capture_output=False)
        return True
    except subprocess.CalledProcessError:
        log_error("Failed to install r4r with uv")
        return False

def install_r4r_with_pip():
    """Install r4r using pip"""
    log_info("Installing r4r using pip...")
    
    try:
        run_command([sys.executable, "-m", "pip", "install", "r4r", "--user"], capture_output=False)
        return True
    except subprocess.CalledProcessError:
        log_error("Failed to install r4r with pip")
        return False

def verify_installation():
    """Verify that r4r was installed correctly"""
    log_info("Verifying installation...")
    
    # Try to run r4r command
    try:
        result = run_command(["r4r", "--version"])
        version = result.stdout.strip()
        log_success(f"r4r installed successfully! {version}")
        
        # Test help command
        run_command(["r4r", "--help"], capture_output=True)
        log_success("r4r CLI is working correctly")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_warning("r4r installed but not found in PATH")
        
        # Try to find r4r in common locations
        possible_paths = [
            Path.home() / ".local" / "bin" / "r4r",
            Path.home() / ".cargo" / "bin" / "r4r",
            Path("/usr/local/bin/r4r"),
        ]
        
        # Add user site packages bin to possible paths
        try:
            import site
            user_base = Path(site.getusersitepackages()).parent / "bin" / "r4r"
            possible_paths.append(user_base)
        except:
            pass
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                log_info(f"Found r4r at: {path}")
                log_info(f"Add this to your shell profile:")
                print(f"{Colors.YELLOW}export PATH=\"{path.parent}:$PATH\"{Colors.NC}")
                return False
        
        log_error("r4r not found in any expected location")
        return False

def show_quick_start():
    """Show quick start information"""
    print()
    log_header("🎯 Quick Start Guide")
    print(f"{Colors.GREEN}1. Get API key:{Colors.NC} https://dashboard.render.com/u/settings#api-keys")
    print(f"{Colors.GREEN}2. Login:{Colors.NC} r4r login")
    print(f"{Colors.GREEN}3. List services:{Colors.NC} r4r list")
    print(f"{Colors.GREEN}4. Deploy:{Colors.NC} r4r deploy myapp")
    print()
    
    log_header("📚 Essential Commands")
    print(f"""
{Colors.CYAN}Authentication:{Colors.NC}
  r4r login              # Login with API key
  r4r whoami             # Show current user info
  r4r logout             # Logout

{Colors.CYAN}Service Management:{Colors.NC}
  r4r list               # List all services
  r4r list --detailed    # Show detailed service info
  r4r info <name>        # Get service details
  r4r deploy <name>      # Deploy service
  r4r deploy <name> -c   # Deploy with cache clear
  r4r rebuild <name>     # Clear cache + deploy

{Colors.CYAN}Logs & Monitoring:{Colors.NC}
  r4r logs <name>        # View service logs
  r4r logs <name> -f     # Follow logs (stream)
  r4r deploys <name>     # List recent deployments

{Colors.CYAN}One-Off Jobs:{Colors.NC}
  r4r job <name> "command"     # Run a job
  r4r job <name> "cmd" --wait  # Run and wait
  r4r jobs <name>              # List recent jobs
  r4r status <job_id>          # Get job status
""")

def main():
    """Main installation function"""
    log_header("r4r (Render CLI) - URL Installer")
    print()
    
    # Check Python version
    python_version = check_python_version()
    
    # Check internet connectivity
    if not check_internet_connectivity():
        sys.exit(1)
    
    # Check if already installed
    try:
        result = run_command(["r4r", "--version"])
        current_version = result.stdout.strip()
        log_warning(f"r4r is already installed: {current_version}")
        print("Installation skipped. Use --force if you want to reinstall.")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # Not installed, continue
    
    # Detect package managers
    managers = detect_package_manager()
    
    installation_successful = False
    
    # Try uv first (if available or install it)
    if 'uv' in managers:
        log_info("Using existing uv installation")
        installation_successful = install_r4r_with_uv()
    elif install_uv():
        installation_successful = install_r4r_with_uv()
    
    # Fall back to pip if uv didn't work
    if not installation_successful and 'pip' in managers:
        log_info("Falling back to pip installation")
        installation_successful = install_r4r_with_pip()
    
    # If no package manager worked
    if not installation_successful:
        log_error("Installation failed with all available methods")
        log_info("Please install manually:")
        print("  1. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("  2. Install r4r: uv tool install r4r")
        print("  OR")
        print("  1. Use pip: python3 -m pip install r4r --user")
        sys.exit(1)
    
    # Verify installation
    success = verify_installation()
    
    # Show usage information
    show_quick_start()
    
    # Installation summary
    print()
    log_header("🚀 Installation Complete!")
    print()
    log_success("r4r is ready to use!")
    log_info("Run 'r4r --help' for full command reference")
    log_info("Visit https://github.com/your-username/r4r for documentation")
    
    print()
    log_info("Installation Summary:")
    print(f"  • Python: {python_version}")
    print(f"  • Platform: {platform.system()} {platform.machine()}")
    if success:
        print("  • Status: ✅ Ready to use")
        print()
        response = input(f"{Colors.YELLOW}Would you like to set up your API key now? (y/N): {Colors.NC}")
        if response.lower().startswith('y'):
            log_info("Starting login process...")
            try:
                subprocess.run(["r4r", "login"], check=True)
            except subprocess.CalledProcessError:
                log_error("Login failed")
        else:
            log_info("You can login later with: r4r login")
    else:
        print("  • Status: ⚠️  PATH configuration needed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Installation cancelled{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        log_info("Please report this issue at: https://github.com/your-username/r4r/issues")
        sys.exit(1)
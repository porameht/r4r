#!/usr/bin/env python3
"""
r4r - Super Easy Render CLI Installation Script

This script installs r4r using the most appropriate method available.
It tries uv first (fastest), then falls back to pip.
"""

import subprocess
import sys
import shutil

def run_command(cmd, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_command(cmd):
    """Check if a command is available."""
    return shutil.which(cmd.split()[0]) is not None

def install_with_uv():
    """Install r4r using uv."""
    print("🚀 Installing r4r using uv (fastest method)...")
    
    # Check if uv is installed
    if not check_command("uv"):
        print("📦 Installing uv first...")
        success, stdout, stderr = run_command("curl -LsSf https://astral.sh/uv/install.sh | sh")
        if not success:
            return False, f"Failed to install uv: {stderr}"
    
    # Install r4r with uv
    success, stdout, stderr = run_command("uv tool install r4r")
    if success:
        return True, "✅ Successfully installed r4r with uv!"
    else:
        return False, f"Failed to install r4r with uv: {stderr}"

def install_with_pip():
    """Install r4r using pip."""
    print("📦 Installing r4r using pip...")
    
    # Check if pip is available
    if not check_command("pip"):
        return False, "pip is not available on this system"
    
    # Install r4r with pip
    success, stdout, stderr = run_command("pip install r4r")
    if success:
        return True, "✅ Successfully installed r4r with pip!"
    else:
        return False, f"Failed to install r4r with pip: {stderr}"

def main():
    """Main installation function."""
    print("🎯 r4r - Super Easy Render CLI Installer")
    print("=" * 50)
    
    # Try uv first (fastest)
    success, message = install_with_uv()
    if success:
        print(message)
        print("\n🎉 Installation complete!")
        print("\n🚀 Quick start:")
        print("  r4r login          # Login with your Render API key")
        print("  r4r list --detailed # List your services")
        print("  r4r deploy myapp    # Deploy a service")
        print("  r4r logs myapp      # View logs")
        print("\n📚 Get help: r4r --help")
        return 0
    
    # Fallback to pip
    print(f"⚠️  uv installation failed: {message}")
    print("🔄 Trying pip installation...")
    
    success, message = install_with_pip()
    if success:
        print(message)
        print("\n🎉 Installation complete!")
        print("\n🚀 Quick start:")
        print("  r4r login          # Login with your Render API key")
        print("  r4r list --detailed # List your services")
        print("  r4r deploy myapp    # Deploy a service")
        print("  r4r logs myapp      # View logs")
        print("\n📚 Get help: r4r --help")
        return 0
    else:
        print(f"❌ pip installation failed: {message}")
        print("\n🔧 Manual installation options:")
        print("  1. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("     Then run: uv tool install r4r")
        print("  2. Use pip: pip install r4r")
        print("  3. Install from source: https://github.com/your-username/r4r")
        return 1

if __name__ == "__main__":
    sys.exit(main())
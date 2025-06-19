#!/usr/bin/env python3
"""
Test runner for r4r
"""

import sys
import subprocess
import argparse
from pathlib import Path

def main():
    """Run tests with various options"""
    parser = argparse.ArgumentParser(description="Run r4r tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("test_file", nargs="?", help="Specific test file to run")
    
    args = parser.parse_args()
    
    # Base command
    cmd = ["python", "-m", "pytest"]
    
    # Add coverage if requested
    if args.coverage:
        cmd = ["python", "-m", "coverage", "run", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add markers
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    
    # Add specific test file or all tests
    if args.test_file:
        cmd.append(args.test_file)
    else:
        cmd.append("tests/")
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    # Show coverage report if coverage was run
    if args.coverage and result.returncode == 0:
        print("\nGenerating coverage report...")
        subprocess.run(["python", "-m", "coverage", "report", "-m"])
        subprocess.run(["python", "-m", "coverage", "html"])
        print("HTML coverage report generated in htmlcov/")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
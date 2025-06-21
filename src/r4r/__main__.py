#!/usr/bin/env python3
"""
r4r CLI entry point for module execution.
This allows running: python -m r4r
"""

if __name__ == "__main__":
    from .cli import app
    app() 
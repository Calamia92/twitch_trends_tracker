#!/usr/bin/env python3
"""
Main entry point for Twitch Trends Tracker.

This script provides a clean interface to the CLI located in the presentation layer.
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import and run the CLI main function  
from src.presentation.cli.main import main

if __name__ == "__main__":
    main()
"""
Helper functions for the Ebook Image Optimiser application.
"""

import os
import sys
from pathlib import Path


def get_script_dir() -> Path:
    # Frozen executable (.exe)
    if getattr(sys, 'frozen', False):
        # Return the directory containing the executable
        return Path(sys.executable).resolve().parent

    # Regular script: __file__ is available
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:
        # Interactive or environments where __file__ is not defined
        return Path(os.getcwd()).resolve()

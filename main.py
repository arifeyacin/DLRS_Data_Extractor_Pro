"""
DLRS Data Extractor Pro
Enterprise Desktop Application Entry Point.

Author: Senior Python Software Engineer & Data Team
Version: 1.0.0
"""

import sys
import os

# Ensure Windows stdout supports UTF-8 Bengali characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.gui.main_window import MainWindow

def main():
    """Launch CustomTkinter Desktop GUI Application."""
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

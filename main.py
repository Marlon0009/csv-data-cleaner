"""
CSV Data Cleaner - Main Entry Point
====================================
Startet die Anwendung und initialisiert die GUI.
"""

import sys
from src.gui import DataCleanerApp


def main() -> None:
    """Startet die CSV Data Cleaner Anwendung."""
    app = DataCleanerApp()
    app.run()


if __name__ == "__main__":
    main()

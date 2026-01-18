"""
Smart-Ops-Term - AI Assisted Remote Terminal
Main entry point for the application.
v1.5.0: Multi-tab terminal window.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from views.multi_terminal_window import MultiTerminalWindow


def main():
    """
    Main entry point for Smart-Ops-Term application.
    """
    # Enable high DPI scaling
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Create application instance
    app = QApplication(sys.argv)
    app.setApplicationName("Smart-Ops-Term")
    app.setOrganizationName("SmartOps")

    # Create multi-terminal window
    window = MultiTerminalWindow()
    window.show()

    # Run event loop
    exit_code = app.exec()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()

"""
Smart-Ops-Term - AI Assisted Remote Terminal
Main entry point for the application.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from controllers.app_controller import AppController


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

    # Create and start controller
    controller = AppController()
    controller.start()

    # Run event loop
    exit_code = app.exec()

    # Cleanup
    controller.cleanup()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()

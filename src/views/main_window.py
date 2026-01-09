"""
Main application window - Split pane layout.
"""
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QSplitter,
                             QMenuBar, QStatusBar, QMessageBox, QDialog,
                             QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from views.terminal_widget import TerminalWidget
from views.chat_widget import AIChatWidget

# Load environment variables
load_dotenv()


class ConnectionDialog(QDialog):
    """Dialog for collecting SSH connection information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Connection")
        self._setup_ui()
        self._load_defaults()

    def _setup_ui(self):
        """Setup connection dialog UI."""
        layout = QVBoxLayout()

        # Host
        layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.1.10")
        layout.addWidget(self.host_input)

        # Port
        layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("22")
        self.port_input.setText("22")
        layout.addWidget(self.port_input)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("root")
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _load_defaults(self):
        """Load default values from .env file."""
        # Load from environment variables
        default_host = os.getenv('DEFAULT_HOST', '')
        default_port = os.getenv('DEFAULT_PORT', '22')
        default_user = os.getenv('DEFAULT_USER', '')

        # Set values if they exist
        if default_host:
            self.host_input.setText(default_host)
        if default_port:
            self.port_input.setText(default_port)
        if default_user:
            self.username_input.setText(default_user)

    def get_connection_info(self):
        """Return connection info as dictionary."""
        return {
            'host': self.host_input.text().strip(),
            'port': int(self.port_input.text().strip() or "22"),
            'username': self.username_input.text().strip(),
            'password': self.password_input.text()
        }


class MainWindow(QMainWindow):
    """
    Main application window with split pane layout.
    Left: Terminal widget
    Right: AI Chat widget
    """

    # Signals
    connect_requested = pyqtSignal(dict)  # Emitted when user wants to connect
    disconnect_requested = pyqtSignal()  # Emitted when user wants to disconnect

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()

    def _setup_ui(self):
        """Setup main window UI."""
        self.setWindowTitle("Smart-Ops-Term - AI Assisted Remote Terminal")
        # Remove minimum size restriction to allow Windows snap features
        self.setMinimumSize(800, 500)  # Smaller minimum to allow half-screen on small displays

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Terminal
        self.terminal_widget = TerminalWidget()
        splitter.addWidget(self.terminal_widget)

        # Right panel - AI Chat
        self.chat_widget = AIChatWidget()
        splitter.addWidget(self.chat_widget)

        # Set initial split ratio (60% terminal, 40% chat)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Connect action
        connect_action = QAction("&Connect...", self)
        connect_action.setShortcut(QKeySequence.StandardKey.Open)
        connect_action.setStatusTip("Connect to remote server via SSH")
        connect_action.triggered.connect(self._show_connection_dialog)
        file_menu.addAction(connect_action)

        # Disconnect action
        disconnect_action = QAction("&Disconnect", self)
        disconnect_action.setShortcut(QKeySequence.StandardKey.Close)
        disconnect_action.setStatusTip("Disconnect from server")
        disconnect_action.triggered.connect(self.disconnect_requested.emit)
        file_menu.addAction(disconnect_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Clear terminal action
        clear_terminal_action = QAction("Clear &Terminal", self)
        clear_terminal_action.setStatusTip("Clear terminal output")
        clear_terminal_action.triggered.connect(self.terminal_widget.clear_output)
        view_menu.addAction(clear_terminal_action)

        # Clear chat action
        clear_chat_action = QAction("Clear &Chat", self)
        clear_chat_action.setStatusTip("Clear chat history")
        clear_chat_action.triggered.connect(self.chat_widget.clear_chat)
        view_menu.addAction(clear_chat_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Smart-Ops-Term")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Press Ctrl+O to connect.")

    def _show_connection_dialog(self):
        """Show SSH connection dialog."""
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            conn_info = dialog.get_connection_info()
            if conn_info['host'] and conn_info['username']:
                self.connect_requested.emit(conn_info)
            else:
                QMessageBox.warning(self, "Connection Error",
                                    "Please provide host and username.")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Smart-Ops-Term",
                         "<h3>Smart-Ops-Term</h3>"
                         "<p>AI Assisted Remote Terminal</p>"
                         "<p>Version 0.1.0 (Phase 1)</p>"
                         "<p>An intelligent terminal emulator with AI assistance.</p>")

    def update_status(self, message, timeout=0):
        """
        Update status bar message.

        Args:
            message: Message to display
            timeout: Timeout in milliseconds (0 for permanent)
        """
        self.status_bar.showMessage(message, timeout)

    def show_connection_success(self, host):
        """Show success message when connected."""
        self.update_status(f"Connected to {host}", 5000)
        self.terminal_widget.set_connection_status(True)

    def show_connection_error(self, error_msg):
        """Show error message when connection fails."""
        QMessageBox.critical(self, "Connection Failed", error_msg)
        self.update_status("Connection failed")
        self.terminal_widget.set_connection_status(False)

    def show_disconnected(self):
        """Show message when disconnected."""
        self.update_status("Disconnected from server")
        self.terminal_widget.set_connection_status(False)

    def _show_connection_dialog(self):
        """Show SSH connection dialog."""
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            conn_info = dialog.get_connection_info()
            if conn_info['host'] and conn_info['username']:
                self.connect_requested.emit(conn_info)
            else:
                QMessageBox.warning(self, "Connection Error",
                                    "Please provide host and username.")

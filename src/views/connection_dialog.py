"""
SSH Connection dialog.
"""
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                             QDialogButtonBox)
from PyQt6.QtCore import Qt

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
        default_host = os.getenv('DEFAULT_HOST', '')
        default_port = os.getenv('DEFAULT_PORT', '22')
        default_user = os.getenv('DEFAULT_USER', '')

        if default_host:
            self.host_input.setText(default_host)
        if default_port:
            self.port_input.setText(default_port)
        if default_user:
            self.username_input.setText(default_user)

    def get_connection_info(self) -> dict:
        """Return connection info as dictionary."""
        return {
            'host': self.host_input.text().strip(),
            'port': int(self.port_input.text().strip() or "22"),
            'username': self.username_input.text().strip(),
            'password': self.password_input.text()
        }

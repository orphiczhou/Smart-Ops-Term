"""
Password input dialog for interactive SSH sessions.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt


class PasswordDialog(QDialog):
    """
    Modal dialog for password input.
    Used when SSH commands require interactive password entry.
    """

    def __init__(self, prompt_text="Enter password:", parent=None):
        super().__init__(parent)
        self.password = ""
        self._setup_ui(prompt_text)

    def _setup_ui(self, prompt_text):
        """Setup dialog UI."""
        self.setWindowTitle("Password Required")
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Prompt label
        prompt_label = QLabel(prompt_text)
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)

        # Password input field
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.returnPressed.connect(self.accept)
        layout.addWidget(self.password_input)

        # Buttons (horizontal layout)
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Push buttons to the right

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setMinimumWidth(80)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumWidth(80)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_password(self):
        """Get entered password."""
        return self.password_input.text()

    def accept(self):
        """Handle OK button click."""
        self.password = self.password_input.text()
        super().accept()

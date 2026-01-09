"""
Terminal widget - Left panel SSH terminal interface.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit,
                             QLabel, QFrame, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPalette, QTextBlockFormat


class TerminalWidget(QWidget):
    """
    Terminal display widget with output area and command input.
    Simulates a real terminal with black background and green text.
    """

    # Signal emitted when user enters a command
    command_sent = pyqtSignal(str)

    # Signal emitted when user clicks connect button
    connect_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_history = []  # Command history
        self.history_index = -1  # Current position in history
        self._setup_ui()

    def _setup_ui(self):
        """Setup terminal UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Terminal output display (read-only)
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFrameStyle(QFrame.Shape.NoFrame)

        # Set terminal-style appearance
        self._set_terminal_style()

        # Command input area with connect button
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)

        # Command input line
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Enter command here...")
        self._set_input_style()

        # Connect return key to send command
        self.input_line.returnPressed.connect(self._send_command)

        # Enable keyboard focus for input line
        self.input_line.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Connect button
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.connect_btn.clicked.connect(self.connect_requested.emit)

        # Add to input layout
        input_layout.addWidget(self.input_line, 1)  # Give input line more space
        input_layout.addWidget(self.connect_btn)

        # Add widgets to layout
        layout.addWidget(QLabel("Terminal Output:"))
        layout.addWidget(self.output_display)
        layout.addWidget(QLabel("Command Input:"))
        layout.addLayout(input_layout)

        self.setLayout(layout)

    def _set_terminal_style(self):
        """Apply terminal-like styling to output display."""
        # Set font to monospace
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.output_display.setFont(font)

        # Set black background with traditional green text
        # Note: HTML colors will override this default
        palette = self.output_display.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))  # Traditional terminal green
        self.output_display.setPalette(palette)

        # Auto-scroll setting
        self.output_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        # Reduce line spacing and paragraph spacing for tighter display
        document = self.output_display.document()
        document.setDocumentMargin(0)  # No margin

        # Set default text block format to reduce spacing
        cursor = self.output_display.textCursor()
        format = QTextBlockFormat()
        format.setLineHeight(100, 1)  # 1 = SingleHeight
        format.setTopMargin(0)
        format.setBottomMargin(0)
        cursor.setBlockFormat(format)

    def _set_input_style(self):
        """Apply styling to input line."""
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.input_line.setFont(font)

    def _send_command(self):
        """Send command from input line."""
        command = self.input_line.text().strip()
        if command:
            # Add to history (skip duplicates)
            if not self.command_history or self.command_history[-1] != command:
                self.command_history.append(command)

            # Reset history index
            self.history_index = len(self.command_history)

            # Emit signal
            self.command_sent.emit(command)
            self.input_line.clear()

    def append_output(self, text):
        """
        Append text to terminal output display.

        Args:
            text: Text to append
        """
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.output_display.setTextCursor(cursor)
        self.output_display.ensureCursorVisible()

    def append_output_html(self, html_text):
        """
        Append HTML-formatted text to terminal output display.
        Used for colored ANSI output.

        Args:
            html_text: HTML text to append
        """
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html_text)
        self.output_display.setTextCursor(cursor)
        self.output_display.ensureCursorVisible()


    def clear_output(self):
        """Clear terminal output display."""
        self.output_display.clear()

    def set_connection_status(self, connected):
        """
        Update UI based on connection status.

        Args:
            connected: True if connected, False otherwise
        """
        if connected:
            self.input_line.setEnabled(True)
            self.input_line.setPlaceholderText("Enter command here...")
            # Update connect button to show disconnect option
            self.connect_btn.setText("🔌 Disconnect")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton:pressed {
                    background-color: #c62828;
                }
            """)
        else:
            self.input_line.setEnabled(False)
            self.input_line.setPlaceholderText("Not connected")
            # Update connect button to show connect option
            self.connect_btn.setText("🔌 Connect")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196f3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #1976d2;
                }
                QPushButton:pressed {
                    background-color: #0d47a1;
                }
            """)

    def keyPressEvent(self, event):
        """
        Handle key press events.
        Phase 3: Enhanced with command history navigation.
        Focus input line when user starts typing.
        """
        from PyQt6.QtGui import QKeyEvent

        # If user types a printable character, focus input line
        if event.text() and event.text().isprintable():
            self.input_line.setFocus()
            self.input_line.keyPressEvent(event)
        else:
            # Handle Up/Down arrows for command history
            if event.key() == Qt.Key.Key_Up:
                self._navigate_history(up=True)
            elif event.key() == Qt.Key.Key_Down:
                self._navigate_history(up=False)
            else:
                super().keyPressEvent(event)

    def _navigate_history(self, up: bool):
        """
        Navigate command history.

        Args:
            up: True to go to previous command, False for next
        """
        if not self.command_history:
            return

        if up:
            # Go to previous command
            if self.history_index > 0:
                self.history_index -= 1
                self.input_line.setText(self.command_history[self.history_index])
        else:
            # Go to next command
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.input_line.setText(self.command_history[self.history_index])
            elif self.history_index == len(self.command_history) - 1:
                # Clear input if at the end
                self.history_index = len(self.command_history)
                self.input_line.clear()

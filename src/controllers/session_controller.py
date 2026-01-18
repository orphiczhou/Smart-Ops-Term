"""
Single session controller.
Manages one SSH session with its terminal and AI chat.
"""
from PyQt6.QtCore import QObject, pyqtSlot, QTimer
from typing import Optional
from models.ssh_handler import SSHHandler
from ai.ai_client import AIClient
from ai.context_manager import TerminalContext
from views.terminal_widget import TerminalWidget
from views.chat_widget import AIChatWidget
from utils.ansi_filter import ansi_to_html, strip_ansi
from config.constants import AppConstants
import re


class SessionController(QObject):
    """
    Single session controller - manages one SSH connection's complete lifecycle.
    Extracted from AppController to support multi-connection in v1.5.0.
    """

    def __init__(
        self,
        session_id: str,
        terminal: TerminalWidget,
        chat: AIChatWidget,
        ai_client: AIClient,
        parent=None
    ):
        super().__init__(parent)
        self.session_id = session_id
        self.terminal_widget = terminal
        self.chat_widget = chat
        self.ai_client = ai_client

        # SSH Handler
        self.ssh_handler: Optional[SSHHandler] = None

        # Context Manager
        self.terminal_context = TerminalContext(
            max_lines=AppConstants.TERMINAL_MAX_LINES,
            max_chars=AppConstants.TERMINAL_MAX_CHARS
        )

        # AI Feedback state
        self._waiting_for_ai_feedback = False
        self._ai_feedback_timer: Optional[QTimer] = None
        self._waiting_for_password = False

        # Password prompt patterns
        self._password_prompt_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in AppConstants.PASSWORD_PATTERNS
        ]

        # AI signal handlers (will be set in initialize)
        self._ai_response_handler = None
        self._ai_error_handler = None

    def initialize(self, ssh_handler: SSHHandler):
        """Initialize session with SSH handler."""
        self.ssh_handler = ssh_handler

        # Connect SSH signals
        self.ssh_handler.data_received.connect(self._on_data_received)
        self.ssh_handler.connection_lost.connect(self._on_connection_lost)
        self.ssh_handler.connection_established.connect(self._on_connection_established)

        # Connect terminal signals
        self.terminal_widget.command_sent.connect(self._handle_command_sent)

        # Connect AI chat signals
        self.chat_widget.message_sent.connect(self._handle_ai_message)
        self.chat_widget.command_execute_requested.connect(self._handle_command_execution)

        # Create unique AI signal handlers for this session
        # Use a wrapper to track which session should handle the response
        self._ai_response_handler = lambda resp: self._on_ai_response(resp)
        self._ai_error_handler = lambda err: self._on_ai_error(err)

        self.ai_client.response_received.connect(self._ai_response_handler)
        self.ai_client.error_occurred.connect(self._ai_error_handler)

    def connect_to_server(self, conn_info: dict) -> bool:
        """
        Connect to SSH server.

        Args:
            conn_info: Dictionary with host, port, username, password

        Returns:
            bool: True if connection initiated successfully
        """
        if not self.ssh_handler:
            return False

        success, message = self.ssh_handler.connect(
            host=conn_info['host'],
            port=conn_info['port'],
            username=conn_info['username'],
            password=conn_info['password'],
            timeout=AppConstants.SSH_TIMEOUT_SECONDS
        )

        return success

    def disconnect(self):
        """Disconnect from server."""
        if self.ssh_handler:
            self.ssh_handler.close()

    def _display_data(self, data: str) -> None:
        """Display data to terminal with HTML formatting."""
        html_data = ansi_to_html(data)
        self.terminal_widget.append_output_html(html_data)

    def _update_context(self, data: str) -> None:
        """Update terminal context manager."""
        clean_data = strip_ansi(data)
        self.terminal_context.append(clean_data)

    def _check_password_prompt(self, data: str) -> None:
        """Check if data contains password prompt."""
        if self._waiting_for_password:
            return

        clean_data = strip_ansi(data)
        for pattern in self._password_prompt_patterns:
            if pattern.search(clean_data):
                self._handle_password_prompt()
                break

    def _trigger_ai_feedback_if_needed(self) -> None:
        """Trigger AI feedback if waiting for command output."""
        if not self._waiting_for_ai_feedback:
            return

        if self._ai_feedback_timer:
            self._ai_feedback_timer.stop()

        self._ai_feedback_timer = QTimer()
        self._ai_feedback_timer.setSingleShot(True)
        self._ai_feedback_timer.timeout.connect(self._send_feedback_to_ai)
        self._ai_feedback_timer.start(AppConstants.AI_FEEDBACK_DELAY_MS)

    def _handle_error(self, location: str, error: Exception) -> None:
        """Handle and display error message."""
        error_msg = f"[ERROR] {location}: {str(error)}"
        self.chat_widget.append_system_message(error_msg)

    @pyqtSlot(str)
    def _on_data_received(self, data):
        """Handle data received from SSH server."""
        try:
            self._display_data(data)
            self._update_context(data)
            self._check_password_prompt(data)
            self._trigger_ai_feedback_if_needed()
        except Exception as e:
            self._handle_error("_on_data_received", e)

    @pyqtSlot()
    def _on_connection_established(self):
        """Handle successful connection."""
        if self.ssh_handler:
            self.terminal_widget.append_output(
                "\n=== Connected to SSH server ===\n"
                "You can now enter commands.\n"
                "Ask AI for help anytime!\n\n"
            )
            self.terminal_widget.set_connection_status(True)

    @pyqtSlot(str)
    def _on_connection_lost(self, reason):
        """Handle lost connection."""
        self.terminal_widget.append_output(
            f"\n=== Connection lost: {reason} ===\n"
        )
        self.terminal_widget.set_connection_status(False)

    @pyqtSlot(str)
    def _handle_command_sent(self, command):
        """Handle command sent from terminal widget."""
        # Cancel AI feedback if user manually enters a command
        if self._waiting_for_ai_feedback:
            self._waiting_for_ai_feedback = False
            if self._ai_feedback_timer:
                self._ai_feedback_timer.stop()
                self._ai_feedback_timer = None

        if self.ssh_handler and self.ssh_handler.is_connected:
            # Send command to server
            success, message = self.ssh_handler.send_command(command)
            if not success:
                self.terminal_widget.append_output(f"Error: {message}\n")
        else:
            self.terminal_widget.append_output(
                "Not connected to server. Please connect first.\n"
            )

    @pyqtSlot(str)
    def _handle_ai_message(self, message):
        """Handle message sent to AI assistant."""
        # Show thinking indicator
        self.chat_widget.show_thinking()

        # Get terminal context (unless in privacy mode)
        context = ""
        if not self.chat_widget.privacy_mode:
            context = self.terminal_context.get_context()

        # Ask AI asynchronously
        self.ai_client.ask_async(message, context)

    @pyqtSlot(str)
    def _handle_command_execution(self, command):
        """Handle command execution request from AI chat."""
        try:
            # Show execution indicator in terminal
            self.terminal_widget.append_output(
                f"\n🤖 Executing command from AI suggestion...\n"
            )

            # Set flag to indicate we're waiting for command output
            self._waiting_for_ai_feedback = True

            # Cancel any existing timer
            if self._ai_feedback_timer:
                self._ai_feedback_timer.stop()
                self._ai_feedback_timer = None

            # Send command directly to SSH handler
            if self.ssh_handler and self.ssh_handler.is_connected:
                success, message = self.ssh_handler.send_command(command)
                if not success:
                    self.terminal_widget.append_output(f"Error: {message}\n")
                    self._waiting_for_ai_feedback = False
            else:
                self.terminal_widget.append_output(
                    "Not connected to server. Please connect first.\n"
                )
                self._waiting_for_ai_feedback = False
        except Exception as e:
            self.chat_widget.append_system_message(f"[ERROR] {str(e)}")
            import traceback
            self.chat_widget.append_system_message(f"[ERROR] {traceback.format_exc()}")

    def _handle_password_prompt(self):
        """Handle password prompt from SSH server."""
        self._waiting_for_password = True

        # Create password dialog
        from views.password_dialog import PasswordDialog
        dialog = PasswordDialog("SSH requires password:", self.terminal_widget)

        # Show dialog and get password
        if dialog.exec():
            password = dialog.get_password()
            if password:
                # Send password to SSH server
                if self.ssh_handler and self.ssh_handler.is_connected:
                    self.ssh_handler.send_command(password)

        # Reset flag
        self._waiting_for_password = False

    def _send_feedback_to_ai(self):
        """Send terminal output back to AI for analysis."""
        try:
            if not self._waiting_for_ai_feedback:
                return

            # Reset the flag
            self._waiting_for_ai_feedback = False
            self._ai_feedback_timer = None

            # Show indicator in chat
            self.chat_widget.append_system_message(AppConstants.MSG_ANALYZING_OUTPUT)

            # Get recent terminal context
            context = self.terminal_context.get_context()

            # Send feedback to AI
            feedback_message = "以上是命令执行结果，请分析并继续下一步"

            # Show thinking indicator
            self.chat_widget.show_thinking()

            # Ask AI to analyze and continue
            self.ai_client.ask_async(feedback_message, context)
        except Exception as e:
            self.chat_widget.append_system_message(f"[ERROR] {str(e)}")
            import traceback
            self.chat_widget.append_system_message(f"[ERROR] {traceback.format_exc()}")

    @pyqtSlot(str)
    def _on_ai_response(self, response):
        """Handle AI response received."""
        self.chat_widget.append_ai_response(response)

    @pyqtSlot(str)
    def _on_ai_error(self, error_msg):
        """Handle AI error."""
        self.chat_widget.show_error(error_msg)

    def cleanup(self):
        """Cleanup session resources."""
        # Disconnect AI signals first to prevent crashes
        try:
            if self._ai_response_handler:
                self.ai_client.response_received.disconnect(self._ai_response_handler)
            if self._ai_error_handler:
                self.ai_client.error_occurred.disconnect(self._ai_error_handler)
        except:
            pass

        self._ai_response_handler = None
        self._ai_error_handler = None

        # Stop and cleanup timer
        if self._ai_feedback_timer:
            self._ai_feedback_timer.stop()
            self._ai_feedback_timer.deleteLater()
            self._ai_feedback_timer = None

        # Close SSH connection
        if self.ssh_handler:
            self.ssh_handler.close()
            self.ssh_handler = None

        # Clear terminal context
        if self.terminal_context:
            self.terminal_context.clear()

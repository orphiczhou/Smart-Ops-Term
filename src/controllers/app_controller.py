"""
Application controller - Coordinates between model, view, and AI.
Phase 2: Integrated with AI assistant functionality.
"""
from PyQt6.QtCore import QObject, pyqtSlot, QTimer
from models.ssh_handler import SSHHandler
from views.main_window import MainWindow
from views.password_dialog import PasswordDialog
from ai.ai_client import AIClient
from ai.context_manager import TerminalContext
from utils.ansi_filter import ansi_to_html, strip_ansi
from config.constants import AppConstants
import re


class AppController(QObject):
    """
    Main application controller that coordinates between
    the connection handler (model), main window (view), and AI assistant.
    """

    def __init__(self):
        super().__init__()
        self.ssh_handler = None
        self.main_window = None
        self.ai_client = None
        self.terminal_context = None
        self._waiting_for_ai_feedback = False  # Track if we're waiting for command output to send to AI
        self._ai_feedback_timer = None  # Timer to detect when command execution is complete
        self._waiting_for_password = False  # Track if we're waiting for password input
        self._password_prompt_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in AppConstants.PASSWORD_PATTERNS
        ]

    def start(self):
        """Initialize and start the application."""
        # Create AI client
        self.ai_client = AIClient()
        self.terminal_context = TerminalContext(
            max_lines=AppConstants.TERMINAL_MAX_LINES,
            max_chars=AppConstants.TERMINAL_MAX_CHARS
        )

        # Create main window
        self.main_window = MainWindow()

        # Connect signals from main window
        self.main_window.connect_requested.connect(self._handle_connect_request)
        self.main_window.disconnect_requested.connect(self._handle_disconnect_request)

        # Connect terminal command signal
        self.main_window.terminal_widget.command_sent.connect(self._handle_command_sent)
        self.main_window.terminal_widget.connect_requested.connect(self._handle_connect_button_click)

        # Connect AI chat signals
        self.main_window.chat_widget.message_sent.connect(self._handle_ai_message)
        self.main_window.chat_widget.command_execute_requested.connect(self._handle_command_execution)

        # Connect AI client signals
        self.ai_client.response_received.connect(self._on_ai_response)
        self.ai_client.error_occurred.connect(self._on_ai_error)

        # Check if AI is configured
        if not self.ai_client.is_configured():
            self.main_window.chat_widget.set_api_config_warning(True)

        # Show main window
        self.main_window.show()

    @pyqtSlot(dict)
    def _handle_connect_request(self, conn_info):
        """
        Handle connection request from UI.

        Args:
            conn_info: Dictionary with host, port, username, password
        """
        try:
            # Create SSH handler
            self.ssh_handler = SSHHandler()

            # Connect signals
            self.ssh_handler.data_received.connect(self._on_data_received)
            self.ssh_handler.connection_lost.connect(self._on_connection_lost)
            self.ssh_handler.connection_established.connect(self._on_connection_established)

            # Initiate connection
            self.main_window.update_status(f"Connecting to {conn_info['host']}...")
            success, message = self.ssh_handler.connect(
                host=conn_info['host'],
                port=conn_info['port'],
                username=conn_info['username'],
                password=conn_info['password'],
                timeout=AppConstants.SSH_TIMEOUT_SECONDS
            )

            if not success:
                # Connection failed
                self.main_window.show_connection_error(message)
                self.ssh_handler = None

        except Exception as e:
            self.main_window.show_connection_error(f"Unexpected error: {str(e)}")
            self.ssh_handler = None

    @pyqtSlot()
    def _handle_disconnect_request(self):
        """Handle disconnect request from UI."""
        if self.ssh_handler:
            self.ssh_handler.close()
            self.ssh_handler = None
            self.main_window.show_disconnected()

    @pyqtSlot(str)
    def _handle_command_sent(self, command):
        """
        Handle command sent from terminal widget.

        Args:
            command: Command string to send to server
        """
        # Cancel AI feedback if user manually enters a command
        if self._waiting_for_ai_feedback:
            self._waiting_for_ai_feedback = False
            if self._ai_feedback_timer:
                self._ai_feedback_timer.stop()
                self._ai_feedback_timer = None

        if self.ssh_handler and self.ssh_handler.is_connected:
            # Echo command to terminal display
            self.main_window.terminal_widget.append_output(f"$ {command}\n")

            # Send command to server
            success, message = self.ssh_handler.send_command(command)
            if not success:
                self.main_window.terminal_widget.append_output(f"Error: {message}\n")
        else:
            self.main_window.terminal_widget.append_output(
                "Not connected to server. Please connect first.\n"
            )

    @pyqtSlot()
    def _handle_connect_button_click(self):
        """Handle connect button click from terminal widget."""
        # If already connected, disconnect
        if self.ssh_handler and self.ssh_handler.is_connected:
            self._handle_disconnect_request()
        else:
            # Show connection dialog
            self.main_window._show_connection_dialog()

    @pyqtSlot(str)
    def _handle_ai_message(self, message):
        """
        Handle message sent to AI assistant.

        Args:
            message: User's question for AI
        """
        # Show thinking indicator
        self.main_window.chat_widget.show_thinking()

        # Get terminal context (unless in privacy mode)
        context = ""
        if not self.main_window.chat_widget.privacy_mode:
            context = self.terminal_context.get_context()

        # Ask AI asynchronously
        self.ai_client.ask_async(message, context)

    @pyqtSlot(str)
    def _handle_command_execution(self, command):
        """
        Handle command execution request from AI chat.
        Phase 3: Enhanced with status feedback and automatic AI feedback loop.

        Args:
            command: Command to execute in terminal
        """
        try:
            # Show execution indicator in terminal
            self.main_window.terminal_widget.append_output(
                f"\n🤖 Executing command from AI suggestion...\n"
            )

            # Set flag to indicate we're waiting for command output to send back to AI
            self._waiting_for_ai_feedback = True

            # Cancel any existing timer
            if self._ai_feedback_timer:
                self._ai_feedback_timer.stop()
                self._ai_feedback_timer = None

            # Send command directly to SSH handler (bypass _handle_command_sent to avoid flag reset)
            if self.ssh_handler and self.ssh_handler.is_connected:
                # Send command to server (SSH will echo it back automatically)
                success, message = self.ssh_handler.send_command(command)
                if not success:
                    self.main_window.terminal_widget.append_output(f"Error: {message}\n")
                    # Reset flag on error
                    self._waiting_for_ai_feedback = False
            else:
                self.main_window.terminal_widget.append_output(
                    "Not connected to server. Please connect first.\n"
                )
                # Reset flag if not connected
                self._waiting_for_ai_feedback = False
        except Exception as e:
            self.main_window.chat_widget.append_system_message(f"[ERROR] {str(e)}")
            import traceback
            self.main_window.chat_widget.append_system_message(f"[ERROR] {traceback.format_exc()}")

    def _display_data(self, data: str) -> None:
        """Display data to terminal with HTML formatting."""
        html_data = ansi_to_html(data)
        self.main_window.terminal_widget.append_output_html(html_data)

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
        self.main_window.chat_widget.append_system_message(error_msg)

    @pyqtSlot(str)
    def _on_data_received(self, data):
        """
        Handle data received from SSH server.
        Enhanced with automatic AI feedback loop and password prompt detection.

        Args:
            data: Text data received from server
        """
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
            self.main_window.show_connection_success("SSH Server")
            self.main_window.terminal_widget.append_output(
                "\n=== Connected to SSH server ===\n"
                "You can now enter commands.\n"
                "Ask AI for help anytime!\n\n"
            )

    def _handle_password_prompt(self):
        """Handle password prompt from SSH server."""
        self._waiting_for_password = True

        # Create password dialog
        dialog = PasswordDialog("SSH requires password:", self.main_window)

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
        """
        Send terminal output back to AI for analysis and next step.
        Called after command execution is complete.
        """
        try:
            if not self._waiting_for_ai_feedback:
                return

            # Reset the flag
            self._waiting_for_ai_feedback = False
            self._ai_feedback_timer = None

            # Show indicator in chat
            self.main_window.chat_widget.append_system_message(AppConstants.MSG_ANALYZING_OUTPUT)

            # Get recent terminal context
            context = self.terminal_context.get_context()

            # Send feedback to AI
            feedback_message = "以上是命令执行结果，请分析并继续下一步"

            # Show thinking indicator
            self.main_window.chat_widget.show_thinking()

            # Ask AI to analyze and continue
            self.ai_client.ask_async(feedback_message, context)
        except Exception as e:
            self.main_window.chat_widget.append_system_message(f"[ERROR] {str(e)}")
            import traceback
            self.main_window.chat_widget.append_system_message(f"[ERROR] {traceback.format_exc()}")

    @pyqtSlot(str)
    def _on_connection_lost(self, reason):
        """
        Handle lost connection.

        Args:
            reason: Reason for connection loss
        """
        self.main_window.terminal_widget.append_output(
            f"\n=== Connection lost: {reason} ===\n"
        )
        self.main_window.show_disconnected()
        self.ssh_handler = None

    @pyqtSlot(str)
    def _on_ai_response(self, response):
        """
        Handle AI response received.

        Args:
            response: AI's response text
        """
        # Remove thinking indicator and show response
        self.main_window.chat_widget.append_ai_response(response)

    @pyqtSlot(str)
    def _on_ai_error(self, error_msg):
        """
        Handle AI error.

        Args:
            error_msg: Error message
        """
        self.main_window.chat_widget.show_error(error_msg)

    def cleanup(self) -> None:
        """Cleanup all resources before exit."""
        # Stop and cleanup timer
        if self._ai_feedback_timer:
            self._ai_feedback_timer.stop()
            self._ai_feedback_timer.deleteLater()
            self._ai_feedback_timer = None

        # Close SSH connection
        if self.ssh_handler:
            self.ssh_handler.close()
            self.ssh_handler = None

        # Clear AI conversation history
        if self.ai_client:
            self.ai_client.clear_history()

        # Clear terminal context
        if self.terminal_context:
            self.terminal_context.clear()

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
    v1.6.1: 添加 AI 配置名称支持
    v1.6.1: 添加流式 AI 响应支持
    """

    def __init__(
        self,
        session_id: str,
        terminal: TerminalWidget,
        chat: AIChatWidget,
        ai_client: AIClient,
        ai_profile_name: Optional[str] = None,  # v1.6.1 新增
        parent=None
    ):
        super().__init__(parent)
        self.session_id = session_id
        self.terminal_widget = terminal
        self.chat_widget = chat
        self.ai_client = ai_client
        self.ai_profile_name = ai_profile_name  # v1.6.1 新增

        # v1.6.1: 如果指定了 AI 配置，设置到 AIClient
        if ai_profile_name:
            self.ai_client.set_profile(ai_profile_name)
            print(f"[DEBUG SessionController:{self.session_id}] Using AI profile: {ai_profile_name}")

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

        # 流式响应状态
        self._is_streaming = False
        self._stream_buffer = ""

    def initialize(self, ssh_handler: SSHHandler):
        """Initialize session with SSH handler."""
        self.ssh_handler = ssh_handler

        # Connect SSH signals
        self.ssh_handler.data_received.connect(self._on_data_received)
        self.ssh_handler.connection_lost.connect(self._on_connection_lost)
        self.ssh_handler.connection_established.connect(self._on_connection_established)

        # Connect terminal signals
        self.terminal_widget.command_sent.connect(self._handle_command_sent)

        # Note: AI chat signals are now connected in MultiTerminalWindow
        # to ensure proper signal routing for each session's AI client

        # Create unique AI signal handlers for this session
        # Use a wrapper to track which session should handle the response
        self._ai_response_handler = lambda resp: self._on_ai_response(resp)
        self._ai_error_handler = lambda err: self._on_ai_error(err)
        self._ai_stream_started_handler = lambda: self._on_stream_started()
        self._ai_stream_chunk_handler = lambda chunk: self._on_stream_chunk(chunk)
        self._ai_stream_finished_handler = lambda full: self._on_stream_finished(full)

        self.ai_client.response_received.connect(self._ai_response_handler)
        self.ai_client.error_occurred.connect(self._ai_error_handler)
        # 流式信号连接
        self.ai_client.stream_started.connect(self._ai_stream_started_handler)
        self.ai_client.stream_chunk_received.connect(self._ai_stream_chunk_handler)
        self.ai_client.stream_finished.connect(self._ai_stream_finished_handler)

    def connect_to_server(self, conn_info: dict) -> bool:
        """
        Connect to SSH server.

        Args:
            conn_info: Dictionary with host, port, username, password

        Returns:
            bool: True if connection initiated successfully
        """
        print(f"[DEBUG SessionController:{self.session_id}] connect_to_server called")
        print(f"[DEBUG SessionController:{self.session_id}] self.ssh_handler = {self.ssh_handler}")
        print(f"[DEBUG SessionController:{self.session_id}] conn_info = {conn_info}")

        if not self.ssh_handler:
            print("[DEBUG] self.ssh_handler is None, returning False")
            return False

        if not conn_info:
            print("[DEBUG] conn_info is None/empty, returning False")
            return False

        try:
            host = conn_info.get('host', '')
            port = conn_info.get('port', 22)
            username = conn_info.get('username', '')
            password = conn_info.get('password', '')

            print(f"[DEBUG] Calling ssh_handler.connect(host={host}, port={port}, username={username})")

            success, message = self.ssh_handler.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                timeout=AppConstants.SSH_TIMEOUT_SECONDS
            )
            print(f"[DEBUG] ssh_handler.connect returned: success={success}, message={message}")
            return success
        except Exception as e:
            import traceback
            print(f"[DEBUG] Exception during connect: {e}")
            self.terminal_widget.append_output(f"Connection error: {str(e)}\n")
            self.terminal_widget.append_output(f"{traceback.format_exc()}\n")
            return False

    def disconnect(self):
        """Disconnect from server."""
        if self.ssh_handler:
            self.ssh_handler.close()
            self.terminal_widget.set_connection_status(False)
            self.terminal_widget.append_output("\n=== Disconnected from server ===\n")

    def reconnect(self, conn_info: dict) -> bool:
        """Reconnect to server using stored connection info."""
        return self.connect_to_server(conn_info)

    def _display_data(self, data: str) -> None:
        """Display data to terminal with HTML formatting."""
        html_data = ansi_to_html(data)
        self.terminal_widget.append_output_html(html_data)

    def _update_context(self, data: str) -> None:
        """Update terminal context manager."""
        clean_data = strip_ansi(data)
        self.terminal_context.append(clean_data)

    def _check_password_prompt(self, data: str) -> None:
        """
        检查是否包含密码提示

        v1.6.1: 当检测到密码提示时，取消等待AI反馈，等待用户输入密码
        """
        if self._waiting_for_password:
            return

        clean_data = strip_ansi(data)
        for pattern in self._password_prompt_patterns:
            if pattern.search(clean_data):
                # 取消等待AI反馈，因为终端正在等待密码输入
                if self._waiting_for_ai_feedback:
                    self._waiting_for_ai_feedback = False
                    if self._ai_feedback_timer:
                        self._ai_feedback_timer.stop()
                        self._ai_feedback_timer = None
                    print(f"[DEBUG SessionController:{self.session_id}] Password prompt detected, canceling AI feedback wait")

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
            print(f"[DEBUG Session:{self.session_id}] Privacy Mode OFF - sending context ({len(context)} chars)", flush=True)
        else:
            print(f"[DEBUG Session:{self.session_id}] Privacy Mode ON - NOT sending context", flush=True)

        # Ask AI asynchronously
        self.ai_client.ask_async(message, context)

    def on_chat_message(self, message: str):
        """Public method to handle chat message from MultiTerminalWindow."""
        self._handle_ai_message(message)

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

    def on_command_execute(self, command: str):
        """Public method to handle command execution from MultiTerminalWindow."""
        self._handle_command_execution(command)

    def _handle_password_prompt(self):
        """
        处理来自SSH服务器的密码提示

        v1.6.1: 用户输入密码后，重新触发AI反馈等待
        """
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

                # v1.6.1: 重新触发AI反馈等待，因为密码输入后应该继续等待命令输出
                self._waiting_for_ai_feedback = True
                print(f"[DEBUG SessionController:{self.session_id}] Password sent, resuming AI feedback wait")

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
        """
        Handle AI response received (非流式模式，向后兼容).
        """
        self.chat_widget.append_ai_response(response)

    @pyqtSlot()
    def _on_stream_started(self):
        """处理流式响应开始。"""
        self._is_streaming = True
        self._stream_buffer = ""
        self.chat_widget.start_streaming_response()

    @pyqtSlot(str)
    def _on_stream_chunk(self, chunk: str):
        """处理流式响应内容块。"""
        if self._is_streaming:
            self._stream_buffer += chunk
            self.chat_widget.append_streaming_content(chunk)

    @pyqtSlot(str)
    def _on_stream_finished(self, full_response: str):
        """处理流式响应完成。"""
        if self._is_streaming:
            self._is_streaming = False
            self.chat_widget.finish_streaming_response(full_response)
            self._stream_buffer = ""

    @pyqtSlot(str)
    def _on_ai_error(self, error_msg):
        """Handle AI error."""
        self.chat_widget.show_error(error_msg)

    def on_ai_profile_changed(self, profile_name: str):
        """
        处理 AI profile 切换请求

        v1.6.1: 支持在会话中动态切换 AI 配置

        Args:
            profile_name: 新的 AI profile 名称
        """
        print(f"[DEBUG SessionController:{self.session_id}] AI profile change requested: {profile_name}")
        try:
            # 切换 AI client 的 profile
            self.ai_client.set_profile(profile_name)
            self.ai_profile_name = profile_name
            print(f"[DEBUG SessionController:{self.session_id}] AI profile switched to: {profile_name}")

            # 在聊天窗口显示提示消息
            self.chat_widget.append_system_message(f"已切换到 AI 配置: {profile_name}")

        except Exception as e:
            print(f"[DEBUG SessionController:{self.session_id}] Failed to switch AI profile: {e}")
            self.chat_widget.show_error(f"切换 AI 配置失败: {str(e)}")

    def cleanup(self):
        """Cleanup session resources."""
        # Disconnect AI signals first to prevent crashes
        try:
            if self._ai_response_handler:
                self.ai_client.response_received.disconnect(self._ai_response_handler)
            if self._ai_error_handler:
                self.ai_client.error_occurred.disconnect(self._ai_error_handler)
            # 断开流式信号连接
            if self._ai_stream_started_handler:
                self.ai_client.stream_started.disconnect(self._ai_stream_started_handler)
            if self._ai_stream_chunk_handler:
                self.ai_client.stream_chunk_received.disconnect(self._ai_stream_chunk_handler)
            if self._ai_stream_finished_handler:
                self.ai_client.stream_finished.disconnect(self._ai_stream_finished_handler)
        except:
            pass

        self._ai_response_handler = None
        self._ai_error_handler = None
        self._ai_stream_started_handler = None
        self._ai_stream_chunk_handler = None
        self._ai_stream_finished_handler = None

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

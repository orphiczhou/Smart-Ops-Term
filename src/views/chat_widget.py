"""
AI Chat widget - Right panel AI assistant interface.
Supports chat history, markdown rendering, and command suggestions.
"""
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit,
                             QLabel, QPushButton, QHBoxLayout,
                             QFrame, QSplitter, QCheckBox, QScrollArea,
                             QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QFont


class MessageBubble(QFrame):
    """
    A styled message bubble for chat interface.
    Supports left/right alignment and different colors for different senders.
    支持流式更新内容。
    """

    def __init__(self, sender: str, message: str, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.message = message
        self.message_label = None  # 保存引用以便更新
        self._setup_ui()

    def update_message(self, new_message: str):
        """
        更新消息内容（用于流式显示）

        Args:
            new_message: 新的完整消息内容
        """
        self.message = new_message
        if self.message_label:
            self.message_label.setText(new_message)

    def append_content(self, content: str):
        """
        追加内容到当前消息（用于流式显示）

        Args:
            content: 要追加的内容
        """
        self.message += content
        if self.message_label:
            self.message_label.setText(self.message)

    def _setup_ui(self):
        """Setup message bubble UI."""
        # Main layout with alignment
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 2, 0, 2)

        # Create content container
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        # Sender label
        sender_label = QLabel(self.sender)
        sender_label.setStyleSheet("font-weight: bold; font-size: 12px;")

        # Message content
        message_label = QLabel(self.message)
        self.message_label = message_label  # 保存引用以便流式更新
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)  # Enable HTML rendering
        message_label.setOpenExternalLinks(False)  # Don't open links automatically
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(sender_label)
        layout.addWidget(message_label)
        content_widget.setLayout(layout)

        # Style and alignment based on sender
        if self.sender == "You":
            # User message: Right align, light green background
            content_widget.setStyleSheet("""
                QWidget {
                    background-color: #d4edda;
                    border-radius: 12px;
                    border: 1px solid #c3e6cb;
                }
            """)
            # Add stretch on left to push to right
            main_layout.addStretch(1)
            main_layout.addWidget(content_widget, stretch=3)  # Max width 75%

        elif self.sender == "AI":
            # AI message: Left align, light gray background
            content_widget.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    border-radius: 12px;
                    border: 1px solid #e9ecef;
                }
            """)
            main_layout.addWidget(content_widget, stretch=3)  # Max width 75%
            main_layout.addStretch(1)  # Add stretch on right

        else:  # System
            # System message: Left align, light yellow/orange background
            content_widget.setStyleSheet("""
                QWidget {
                    background-color: #fff3cd;
                    border-radius: 8px;
                    border: 1px solid #ffeaa7;
                }
            """)
            main_layout.addWidget(content_widget, stretch=4)  # System messages can be wider
            main_layout.addStretch(1)

        self.setLayout(main_layout)


class AIChatWidget(QWidget):
    """
    AI chat interface for interacting with the AI assistant.
    Phase 2: Full implementation with AI integration.
    v1.6.1: 添加 AI profile 切换功能
    """

    # Signals
    message_sent = pyqtSignal(str)  # Emitted when user sends a message
    command_execute_requested = pyqtSignal(str)  # Emitted when user clicks execute on a command
    ai_profile_changed = pyqtSignal(str)  # Emitted when AI profile is changed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.privacy_mode = False
        self.streaming_bubble = None  # 当前流式消息气泡
        self.streaming_buffer = ""  # 流式内容缓冲区
        self._setup_ui()

    def _setup_ui(self):
        """Setup chat UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with privacy mode toggle
        header_layout = QHBoxLayout()

        title_label = QLabel("AI Assistant")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2196f3;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # AI Profile selector
        self.ai_profile_combo = QComboBox()
        self.ai_profile_combo.setMinimumWidth(120)
        self.ai_profile_combo.setToolTip("选择 AI 配置")
        self.ai_profile_combo.currentIndexChanged.connect(self._on_ai_profile_changed)
        header_layout.addWidget(self.ai_profile_combo)

        # Privacy mode checkbox
        self.privacy_checkbox = QCheckBox("Privacy Mode")
        self.privacy_checkbox.setToolTip("When enabled, terminal context won't be sent to AI")
        self.privacy_checkbox.stateChanged.connect(self._toggle_privacy_mode)
        header_layout.addWidget(self.privacy_checkbox)

        layout.addLayout(header_layout)

        # Chat history scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container for messages
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_container.setLayout(self.chat_layout)

        self.scroll_area.setWidget(self.chat_container)

        # Placeholder message
        self._show_welcome_message()

        layout.addWidget(self.scroll_area, 1)  # Stretch factor 1

        # Message input area
        input_layout = QVBoxLayout()

        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("Ask AI anything about your terminal...")
        self.input_area.setMaximumHeight(80)
        self.input_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        # Support Shift+Enter for new line, Enter to send
        self.input_area.installEventFilter(self)

        # Button layout
        button_layout = QHBoxLayout()

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_chat)
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()

        self.send_button = QPushButton("Send (Enter)")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.send_button.clicked.connect(self._send_message)
        button_layout.addWidget(self.send_button)

        input_layout.addWidget(self.input_area)
        input_layout.addLayout(button_layout)

        layout.addLayout(input_layout)

        self.setLayout(layout)

    def _show_welcome_message(self):
        """Show welcome message in chat."""
        welcome_text = """
        <b>Welcome to AI Assistant! 🤖</b><br><br>
        I can help you with:<br>
        • Analyze terminal output and errors<br>
        • Suggest Linux commands<br>
        • Explain system concepts<br>
        • Troubleshoot issues<br><br>
        <i>Note: Make sure to configure your API key in .env file</i>
        """
        self._append_message("AI", welcome_text)

    def _toggle_privacy_mode(self, state):
        """Toggle privacy mode."""
        self.privacy_mode = (state == 2)  # Qt.CheckState.Checked
        # Debug output
        print(f"[DEBUG] Privacy Mode toggled: {self.privacy_mode} (state={state})", flush=True)

    def _send_message(self):
        """Send message to AI."""
        message = self.input_area.toPlainText().strip()
        if message:
            # Display user message
            self._append_message("You", message)

            # Emit signal
            self.message_sent.emit(message)

            # Clear input
            self.input_area.clear()

    def _append_message(self, sender: str, message: str):
        """
        Append a message to chat display.

        Args:
            sender: 'You' or 'AI'
            message: Message content (can contain HTML)
        """
        # Create message bubble
        bubble = MessageBubble(sender, message, self.chat_container)

        # Add to layout
        self.chat_layout.addWidget(bubble)

        # Scroll to bottom with delay to ensure widget is rendered
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        # Force UI update before scrolling
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

        # Process events again to ensure scroll takes effect
        QApplication.processEvents()

    def append_ai_response(self, response: str):
        """
        Append AI response to chat.
        Phase 3: Parse and display executable command cards.

        Args:
            response: AI response text
        """
        # Import command parser
        from ai.command_parser import CommandParser
        from PyQt6.QtCore import QTimer

        # Parse commands from response
        parser = CommandParser()
        commands = parser.parse_commands(response)

        # If no commands, use simple formatting and scroll
        if not commands:
            formatted_response = self._format_ai_response(response)
            self._append_message("AI", formatted_response)
            # Ensure scroll after appending
            QTimer.singleShot(100, self._scroll_to_bottom)
            return

        # Display AI message (without code blocks)
        response_without_code = re.sub(r'```(\w*)\n(.*?)```', '', response, flags=re.DOTALL)
        formatted_text = self._format_ai_response(response_without_code.strip())

        if formatted_text:
            self._append_message("AI", formatted_text)

        # Display command cards
        for cmd_block in commands:
            explanation = parser.explain_command(cmd_block.command) or ""
            warning = cmd_block.get_warning() or ""

            card = ExecutableCommandCard(
                command=cmd_block.command,
                explanation=explanation,
                warning=warning,
                parent=self.chat_container
            )

            # Connect signal
            card.execute_clicked.connect(self.command_execute_requested)

            # Add to chat
            self.chat_layout.addWidget(card)

        # Scroll to bottom with delay to ensure all widgets are rendered
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _format_ai_response(self, response: str) -> str:
        """
        Format AI response with basic markdown rendering.

        Args:
            response: Raw response text

        Returns:
            HTML-formatted response
        """
        # Escape HTML special characters first
        response = response.replace('&', '&amp;')
        response = response.replace('<', '&lt;')
        response = response.replace('>', '&gt;')

        # Convert markdown code blocks to HTML
        # ```bash code ``` -> <pre><code>code</code></pre>
        code_pattern = r'```(\w*)\n(.*?)```'
        response = re.sub(code_pattern, r'<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;"><code>\2</code></pre>', response, flags=re.DOTALL)

        # Convert inline code `code` to <code>code</code>
        response = re.sub(r'`([^`]+)`', r'<code style="background-color: #e0e0e0; padding: 2px 4px; border-radius: 3px;">\1</code>', response)

        # Convert **bold** to <b>bold</b>
        response = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', response)

        # Convert *italic* to <i>italic</i>
        response = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', response)

        # Convert newlines to <br>
        response = response.replace('\n', '<br>')

        return response

    def start_streaming_response(self):
        """
        开始流式响应，创建一个空的消息气泡用于逐步更新

        Returns:
            创建的消息气泡
        """
        # 创建一个初始为空的消息气泡
        bubble = MessageBubble("AI", "Thinking...", self.chat_container)
        self.chat_layout.addWidget(bubble)

        # 保存引用
        self.streaming_bubble = bubble
        self.streaming_buffer = ""

        # 立即滚动到底部
        self._scroll_to_bottom()

        return bubble

    def append_streaming_content(self, content: str):
        """
        追加流式内容到当前消息

        Args:
            content: 新收到的内容块
        """
        if self.streaming_bubble:
            self.streaming_buffer += content
            # 实时格式化并显示（简化版，不做完整 markdown 渲染以提高性能）
            formatted = self._format_ai_response(self.streaming_buffer)
            self.streaming_bubble.update_message(formatted)

            # 滚动到底部
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(10, self._scroll_to_bottom)

    def finish_streaming_response(self, full_response: str):
        """
        完成流式响应，执行最终渲染

        Args:
            full_response: 完整的响应内容
        """
        # 清除流式状态
        self.streaming_bubble = None
        self.streaming_buffer = ""

        # 使用完整响应重新渲染（包括命令卡片等）
        # 先移除临时气泡
        if self.chat_layout.count() > 0:
            last_item = self.chat_layout.takeAt(self.chat_layout.count() - 1)
            if last_item.widget():
                last_item.widget().deleteLater()

        # 正常渲染完整响应
        self.append_ai_response(full_response)

    def show_error(self, error_msg: str):
        """
        Show error message in chat.

        Args:
            error_msg: Error message text
        """
        error_html = f'<span style="color: red; font-weight: bold;">Error: {error_msg}</span>'
        self._append_message("System", error_html)

    def append_system_message(self, message: str):
        """
        Append a system message to chat.

        Args:
            message: System message text
        """
        self._append_message("System", message)

    def show_thinking(self):
        """Show thinking indicator."""
        thinking_html = '<i>AI is thinking...</i>'
        self._append_message("System", thinking_html)

    def clear_chat(self):
        """Clear chat history."""
        # Remove all messages from layout
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show welcome message again
        self._show_welcome_message()

    def eventFilter(self, obj, event):
        """Event filter for handling Enter key in input area."""
        if obj == self.input_area:
            from PyQt6.QtCore import QEvent
            from PyQt6.QtGui import QKeyEvent

            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    # Check if Shift is pressed
                    modifiers = event.modifiers()
                    if modifiers & Qt.KeyboardModifier.ShiftModifier:
                        # Shift+Enter: Insert newline (default behavior)
                        return False
                    else:
                        # Enter: Send message
                        self._send_message()
                        return True

        return super().eventFilter(obj, event)

    def set_api_config_warning(self, show: bool):
        """
        Show/hide API configuration warning.

        Args:
            show: True to show warning, False to hide
        """
        if show:
            warning_html = """
            <span style="color: orange; font-weight: bold;">
            ⚠️ API Key Not Configured<br><br>
            Please set OPENAI_API_KEY in .env file to use AI features.
            </span>
            """
            self._append_message("System", warning_html)

    def load_ai_profiles(self, current_profile: str = None):
        """
        加载可用的 AI profile 列表到下拉框

        Args:
            current_profile: 当前选中的 profile 名称
        """
        try:
            from managers.ai_profile_manager import AIProfileManager
            ai_manager = AIProfileManager()
            profiles = ai_manager.get_all_profiles()

            # 阻止信号发送以避免重复触发
            self.ai_profile_combo.blockSignals(True)
            self.ai_profile_combo.clear()

            if profiles:
                for profile in profiles:
                    self.ai_profile_combo.addItem(profile.name, profile.name)

                # 设置当前选中的 profile
                if current_profile:
                    index = self.ai_profile_combo.findData(current_profile)
                    if index >= 0:
                        self.ai_profile_combo.setCurrentIndex(index)
                else:
                    # 尝试选中默认 profile
                    default_profile = ai_manager.get_default_profile()
                    if default_profile:
                        index = self.ai_profile_combo.findData(default_profile.name)
                        if index >= 0:
                            self.ai_profile_combo.setCurrentIndex(index)
            else:
                # 没有 AI profiles，显示提示
                self.ai_profile_combo.addItem("无 AI 配置", None)

            print(f"[DEBUG AIChatWidget] Loaded {len(profiles) if profiles else 0} AI profiles")

        except Exception as e:
            print(f"[DEBUG AIChatWidget] Failed to load AI profiles: {e}")
            self.ai_profile_combo.addItem("加载失败", None)
        finally:
            # 恢复信号
            self.ai_profile_combo.blockSignals(False)

    def _on_ai_profile_changed(self, index: int):
        """
        处理 AI profile 切换事件

        Args:
            index: 选中的索引
        """
        profile_name = self.ai_profile_combo.currentData()
        if profile_name:
            print(f"[DEBUG AIChatWidget] AI profile changed to: {profile_name}")
            self.ai_profile_changed.emit(profile_name)
        else:
            print(f"[DEBUG AIChatWidget] AI profile changed to None or invalid")


class ExecutableCommandCard(QFrame):
    """
    A card widget displaying an executable command with run button.
    Phase 3: Interactive command execution.
    """

    # Signal emitted when user clicks execute
    execute_clicked = pyqtSignal(str)

    def __init__(self, command: str, explanation: str = "", warning: str = "", parent=None):
        """
        Initialize command card.

        Args:
            command: The command to execute
            explanation: Command explanation
            warning: Warning message for dangerous commands
            parent: Parent widget
        """
        super().__init__(parent)
        self.command = command
        self.explanation = explanation
        self.warning = warning
        self._setup_ui()

    def _setup_ui(self):
        """Setup command card UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ExecutableCommandCard {
                background-color: #263238;
                border-radius: 8px;
                border: 2px solid #37474f;
                margin: 5px;
            }
            ExecutableCommandCard:hover {
                border: 2px solid #4caf50;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header with explanation
        if self.explanation:
            expl_label = QLabel(f"💡 {self.explanation}")
            expl_label.setStyleSheet("color: #81c784; font-size: 12px;")
            expl_label.setWordWrap(True)
            layout.addWidget(expl_label)

        # Command display
        cmd_label = QLabel(self.command)
        cmd_label.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                color: #a5d6a7;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        cmd_label.setWordWrap(True)
        cmd_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(cmd_label)

        # Warning message
        if self.warning:
            warn_label = QLabel(f"⚠️ {self.warning}")
            warn_label.setStyleSheet("color: #ff9800; font-size: 11px; font-style: italic;")
            warn_label.setWordWrap(True)
            layout.addWidget(warn_label)

        # Execute button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.execute_btn = QPushButton("▶ Run Command")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.execute_btn.clicked.connect(self._on_execute_clicked)
        button_layout.addWidget(self.execute_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_execute_clicked(self):
        """Handle execute button click."""
        # Visual feedback
        self.execute_btn.setText("✓ Sent!")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        # Emit signal
        self.execute_clicked.emit(self.command)

        # Reset button after delay
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, self._reset_button)

    def _reset_button(self):
        """Reset execute button text."""
        self.execute_btn.setText("▶ Run Command")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

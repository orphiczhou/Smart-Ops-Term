"""
Application-wide constants.
Centralized configuration to avoid magic numbers and hardcoded values.
"""


class AppConstants:
    """Application constants"""

    # AI Feedback Timing
    AI_FEEDBACK_DELAY_MS = 1000

    # SSH Connection
    SSH_DEFAULT_PORT = 22
    SSH_TIMEOUT_SECONDS = 10
    SSH_CHANNEL_RECV_SIZE = 4096
    SSH_READ_THREAD_SLEEP_SEC = 0.01
    SSH_INIT_DELAY_SEC = 0.2
    THREAD_JOIN_TIMEOUT_SECONDS = 2

    # Terminal
    TERMINAL_MAX_LINES = 500
    TERMINAL_MAX_CHARS = 3000
    DEFAULT_TERMINAL_FONT_FAMILY = 'Consolas'
    DEFAULT_TERMINAL_FONT_SIZE = 14
    DEFAULT_TERMINAL_BACKGROUND = '#1e1e1e'
    DEFAULT_TERMINAL_TEXT_COLOR = '#00ff00'

    # Messages
    MSG_CONNECTING = "Connecting to {host}..."
    MSG_CONNECTED = "Connected to {host}"
    MSG_DISCONNECTED = "Disconnected from server"
    MSG_CONNECTION_FAILED = "Connection failed"
    MSG_NOT_CONNECTED = "Not connected to server. Please connect first."
    MSG_ANALYZING_OUTPUT = "正在分析命令执行结果..."

    # Password Prompts (Regex Patterns)
    PASSWORD_PATTERNS = [
        r'password\s*:',
        r'password\s+for\s+\S+:',
        r'enter\s+password',
        r'\[sudo\]\s+password',
        r'密码\s*:',
        r'请输入密码',
    ]

"""
AI Client - Interface to LLM APIs (OpenAI compatible).
Supports OpenAI, DeepSeek, Claude, and other OpenAI-compatible providers.
"""
import os
from typing import List, Dict, Optional, Callable
from openai import OpenAI
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from dotenv import load_dotenv

# Load environment variables
# Try to load from project root
env_loaded = load_dotenv()
if not env_loaded:
    # Try loading from parent directory (src/)
    load_dotenv('../.env')


class AIResponseThread(QThread):
    """
    Worker thread for AI API calls to prevent blocking UI.
    """

    # Signals
    response_received = pyqtSignal(str)  # Emitted when response is received
    error_occurred = pyqtSignal(str)  # Emitted when error occurs

    def __init__(self, client: 'AIClient', messages: List[Dict], parent=None):
        super().__init__(parent)
        self.client = client
        self.messages = messages

    def run(self):
        """Execute AI API call in background thread."""
        try:
            response = self.client._call_api(self.messages)
            self.response_received.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AIClient(QObject):
    """
    AI Client for communicating with LLM APIs.
    Supports OpenAI and compatible APIs (DeepSeek, Claude, etc.).
    """

    # Signals
    response_received = pyqtSignal(str)  # Emitted when response is received
    error_occurred = pyqtSignal(str)  # Emitted when error occurs

    # System prompt for Linux operations assistant
    DEFAULT_SYSTEM_PROMPT = """你是一名专业的 Linux 系统运维专家，拥有 10 年以上的实战经验。

## 核心工作原则

### 1. 分步骤解决问题
当用户询问如何完成某个任务时，请按以下方式回答：

**步骤化回答模式：**
```
### 第 1 步：[步骤名称] - [简短说明]

**操作目的：** 简要说明这一步要做什么

**执行命令：**
```bash
[第一个命令]
```

[必要的参数说明或注意事项]

--- 等待执行结果 ---
```

然后停止，等待用户执行并查看结果后，再继续下一步。

### 2. 上下文感知
你可以实时看到用户的终端屏幕输出。
- **如果命令执行成功**，继续下一步
- **如果命令执行失败**，分析错误原因，提供替代方案
- **根据实际输出调整后续步骤**

### 3. 命令格式规范
- 只提供具体可执行的命令，用 Markdown 代码块格式：```bash command ```
- **严禁**直接在代码块中说明文字、解释或示例
- 所有文字说明放在代码块外面
- 命令要完整、可直接复制粘贴执行

### 4. 交互节奏控制
- **一次只给一个命令**，除非多个命令必须连续执行
- 每个命令后明确标注 "--- 等待执行结果 ---"
- 不要一次给出长串命令列表
- 让用户按步骤执行，根据实际反馈调整

### 5. 能力范围说明
用户问你"你能做什么"时，请简洁列举核心能力：
- 📊 系统监控（CPU、内存、磁盘、网络）
- 🔧 故障诊断（日志分析、进程管理、服务管理）
- 🛡️ 安全管理（防火墙、权限、SSH 密钥）
- 📦 软件管理（安装、更新、配置）
- 🌐 网络配置（网卡、路由、DNS、端口）
- 💾 数据管理（备份、恢复、压缩、同步）
- 📝 日志分析（系统日志、应用日志、错误排查）

### 6. 安全准则
- 涉及数据删除、系统修改的操作，先明确警告风险
- 不要执行 `rm -rf /`、`dd`、`mkfs` 等危险命令，除非用户明确要求
- 建议使用 `--dry-run` 参数预演 destructive 操作
- 生产环境操作前提醒备份

### 7. 专业建议
- 命令优先使用现代 Linux 发行版的通用语法
- 说明命令的适用场景和限制条件
- 提供命令的替代方案（多种工具可选）
- 遵循最小权限原则

## 当前会话
你可以看到用户的终端输出（terminal_context），请基于实际情况给出精准的建议。

开始工作吧！根据用户的问题，一步步给出专业的指导。"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load configuration from environment
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')

        # Debug: Print configuration
        print(f"[AI Client] Configuration loaded:")
        print(f"  API Key: {self.api_key[:10] if self.api_key else 'NOT SET'}...")
        print(f"  API Base: {self.api_base}")
        print(f"  Model: {self.model}")

        # Initialize OpenAI client
        self.client = None
        self._init_client()

        # Conversation history
        self.conversation_history: List[Dict] = []

    def _init_client(self):
        """Initialize OpenAI client with configured settings."""
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not set in environment")
            return

        try:
            # Create OpenAI client (compatible with v1.0+)
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            print(f"AI Client initialized: {self.api_base} with model {self.model}")
        except Exception as e:
            print(f"Failed to initialize AI client: {e}")
            self.client = None

    def is_configured(self) -> bool:
        """Check if AI client is properly configured."""
        # Just check if we have an API key, the client can be created when needed
        return bool(self.api_key)

    def _call_api(self, messages: List[Dict]) -> str:
        """
        Call the AI API and return response text.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Response text from AI

        Raises:
            Exception: If API call fails
        """
        # Lazy initialization: create client when needed
        if not self.client:
            if not self.api_key:
                raise Exception("API Key not configured. Please set OPENAI_API_KEY in .env file")

            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base
                )
                print(f"[AI Client] Lazy initialization successful")
            except Exception as e:
                raise Exception(f"Failed to initialize AI client: {str(e)}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            # Extract response text
            assistant_message = response.choices[0].message.content
            return assistant_message.strip()

        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")

    def ask_async(self, user_message: str, terminal_context: str = ""):
        """
        Send question to AI asynchronously (non-blocking).

        Args:
            user_message: User's question
            terminal_context: Recent terminal output for context
        """
        # Build messages
        messages = self._build_messages(user_message, terminal_context)

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Create worker thread
        worker = AIResponseThread(self, messages, self)
        worker.response_received.connect(self._on_response_received)
        worker.error_occurred.connect(self._on_error)
        worker.start()

    def ask_sync(self, user_message: str, terminal_context: str = "") -> str:
        """
        Send question to AI synchronously (blocking).

        Args:
            user_message: User's question
            terminal_context: Recent terminal output for context

        Returns:
            AI response text
        """
        messages = self._build_messages(user_message, terminal_context)
        self.conversation_history.append({"role": "user", "content": user_message})

        response = self._call_api(messages)

        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def _build_messages(self, user_message: str, terminal_context: str) -> List[Dict]:
        """
        Build message list for API call.

        Args:
            user_message: User's question
            terminal_context: Recent terminal output

        Returns:
            List of message dictionaries
        """
        messages = []

        # System prompt
        messages.append({
            "role": "system",
            "content": self.DEFAULT_SYSTEM_PROMPT
        })

        # Add conversation history (excluding the last user message which will be added below)
        # This maintains context of the ongoing conversation
        # Keep only recent history to save tokens (last 10 messages = 5 turns)
        if len(self.conversation_history) >= 2:
            # Keep only the most recent 10 messages to save tokens while maintaining context
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history[:-1]
            messages.extend(recent_history)

        # Add terminal context if available
        if terminal_context:
            context_msg = f"当前终端屏幕内容：\n```\n{terminal_context}\n```\n\n用户问题：{user_message}"
            messages.append({
                "role": "user",
                "content": context_msg
            })
        else:
            messages.append({
                "role": "user",
                "content": user_message
            })

        return messages

    def _on_response_received(self, response: str):
        """Handle response from worker thread."""
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})

        # Emit signal
        self.response_received.emit(response)

    def _on_error(self, error_msg: str):
        """Handle error from worker thread."""
        # Remove last user message from history since it failed
        if self.conversation_history and self.conversation_history[-1]["role"] == "user":
            self.conversation_history.pop()

        # Emit error signal
        self.error_occurred.emit(error_msg)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def set_config(self, api_key: str, api_base: str = None, model: str = None):
        """
        Update AI client configuration.

        Args:
            api_key: OpenAI API key
            api_base: API base URL (optional)
            model: Model name (optional)
        """
        self.api_key = api_key
        if api_base:
            self.api_base = api_base
        if model:
            self.model = model

        # Reinitialize client
        self._init_client()

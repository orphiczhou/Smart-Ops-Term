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
    支持流式和非流式两种模式。
    """

    # Signals - 流式模式专用
    stream_chunk_received = pyqtSignal(str)  # Emitted when each chunk is received
    stream_finished = pyqtSignal(str)  # Emitted when stream is complete

    # Signals - 非流式模式专用
    response_received = pyqtSignal(str)  # Emitted when response is received

    # Signals - 通用
    error_occurred = pyqtSignal(str)  # Emitted when error occurs

    def __init__(self, client: 'AIClient', messages: List[Dict], stream: bool = True, parent=None):
        """
        初始化 AI 响应线程

        Args:
            client: AIClient 实例
            messages: 消息列表
            stream: 是否使用流式调用（默认 True）
            parent: 父对象
        """
        super().__init__(parent)
        self.client = client
        self.messages = messages
        self.stream = stream

    def run(self):
        """Execute AI API call in background thread."""
        try:
            if self.stream:
                # 流式调用
                self.client._call_api_stream(self.messages, self.stream_chunk_received, self.stream_finished)
            else:
                # 非流式调用
                response = self.client._call_api(self.messages)
                self.response_received.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AIClient(QObject):
    """
    AI Client for communicating with LLM APIs.
    Supports OpenAI and compatible APIs (DeepSeek, Claude, etc.).
    v1.6.1: 添加流式响应支持
    """

    # Signals - 非流式模式（向后兼容）
    response_received = pyqtSignal(str)  # Emitted when complete response is received

    # Signals - 流式模式专用
    stream_started = pyqtSignal()  # 流式响应开始
    stream_chunk_received = pyqtSignal(str)  # 每收到一块内容时发出
    stream_finished = pyqtSignal(str)  # 流式响应完成，参数是完整响应

    # Signals - 通用
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

        # v1.6.0: Load configuration from ConfigManager (priority) or environment (fallback)
        self._load_config()

        # Initialize OpenAI client
        self.client = None
        self._init_client()

        # Conversation history
        self.conversation_history: List[Dict] = []

    def _load_config(self, profile_name: Optional[str] = None):
        """
        Load configuration from AIProfileManager, ConfigManager or environment variables.

        v1.6.1: 支持从 AIProfileManager 加载配置

        Args:
            profile_name: 可选的 AI 配置名称
        """
        # 优先级 1: AIProfileManager (指定配置)
        # 优先级 2: AIProfileManager (默认配置)
        # 优先级 3: ConfigManager
        # 优先级 4: 环境变量

        source = "unknown"

        # 尝试从 AIProfileManager 加载
        try:
            from managers.ai_profile_manager import AIProfileManager

            ai_profile_manager = AIProfileManager()

            # 获取配置
            if profile_name:
                ai_profile = ai_profile_manager.get_profile(profile_name)
            else:
                ai_profile = ai_profile_manager.get_default_profile()

            if ai_profile:
                self.api_key = ai_profile.api_key
                self.api_base = ai_profile.api_base
                self.model = ai_profile.model
                self.timeout = 10
                self.max_history = 10
                self._profile_name = ai_profile.name
                # 从 ConfigManager 读取 temperature, max_tokens, system_prompt
                try:
                    from config.config_manager import ConfigManager
                    config_manager = ConfigManager.get_instance()
                    ai_settings = config_manager.settings.ai
                    self.temperature = ai_settings.temperature
                    self.max_tokens = ai_settings.max_tokens
                    # 如果配置中的 system_prompt 为空或使用旧版本，使用完整的 DEFAULT_SYSTEM_PROMPT
                    if not ai_settings.system_prompt or ai_settings.system_prompt == "你是一个专业的 Linux 系统运维助手。":
                        self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
                    else:
                        self.system_prompt = ai_settings.system_prompt
                except Exception:
                    self.temperature = 0.7
                    self.max_tokens = 2000
                    self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
                source = f"AIProfileManager ('{ai_profile.name}')"
                print(f"[DEBUG] Loaded AI profile: {ai_profile.name}")
            else:
                # 回退到 ConfigManager
                raise ValueError("No AI profile found")

        except Exception as e:
            # 尝试从 ConfigManager 加载
            print(f"[DEBUG] AIProfileManager not available or no profile: {e}")
            try:
                from config.config_manager import ConfigManager
                config_manager = ConfigManager.get_instance()
                ai_settings = config_manager.settings.ai

                # Use ConfigManager values if set, otherwise fall back to environment
                self.api_key = ai_settings.api_key or os.getenv('OPENAI_API_KEY', '')
                self.api_base = ai_settings.api_base or os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
                self.model = ai_settings.model or os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
                self.timeout = ai_settings.timeout
                self.max_history = ai_settings.max_history
                self.temperature = ai_settings.temperature
                self.max_tokens = ai_settings.max_tokens
                # 如果配置中的 system_prompt 为空或使用旧版本，使用完整的 DEFAULT_SYSTEM_PROMPT
                if not ai_settings.system_prompt or ai_settings.system_prompt == "你是一个专业的 Linux 系统运维助手。":
                    self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
                else:
                    self.system_prompt = ai_settings.system_prompt
                self._profile_name = None
                source = "ConfigManager" if ai_settings.api_key else "environment (.env)"
            except Exception as e2:
                # 回退到环境变量
                print(f"[DEBUG] ConfigManager not available, using environment: {e2}")
                self.api_key = os.getenv('OPENAI_API_KEY', '')
                self.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
                self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
                self.timeout = 10
                self.max_history = 10
                self.temperature = 0.7
                self.max_tokens = 2000
                self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
                self._profile_name = None
                source = "environment (.env)"

        # Debug: Print configuration
        print(f"[AI Client] Configuration loaded from {source}:")
        print(f"  API Key: {self.api_key[:10] if self.api_key else 'NOT SET'}...")
        print(f"  API Base: {self.api_base}")
        print(f"  Model: {self.model}")

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

    def _reload_ai_settings(self):
        """
        重新从 ConfigManager 加载 AI 设置

        v1.6.1: 每次调用 API 前重新加载配置，确保使用最新设置
        """
        try:
            from config.config_manager import ConfigManager
            config_manager = ConfigManager.get_instance()
            ai_settings = config_manager.settings.ai

            # 更新 AI 参数
            self.temperature = ai_settings.temperature
            self.max_tokens = ai_settings.max_tokens

            # 更新系统提示词
            if not ai_settings.system_prompt or ai_settings.system_prompt == "你是一个专业的 Linux 系统运维助手。":
                self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
            else:
                self.system_prompt = ai_settings.system_prompt

            print(f"[DEBUG] AI settings reloaded: temperature={self.temperature}, max_tokens={self.max_tokens}")

        except Exception as e:
            print(f"[DEBUG] Failed to reload AI settings: {e}, using cached values")

    def is_configured(self) -> bool:
        """Check if AI client is properly configured."""
        # Just check if we have an API key, the client can be created when needed
        return bool(self.api_key)

    def _call_api(self, messages: List[Dict]) -> str:
        """
        Call the AI API and return response text.

        v1.6.1: 每次调用时重新从 ConfigManager 读取最新配置

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Response text from AI

        Raises:
            Exception: If API call fails
        """
        # v1.6.1: 每次调用时重新加载配置，确保使用最新设置
        self._reload_ai_settings()

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
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Extract response text
            assistant_message = response.choices[0].message.content
            return assistant_message.strip()

        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")

    def _call_api_stream(self, messages: List[Dict], chunk_signal: pyqtSignal, finished_signal: pyqtSignal):
        """
        流式调用 AI API，逐块发送响应

        v1.6.1: 每次调用时重新从 ConfigManager 读取最新配置

        Args:
            messages: 消息列表
            chunk_signal: 每收到一块内容时发出的信号
            finished_signal: 流式调用完成时发出的信号

        Raises:
            Exception: If API call fails
        """
        # v1.6.1: 每次调用时重新加载配置，确保使用最新设置
        self._reload_ai_settings()

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
            # 流式调用
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # 发送新内容块
                    chunk_signal.emit(content)

            # 流式调用完成
            finished_signal.emit(full_response)

        except Exception as e:
            raise Exception(f"API streaming call failed: {str(e)}")

    def ask_async(self, user_message: str, terminal_context: str = ""):
        """
        Send question to AI asynchronously (non-blocking).
        默认使用流式调用。

        Args:
            user_message: User's question
            terminal_context: Recent terminal output for context
        """
        # 默认使用流式调用
        return self.ask_async_stream(user_message, terminal_context)

    def ask_async_stream(self, user_message: str, terminal_context: str = ""):
        """
        流式异步发送问题到 AI，实时显示响应。

        Args:
            user_message: User's question
            terminal_context: Recent terminal output for context
        """
        # Build messages
        messages = self._build_messages(user_message, terminal_context)

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        # 发出流式开始信号
        self.stream_started.emit()

        # Create worker thread with streaming enabled
        worker = AIResponseThread(self, messages, stream=True, parent=self)
        worker.stream_finished.connect(self._on_stream_finished)
        worker.error_occurred.connect(self._on_error)

        # 连接流式块信号到 AIClient 的流式信号（透传给 UI）
        worker.stream_chunk_received.connect(self.stream_chunk_received.emit)

        worker.start()

    def _on_stream_finished(self, full_response: str):
        """流式调用完成时的处理。"""
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": full_response})

        # 发出流式完成信号
        self.stream_finished.emit(full_response)

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

        # System prompt - 使用配置的系统提示词，如果没有则使用默认值
        system_prompt = getattr(self, 'system_prompt', self.DEFAULT_SYSTEM_PROMPT)
        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # Add conversation history (excluding the last user message which will be added below)
        # This maintains context of the ongoing conversation
        # Keep only recent history to save tokens (configurable via max_history)
        if len(self.conversation_history) >= 2:
            # Use max_history from config (default 10 messages = 5 turns)
            history_limit = getattr(self, 'max_history', 10) * 2  # Convert to message count
            recent_history = self.conversation_history[-history_limit:] if len(self.conversation_history) > history_limit else self.conversation_history[:-1]
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

    def set_profile(self, profile_name: str):
        """
        设置使用的 AI 配置并重新初始化客户端

        v1.6.1: 多 AI API 配置支持，保留对话历史和上下文

        Args:
            profile_name: AI 配置名称
        """
        # 保存现有的对话历史和上下文
        existing_history = self.conversation_history.copy()

        # 切换配置
        self._profile_name = profile_name
        self._load_config(profile_name)
        self._init_client()

        # 恢复对话历史，保留上下文
        self.conversation_history = existing_history

        print(f"[DEBUG] AI Client switched to profile: {profile_name} (conversation history preserved: {len(existing_history)} messages)")

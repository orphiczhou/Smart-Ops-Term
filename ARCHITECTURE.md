# Smart-Ops-Term 架构设计说明书

## 项目概述

Smart-Ops-Term 是一款基于 AI 的智能 SSH 终端管理工具，通过集成大语言模型（LLM）提供智能化的远程服务器运维辅助功能。

### 核心功能特性

1. **SSH 远程终端** - 支持多服务器连接，实时命令执行
2. **AI 智能助手** - 基于上下文理解，提供运维建议和自动化命令生成
3. **ANSI 颜色支持** - 完整的终端颜色渲染，还原真实终端体验
4. **自动反馈循环** - AI 分析命令执行结果并主动提出下一步操作
5. **安全检测** - 危险命令警告，隐私模式保护

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 开发语言 |
| PyQt6 | 6.7.0 | GUI 框架 |
| Paramiko | 3.4.0 | SSH 连接 |
| OpenAI SDK | >=1.50.0 | AI API 集成 |
| python-dotenv | 1.0.0 | 环境变量管理 |

### 技术选型理由

- **PyQt6**：成熟的跨平台 GUI 框架，信号槽机制适合异步事件处理
- **Paramiko**：Python 生态中最完善的 SSH 库，支持 PTY 交互式 shell
- **OpenAI SDK**：标准化 API 接口，兼容多家 LLM 提供商
- **MVC 架构**：分离关注点，便于维护和扩展

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        主窗口 (MainWindow)                    │
│  ┌──────────────────────┬──────────────────────────────────┐ │
│  │   终端面板 (60%)     │   AI 聊天面板 (40%)              │ │
│  │  ┌────────────────┐  │  ┌────────────────────────────┐  │ │
│  │  │ TerminalWidget │  │  │   AIChatWidget             │  │ │
│  │  │                │  │  │  - 消息气泡                │  │ │
│  │  │ - 命令输入     │  │  │  - Markdown 渲染           │  │ │
│  │  │ - 输出显示     │  │  │  - 可执行命令卡片          │  │ │
│  │  │ - ANSI 颜色    │  │  │  - 隐私模式开关            │  │ │
│  │  └────────────────┘  │  └────────────────────────────┘  │ │
│  └──────────────────────┴──────────────────────────────────┘ │
│                          状态栏                                │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    主控制器 (AppController)                   │
│  - 协调模型、视图、AI 之间的交互                              │
│  - 管理应用状态和流程控制                                    │
│  - 处理用户输入和系统事件                                    │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  SSH Handler   │  │  AI Client     │  │ Context Manager│
│  (Model)       │  │  (AI)          │  │  (AI)          │
├────────────────┤  ├────────────────┤  ├────────────────┤
│ - SSH 连接     │  │ - LLM API 调用 │  │ - 终端上下文   │
│ - 命令执行     │  │ - 对话历史     │  │ - 滑动窗口     │
│ - 数据流读取   │  │ - 异步处理     │  │ - 格式化输出   │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## MVC 架构设计

### Model 层（业务逻辑）

#### SSH Handler (`src/models/ssh_handler.py`)

**职责**：管理 SSH 连接和命令执行

**关键类**：
- `SSHHandler` - SSH 连接处理器

**核心方法**：
```python
class SSHHandler(ConnectionHandler):
    def connect(self, host, port, username, password):
        """建立 SSH 连接，分配交互式 PTY"""

    def send_command(self, command):
        """发送命令到远程 shell，返回 (success, message)"""

    def _read_output(self):
        """后台线程持续读取 SSH channel 数据"""
```

**技术实现**：
- 使用 Paramiko 的 `SSHClient` 和 `invoke_shell()`
- 后台线程 `_read_output()` 非阻塞读取数据
- 通过 PyQt6 信号 (`data_received`) 通知新数据
- 自动设置环境变量支持颜色输出：
  ```python
  channel.send('export TERM=xterm-256color\n')
  channel.send('export COLORTERM=256color\n')
  channel.send('export FORCE_COLOR=1\n')
  channel.send('alias ls="ls --color=always"\n')
  ```

### View 层（用户界面）

#### Main Window (`src/views/main_window.py`)

**职责**：提供主界面框架和布局管理

**组件结构**：
- `QMainWindow` 作为主窗口
- `QSplitter` 水平分割器（可拖动调整面板大小）
- `ConnectionDialog` - SSH 连接信息收集对话框
- 菜单栏：文件、视图、帮助
- 状态栏：显示连接状态和操作提示

**布局代码示例**：
```python
splitter = QSplitter(Qt.Orientation.Horizontal)
splitter.addWidget(self.terminal_widget)
splitter.addWidget(self.chat_widget)
splitter.setSizes([60, 40])  # 60% 终端, 40% 聊天
```

#### Terminal Widget (`src/views/terminal_widget.py`)

**职责**：提供终端显示和命令输入界面

**关键特性**：
- 模拟真实终端外观（黑色背景 `#1e1e1e`，绿色文字 `#00ff00`）
- 支持命令历史（上/下箭头导航）
- ANSI 颜色代码的 HTML 渲染
- 连接状态实时反馈

**核心方法**：
```python
class TerminalWidget(QWidget):
    def append_output(self, text):
        """添加纯文本输出"""

    def append_output_html(self, html):
        """添加 HTML 格式化输出（带颜色）"""

    def keyPressEvent(self, event):
        """处理键盘事件，支持历史命令导航"""
```

**样式设置**：
```python
# 终端显示区域
self.terminal_output = QTextEdit()
self.terminal_output.setStyleSheet("""
    QTextEdit {
        background-color: #1e1e1e;
        color: #00ff00;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 14px;
        border: none;
    }
""")

# 文档边距设置为 0，减少行距
document.setDocumentMargin(0)
format = QTextBlockFormat()
format.setLineHeight(100, 1)  # 单倍行高
```

#### AI Chat Widget (`src/views/chat_widget.py`)

**职责**：提供与 AI 助手的交互界面

**关键组件**：
- `MessageBubble` - 消息气泡 UI 组件
  - 用户消息：右侧蓝色气泡
  - AI 消息：左侧灰色气泡
  - 系统消息：居中黄色文字
- `ExecutableCommandCard` - 可执行命令卡片
  - 美观的命令展示（代码块样式）
  - "Run Command" 按钮
  - 危险命令警告（红色高亮）
- 隐私模式开关

**核心方法**：
```python
class AIChatWidget(QWidget):
    def append_message(self, role, message):
        """添加消息到聊天界面"""

    def append_command_card(self, command, is_dangerous):
        """添加可执行命令卡片"""

    def get_chat_history(self):
        """获取对话历史"""
```

### Controller 层（流程控制）

#### App Controller (`src/controllers/app_controller.py`)

**职责**：协调模型、视图和 AI 之间的交互

**核心状态管理**：
```python
class AppController:
    def __init__(self):
        self.ssh_handler = SSHHandler()          # SSH 处理器
        self.ai_client = AIClient()              # AI 客户端
        self.context_manager = TerminalContext() # 上下文管理器
        self._waiting_for_ai_feedback = False   # AI 反馈标志
        self._ai_feedback_timer = None          # 反馈定时器
```

**关键流程控制**：

1. **SSH 连接建立**：
```python
def _handle_connect_request(self, connection_info):
    """处理 SSH 连接请求"""
    self.terminal_widget.show_connecting()

    success, message = self.ssh_handler.connect(**connection_info)

    if success:
        self.terminal_widget.show_connected()
        self.chat_widget.append_system_message("SSH 连接成功")
    else:
        self.terminal_widget.show_disconnected()
        self.chat_widget.append_system_message(f"连接失败: {message}")
```

2. **命令执行流程**：
```python
@pyqtSlot(str)
def _handle_command_execution(self, command):
    """处理命令执行（来自 AI 卡片）"""
    # 设置标志，表示我们正在等待命令执行结果
    self._waiting_for_ai_feedback = True

    # 发送命令到 SSH（直接调用，绕过 _handle_command_sent 避免标志重置）
    if self.ssh_handler and self.ssh_handler.is_connected:
        success, message = self.ssh_handler.send_command(command)
```

3. **AI 自动反馈机制**：
```python
@pyqtSlot(str)
def _on_data_received(self, data):
    """处理从 SSH 接收的数据"""
    # 检测密码提示
    if 'password:' in data.lower():
        self._handle_password_prompt()
        return

    # 转换 ANSI 颜色并显示
    html_output = ansi_to_html(data)
    self.terminal_widget.append_output_html(html_output)

    # 如果正在等待 AI 反馈，启动定时器收集输出
    if self._waiting_for_ai_feedback:
        if self._ai_feedback_timer:
            self._ai_feedback_timer.stop()

        self._ai_feedback_timer = QTimer()
        self._ai_feedback_timer.setSingleShot(True)
        self._ai_feedback_timer.timeout.connect(
            lambda: self._send_feedback_to_ai()
        )
        self._ai_feedback_timer.start(5000)  # 5 秒后收集

def _send_feedback_to_ai(self):
    """将终端结果发送给 AI 分析"""
    self._waiting_for_ai_feedback = False

    terminal_context = self.context_manager.get_context()
    feedback_message = "以上是命令执行结果，请分析并继续下一步"

    self.ai_client.ask_async(
        feedback_message,
        terminal_context,
        self._on_ai_response,
        self._on_ai_error
    )
```

4. **AI 交互流程**：
```python
@pyqtSlot(str)
def _handle_ai_message(self, user_message):
    """处理用户发送给 AI 的消息"""
    # 获取终端上下文（除非隐私模式开启）
    terminal_context = ""
    if not self.chat_widget.privacy_mode:
        terminal_context = self.context_manager.get_context()

    # 调用 AI（异步）
    self.ai_client.ask_async(
        user_message,
        terminal_context,
        self._on_ai_response,
        self._on_ai_error
    )

def _on_ai_response(self, response):
    """处理 AI 响应"""
    self.chat_widget.append_message("assistant", response)

    # 解析命令并创建卡片
    commands = self.command_parser.parse_commands(response)
    for cmd in commands:
        is_dangerous = self.command_parser.is_dangerous(cmd)
        self.chat_widget.append_command_card(cmd, is_dangerous)
```

---

## 技术实现细节

### PyQt6 信号槽机制

**组件间通信**：

```python
# 在 terminal_widget.py 中定义信号
class TerminalWidget(QWidget):
    command_sent = pyqtSignal(str)      # 命令发送信号
    connect_requested = pyqtSignal(dict) # 连接请求信号

# 在 app_controller.py 中连接信号
def _setup_connections(self):
    self.terminal_widget.command_sent.connect(self._handle_command_sent)
    self.terminal_widget.connect_requested.connect(self._handle_connect_request)
```

**自定义信号**：
- `SSHHandler.data_received(str)` - SSH 数据到达
- `SSHHandler.connected()` - SSH 连接成功
- `SSHHandler.disconnected()` - SSH 连接断开
- `AIChatWidget.message_sent(str)` - 用户发送消息给 AI
- `AIChatWidget.command_execution_requested(str)` - 请求执行命令

### 异步处理架构

#### 1. AI API 异步调用

**问题**：AI API 调用耗时较长（3-10秒），会阻塞 UI

**解决方案**：使用 `QThread` 异步处理

```python
class AIResponseThread(QThread):
    """后台线程处理 AI 响应"""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, ai_client, user_message, terminal_context):
        super().__init__()
        self.ai_client = ai_client
        self.user_message = user_message
        self.terminal_context = terminal_context

    def run(self):
        try:
            response = self.ai_client.ask(
                self.user_message,
                self.terminal_context
            )
            self.response_received.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

# 使用方式
def ask_async(self, user_message, terminal_context, on_response, on_error):
    thread = AIResponseThread(self, user_message, terminal_context)
    thread.response_received.connect(on_response)
    thread.error_occurred.connect(on_error)
    thread.start()
```

#### 2. SSH 数据流读取

**问题**：SSH 数据流持续到达，需要非阻塞读取

**解决方案**：后台线程持续监听

```python
class SSHHandler(ConnectionHandler):
    def _read_output(self):
        """后台线程读取 SSH 输出"""
        while self.is_connected and self.channel:
            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(1024).decode('utf-8')
                    self.data_received.emit(data)
                else:
                    time.sleep(0.1)  # 避免 CPU 占用过高
            except Exception as e:
                self.data_received.emit(f"\r\n[连接错误] {str(e)}\r\n")
                break

# 启动读取线程
read_thread = threading.Thread(target=self._read_output, daemon=True)
read_thread.start()
```

#### 3. QTimer 定时器使用

**场景**：检测命令执行完成

```python
# 延迟 5 秒后收集终端输出发送给 AI
self._ai_feedback_timer = QTimer()
self._ai_feedback_timer.setSingleShot(True)  # 单次触发
self._ai_feedback_timer.timeout.connect(
    lambda: self._send_feedback_to_ai()
)
self._ai_feedback_timer.start(5000)
```

### ANSI 颜色支持

#### ANSI SGR 序列解析

**SGR (Select Graphic Rendition)** 格式：`\x1b[<code>m`

**常用代码**：
- `0` - 重置所有属性
- `1` - 加粗
- `3` - 斜体
- `4` - 下划线
- `30-37` - 前景色（黑红黄绿蓝紫青白）
- `40-47` - 背景色
- `90-97` - 亮前景色
- `100-107` - 亮背景色

**颜色映射表**：
```python
ANSI_COLORS = {
    '30': '#000000',  # Black
    '31': '#cd0000',  # Red
    '32': '#00cd00',  # Green
    '33': '#cdcd00',  # Yellow
    '34': '#0000ee',  # Blue
    '35': '#cd00cd',  # Magenta
    '36': '#00cdcd',  # Cyan
    '37': '#e5e5e5',  # White
    '90': '#7f7f7f',  # Bright Black
    '91': '#ff0000',  # Bright Red
    '92': '#00ff00',  # Bright Green
    '93': '#ffff00',  # Bright Yellow
    '94': '#5c5cff',  # Bright Blue
    '95': '#ff00ff',  # Bright Magenta
    '96': '#00ffff',  # Bright Cyan
    '97': '#ffffff',  # Bright White
}
```

#### HTML/CSS 渲染方案

**转换流程**：
1. 使用占位符保护 SGR 序列
2. 移除非 SGR 控制序列（光标移动等）
3. 按颜色代码分割文本
4. 为每段应用对应 CSS 样式
5. 转换换行符为 `<br>` 标签

**核心代码**：
```python
def convert(self, text: str) -> str:
    # 1. 保护 SGR 序列
    sgr_placeholders = []
    def protect_sgr(match):
        placeholder = f'\x00SGR{len(sgr_placeholders)}\x00'
        sgr_placeholders.append(match.group(0))
        return placeholder

    text_with_placeholders = self.csi_pattern.sub(protect_sgr, text)

    # 2. 移除其他控制序列
    cleaned = text_with_placeholders
    for pattern in self.control_patterns:
        cleaned = pattern.sub('', cleaned)

    # 3. 恢复 SGR 序列
    for i, sgr_seq in enumerate(sgr_placeholders):
        cleaned = cleaned.replace(f'\x00SGR{i}\x00', sgr_seq)

    # 4. 分割并应用样式
    parts = self.csi_pattern.split(cleaned)
    result = []
    current_style = {}

    for i, part in enumerate(parts):
        if i % 2 == 0:  # 文本
            if current_style:
                style = self._build_style(current_style)
                escaped = self._escape_html(part).replace('\n', '<br style="line-height: 1.0">')
                result.append(f'<span style="{style}">{escaped}</span>')
            else:
                escaped = self._escape_html(part).replace('\n', '<br style="line-height: 1.0">')
                result.append(escaped)
        else:  # ANSI 代码
            current_style = self._parse_ansi_codes(part)

    return ''.join(result)
```

**生成的 HTML 示例**：
```html
<span style="color: #0000ee; font-weight: bold">file1.txt</span>
<span style="color: #00cd00">file2.py</span>
<br style="line-height: 1.0">
<span style="color: #cd00cd">directory</span>
```

### AI 上下文管理

#### 对话历史维护

**数据结构**：
```python
self.conversation_history = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    # ...
]
```

**历史限制**：保留最近 10 条消息（节省 token）

```python
def _build_messages(self, user_message: str, terminal_context: str):
    messages = [{"role": "system", "content": self.system_prompt}]

    # 添加对话历史（最多 10 条）
    if len(self.conversation_history) >= 2:
        recent_history = self.conversation_history[-10:] \
            if len(self.conversation_history) > 10 \
            else self.conversation_history[:-1]
        messages.extend(recent_history)

    # 添加当前消息
    messages.append({"role": "user", "content": user_message})

    # 添加终端上下文
    if terminal_context:
        messages.append({
            "role": "user",
            "content": f"\n当前终端上下文：\n```\n{terminal_context}\n```"
        })

    return messages
```

#### 终端上下文收集（滑动窗口）

**窗口大小**：最多 500 行，3000 字符

**实现**：
```python
class TerminalContext:
    def __init__(self, max_lines=500, max_chars=3000):
        self.max_lines = max_lines
        self.max_chars = max_chars
        self.buffer = []

    def add_output(self, text: str):
        """添加输出到缓冲区"""
        lines = text.split('\n')
        self.buffer.extend(lines)

        # 超过行数限制，从开头截断
        if len(self.buffer) > self.max_lines:
            self.buffer = self.buffer[-self.max_lines:]

    def get_context(self) -> str:
        """获取格式化的上下文"""
        context = '\n'.join(self.buffer)

        # 超过字符限制，从开头截断
        if len(context) > self.max_chars:
            context = context[-self.max_chars:]

        return context
```

#### 自动反馈机制

**触发条件**：用户执行 AI 生成的命令

**流程**：
1. 设置 `_waiting_for_ai_feedback = True`
2. 发送命令到 SSH
3. 每次接收到数据，重置 5 秒定时器
4. 定时器触发后，收集终端输出
5. 自动发送给 AI："以上是命令执行结果，请分析并继续下一步"

**代码**：
```python
def _on_data_received(self, data):
    # ... 显示数据 ...

    # 如果正在等待 AI 反馈，启动定时器
    if self._waiting_for_ai_feedback:
        if self._ai_feedback_timer:
            self._ai_feedback_timer.stop()

        self._ai_feedback_timer = QTimer()
        self._ai_feedback_timer.setSingleShot(True)
        self._ai_feedback_timer.timeout.connect(self._send_feedback_to_ai)
        self._ai_feedback_timer.start(5000)
```

---

## 数据流设计

### SSH 连接建立流程

```
用户操作: 点击 "连接" 按钮
    ↓
MainWindow._on_connect_action()
    ↓
发射信号: connect_requested.emit(connection_info)
    ↓
AppController._handle_connect_request(connection_info)
    ↓
TerminalWidget.show_connecting()
    ↓
SSHHandler.connect(host, port, username, password)
    ↓
SSHClient.connect() + invoke_shell()
    ↓
启动后台线程: _read_output()
    ↓
发射信号: connected.emit()
    ↓
AppController 收到连接成功
    ↓
TerminalWidget.show_connected()
ChatWidget.append_system_message("SSH 连接成功")
```

### 命令执行流程

```
用户操作: 在终端输入命令或点击 AI 卡片的 "Run Command"
    ↓
TerminalWidget._send_command() 或 ChatWidget._on_run_command()
    ↓
发射信号: command_sent.emit(command) 或 command_execution_requested.emit(command)
    ↓
AppController._handle_command_execution(command)
    ↓
设置标志: _waiting_for_ai_feedback = True
    ↓
SSHHandler.send_command(command)
    ↓
Channel.send(command + "\n")
    ↓
后台线程 _read_output() 持续接收数据
    ↓
发射信号: data_received.emit(data)
    ↓
AppController._on_data_received(data)
    ↓
ansi_to_html(data) 转换颜色
    ↓
TerminalWidget.append_output_html(html)
    ↓
5 秒后 QTimer 触发
    ↓
AppController._send_feedback_to_ai()
    ↓
AIClient.ask_async("以上是命令执行结果...")
    ↓
AIResponseThread 在后台调用 LLM API
    ↓
发射信号: response_received.emit(response)
    ↓
AppController._on_ai_response(response)
    ↓
ChatWidget.append_message("assistant", response)
    ↓
CommandParser.parse_commands(response) 提取命令
    ↓
ChatWidget.append_command_card() 创建命令卡片
```

### AI 交互流程

```
用户操作: 在聊天框输入问题
    ↓
ChatWidget._send_message()
    ↓
发射信号: message_sent.emit(user_message)
    ↓
AppController._handle_ai_message(user_message)
    ↓
获取终端上下文: ContextManager.get_context()
    ↓
AIClient.ask_async(user_message, terminal_context)
    ↓
AIResponseThread.run()
    ↓
构建消息列表: _build_messages()
    ├─ System Prompt
    ├─ Conversation History (最近 10 条)
    ├─ User Message
    └─ Terminal Context (如果有)
    ↓
OpenAI API 调用
    ↓
等待响应 (3-10 秒)
    ↓
发射信号: response_received.emit(response)
    ↓
AppController._on_ai_response(response)
    ↓
ChatWidget.append_message("assistant", response)
    ↓
解析命令: CommandParser.parse_commands(response)
    ↓
为每个命令创建卡片: ChatWidget.append_command_card()
    ├─ 检测危险: CommandParser.is_dangerous()
    ├─ 显示命令 (语法高亮)
    ├─ 添加 "Run Command" 按钮
    └─ 如果危险，显示红色警告
```

---

## 安全设计

### 密码输入对话框

**问题**：sudo 等命令需要交互式输入密码，终端无法处理

**解决方案**：模态对话框

```python
class PasswordDialog(QDialog):
    def __init__(self, prompt_text="Enter password:", parent=None):
        super().__init__(parent)
        self.setModal(True)  # 模态，阻塞主窗口
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

# 检测密码提示
if 'password:' in data.lower():
    dialog = PasswordDialog("请输入密码:", self.main_window)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        password = dialog.get_password()
        self.ssh_handler.send_command(password)
```

### 危险命令检测

**检测规则**：
```python
DANGEROUS_PATTERNS = {
    r'\brm\s+-rf\s+/': "永久删除根目录文件",
    r'\bdd\s+if=': "覆盖磁盘数据",
    r'\bmkfs\.': "格式化文件系统",
    r'\bshutdown\b': "关闭系统",
    r'\breboot\b': "重启系统",
    r'\bsudo\b': "超级用户权限",
}
```

**警告消息**：
```python
WARNINGS = {
    'rm': "⚠️ 此命令将永久删除文件，请确认路径正确",
    'dd': "⚠️ 此命令将覆盖数据，无法恢复",
    'sudo': "⚠️ 此命令需要超级用户权限",
    # ...
}
```

### 隐私模式

**功能**：开关控制是否向 AI 发送终端上下文

**实现**：
```python
# 在 ChatWidget 中
self.privacy_mode = False  # 默认关闭隐私模式

# 在 AppController 中
terminal_context = ""
if not self.chat_widget.privacy_mode:
    terminal_context = self.context_manager.get_context()
```

### API Key 管理

**存储方式**：环境变量 (.env 文件)

```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4
```

**加载**：
```python
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
```

---

## 配置管理

### 环境变量配置 (.env)

```env
# OpenAI / 兼容 API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4

# 或使用其他提供商
# DEEPSEEK_API_KEY=sk-xxx
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# AI_MODEL=deepseek-chat
```

### 设置文件 (config/settings.json)

```json
{
  "default_connection": {
    "host": "192.168.1.100",
    "port": 22,
    "username": "root"
  },
  "terminal": {
    "font_family": "Consolas",
    "font_size": 14,
    "background_color": "#1e1e1e",
    "text_color": "#00ff00"
  },
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

### 运行时配置

**上下文管理**：
```python
self.context_manager = TerminalContext(
    max_lines=500,
    max_chars=3000
)
```

**定时器配置**：
```python
AI_FEEDBACK_DELAY = 5000  # 5 秒后收集输出
```

---

## 扩展性设计

### AI 服务提供商切换

**配置方式**：修改 .env 文件

```env
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat

# Claude (通过 OpenAI 兼容接口)
ANTHROPIC_API_KEY=sk-xxx
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
AI_MODEL=claude-3-5-sonnet-20241022
```

**代码适配**：
```python
def _create_client(self):
    """延迟创建客户端，支持多种提供商"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")
    model = os.getenv("AI_MODEL", "gpt-3.5-turbo")

    self.client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    self.model = model
```

### 自定义系统提示

**位置**：`src/ai/ai_client.py`

**默认提示**：
```python
DEFAULT_SYSTEM_PROMPT = """
你是一个专业的 Linux 运维专家助手。
你的职责是帮助用户诊断和解决服务器问题。
...
"""
```

**自定义方式**：修改 `ai_client.py` 中的 `system_prompt` 或通过环境变量加载

### 插件化架构预留

**命令解析器扩展**：
```python
class CommandParser:
    def __init__(self):
        self.parsers = [
            self._parse_markdown_block,
            self._parse_code_fence,
            # 可添加更多解析器
        ]

    def register_parser(self, parser_func):
        """注册自定义命令解析器"""
        self.parsers.append(parser_func)
```

**危险命令检测扩展**：
```python
class CommandParser:
    def __init__(self):
        self.dangerous_patterns = {...}
        self.warning_messages = {...}

    def add_dangerous_pattern(self, pattern, warning):
        """添加自定义危险模式"""
        self.dangerous_patterns[pattern] = warning
```

---

## 性能优化

### 正则表达式预编译

**问题**：频繁调用正则表达式影响性能

**解决方案**：在 `__init__` 中预编译

```python
class ANSItoHTML:
    def __init__(self):
        self.csi_pattern = re.compile(r'\x1b\[([0-9;]*)m')
        self.control_patterns = [
            re.compile(r'\x1b\[[0-9;]*[GKHfABCDsu]'),
            re.compile(r'\x1b\][^\x07\x1b]*[\x07\x1b\\]'),
            # ... 更多模式
        ]
```

### 上下文缓冲区限制

**问题**：长时间运行导致上下文过大

**解决方案**：滑动窗口限制

```python
class TerminalContext:
    def __init__(self, max_lines=500, max_chars=3000):
        # 超过限制时从开头截断
        if len(self.buffer) > self.max_lines:
            self.buffer = self.buffer[-self.max_lines:]
```

### 异步处理

**问题**：AI API 调用阻塞 UI

**解决方案**：`QThread` 后台处理

---

## 已知限制

### 1. 终端输入方式

**当前**：使用独立的 `QLineEdit` 输入框

**限制**：不是真正的终端模拟器，不支持光标在输出区域移动

**后续改进**：在显示区域实现光标定位（预估 15-30 小时）

### 2. 单 SSH 连接

**当前**：每次只能连接一个服务器

**限制**：需要多窗口管理多个连接

**后续改进**：多标签页支持

### 3. AI 上下文记忆

**当前**：保留最近 10 条消息

**限制**：长时间对话可能丢失早期上下文

**后续改进**：智能摘要压缩上下文

### 4. 内存管理

**当前**：缓冲区持续增长

**限制**：长时间运行可能导致内存占用增加

**后续改进**：定期清理机制

---

## 技术债务

### 1. 硬编码配置

**位置**：终端颜色、字体等硬编码在代码中

**改进**：移到配置文件

### 2. 错误处理

**问题**：某些异常情况处理不够细致

**改进**：添加更详细的错误分类和处理

### 3. 测试覆盖

**问题**：缺少单元测试和集成测试

**改进**：添加 pytest 测试套件

---

## 附录

### 目录结构

```
Smart-Ops-Term/
├── src/
│   ├── main.py                          # 应用入口
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── app_controller.py            # 主控制器
│   ├── views/
│   │   ├── __init__.py
│   │   ├── main_window.py               # 主窗口
│   │   ├── terminal_widget.py           # 终端组件
│   │   ├── chat_widget.py               # AI 聊天组件
│   │   └── password_dialog.py           # 密码对话框
│   ├── models/
│   │   ├── __init__.py
│   │   ├── connection_handler.py        # 连接基类
│   │   └── ssh_handler.py               # SSH 处理器
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── ai_client.py                 # AI 客户端
│   │   ├── context_manager.py           # 上下文管理
│   │   └── command_parser.py            # 命令解析器
│   └── utils/
│       ├── __init__.py
│       └── ansi_filter.py               # ANSI 转换器
├── config/
│   └── settings.json                    # 配置文件
├── .env.example                         # 环境变量模板
├── requirements.txt                     # Python 依赖
├── README.md                            # 项目说明
├── ARCHITECTURE.md                      # 本文档
├── CHANGELOG.md                         # 开发记录
└── version.txt                          # 版本标记
```

### 依赖项

```
PyQt6==6.7.0
paramiko==3.4.0
openai>=1.50.0
python-dotenv==1.0.0
```

### 系统要求

- Python 3.10+
- Windows / Linux / macOS
- 网络连接（SSH 和 AI API）

---

**文档版本**: 1.0.0
**最后更新**: 2025-01-08
**作者**: Smart-Ops-Term 开发团队

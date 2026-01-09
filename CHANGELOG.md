# Smart-Ops-Term 开发更新记录

## 版本历史

| 版本 | 日期 | 阶段 | 主要变更 |
|------|------|------|----------|
| v0.1.0 | 2024-12-XX | Phase 1 | 基础终端功能（SSH 连接、命令执行） |
| v0.2.0 | 2024-12-XX | Phase 2 | AI 集成（聊天界面、上下文管理） |
| v0.3.0 | 2024-12-XX | Phase 3 | 交互闭环（命令解析、可执行卡片） |
| v1.0.0 | 2025-01-08 | 正式版 | 功能完善、Bug 修复、ANSI 颜色支持 |

---

## v1.0.0 正式版本 (2025-01-08)

### 新增功能

#### 1. AI 自动反馈机制
**问题**：点击 "Run Command" 后 AI 不自动分析结果，需要手动发送提示信号

**解决方案**：
- 在 `app_controller.py` 中添加 `_waiting_for_ai_feedback` 标志位
- 使用 `QTimer` 延迟 5 秒收集终端输出
- 自动将执行结果发送给 AI："以上是命令执行结果，请分析并继续下一步"

**相关文件**：
- [app_controller.py:180-252](src/controllers/app_controller.py#L180-L252)

**关键代码**：
```python
def _handle_command_execution(self, command):
    # 设置标志
    self._waiting_for_ai_feedback = True

    # 发送命令
    if self.ssh_handler and self.ssh_handler.is_connected:
        success, message = self.ssh_handler.send_command(command)

def _on_data_received(self, data):
    # 每次接收数据，重置定时器
    if self._waiting_for_ai_feedback:
        if self._ai_feedback_timer:
            self._ai_feedback_timer.stop()

        self._ai_feedback_timer = QTimer()
        self._ai_feedback_timer.setSingleShot(True)
        self._ai_feedback_timer.timeout.connect(self._send_feedback_to_ai)
        self._ai_feedback_timer.start(5000)
```

#### 2. 密码输入支持
**问题**：无法在终端输入密码（sudo 等命令），只能在对话框输入明文且无法回车

**解决方案**：
- 创建 `PasswordDialog` 模态对话框
- 检测 SSH 密码提示（"password:" 不区分大小写）
- 自动弹出密码输入窗口
- 支持 Enter 键快速确认

**相关文件**：
- [password_dialog.py](src/views/password_dialog.py)
- [app_controller.py](src/controllers/app_controller.py)

**关键代码**：
```python
# 密码提示检测
if 'password:' in data.lower():
    dialog = PasswordDialog("请输入密码:", self.main_window)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        password = dialog.get_password()
        self.ssh_handler.send_command(password)
```

**UI 特性**：
- 固定窗口大小（400x150）确保布局一致
- 密码显示为星号（`QLineEdit.EchoMode.Password`）
- 水平按钮布局（OK、Cancel）

#### 3. AI 上下文记忆
**问题**：AI 忘记之前对话的上下文，执行完第一步后忘记要继续做什么

**解决方案**：
- 修改 `ai_client.py` 的 `_build_messages()` 方法
- 包含 `conversation_history` 对话历史
- 限制为最近 10 条消息以节省 token

**相关文件**：
- [ai_client.py:_build_messages](src/ai/ai_client.py)

**关键代码**：
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
    # ...
```

#### 4. ANSI 颜色支持
**功能**：完整的终端颜色渲染，还原真实终端体验

**实现位置**：[ansi_filter.py](src/utils/ansi_filter.py)

**支持特性**：
- 8 基础色 + 8 亮色（前景色和背景色）
- 加粗、斜体、下划线
- 智能控制序列过滤

**颜色映射**：
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
    # ... 更多颜色
}
```

**SSH 服务器配置**：
```python
# ssh_handler.py 连接时设置
channel.send('export TERM=xterm-256color\n')
channel.send('export COLORTERM=256color\n')
channel.send('export FORCE_COLOR=1\n')
channel.send('alias ls="ls --color=always"\n')
channel.send('alias grep="grep --color=always"\n')
```

### Bug 修复

#### Bug #1: 命令重复显示
**现象**：命令在终端显示两次

**原因**：手动 echo + SSH 自动返回

**解决方案**：移除手动 echo 代码

**相关文件**：[app_controller.py:_handle_command_execution](src/controllers/app_controller.py)

**修复前**：
```python
def _handle_command_execution(self, command):
    self.terminal_widget.append_output(command + "\n")  # 手动 echo
    # ...
```

**修复后**：
```python
def _handle_command_execution(self, command):
    # 不再手动 echo，SSH 会自动返回
    if self.ssh_handler and self.ssh_handler.is_connected:
        success, message = self.ssh_handler.send_command(command)
```

#### Bug #2: 行距过大
**现象**：行距过大，显示输出中间空了大概一行左右

**原因**：HTML `<div>` 标签添加额外段落间距

**解决方案**：
1. 移除 `<div>` 包装，只使用 `<span>`
2. 设置 `document.setDocumentMargin(0)`
3. 使用 `QTextBlockFormat` 设置行高为 100%

**相关文件**：[terminal_widget.py:108-118](src/views/terminal_widget.py#L108-L118)

**关键代码**：
```python
# terminal_widget.py
document = self.terminal_output.document()
document.setDocumentMargin(0)

format = QTextBlockFormat()
format.setLineHeight(100, 1)  # 100% 行高
format.setTopMargin(0)
format.setBottomMargin(0)

# ansi_filter.py - 使用 <br> 控制换行
escaped = self._escape_html(part).replace('\n', '<br style="line-height: 1.0">')
```

#### Bug #3: 文本不换行
**现象**：所有文本在一行不换行

**原因**：`white-space: pre-wrap` 与 inline `<span>` 不兼容

**解决方案**：手动转换 `\n` 为 `<br style="line-height: 1.0">`

**相关文件**：[ansi_filter.py:133](src/utils/ansi_filter.py#L133)

#### Bug #4: QTextBlockFormat 枚举错误
**现象**：`QTextCursor.LineHeightMode` 不存在

**解决方案**：使用整数值 1 代替枚举

**相关文件**：[terminal_widget.py:116](src/views/terminal_widget.py#L116)

**修复代码**：
```python
# 错误写法
format.setLineHeight(100, QTextCursor.LineHeightMode.SingleHeight)

# 正确写法
format.setLineHeight(100, 1)  # 1 = SingleHeight
```

#### Bug #5: 颜色不显示
**现象**：SSH 服务器不发送颜色代码

**原因**：`TERM` 设置为 `vt100`（无颜色支持）

**解决方案**：设置 `TERM=xterm-256color` 等环境变量

**相关文件**：[ssh_handler.py](src/models/ssh_handler.py)

#### Bug #6: 终端默认颜色
**现象**：默认白色不够"终端感"

**解决方案**：改为传统绿色 (0, 255, 0)

**相关文件**：[terminal_widget.py:107](src/views/terminal_widget.py#L107)

**代码**：
```python
palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))
```

---

## ANSI 颜色支持实现过程

### 阶段 1：基础转换器
**目标**：创建 ANSI 到 HTML 的转换器

**实现**：
- 创建 `ANSItoHTML` 类
- 定义完整的颜色映射表（8 基础色 + 8 亮色）
- 支持前景色、背景色、加粗、斜体、下划线

**代码位置**：[ansi_filter.py](src/utils/ansi_filter.py)

### 阶段 2：控制序列过滤
**问题**：控制序列被误删或显示乱码

**尝试方案**：
1. 直接删除所有控制序列 → **失败**（SGR 颜色序列也被删除）
2. 精确匹配每个控制序列 → **复杂**（需要 11 个正则表达式）
3. 使用占位符保护 SGR 序列 → **成功**

**最终方案**：
```python
# 1. 用占位符保护 SGR 序列
sgr_placeholders = []
def protect_sgr(match):
    placeholder = f'\x00SGR{len(sgr_placeholders)}\x00'
    sgr_placeholders.append(match.group(0))
    return placeholder

text_with_placeholders = self.csi_pattern.sub(protect_sgr, text)

# 2. 删除其他控制序列
cleaned = text_with_placeholders
for pattern in self.control_patterns:
    cleaned = pattern.sub('', cleaned)

# 3. 恢复 SGR 序列
for i, sgr_seq in enumerate(sgr_placeholders):
    cleaned = cleaned.replace(f'\x00SGR{i}\x00', sgr_seq)
```

**定义的 11 种控制模式**：
```python
self.control_patterns = [
    re.compile(r'\x1b\[[0-9;]*[GKHfABCDsu]'),  # Cursor movement
    re.compile(r'\x1b\][^\x07\x1b]*[\x07\x1b\\]'),  # OSC sequences
    re.compile(r'\x1b\?\d+[hl]'),  # Private mode sequences
    re.compile(r'\[\?2004[hl]'),  # Bracketed paste mode
    re.compile(r'\x1bP[^\x1b]*\x1b\\'),  # DCS sequences
    re.compile(r'\x1b\[[0-9;]*n'),  # Device status reports
    re.compile(r'\x1b\[>[0-9;]*l'),  # Keyboard mode
    re.compile(r'\x1b\[[0-9;]*r'),  # Cursor positioning
    re.compile(r'\x1b\[\?[0-9;]*[lh]'),  # Mode setting
    re.compile(r'\[\?[0-9;]*[hl]'),  # Bracketed paste variants
]
```

### 阶段 3：行距和换行问题
**问题 1**：行距过大（约一行空白）
**问题 2**：所有文本在一行不换行

**尝试方案**：
1. 使用 `<div>` 包装 → **失败**（添加额外段落间距）
2. 使用 `white-space: pre-wrap` → **失败**（与 inline span 不兼容）
3. 手动控制换行 → **成功**

**最终方案**：
```python
# 移除 <div>，只使用 <span>
result.append(f'<span style="{style}">{escaped}</span>')

# 设置文档边距为 0
document.setDocumentMargin(0)

# 手动转换 \n 为 <br>
escaped = self._escape_html(part).replace('\n', '<br style="line-height: 1.0">')
```

### 阶段 4：终端默认颜色
**问题**：默认白色不够"终端感"

**解决方案**：改为传统绿色

**代码**：
```python
# terminal_widget.py
palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))
```

**效果**：显示为经典的绿色终端文字

### 阶段 5：SSH 服务器颜色支持
**问题**：服务器不发送颜色代码

**诊断过程**：
1. 检查本地 `ls` → 有颜色
2. SSH 连接后 `ls` → 无颜色
3. 检查 `TERM` 环境变量 → `vt100`（无颜色支持）
4. 设置 `TERM=xterm-256color` → 部分命令有颜色
5. 添加 `alias ls="ls --color=always"` → 完全成功

**解决方案**：
```python
# ssh_handler.py 连接时设置
channel.send('export TERM=xterm-256color\n')
channel.send('export COLORTERM=256color\n')
channel.send('export FORCE_COLOR=1\n')
channel.send('alias ls="ls --color=always"\n')
channel.send('alias grep="grep --color=always"\n')
```

**效果**：
- 文件名显示颜色（蓝色、紫色、绿色）
- `grep` 匹配结果高亮

---

## 技术难点和解决方案

### 难点 1：HTML 与 QTextEdit 的兼容性
**问题**：某些 HTML 样式在 QTextEdit 中不生效

**尝试方案**：
1. 使用 `<div>` + CSS `line-height` → **失败**（额外段落间距）
2. 使用 `<pre>` 标签 → **失败**（格式错乱）
3. 使用内联 `<span>` + 手动 `<br>` → **成功**

**经验总结**：
- QTextEdit 对 HTML 支持有限
- 避免使用块级元素（`<div>`, `<p>`）
- 使用内联元素（`<span>`）+ CSS
- 手动控制换行（`<br>`）

### 难点 2：QTextBlockFormat 枚举错误
**问题**：`QTextCursor.LineHeightMode` 不存在

**原因**：PyQt6 版本差异

**解决方案**：使用整数值代替枚举

**代码**：
```python
# 错误写法（PyQt5 风格）
format.setLineHeight(100, QTextCursor.LineHeightMode.SingleHeight)

# 正确写法（PyQt6 风格）
format.setLineHeight(100, 1)  # 1 = SingleHeight
```

### 难点 3：正则表达式性能
**问题**：大量文本处理时性能较差

**解决方案**：预编译所有正则表达式

**代码**：
```python
class ANSItoHTML:
    def __init__(self):
        # 预编译（只执行一次）
        self.csi_pattern = re.compile(r'\x1b\[([0-9;]*)m')
        self.control_patterns = [
            re.compile(r'\x1b\[[0-9;]*[GKHfABCDsu]'),
            # ... 更多
        ]
```

**性能提升**：避免每次调用 `convert()` 时重新编译

### 难点 4：字符编码问题
**问题**：中文显示乱码

**原因**：SSH 数据流未正确解码

**解决方案**：统一使用 UTF-8

**代码**：
```python
# ssh_handler.py
data = self.channel.recv(1024).decode('utf-8')

# 错误处理
try:
    data = self.channel.recv(1024).decode('utf-8')
except UnicodeDecodeError:
    data = self.channel.recv(1024).decode('utf-8', errors='ignore')
```

### 难点 5：AI 反馈标志被重置
**问题**：`_waiting_for_ai_feedback` 标志被意外重置

**原因**：`_handle_command_sent` 方法也使用了这个标志

**解决方案**：绕过 `_handle_command_sent`，直接调用 SSH handler

**代码**：
```python
def _handle_command_execution(self, command):
    self._waiting_for_ai_feedback = True

    # 直接调用 SSH handler，不通过 _handle_command_sent
    if self.ssh_handler and self.ssh_handler.is_connected:
        success, message = self.ssh_handler.send_command(command)
```

---

## 已知问题和 Workaround

### 问题 1：Python 3.14 兼容性
**现象**：Pydantic V1 警告

**影响**：不影响当前功能

**Workaround**：使用 Python 3.10-3.13

**后续**：升级到 Pydantic V2

### 问题 2：Paramiko 加密警告
**现象**：TripleDES 警告

```
Cryptography Deprecation Warning: TripleDES has been moved to the legacy group
```

**影响**：安全性建议，不影响功能

**Workaround**：忽略警告

**后续**：升级 Paramiko 到新版本（使用 AES 加密）

### 问题 3：长时间运行内存增长
**现象**：长时间使用后内存占用增加

**原因**：
- 终端缓冲区持续增长
- 对话历史无限累积
- HTML 渲染缓存

**Workaround**：定期重启应用

**后续**：实现缓冲区清理机制

**计划方案**：
```python
class TerminalContext:
    def cleanup_old_lines(self):
        """定期清理旧行"""
        if len(self.buffer) > self.max_lines:
            self.buffer = self.buffer[-self.max_lines:]
```

### 问题 4：QTextEdit 颜色覆盖
**现象**：设置 `QPalette.Text` 颜色后，HTML 颜色不显示

**原因**：Palette 颜色优先级高于 CSS

**解决方案**：不设置 `QPalette.Text`，或使用白色作为默认

**代码**：
```python
# 错误写法（HTML 颜色不显示）
palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))

# 正确写法（使用白色或透明）
# 不设置，或使用白色作为默认
```

---

## 后续改进计划

### 优先级 P0（已列入计划）

#### 1. 改进终端输入方式
**需求**：光标定位在显示区域，像其他终端软件一样

**预估工作量**：15-30 小时

**技术要点**：
- 移除独立 `QLineEdit`
- 在 `QTextEdit` 文档末尾设置可编辑区域
- 重写 `keyPressEvent` 处理键盘事件
- 限制光标只能在当前输入行移动
- 支持历史命令导航（上/下箭头）
- 支持 Tab 自动补全

**潜在问题**：
- ANSI 颜色可能与光标定位冲突
- 多行输入处理更复杂
- 撤销/重做需要重新实现

### 优先级 P1

#### 1. 多标签页支持
**需求**：同时管理多个 SSH 连接

**预估工作量**：20-30 小时

**实现方案**：
- 使用 `QTabWidget` 管理多个终端
- 每个 Tab 包含独立的 TerminalWidget 和 AIChatWidget
- 支持标签页拖拽排序
- 支持标签页关闭和切换

#### 2. 配置文件持久化
**需求**：保存用户配置到文件

**预估工作量**：8-12 小时

**配置项**：
- 默认连接信息
- 终端颜色和字体
- AI 模型和 API 设置
- 窗口大小和位置

#### 3. 命令自动补全
**需求**：Tab 键自动补全命令和路径

**预估工作量**：10-15 小时

**实现方案**：
- 解析当前输入
- 查询远程服务器路径（`ls` 命令）
- 显示补全候选列表
- 支持多次 Tab 切换候选

#### 4. 主题切换
**需求**：支持多种终端主题

**预估工作量**：6-10 小时

**预设主题**：
- 经典黑底绿字
- Solarized Light
- Solarized Dark
- Monokai
- 自定义主题

### 优先级 P2

#### 1. SFTP 文件传输
**需求**：支持文件上传下载

**预估工作量**：30-40 小时

**功能**：
- 双栏文件管理器
- 拖拽上传/下载
- 断点续传
- 权限管理

#### 2. 会话录制和回放
**需求**：记录终端操作并支持回放

**预估工作量**：20-25 小时

**实现方案**：
- 记录所有输入和输出
- 支持 asciinema 格式
- 可视化回放界面

#### 3. 脚本自动化执行
**需求**：批量执行脚本

**预估工作量**：15-20 小时

**功能**：
- 脚本编辑器
- 多服务器批量执行
- 执行结果汇总
- 错误处理和重试

#### 4. 性能优化和内存管理
**需求**：减少内存占用，提升性能

**预估工作量**：20-30 小时

**优化点**：
- 缓冲区定期清理
- 对话历史压缩
- HTML 渲染优化
- 延迟加载

---

## 开发经验总结

### 1. 架构设计

#### MVC 架构优势
- **分离关注点**：UI、逻辑、数据分开，易于维护
- **可测试性**：每层可独立测试
- **可扩展性**：新增功能只需修改对应层

#### 信号槽机制
- **松耦合**：组件间通过信号通信，无需直接引用
- **异步处理**：适合处理耗时操作（AI API 调用）
- **类型安全**：PyQt6 的类型注解帮助调试

### 2. 技术选型

#### PyQt6 vs 其他 GUI 框架
| 框架 | 优势 | 劣势 |
|------|------|------|
| PyQt6 | 成熟稳定、文档丰富、跨平台 | 体积大、学习曲线陡 |
| Tkinter | 内置、轻量 | UI 简陋、功能有限 |
| Electron | 现代、Web 技术 | 资源占用高、启动慢 |

**选择 PyQt6 的原因**：
- 需要复杂的 UI（分割器、气泡、卡片）
- 需要异步处理（AI API 调用）
- 需要丰富的控件（QTextEdit 支持 HTML）

#### Paramiko vs 其他 SSH 库
| 库 | 优势 | 劣势 |
|------|------|------|
| Paramiko | 纯 Python、跨平台、功能完整 | 速度较慢 |
| Fabric | 基于 Paramiko、更高级 | 过度封装 |
| asyncssh | 异步、高性能 | 文档少、兼容性差 |

**选择 Paramiko 的原因**：
- 稳定性好，社区活跃
- 支持交互式 shell（`invoke_shell`）
- 文档完善，示例丰富

### 3. 踩坑经验

####坑 1：QTextEdit 的 HTML 限制
**教训**：
- 不要期望完全兼容浏览器 HTML
- 避免 CSS 复杂样式
- 使用简单的内联样式

#### 坑 2：PyQt6 版本差异
**教训**：
- 注意 PyQt5 和 PyQt6 的枚举差异
- 优先使用整数值代替枚举
- 查阅 PyQt6 官方文档

#### 坑 3：SSH 字符编码
**教训**：
- 统一使用 UTF-8
- 处理解码错误（`errors='ignore'`）
- 测试中文路径和文件名

#### 坑 4：AI Token 消耗
**教训**：
- 限制上下文大小（500 行，3000 字符）
- 限制对话历史（最近 10 条）
- 考虑使用更便宜的模型（如 DeepSeek）

#### 坑 5：定时器内存泄漏
**教训**：
- 每次创建新的 QTimer 实例
- 使用前停止旧的定时器
- 考虑使用单个定时器重复触发

### 4. 最佳实践

#### 代码组织
```
src/
├── controllers/  # 业务逻辑
├── views/       # UI 组件
├── models/      # 数据模型
├── ai/          # AI 功能
└── utils/       # 工具函数
```

#### 命名规范
- 类名：`PascalCase`（如 `SSHHandler`）
- 方法名：`snake_case`（如 `send_command`）
- 私有方法：`_leading_underscore`（如 `_read_output`）
- 信号名：`descriptive_noun`（如 `data_received`）

#### 错误处理
```python
try:
    # 可能出错的代码
    success, message = self.ssh_handler.send_command(command)
except Exception as e:
    # 详细记录错误
    logger.error(f"Command execution failed: {str(e)}")
    # 通知用户
    self.chat_widget.append_system_message(f"错误: {str(e)}")
```

#### 文档注释
```python
def send_command(self, command: str) -> tuple[bool, str]:
    """
    发送命令到远程 shell。

    Args:
        command: 要执行的命令

    Returns:
        (success, message) 元组
        - success: 是否成功
        - message: 错误消息或空字符串
    """
```

### 5. 测试策略

#### 单元测试（计划中）
- SSH Handler 连接测试
- ANSI 转换器测试
- 命令解析器测试

#### 集成测试（计划中）
- 完整的连接-命令-反馈流程
- AI 交互流程
- 错误恢复流程

#### 手动测试
- 多服务器连接测试
- 长时间运行稳定性测试
- 中文路径和文件名测试
- 危险命令检测测试

---

## 附录

### 关键文件清单

| 文件 | 行数 | 职责 |
|------|------|------|
| [main.py](src/main.py) | 20 | 应用入口 |
| [app_controller.py](src/controllers/app_controller.py) | 350 | 主控制器 |
| [main_window.py](src/views/main_window.py) | 150 | 主窗口 |
| [terminal_widget.py](src/views/terminal_widget.py) | 200 | 终端组件 |
| [chat_widget.py](src/views/chat_widget.py) | 250 | AI 聊天组件 |
| [ssh_handler.py](src/models/ssh_handler.py) | 180 | SSH 处理器 |
| [ai_client.py](src/ai/ai_client.py) | 200 | AI 客户端 |
| [ansi_filter.py](src/utils/ansi_filter.py) | 300 | ANSI 转换器 |
| **总计** | **1650** | |

### 依赖版本

```
PyQt6==6.7.0
paramiko==3.4.0
openai>=1.50.0
python-dotenv==1.0.0
```

### 系统要求

- Python 3.10+
- Windows 10+ / Linux / macOS
- 网络连接（SSH 和 AI API）
- 内存：至少 2GB
- 磁盘：至少 100MB

---

**文档版本**: 1.0.0
**最后更新**: 2025-01-08
**作者**: Smart-Ops-Term 开发团队

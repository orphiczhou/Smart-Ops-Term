# Smart-Ops-Term 项目文档

## 📋 项目概述

**Smart-Ops-Term** 是一个基于 Python 的 AI 辅助远程运维终端，采用 PyQt6 构建 GUI，通过 Paramiko 实现 SSH 连接，并集成 AI 大模型实现智能运维辅助。

## 🏗️ 项目结构

```
Smart-Ops-Term/
│
├── config/                          # 配置文件目录
│   └── settings.json               # 应用配置（API Key、默认连接等）
│
├── src/                            # 源代码目录
│   ├── __init__.py
│   ├── main.py                     # 程序入口点
│   │
│   ├── models/                     # 数据模型层（MVC 中的 Model）
│   │   ├── __init__.py
│   │   ├── connection_handler.py   # 连接处理基类
│   │   └── ssh_handler.py          # SSH 连接实现（基于 Paramiko）
│   │
│   ├── views/                      # 视图层（MVC 中的 View）
│   │   ├── __init__.py
│   │   ├── main_window.py          # 主窗口（包含连接对话框）
│   │   ├── terminal_widget.py      # 左侧终端组件
│   │   └── chat_widget.py          # 右侧 AI 聊天组件
│   │
│   └── controllers/                # 控制层（MVC 中的 Controller）
│       ├── __init__.py
│       └── app_controller.py       # 应用主控制器
│
├── tests/                          # 测试目录（预留）
│
├── requirements.txt                # Python 依赖列表
├── .env.example                    # 环境变量示例
├── .gitignore                      # Git 忽略文件
├── README.md                       # 项目说明
├── PHASE1_COMPLETE.md              # 第一阶段完成说明
├── run.bat                         # Windows 启动脚本
└── run.sh                          # Linux/Mac 启动脚本
```

## 📂 核心文件说明

### 1. 程序入口
**[src/main.py](src/main.py)**
- 应用程序的入口点
- 创建 QApplication 实例
- 初始化并启动 AppController
- 处理应用退出清理

### 2. Model 层

#### [src/models/connection_handler.py](src/models/connection_handler.py)
- 连接处理的基类
- 定义信号接口：`data_received`, `connection_lost`, `connection_established`
- 定义抽象方法：`connect()`, `send_command()`, `close()`

#### [src/models/ssh_handler.py](src/models/ssh_handler.py)
- SSH 连接的具体实现
- 使用 Paramiko 库处理 SSH 协议
- 后台线程持续读取服务器输出
- 通过信号发送接收到的数据

### 3. View 层

#### [src/views/main_window.py](src/views/main_window.py)
- 主窗口，使用 `QSplitter` 实现左右分栏布局
- 包含菜单栏（文件、查看、帮助）
- 包含状态栏显示连接状态
- 包含 `ConnectionDialog` 对话框用于输入连接信息

#### [src/views/terminal_widget.py](src/views/terminal_widget.py)
- 左侧终端显示组件
- 使用 `QTextEdit` 显示终端输出（黑底绿字）
- 使用 `QLineEdit` 接收用户命令输入
- 发射 `command_sent` 信号将命令传递给控制器

#### [src/views/chat_widget.py](src/models/chat_widget.py)
- 右侧 AI 聊天组件
- 第一阶段为占位符实现
- 第二阶段将集成完整的 AI 对话功能

### 4. Controller 层

#### [src/controllers/app_controller.py](src/controllers/app_controller.py)
- 应用的核心控制器
- 协调 Model 和 View 之间的交互
- 处理连接请求、断开连接
- 路由终端输入和输出
- 管理终端缓冲区（`terminal_buffer`）为 AI 提供上下文

## 🔄 数据流

### 连接流程
```
用户点击 "Connect"
    ↓
MainWindow 弹出 ConnectionDialog
    ↓
用户输入连接信息并确认
    ↓
发射 connect_requested 信号
    ↓
AppController._handle_connect_request()
    ↓
创建 SSHHandler 并调用 connect()
    ↓
SSH 连接建立 → 发射 connection_established 信号
    ↓
AppController._on_connection_established()
    ↓
MainWindow 显示连接成功
```

### 命令执行流程
```
用户在 TerminalWidget 输入命令
    ↓
发射 command_sent 信号
    ↓
AppController._handle_command_sent()
    ↓
调用 SSHHandler.send_command()
    ↓
命令发送到 SSH 服务器
    ↓
服务器返回输出
    ↓
SSHHandler 后台线程接收数据
    ↓
发射 data_received 信号
    ↓
AppController._on_data_received()
    ↓
TerminalWidget.append_output() 显示输出
    ↓
同时存储到 terminal_buffer（供 AI 使用）
```

### 连接断开流程
```
用户点击 "Disconnect" 或连接异常
    ↓
发射 disconnect_requested 信号 或 connection_lost 信号
    ↓
AppController 调用 SSHHandler.close()
    ↓
SSH 连接关闭
    ↓
MainWindow 更新 UI 状态
```

## 🎨 UI 组件关系

```
MainWindow (QMainWindow)
├── MenuBar (菜单栏)
│   ├── File Menu (文件菜单)
│   │   ├── Connect... (连接)
│   │   ├── Disconnect (断开)
│   │   └── Exit (退出)
│   ├── View Menu (查看菜单)
│   │   ├── Clear Terminal (清空终端)
│   │   └── Clear Chat (清空聊天)
│   └── Help Menu (帮助菜单)
│       └── About (关于)
│
├── QSplitter (分割器)
│   ├── Left: TerminalWidget (左侧终端)
│   │   ├── QTextEdit (终端输出显示)
│   │   └── QLineEdit (命令输入框)
│   │
│   └── Right: AIChatWidget (右侧 AI 聊天)
│       ├── QTextEdit (聊天历史显示)
│       ├── QTextEdit (消息输入框)
│       └── QPushButton (发送按钮)
│
└── StatusBar (状态栏)
```

## 🔧 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 编程语言 | Python | 3.10+ |
| GUI 框架 | PyQt6 | 6.7.0 |
| SSH 库 | Paramiko | 3.4.0 |
| AI SDK | OpenAI | 1.12.0 |
| 环境管理 | python-dotenv | 1.0.1 |

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
**Windows:**
```bash
run.bat
```
**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**直接运行:**
```bash
python src/main.py
```

## 📝 开发阶段

### ✅ 第一阶段：基础终端（已完成）
- [x] PyQt6 双栏布局
- [x] SSH 连接功能
- [x] 终端输入输出
- [x] 多线程网络 I/O
- [x] 基础 UI 组件

### 🔄 第二阶段：AI 集成（待开发）
- [ ] OpenAI API 集成
- [ ] 终端上下文管理
- [ ] Prompt 构建逻辑
- [ ] AI 对话界面完善
- [ ] Markdown 解析
- [ ] 代码块渲染

### ⏳ 第三阶段：交互闭环（待开发）
- [ ] 点击执行按钮
- [ ] 命令卡片组件
- [ ] 自动滚动优化
- [ ] 错误处理增强
- [ ] 用户体验优化

## 🛡️ 安全考虑

1. **凭证管理**: 密码仅在运行时使用，不持久化存储
2. **隐私保护**: 计划在第二阶段添加"隐私模式"开关
3. **人机回环**: AI 不能自动执行命令，必须由用户点击确认

## 📄 许可证

MIT License

---

**最后更新**: 2026-01-08
**当前版本**: 0.1.0 (Phase 1)

# Smart-Ops-Term

🚀 **AI 辅助远程运维终端** - 人机协同的智能远程终端工具

[![Version](https://img.shields.io/badge/Version-1.6.1-blue)](version.txt)
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.14+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 项目概述

Smart-Ops-Term 是一个基于 Python 的 GUI 应用程序，实现**"人机协同"**的远程运维。

### 🎯 核心功能

- **🖥️ 功能完整的远程终端**
  - SSH 连接管理
  - 实时命令执行
  - 完整的 ANSI 颜色支持（16 色 + 样式）
  - 命令历史导航（上下箭头）
  - 自动密码输入（sudo 等交互式命令）
  - **多标签页支持** (v1.5.0) - 同时管理多个 SSH 连接

- **🤖 AI 智能助手**
  - 深度集成大语言模型（OpenAI/DeepSeek/Claude 等）
  - 自动分析命令执行结果并继续下一步
  - 对话上下文记忆（最近 10-15 条消息）
  - 终端上下文感知（滑动窗口，500 行）
  - 危险命令检测和安全警告
  - 可执行命令卡片（一键运行）
  - **AI 配置管理** (v1.6.0) - 可视化配置界面，支持多 AI API

- **🎨 现代化 UI 设计**
  - 左右分栏布局（可拖动调整）
  - Markdown 渲染支持
  - 消息气泡设计
  - 经典终端风格（黑底绿字）
  - **可定制化界面** (v1.6.0) - 字体、颜色、窗口大小可配置

- **💾 配置持久化** (v1.6.0)
  - 可视化设置对话框（4 个标签页）
  - 自动保存配置到 `~/.smartops/app_config.json`
  - 窗口状态记忆（位置、大小、分割器）
  - 从旧版 .env 自动迁移配置

---

## 🏗️ 技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 编程语言 | Python | 3.14+ | 开发语言 |
| GUI 框架 | PyQt6 | 6.7.0 | 用户界面 |
| SSH 库 | Paramiko | 3.4.0 | 远程连接 |
| AI SDK | OpenAI | >=1.50.0 | LLM 集成 |
| 环境管理 | python-dotenv | 1.0.0 | 配置管理（回退） |

---

## 📦 安装

### 1. 克隆项目

```bash
git clone https://github.com/orphiczhou/Smart-Ops-Term.git
cd Smart-Ops-Term
```

### 2. 创建虚拟环境

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置应用

**方式一：首次启动自动配置** (推荐)

首次启动时，如果有 `.env` 文件，会自动迁移到新配置系统。

**方式二：通过设置界面配置**

1. 启动应用
2. 点击工具栏的 "⚙️ Settings" 按钮
3. 在 "AI Settings" 标签页中配置：
   - API Key
   - API Base
   - Model
   - Temperature
   - Max Tokens
   - Max History
   - System Prompt

**方式三：使用 .env 文件** (向后兼容)

创建 `.env` 文件：

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo

# 或使用 DeepSeek
# OPENAI_API_BASE=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

**配置文件位置**：
- 新版配置: `~/.smartops/app_config.json` (优先)
- 旧版配置: `.env` (回退)

---

## 🚀 快速开始

### 启动应用

**直接运行:**
```bash
python src/main.py
```

**使用启动脚本:**

- **Windows**: 双击 `run.bat`
- **Linux/Mac**: 运行 `./run.sh`

### 使用流程

1. **启动应用**
   - 应用启动后，你会看到多标签页界面
   - 每个标签页包含左右分栏（终端 + AI 助手）

2. **创建新连接**
   - 点击 "New Connection" 按钮创建新标签页
   - 按 `Ctrl+O` 或点击菜单 `File > Connect...`
   - 输入服务器信息（Host、Port、Username、Password）
   - 点击 OK 连接

3. **使用 AI 助手**
   - 在右侧输入框输入问题
   - 按 `Enter` 发送
   - AI 会看到最近的终端输出并给出建议
   - 点击 "Run Command" 按钮执行命令
   - AI 会自动分析结果并继续下一步

4. **多标签页管理** (v1.5.0)
   - 每个标签页有独立的终端会话和 AI 对话
   - 点击标签页切换不同连接
   - 点击标签页的关闭按钮断开连接

5. **配置设置** (v1.6.0)
   - 点击工具栏 "⚙️ Settings" 按钮打开设置对话框
   - 配置 AI、终端、界面、连接等选项
   - 点击 Apply 应用，或 OK 应用并关闭
   - 配置自动保存，重启后生效

6. **隐私模式**
   - 勾选 "Privacy Mode" 复选框
   - 终端内容不会发送给 AI（适合敏感操作）

---

## 🎬 功能演示

### 场景 1：分析错误并自动修复

```
终端输出：Permission denied

你问 AI：为什么我被拒绝访问了？

AI 回复：
你收到了 Permission denied 错误，这是因为该文件需要 root 权限。
解决方法：
```bash
sudo cat /etc/hosts
```

[Run Command] ← 点击按钮

终端提示：[sudo] password for user:
→ 自动弹出密码对话框
→ 输入密码后继续执行

AI 自动分析：现在可以看到 /etc/hosts 的内容了...
```

### 场景 2：多步骤自动化

```
你问 AI：帮我检查一下服务器的磁盘使用情况，如果有问题就清理

AI 回复：
好的，我先查看磁盘使用情况。
```bash
df -h
```

[Run Command] ← 点击按钮

5 秒后 AI 自动分析：
磁盘使用正常，最大的分区 / 使用了 45%。
是否需要查看大文件？

你说：是的，查看前 10 个最大的文件

AI 回复：
```bash
find / -type f -size +100M 2>/dev/null | xargs du -h | sort -rh | head -10
```

[Run Command] ← 点击按钮
```

---

## 📂 项目结构

```
Smart-Ops-Term/
├── src/
│   ├── main.py                    # 程序入口
│   ├── controllers/               # Controller 层（业务逻辑）
│   │   ├── app_controller.py      # 主控制器
│   │   └── session_controller.py  # 会话控制器 (v1.5.0)
│   ├── views/                     # View 层（UI 组件）
│   │   ├── multi_terminal_window.py   # 多标签页主窗口 (v1.5.0)
│   │   ├── session_tab.py             # 会话标签页 (v1.5.0)
│   │   ├── terminal_widget.py         # 终端组件
│   │   ├── chat_widget.py             # AI 聊天组件
│   │   ├── settings_dialog.py         # 设置对话框 (v1.6.0)
│   │   ├── ai_profiles_tab.py         # AI 配置管理 (v1.6.0)
│   │   ├── connection_profiles_tab.py # 连接配置管理 (v1.6.0)
│   │   └── password_dialog.py         # 密码对话框
│   ├── config/                    # 配置模块 (v1.6.0)
│   │   ├── settings.py             # 配置数据模型
│   │   └── config_manager.py       # 配置管理器
│   ├── managers/                  # 管理器模块
│   │   └── connection_manager.py   # 连接管理器 (v1.5.0)
│   ├── models/                    # Model 层（SSH 连接）
│   │   ├── connection_handler.py  # 连接基类
│   │   └── ssh_handler.py         # SSH 处理器
│   ├── ai/                        # AI 模块
│   │   ├── ai_client.py           # AI 客户端
│   │   ├── context_manager.py     # 上下文管理
│   │   └── command_parser.py      # 命令解析器
│   └── utils/                     # 工具模块
│       └── ansi_filter.py         # ANSI 转换器
├── docs/                          # 文档目录
│   ├── plans/                     # 开发计划
│   ├── v1.6.0-config-persistence-summary.md
│   └── feature-verification-report.md
├── .env.example                   # 环境变量示例
├── requirements.txt               # 依赖列表
├── README.md                      # 项目说明
├── ARCHITECTURE.md                # 架构设计说明书
├── CHANGELOG.md                   # 开发更新记录
├── version.txt                    # 版本标记
├── PHASE1_COMPLETE.md             # 第一阶段文档
├── PHASE2_COMPLETE.md             # 第二阶段文档
└── PHASE3_COMPLETE.md             # 第三阶段文档
```

📖 **详细文档**：
- [架构设计说明书](ARCHITECTURE.md) - 完整的技术架构和实现细节
- [开发更新记录](CHANGELOG.md) - 开发过程中的经验总结和踩坑记录

---

## 🎯 版本历史

### ✅ v1.6.1 配置持久化修复版 (2026-01-20)

**Bug 修复**：
- ✅ 修复配置持久化功能，配置现在可以正确保存和加载
- ✅ 修复 SettingsDialog 显示旧值的问题
- ✅ 修复短提示词被错误判断为不完整的问题
- ✅ 修复 AI 配置实时更新机制

### ✅ v1.6.0 配置持久化版 (2026-01-19)

**新增功能**：
- ✅ **配置管理界面**：4 标签页可视化设置（AI、终端、界面、连接）
- ✅ **JSON 持久化**：自动保存到 `~/.smartops/app_config.json`
- ✅ **窗口记忆**：记住窗口位置、大小、分割器位置
- ✅ **自动迁移**：从旧版 .env 文件自动迁移配置
- ✅ **AI 配置管理**：支持多 AI API 配置切换

### ✅ v1.5.0 多连接管理版 (2026-01-18)

**新增功能**：
- ✅ **多标签页 SSH**：同时管理多个 SSH 连接，每个连接独立会话
- ✅ **连接配置管理**：保存和管理常用连接配置
- ✅ **独立会话**：每个标签页有独立的终端和 AI 聊天
- ✅ **SessionController**：重构为支持多连接的会话控制器

### ✅ v1.0.0 正式版本 (2025-01-08)

**核心功能**：
- ✅ AI 自动反馈机制（执行命令后自动分析结果）
- ✅ 密码输入支持（sudo 等交互式命令）
- ✅ AI 上下文记忆（保留最近 10 条对话历史）
- ✅ 完整的 ANSI 颜色支持（16 色 + 样式）
- ✅ 命令历史导航（上下箭头）
- ✅ 危险命令检测和安全警告

**Bug 修复**：
- ✅ 修复命令重复显示问题
- ✅ 修复终端行距过大问题
- ✅ 修复文本不换行问题
- ✅ 修复颜色不显示问题

📖 **详细信息**：
- [架构设计说明书](ARCHITECTURE.md) - 完整的技术架构
- [开发更新记录](CHANGELOG.md) - 完整的开发过程和踩坑经验
- [功能验证报告](docs/feature-verification-report.md) - v1.5.0/v1.6.0/v1.6.1 验证报告

### 📋 历史阶段

**Phase 1：基础终端** (v0.1.0)
- PyQt6 双栏布局
- SSH 连接功能
- 终端输入输出
- 多线程网络 I/O

**Phase 2：AI 集成** (v0.2.0)
- OpenAI SDK 集成
- 终端上下文管理
- AI 对话界面
- Markdown 渲染

**Phase 3：交互闭环** (v0.3.0)
- 命令解析和执行
- 可执行命令卡片
- 危险命令检测
- 用户体验优化

---

## 🔧 配置说明

### AI 提供商

**OpenAI:**
```env
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo
```

**DeepSeek:**
```env
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

**其他兼容 API:**
```env
OPENAI_API_BASE=https://your-provider.com/v1
OPENAI_MODEL=your-model-name
```

### 上下文管理

- **最大行数**: 500 行
- **最大字符数**: 3000 字符
- **自动截断**: 保留最新内容

---

## 🔒 安全与隐私

### 凭证管理
- 密码仅在运行时使用，不持久化存储
- API Key 存储在本地 `.env` 文件中

### 隐私模式
- **启用时**: 终端上下文完全不发送给 AI
- **适用场景**: 处理敏感数据（密码、密钥、IP）

### 数据传输
- 终端输出通过 HTTPS 发送到 AI API
- 对话历史仅在内存中，退出后清除

---

## 🔮 后续计划

### 优先级 P0（已列入计划）
- **改进终端输入方式** - 光标定位在显示区域，像其他终端软件一样
  - 预估工作量：15-30 小时

### 优先级 P1
- **命令自动补全** - Tab 键补全命令和路径
- **主题切换** - 支持多种终端主题
- **单元测试** - 添加测试覆盖

### 优先级 P2
- **SFTP 文件传输** - 支持文件上传下载
- **会话录制和回放** - 记录终端操作
- **脚本自动化执行** - 批量执行脚本
- **性能优化** - 减少内存占用

详见 [开发更新记录](CHANGELOG.md)

## 🐛 已知问题

1. **Python 3.14 兼容性**
   - Pydantic V1 与 Python 3.14 不完全兼容
   - **影响**: 无（仅警告）
   - **解决**: 使用 Python 3.10-3.13

2. **Paramiko 加密警告**
   - TripleDES 算法废弃警告
   - **影响**: 无（仅警告）
   - **解决**: 可忽略，等待 Paramiko 更新

3. **长时间运行内存增长**
   - 长时间使用后内存占用增加
   - **Workaround**: 定期重启应用
   - **后续**: 实现缓冲区清理机制

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发指南

**环境设置**：
```bash
git clone https://github.com/orphiczhou/Smart-Ops-Term.git
cd Smart-Ops-Term
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**运行测试**（计划中）：
```bash
pytest tests/
```

**代码风格**：
- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 添加文档字符串（Docstrings）

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/orphiczhou/Smart-Ops-Term)
- **问题反馈**: [Issues](https://github.com/orphiczhou/Smart-Ops-Term/issues)
- **文档中心**:
  - [架构设计说明书](ARCHITECTURE.md)
  - [开发更新记录](CHANGELOG.md)

---

## 🙏 致谢

- **PyQt6**: 优秀的 Python GUI 框架
- **Paramiko**: 强大的 SSH 库
- **OpenAI**: AI 能力支持

---

**当前版本**: 1.6.1 (Stable Release)
**发布日期**: 2026-01-20
**项目状态**: ✅ 功能完整，可用于生产环境

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

Made with ❤️ by Smart-Ops-Term Development Team

**文档**:
- [架构设计说明书](ARCHITECTURE.md)
- [开发更新记录](CHANGELOG.md)
- [版本信息](version.txt)

</div>

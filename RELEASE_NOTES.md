# 🎉 Smart-Ops-Term v1.6.1 - 配置持久化修复版

> **发布日期**: 2026-01-20
> **项目地址**: [GitHub](https://github.com/orphiczhou/Smart-Ops-Term)

---

## 📋 版本概述

v1.6.1 是一个修复版本，解决了 v1.6.0 中配置持久化相关的问题，确保配置能够正确保存和加载。同时继承和稳定了 v1.5.0 和 v1.6.0 的所有功能。

---

## ✨ 本版本更新

### Bug 修复

| 问题 | 描述 |
|------|------|
| **配置持久化失效** | 修复 `migrate_env_to_config()` 每次启动都运行导致配置被覆盖的问题 |
| **设置对话框显示旧值** | 修复打开设置时显示缓存数据而非最新配置的问题 |
| **短提示词被误判** | 修复短提示词（如 "111"）被错误判断为不完整的问题 |
| **AI 配置不实时更新** | 修复 AI 配置修改后不立即生效的问题 |

### 技术改进

- 配置迁移逻辑优化：只在配置文件不存在时执行迁移
- 设置对话框初始化改进：每次打开时重新加载配置
- 系统提示词逻辑简化：只有空字符串才使用默认值

---

## 🎯 功能特性（完整列表）

### 🖥️ 多标签页终端 (v1.5.0)

- **多 SSH 连接管理**：同时管理多个 SSH 连接
- **独立会话**：每个标签页有独立的终端和 AI 聊天
- **连接配置管理**：保存和管理常用连接配置

### 🤖 AI 智能助手

- **深度集成 LLM**：支持 OpenAI、DeepSeek、Claude 等
- **自动分析**：执行命令后自动分析结果并继续下一步
- **上下文记忆**：保留最近 10-15 条对话历史
- **终端感知**：滑动窗口获取最近 500 行终端输出
- **危险命令检测**：自动检测并警告危险操作

### 💾 配置持久化 (v1.6.0)

- **可视化设置**：4 标签页设置对话框（AI、终端、界面、连接）
- **JSON 存储**：自动保存到 `~/.smartops/app_config.json`
- **窗口记忆**：记住窗口位置、大小、分割器位置
- **自动迁移**：从旧版 .env 文件自动迁移配置

### 🎨 现代化 UI

- **左右分栏布局**：可拖动调整
- **Markdown 渲染**：支持富文本显示
- **消息气泡设计**：直观的对话界面
- **可定制化**：字体、颜色、窗口大小可配置

---

## 📦 下载

### 源代码

```
Smart-Ops-Term-v1.6.1-Source.zip
```

**包含**：
- 完整源代码
- requirements.txt
- 文档和说明

### Windows 可执行文件

```
Smart-Ops-Term-v1.6.1-Windows.zip
```

**系统要求**：
- Windows 10/11
- 无需安装 Python

---

## 🚀 快速开始

### 方式一：从源代码运行

```bash
# 1. 克隆仓库
git clone https://github.com/orphiczhou/Smart-Ops-Term.git
cd Smart-Ops-Term

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. 安装依赖（使用清华镜像）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 运行应用
python src/main.py
```

### 方式二：Windows 可执行文件

1. 下载 `Smart-Ops-Term-v1.6.1-Windows.zip`
2. 解压到任意目录
3. 双击 `Smart-Ops-Term.exe` 运行

### 方式三：首次运行配置

首次启动时，应用会自动：
- 创建配置目录 `~/.smartops/`
- 从 `.env` 文件迁移配置（如果存在）
- 生成默认配置文件

您也可以通过设置界面配置：

1. 点击工具栏 **⚙️ Settings** 按钮
2. 在 **AI Settings** 标签页配置：
   - API Key
   - API Base
   - Model
   - Temperature
   - Max Tokens
   - System Prompt

---

## 📖 配置说明

### AI 提供商配置

**OpenAI**:
```env
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo
```

**DeepSeek**:
```env
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

**其他兼容 API**:
```env
OPENAI_API_BASE=https://your-provider.com/v1
OPENAI_MODEL=your-model-name
```

### 配置文件位置

- **新版配置**: `~/.smartops/app_config.json` (优先)
- **旧版配置**: `.env` (向后兼容)

---

## 📸 界面预览

### 主界面
- 多标签页 SSH 终端
- 左右分栏布局
- AI 助手实时对话

### 设置对话框
- **AI Settings**: AI 相关配置
- **Terminal**: 终端外观和行为
- **Interface**: 窗口和 UI 设置
- **Connection**: SSH 连接设置

---

## 📚 文档

| 文档 | 描述 |
|------|------|
| [使用指南](docs/USER_GUIDE.md) | 详细的使用说明 |
| [功能验证报告](docs/feature-verification-report.md) | v1.5.0/v1.6.0/v1.6.1 功能验证 |
| [架构设计文档](ARCHITECTURE.md) | 技术架构和实现细节 |
| [开发更新记录](CHANGELOG.md) | 完整的开发历史 |

---

## 🔜 后续计划

### 优先级 P0
- **改进终端输入方式** - 光标定位在显示区域

### 优先级 P1
- **命令自动补全** - Tab 键补全
- **主题切换** - 多种终端主题
- **单元测试** - 测试覆盖

### 优先级 P2
- **SFTP 文件传输** - 文件上传下载
- **会话录制和回放** - 记录操作
- **性能优化** - 减少内存占用

---

## 🐛 问题反馈

如有问题或建议，请在 [Issues](https://github.com/orphiczhou/Smart-Ops-Term/issues) 中提出。

### 常见问题

**Q: 配置没有保存？**
A: v1.6.1 已修复配置持久化问题。如果仍有问题，请检查 `~/.smartops/app_config.json` 文件权限。

**Q: AI 不响应？**
A: 请检查 API Key 和 API Base 配置是否正确，可在设置对话框中测试连接。

**Q: 多标签页切换慢？**
A: 这是正常现象，每个标签页维护独立的 SSH 连接和 AI 上下文。

---

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢以下开源项目：

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 优秀的 Python GUI 框架
- [Paramiko](https://www.paramiko.org/) - 强大的 SSH 库
- [OpenAI](https://openai.com/) - AI 能力支持

---

**完整更新日志**: [CHANGELOG.md](https://github.com/orphiczhou/Smart-Ops-Term/blob/main/CHANGELOG.md)

**上一版本**: [v1.6.0](https://github.com/orphiczhou/Smart-Ops-Term/releases/tag/v1.6.0)

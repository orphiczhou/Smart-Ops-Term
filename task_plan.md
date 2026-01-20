# GitHub Release Plan for Smart-Ops-Term v1.6.1

> **创建时间**: 2026-01-20
> **项目**: Smart-Ops-Term
> **目标版本**: v1.6.1 (配置持久化修复版)

---

## 📋 任务目标

发布 Smart-Ops-Term v1.6.1 到 GitHub，包含：
1. 创建 GitHub Release
2. 准备发布说明（Release Notes）
3. 编译 Windows 可执行文件（可选）
4. 准备使用文档和截图
5. 打包源代码

---

## 🎯 执行阶段

### Phase 1: 准备发布材料 ⏳

**状态**: `in_progress`

**任务清单**:
- [x] 更新 version.txt
- [x] 更新 CHANGELOG.md
- [x] 创建功能验证报告
- [x] 更新 README.md
- [ ] 创建 Release Notes
- [ ] 准备截图
- [ ] 创建使用指南
- [ ] 创建二进制发布包（可选）

**输出文件**:
- `RELEASE_NOTES.md` - 发布说明
- `docs/USER_GUIDE.md` - 使用指南
- `screenshots/` - 截图目录

---

### Phase 2: 创建 Git Tag

**状态**: `pending`

**任务**:
```bash
# 创建 annotated tag
git tag -a v1.6.1 -m "Release v1.6.1: 配置持久化修复版"

# 推送 tag 到远程
git push origin v1.6.1
```

---

### Phase 3: 打包发布文件

**状态**: `pending`

**任务**:
- 打包源代码压缩包
- 创建 Windows 可执行文件（可选，使用 PyInstaller）
- 准备安装说明

**输出文件**:
- `Smart-Ops-Term-v1.6.1-Source.zip` - 源代码压缩包
- `Smart-Ops-Term-v1.6.1-Windows.zip` - Windows 可执行文件（可选）

---

### Phase 4: 创建 GitHub Release

**状态**: `pending`

**任务**:
1. 访问 GitHub Releases 页面
2. 点击 "Draft a new release"
3. 选择标签 v1.6.1
4. 填写发布标题和说明
5. 上传发布文件
6. 发布

---

### Phase 5: 发布后验证

**状态**: `pending`

**任务**:
- 验证 Release 页面正确显示
- 验证下载链接可用
- 测试安装流程

---

## 📝 Release Notes 模板

```markdown
# 🎉 Smart-Ops-Term v1.6.1 - 配置持久化修复版

## ✨ 更新内容

### Bug 修复
- ✅ 修复配置持久化功能，配置现在可以正确保存和加载
- ✅ 修复 SettingsDialog 显示旧值的问题
- ✅ 修复短提示词被错误判断为不完整的问题
- ✅ 修复 AI 配置实时更新机制

### 新增功能（继承自 v1.6.0）
- 💾 配置持久化 - 可视化设置对话框
- 🖥️ 多标签页支持 - 同时管理多个 SSH 连接
- 🤖 AI 配置管理 - 支持多 AI API

## 📦 下载

### 源代码
[Smart-Ops-Term-v1.6.1-Source.zip](Smart-Ops-Term-v1.6.1-Source.zip)

### Windows 可执行文件（可选）
[Smart-Ops-Term-v1.6.1-Windows.zip](Smart-Ops-Term-v1.6.1-Windows.zip)

## 🚀 快速开始

### 从源代码运行

```bash
# 克隆仓库
git clone https://github.com/orphiczhou/Smart-Ops-Term.git
cd Smart-Ops-Term

# 安装依赖
pip install -r requirements.txt

# 运行应用
python src/main.py
```

### Windows 用户

下载可执行文件压缩包，解压后双击 `Smart-Ops-Term.exe` 即可运行。

## 📖 文档

- [使用指南](docs/USER_GUIDE.md)
- [功能验证报告](docs/feature-verification-report.md)
- [架构设计文档](ARCHITECTURE.md)
- [开发更新记录](CHANGELOG.md)

## 🐛 问题反馈

如有问题请在 [Issues](https://github.com/orphiczhou/Smart-Ops-Term/issues) 中提出。

---

**完整更新日志**: [CHANGELOG.md](https://github.com/orphiczhou/Smart-Ops-Term/blob/main/CHANGELOG.md)
```

---

## 📸 截图计划

需要准备的截图：

1. **主界面** - 多标签页 SSH 终端
2. **设置对话框** - AI Settings 标签页
3. **设置对话框** - Terminal 标签页
4. **AI 对话** - 显示 AI 助手交互
5. **配置文件** - `~/.smartops/app_config.json` 示例

---

## 🔧 可选：PyInstaller 打包

**打包命令**:
```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --onefile --windowed --name Smart-Ops-Term ^
    --icon=assets/icon.ico ^
    --add-data "src;src" ^
    --hidden-import=PyQt6 ^
    --hidden-import=paramiko ^
    src/main.py
```

---

## 📊 检查清单

发布前检查：

| 项目 | 状态 |
|------|------|
| version.txt 更新到 v1.6.1 | ✅ |
| CHANGELOG.md 添加版本记录 | ✅ |
| README.md 更新新功能 | ✅ |
| 功能验证报告完成 | ✅ |
| Release Notes 编写 | ⏳ |
| 截图准备 | ⏳ |
| 源代码打包 | ⏳ |
| Git Tag 创建 | ⏳ |
| GitHub Release 创建 | ⏳ |

---

## 🚨 已知问题

| 问题 | 严重程度 | 状态 |
|------|---------|------|
| 无 | - | ✅ |

---

## 📌 下一步

1. 创建 Release Notes 文档
2. 准备截图
3. 创建 Git Tag
4. 打包发布文件
5. 创建 GitHub Release

---

**最后更新**: 2026-01-20

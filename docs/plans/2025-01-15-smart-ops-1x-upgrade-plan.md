# Smart Ops 1.x 持续升级实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 在现有 Python + PyQt6 架构基础上，通过渐进式升级添加 2.0 计划中的核心功能

**架构:** 保持现有 MVC 架构不变，通过增量功能模块扩展，每个版本专注一个主题，按主题发布

**技术栈:** Python 3.10+, PyQt6 6.7.0, Paramiko 3.4.0, OpenAI SDK >=1.50.0

---

## 📋 升级路线图

```
v1.0.0 (2025-01-08) ✅ 已发布
    ↓
v1.5.0 - 多连接管理版 (6-8 周)
    ├── 多标签页 SSH (P0, 20-30h)
    ├── 连接池管理 (P0, 15-20h)
    ├── 快速连接搜索 (P1, 8-12h)
    ├── 连接分组/标签 (P1, 10-15h)
    └── 批量操作 (P1, 15-20h)
    ↓
v1.6.0 - AI 增强版 (6-8 周)
    ├── 多模型切换 (P0, 10-15h)
    ├── 本地 LLM 支持 (P0, 15-20h)
    ├── 智能上下文压缩 (P1, 20-25h)
    └── AI 工作流模板 (P1, 15-20h)
    ↓
v1.7.0 - 体验优化版 (6-8 周)
    ├── 命令自动补全 (P0, 15-20h)
    ├── 主题系统 (P0, 12-18h)
    ├── 配置持久化 (P0, 10-15h)
    └── 终端光标定位 (P1, 20-30h)
    ↓
v1.8.0 - 运维效率版 (6-8 周)
    ├── 批量命令执行 (P0, 15-20h)
    ├── 会话录制/回放 (P0, 12-18h)
    ├── 简易仪表盘 (P1, 20-25h)
    └── 脚本自动化 (P1, 15-20h)
    ↓
v1.9.0 - 扩展生态版 (6-8 周)
    ├── 插件系统 (P0, 25-30h)
    ├── 自定义命令 (P1, 12-15h)
    └── Web 版（可选）(P2, 40-60h)
```

---

## 📂 关键文件路径

### 现有核心文件
```
d:\Codes\Smart-Ops-Term\
├── src/
│   ├── main.py                          # 应用入口
│   ├── controllers/
│   │   └── app_controller.py            # 主控制器 - 需要扩展
│   ├── views/
│   │   ├── main_window.py               # 主窗口 - 需要改为多标签
│   │   ├── terminal_widget.py           # 终端组件 - 可复用
│   │   ├── chat_widget.py               # AI聊天组件 - 可复用
│   │   └── password_dialog.py           # 密码对话框 - 可复用
│   ├── models/
│   │   ├── connection_handler.py        # 连接基类 - 需要扩展连接池
│   │   └── ssh_handler.py               # SSH处理器 - 可复用
│   ├── ai/
│   │   ├── ai_client.py                 # AI客户端 - 需要扩展多模型
│   │   ├── context_manager.py           # 上下文管理 - 需要添加压缩
│   │   └── command_parser.py            # 命令解析 - 可复用
│   └── utils/
│       └── ansi_filter.py               # ANSI过滤器 - 可复用
├── config/
│   └── settings.json                    # 需要创建
├── .env                                 # 环境变量 - 需要扩展
└── requirements.txt                     # 依赖 - 需要更新
```

---

## 🔧 v1.5.0 - 多连接管理版详细任务

### Task 1: 创建多标签页窗口

**目标:** 使用 QTabWidget 替换单一终端，支持多个 SSH 连接

**文件:**
- Modify: `src/views/main_window.py`
- Create: `src/views/multi_terminal_window.py`
- Test: `tests/test_multi_terminal.py`

**Step 1: 创建多终端窗口类**

创建新文件 `src/views/multi_terminal_window.py`:

```python
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget,
                             QHBoxLayout, QVBoxLayout, QPushButton)
from PyQt6.QtCore import Qt
from .terminal_widget import TerminalWidget
from .chat_widget import AIChatWidget
from controllers.app_controller import AppController


class MultiTerminalWindow(QMainWindow):
    """多标签页终端窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Ops Terminal - Multi Session")
        self.setGeometry(100, 100, 1400, 800)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 标签页组件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tab_widget)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 存储 tab 信息: tab_id -> {terminal, chat, controller}
        self.tabs = {}
        self.next_tab_id = 1

    def _create_toolbar(self):
        """创建工具栏"""
        from PyQt6.QtWidgets import QToolBar
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # 新建连接按钮
        new_conn_btn = QPushButton("新建连接")
        new_conn_btn.clicked.connect(self.new_connection)
        toolbar.addWidget(new_conn_btn)

        return toolbar

    def new_connection(self, connection_info=None):
        """新建 SSH 连接标签页"""
        # 创建组件
        terminal = TerminalWidget()
        ai_chat = AIChatWidget()
        controller = AppController(terminal, ai_chat)

        # 创建标签页
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.addWidget(terminal, stretch=6)
        layout.addWidget(ai_chat, stretch=4)

        # 添加到标签页
        tab_id = self.next_tab_id
        self.next_tab_id += 1

        tab_name = connection_info.get('name', f'SSH-{tab_id}') if connection_info else f'SSH-{tab_id}'
        index = self.tab_widget.addTab(tab, tab_name)
        self.tab_widget.setCurrentIndex(index)

        # 存储 tab 信息
        self.tabs[tab_id] = {
            'terminal': terminal,
            'chat': ai_chat,
            'controller': controller,
            'connection_info': connection_info
        }

        # 如果提供了连接信息，自动连接
        if connection_info:
            controller.connect_to_server(connection_info)

        return tab_id

    def close_tab(self, index):
        """关闭标签页"""
        tab = self.tab_widget.widget(index)
        if tab:
            # 断开 SSH 连接
            # 清理资源
            self.tab_widget.removeTab(index)

    def get_current_tab_id(self):
        """获取当前标签页 ID"""
        current_widget = self.tab_widget.currentWidget()
        for tab_id, info in self.tabs.items():
            if info['terminal'].parent() == current_widget:
                return tab_id
        return None
```

**Step 2: 修改 main.py 使用新窗口**

修改 `src/main.py`:

```python
# 原来的导入
# from views.main_window import MainWindow

# 新的导入
from views.multi_terminal_window import MultiTerminalWindow

def main():
    app = QApplication(sys.argv)
    # window = MainWindow()
    window = MultiTerminalWindow()
    window.show()
    sys.exit(app.exec())
```

**Step 3: 添加测试**

创建 `tests/test_multi_terminal.py`:

```python
import pytest
from PyQt6.QtWidgets import QApplication
import sys
from src.views.multi_terminal_window import MultiTerminalWindow

@pytest.fixture
def app():
    return QApplication.instance() or QApplication(sys.argv)

def test_multi_terminal_creation(app):
    """测试多终端窗口创建"""
    window = MultiTerminalWindow()
    assert window.tab_widget is not None
    assert window.tab_widget.tabsClosable() == True

def test_new_tab_creation(app):
    """测试新建标签页"""
    window = MultiTerminalWindow()
    initial_count = window.tab_widget.count()
    tab_id = window.new_connection()
    assert window.tab_widget.count() == initial_count + 1
    assert tab_id is not None
```

**Step 4: 运行测试验证**

```bash
cd d:\Codes\Smart-Ops-Term
pytest tests/test_multi_terminal.py -v
```

**Step 5: 提交**

```bash
git add src/views/multi_terminal_window.py src/main.py tests/test_multi_terminal.py
git commit -m "feat(v1.5.0): add multi-tab terminal window support"
```

---

### Task 2: 实现连接管理器

**目标:** 管理多个 SSH 连接，支持连接池和自动重连

**文件:**
- Create: `src/managers/connection_manager.py`
- Modify: `src/models/connection_handler.py`
- Test: `tests/test_connection_manager.py`

**Step 1: 扩展连接基类**

修改 `src/models/connection_handler.py` 添加连接状态:

```python
from PyQt6.QtCore import QObject, pyqtSignal
from enum import Enum
from typing import Optional

class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

class ConnectionHandler(QObject):
    # 现有信号...
    status_changed = pyqtSignal(str)  # 状态变更信号

    def __init__(self):
        super().__init__()
        self._status = ConnectionStatus.DISCONNECTED
        self._connection_id = None

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def connection_id(self) -> Optional[str]:
        return self._connection_id

    def set_connection_id(self, conn_id: str):
        """设置连接 ID"""
        self._connection_id = conn_id

    def _set_status(self, status: ConnectionStatus):
        """设置状态并发送信号"""
        if self._status != status:
            self._status = status
            self.status_changed.emit(status.value)
```

**Step 2: 创建连接管理器**

创建 `src/managers/connection_manager.py`:

```python
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from src.models.ssh_handler import SSHHandler
from src.models.connection_handler import ConnectionStatus

class ConnectionManager(QObject):
    """连接管理器 - 管理多个 SSH 连接"""

    connection_added = pyqtSignal(str)  # 连接添加信号
    connection_removed = pyqtSignal(str)  # 连接移除信号
    connection_status_changed = pyqtSignal(str, str)  # conn_id, status

    def __init__(self):
        super().__init__()
        self._connections: Dict[str, SSHHandler] = {}
        self._next_conn_id = 1

    def create_connection(self, connection_info: dict) -> str:
        """创建新连接并返回连接 ID"""
        conn_id = f"conn_{self._next_conn_id}"
        self._next_conn_id += 1

        # 创建 SSH 处理器
        ssh_handler = SSHHandler()
        ssh_handler.set_connection_id(conn_id)

        # 监听状态变化
        ssh_handler.status_changed.connect(
            lambda status: self.connection_status_changed.emit(conn_id, status)
        )

        # 建立连接
        success, message = ssh_handler.connect(
            host=connection_info.get('host'),
            port=connection_info.get('port', 22),
            username=connection_info.get('username'),
            password=connection_info.get('password')
        )

        if success:
            self._connections[conn_id] = ssh_handler
            self.connection_added.emit(conn_id)
            return conn_id
        else:
            raise ConnectionError(f"连接失败: {message}")

    def get_connection(self, conn_id: str) -> Optional[SSHHandler]:
        """获取连接"""
        return self._connections.get(conn_id)

    def remove_connection(self, conn_id: str):
        """移除连接"""
        if conn_id in self._connections:
            handler = self._connections[conn_id]
            handler.disconnect()
            del self._connections[conn_id]
            self.connection_removed.emit(conn_id)

    def get_all_connections(self) -> Dict[str, SSHHandler]:
        """获取所有连接"""
        return self._connections.copy()

    def reconnect(self, conn_id: str) -> bool:
        """重新连接"""
        if conn_id not in self._connections:
            return False

        handler = self._connections[conn_id]
        # 保存连接信息
        # TODO: 实现重连逻辑
        return True
```

**Step 3: 集成到多终端窗口**

修改 `src/views/multi_terminal_window.py`:

```python
from src.managers.connection_manager import ConnectionManager

class MultiTerminalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有代码 ...
        self.connection_manager = ConnectionManager()

    def new_connection(self, connection_info=None):
        """新建 SSH 连接标签页"""
        # 如果提供了连接信息，使用连接管理器
        if connection_info:
            try:
                conn_id = self.connection_manager.create_connection(connection_info)
                # 使用连接管理器的 handler 创建 controller
                ssh_handler = self.connection_manager.get_connection(conn_id)
                # ... 继续创建 UI
            except ConnectionError as e:
                print(f"连接失败: {e}")
                return None
        # ... 其余代码
```

**Step 4: 添加测试**

创建 `tests/test_connection_manager.py`:

```python
import pytest
from src.managers.connection_manager import ConnectionManager

def test_create_connection():
    """测试创建连接"""
    manager = ConnectionManager()
    conn_info = {
        'host': 'localhost',
        'port': 22,
        'username': 'test',
        'password': 'test'
    }
    # 注意: 需要 mock SSH 连接
    # conn_id = manager.create_connection(conn_info)
    # assert conn_id in manager.get_all_connections()

def test_remove_connection():
    """测试移除连接"""
    manager = ConnectionManager()
    # 添加连接后移除
    # manager.remove_connection(conn_id)
    # assert conn_id not in manager.get_all_connections()
```

**Step 5: 运行测试**

```bash
pytest tests/test_connection_manager.py -v
```

**Step 6: 提交**

```bash
git add src/managers/connection_manager.py src/models/connection_handler.py tests/test_connection_manager.py
git commit -m "feat(v1.5.0): add connection manager with connection pool support"
```

---

### Task 3: 添加快速连接搜索

**目标:** 快捷键搜索并连接到已保存的服务器

**文件:**
- Create: `src/widgets/quick_connect_dialog.py`
- Create: `src/managers/connection_profile_manager.py`
- Test: `tests/test_quick_connect.py`

**Step 1: 创建连接配置管理器**

创建 `src/managers/connection_profile_manager.py`:

```python
import json
from pathlib import Path
from typing import Dict, List, Optional

class ConnectionProfileManager:
    """连接配置管理器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path.home() / '.smartops' / 'connections.json'
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, dict] = {}
        self.load()

    def save_profile(self, name: str, profile: dict):
        """保存连接配置"""
        self.profiles[name] = profile
        self._save()

    def get_profile(self, name: str) -> Optional[dict]:
        """获取连接配置"""
        return self.profiles.get(name)

    def search_profiles(self, query: str) -> List[dict]:
        """搜索连接配置"""
        query = query.lower()
        results = []
        for name, profile in self.profiles.items():
            if query in name.lower() or query in profile.get('host', '').lower():
                results.append({'name': name, **profile})
        return results

    def delete_profile(self, name: str):
        """删除连接配置"""
        if name in self.profiles:
            del self.profiles[name]
            self._save()

    def load(self):
        """从文件加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.profiles = json.load(f)

    def _save(self):
        """保存到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)
```

**Step 2: 创建快速连接对话框**

创建 `src/widgets/quick_connect_dialog.py`:

```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit,
                             QListWidget, QListWidgetItem, QPushButton)
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from typing import Optional
from src.managers.connection_profile_manager import ConnectionProfileManager

class QuickConnectDialog(QDialog):
    """快速连接对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快速连接")
        self.setFixedSize(600, 400)

        self.profile_manager = ConnectionProfileManager()
        self.selected_profile: Optional[dict] = None

        self._setup_ui()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索服务器名称或地址...")
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # 结果列表
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self.results_list)

        # 按钮
        button_layout = QVBoxLayout()
        connect_btn = QPushButton("连接")
        connect_btn.clicked.connect(self._on_connect_clicked)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(connect_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # 初始加载
        self._load_all_profiles()

    def _load_all_profiles(self):
        """加载所有配置"""
        self.results_list.clear()
        for name, profile in self.profile_manager.profiles.items():
            item = QListWidgetItem(f"{name} ({profile.get('host', '')})")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.results_list.addItem(item)

    def _on_search_changed(self, text: str):
        """搜索文本变化"""
        results = self.profile_manager.search_profiles(text)
        self.results_list.clear()
        for profile in results:
            item = QListWidgetItem(f"{profile['name']} ({profile.get('host', '')})")
            item.setData(Qt.ItemDataRole.UserRole, profile['name'])
            self.results_list.addItem(item)

    def _on_item_selected(self, item: QListWidgetItem):
        """双击选中"""
        profile_name = item.data(Qt.ItemDataRole.UserRole)
        self.selected_profile = self.profile_manager.get_profile(profile_name)
        self.accept()

    def _on_connect_clicked(self):
        """连接按钮点击"""
        current_item = self.results_list.currentItem()
        if current_item:
            self._on_item_selected(current_item)

    def get_selected_profile(self) -> Optional[dict]:
        """获取选中的配置"""
        return self.selected_profile
```

**Step 3: 集成快捷键**

修改 `src/views/multi_terminal_window.py`:

```python
from PyQt6.QtGui import QKeySequence, QShortcut
from src.widgets.quick_connect_dialog import QuickConnectDialog

class MultiTerminalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有代码 ...

        # 添加快速连接快捷键 (Ctrl+K)
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """设置快捷键"""
        quick_connect_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        quick_connect_shortcut.activated.connect(self.show_quick_connect)

    def show_quick_connect(self):
        """显示快速连接对话框"""
        dialog = QuickConnectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile = dialog.get_selected_profile()
            if profile:
                self.new_connection(profile)
```

**Step 4: 添加测试**

创建 `tests/test_quick_connect.py`:

```python
import pytest
from src.managers.connection_profile_manager import ConnectionProfileManager
import tempfile

def test_save_and_load_profile():
    """测试保存和加载配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ConnectionProfileManager(f"{tmpdir}/test.json")

        profile = {
            'host': '192.168.1.100',
            'port': 22,
            'username': 'root'
        }
        manager.save_profile('test-server', profile)

        loaded = manager.get_profile('test-server')
        assert loaded == profile

def test_search_profiles():
    """测试搜索配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ConnectionProfileManager(f"{tmpdir}/test.json")

        manager.save_profile('prod-1', {'host': '192.168.1.1'})
        manager.save_profile('prod-2', {'host': '192.168.1.2'})
        manager.save_profile('test-1', {'host': '10.0.0.1'})

        results = manager.search_profiles('prod')
        assert len(results) == 2

        results = manager.search_profiles('192.168.1.1')
        assert len(results) == 1
```

**Step 5: 运行测试**

```bash
pytest tests/test_quick_connect.py -v
```

**Step 6: 提交**

```bash
git add src/widgets/quick_connect_dialog.py src/managers/connection_profile_manager.py tests/test_quick_connect.py
git commit -m "feat(v1.5.0): add quick connect dialog with profile search"
```

---

### Task 4: 实现连接分组

**目标:** 支持按环境/项目对连接进行分组管理

**文件:**
- Modify: `src/managers/connection_profile_manager.py`
- Create: `src/widgets/connection_group_widget.py`
- Test: `tests/test_connection_groups.py`

**Step 1: 扩展配置管理器支持分组**

修改 `src/managers/connection_profile_manager.py`:

```python
class ConnectionProfileManager:
    def __init__(self, config_path: str = None):
        # ... 现有代码 ...
        self.groups: Dict[str, List[str]] = {}  # group -> [profile_names]

    def create_group(self, group_name: str):
        """创建分组"""
        if group_name not in self.groups:
            self.groups[group_name] = []
            self._save()

    def add_to_group(self, group_name: str, profile_name: str):
        """添加配置到分组"""
        if group_name in self.groups:
            if profile_name not in self.groups[group_name]:
                self.groups[group_name].append(profile_name)
                self._save()

    def get_group_profiles(self, group_name: str) -> List[dict]:
        """获取分组中的所有配置"""
        if group_name not in self.groups:
            return []

        profiles = []
        for profile_name in self.groups[group_name]:
            profile = self.get_profile(profile_name)
            if profile:
                profiles.append({'name': profile_name, **profile})
        return profiles

    def get_all_groups(self) -> Dict[str, List[str]]:
        """获取所有分组"""
        return self.groups.copy()

    def _save(self):
        """保存到文件"""
        data = {
            'profiles': self.profiles,
            'groups': self.groups
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        """从文件加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.profiles = data.get('profiles', {})
                self.groups = data.get('groups', {})
```

**Step 2: 创建分组管理 UI**

创建 `src/widgets/connection_group_widget.py`:

```python
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QPushButton,
                             QLineEdit, QDialog, QFormLayout, QComboBox)
from PyQt6.QtCore import Qt
from src.managers.connection_profile_manager import ConnectionProfileManager

class ConnectionGroupWidget(QWidget):
    """连接分组管理组件"""

    group_selected = pyqtSignal(str)  # 分组选中信号
    profile_selected = pyqtSignal(dict)  # 配置选中信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile_manager = ConnectionProfileManager()
        self._setup_ui()
        self._load_groups()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)

        # 工具栏
        toolbar = QHBoxLayout()

        new_group_btn = QPushButton("新建分组")
        new_group_btn.clicked.connect(self._new_group)
        toolbar.addWidget(new_group_btn)

        layout.addLayout(toolbar)

        # 分组树
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "类型"])
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

    def _load_groups(self):
        """加载分组"""
        self.tree.clear()

        # 添加"全部"节点
        all_item = QTreeWidgetItem(["全部", "分组"])
        self.tree.addTopLevelItem(all_item)

        # 添加分组
        for group_name in self.profile_manager.get_all_groups().keys():
            group_item = QTreeWidgetItem([group_name, "分组"])
            self.tree.addTopLevelItem(group_item)

            # 添加分组下的配置
            profiles = self.profile_manager.get_group_profiles(group_name)
            for profile in profiles:
                profile_item = QTreeWidgetItem([profile['name'], "服务器"])
                profile_item.setData(0, Qt.ItemDataRole.UserRole, profile)
                group_item.addChild(profile_item)

        self.tree.expandAll()

    def _new_group(self):
        """新建分组"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新建分组")

        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        layout.addRow("分组名称:", name_input)

        # 添加要包含的配置
        profile_combo = QComboBox()
        for profile_name in self.profile_manager.profiles.keys():
            profile_combo.addItem(profile_name)
        layout.addRow("包含配置:", profile_combo)

        def save():
            name = name_input.text()
            if name:
                self.profile_manager.create_group(name)
                profile_name = profile_combo.currentText()
                if profile_name:
                    self.profile_manager.add_to_group(name, profile_name)
                self._load_groups()
                dialog.accept()

        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        dialog.exec()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击项目"""
        profile = item.data(0, Qt.ItemDataRole.UserRole)
        if profile:
            self.profile_selected.emit(profile)
```

**Step 3: 添加测试**

创建 `tests/test_connection_groups.py`:

```python
import pytest
from src.managers.connection_profile_manager import ConnectionProfileManager
import tempfile

def test_create_group():
    """测试创建分组"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ConnectionProfileManager(f"{tmpdir}/test.json")

        manager.create_group("production")
        assert "production" in manager.get_all_groups()

def test_add_to_group():
    """测试添加到分组"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ConnectionProfileManager(f"{tmpdir}/test.json")

        manager.save_profile("server1", {"host": "192.168.1.1"})
        manager.create_group("production")
        manager.add_to_group("production", "server1")

        profiles = manager.get_group_profiles("production")
        assert len(profiles) == 1
        assert profiles[0]["name"] == "server1"
```

**Step 4: 运行测试**

```bash
pytest tests/test_connection_groups.py -v
```

**Step 5: 提交**

```bash
git add src/widgets/connection_group_widget.py src/managers/connection_profile_manager.py tests/test_connection_groups.py
git commit -m "feat(v1.5.0): add connection grouping support"
```

---

### Task 5: 实现批量操作

**目标:** 在多个服务器上同时执行命令

**文件:**
- Create: `src/managers/batch_executor.py`
- Create: `src/widgets/batch_operation_dialog.py`
- Test: `tests/test_batch_operations.py`

**Step 1: 创建批量执行器**

创建 `src/managers/batch_executor.py`:

```python
from typing import List, Dict
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from src.models.ssh_handler import SSHHandler

class BatchExecutionWorker(QThread):
    """批量执行工作线程"""
    progress = pyqtSignal(str, str, str)  # server, output, status
    finished = pyqtSignal(dict)  # results

    def __init__(self, connections: Dict[str, SSHHandler], command: str):
        super().__init__()
        self.connections = connections
        self.command = command
        self.results = {}

    def run(self):
        """执行批量命令"""
        for conn_id, handler in self.connections.items():
            try:
                if not handler.is_connected:
                    self.progress.emit(conn_id, "", "跳过（未连接）")
                    continue

                success, output = handler.send_command(self.command)

                if success:
                    self.progress.emit(conn_id, output, "成功")
                    self.results[conn_id] = {"status": "success", "output": output}
                else:
                    self.progress.emit(conn_id, output, "失败")
                    self.results[conn_id] = {"status": "failed", "output": output}
            except Exception as e:
                error_msg = str(e)
                self.progress.emit(conn_id, error_msg, "错误")
                self.results[conn_id] = {"status": "error", "output": error_msg}

        self.finished.emit(self.results)

class BatchExecutor(QObject):
    """批量执行管理器"""

    def __init__(self):
        super().__init__()
        self.current_worker = None

    def execute_on_servers(self, connections: Dict[str, SSHHandler],
                          command: str, callback=None):
        """在多个服务器上执行命令"""
        self.current_worker = BatchExecutionWorker(connections, command)

        if callback:
            self.current_worker.finished.connect(callback)

        self.current_worker.start()
        return self.current_worker

    def is_running(self) -> bool:
        """检查是否有任务在运行"""
        return self.current_worker is not None and self.current_worker.isRunning()
```

**Step 2: 创建批量操作对话框**

创建 `src/widgets/batch_operation_dialog.py`:

```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QLineEdit, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from src.managers.batch_executor import BatchExecutor

class BatchOperationDialog(QDialog):
    """批量操作对话框"""

    def __init__(self, connections: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量命令执行")
        self.setFixedSize(800, 600)

        self.connections = connections
        self.executor = BatchExecutor()

        self._setup_ui()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)

        # 命令输入
        cmd_layout = QHBoxLayout()
        cmd_layout.addWidget(QLabel("命令:"))
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入要在所有服务器上执行的命令...")
        cmd_layout.addWidget(self.command_input)
        layout.addLayout(cmd_layout)

        # 执行按钮
        btn_layout = QHBoxLayout()
        self.execute_btn = QPushButton("执行")
        self.execute_btn.clicked.connect(self._execute_command)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self._stop_execution)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.execute_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["服务器", "状态", "输出", "时间"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.results_table)

        # 初始化表格行
        self.results_table.setRowCount(len(self.connections))
        for row, (conn_id, handler) in enumerate(self.connections.items()):
            self.results_table.setItem(row, 0, QTableWidgetItem(conn_id))
            self.results_table.setItem(row, 1, QTableWidgetItem("待执行"))

    def _execute_command(self):
        """执行命令"""
        command = self.command_input.text().strip()
        if not command:
            return

        self.execute_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 执行批量命令
        self.executor.execute_on_servers(
            self.connections,
            command,
            callback=self._on_execution_finished
        )

        # 连接进度信号
        if self.executor.current_worker:
            self.executor.current_worker.progress.connect(self._on_progress)

    def _on_progress(self, conn_id: str, output: str, status: str):
        """处理执行进度"""
        # 找到对应行
        for row in range(self.results_table.rowCount()):
            if self.results_table.item(row, 0).text() == conn_id:
                self.results_table.setItem(row, 1, QTableWidgetItem(status))
                self.results_table.setItem(row, 2, QTableWidgetItem(output[:100]))  # 限制显示长度
                break

    def _on_execution_finished(self, results: dict):
        """执行完成"""
        self.execute_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _stop_execution(self):
        """停止执行"""
        if self.executor.is_running():
            self.executor.current_worker.terminate()
            self.execute_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
```

**Step 3: 集成到多终端窗口**

修改 `src/views/multi_terminal_window.py`:

```python
from src.widgets.batch_operation_dialog import BatchOperationDialog

class MultiTerminalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有代码 ...

        # 添加批量操作按钮
        batch_btn = QPushButton("批量操作")
        batch_btn.clicked.connect(self.show_batch_operation)
        # toolbar.addWidget(batch_btn)

    def show_batch_operation(self):
        """显示批量操作对话框"""
        # 获取所有活跃连接
        connections = {}
        for tab_id, info in self.tabs.items():
            controller = info['controller']
            if controller.ssh_handler and controller.ssh_handler.is_connected:
                connections[tab_id] = controller.ssh_handler

        if connections:
            dialog = BatchOperationDialog(connections, self)
            dialog.exec()
```

**Step 4: 添加测试**

创建 `tests/test_batch_operations.py`:

```python
import pytest
from unittest.mock import Mock
from src.managers.batch_executor import BatchExecutor, BatchExecutionWorker

def test_batch_execution():
    """测试批量执行"""
    # 创建 mock SSH handlers
    connections = {}
    for i in range(3):
        mock_handler = Mock()
        mock_handler.is_connected = True
        mock_handler.send_command.return_value = (True, f"output{i}")
        connections[f"conn{i}"] = mock_handler

    # 创建执行器
    worker = BatchExecutionWorker(connections, "ls -la")
    # 在实际测试中需要运行线程并等待完成
    # worker.start()
    # worker.wait()
    # assert len(worker.results) == 3
```

**Step 5: 运行测试**

```bash
pytest tests/test_batch_operations.py -v
```

**Step 6: 提交**

```bash
git add src/managers/batch_executor.py src/widgets/batch_operation_dialog.py tests/test_batch_operations.py
git commit -m "feat(v1.5.0): add batch command execution support"
```

---

## 📦 v1.5.0 发布检查清单

**功能验证:**
- [ ] 多标签页可以正常创建和关闭
- [ ] 连接管理器可以管理多个连接
- [ ] 快速连接搜索功能正常
- [ ] 连接分组功能正常
- [ ] 批量操作可以在多服务器执行命令

**性能验证:**
- [ ] 多个连接同时打开时内存占用正常
- [ ] 批量操作不阻塞 UI
- [ ] 长时间运行无内存泄漏

**文档更新:**
- [ ] 更新 CHANGELOG.md
- [ ] 更新 version.txt (v1.5.0)
- [ ] 更新 README.md 新功能说明
- [ ] 更新 requirements.txt (如有新依赖)

**测试覆盖:**
- [ ] 所有新功能有对应测试
- [ ] 测试通过率 > 80%

---

## 🔧 v1.6.0 - AI 增强版任务概要

### Task 1: 多模型切换
- 扩展 AI 客户端支持多个提供商
- 统一接口封装 OpenAI、DeepSeek、Claude、Ollama
- 模型配置持久化

### Task 2: 本地 LLM 支持
- 集成 Ollama API
- 支持本地模型列表获取
- 本地模型性能优化

### Task 3: 智能上下文压缩
- 实现基于语义的上下文压缩算法
- 关键信息提取和保留
- Token 使用优化

### Task 4: AI 工作流模板
- 预定义运维场景模板
- 工作流执行引擎
- 自定义工作流支持

---

## 🔧 v1.7.0 - 体验优化版任务概要

### Task 1: 命令自动补全
- SSH 远程路径补全
- 命令历史补全
- 补全候选列表显示

### Task 2: 主题系统
- 预设主题集合
- QSS 样式表支持
- 主题切换和保存

### Task 3: 配置持久化
- JSON 配置文件
- 配置导入导出
- 配置版本管理

### Task 4: 终端光标定位
- 在 QTextEdit 中实现光标定位
- 光标移动限制
- 历史命令导航改进

---

## 🔧 v1.8.0 - 运维效率版任务概要

### Task 1: 批量命令执行 (已在 v1.5.0 实现，可增强)
- 脚本文件支持
- 执行结果导出
- 定时任务支持

### Task 2: 会话录制/回放
- asciinema 格式支持
- 会话录制控制
- 可视化回放界面

### Task 3: 简易仪表盘
- PyQt6 + pyqtgraph 图表
- 实时 CPU/内存监控
- SSH 命令收集系统信息

### Task 4: 脚本自动化
- 脚本编辑器
- 脚本模板库
- 执行日志记录

---

## 🔧 v1.9.0 - 扩展生态版任务概要

### Task 1: 插件系统
- Python 动态模块加载
- 插件 API 定义
- 插件沙箱隔离
- 插件管理 UI

### Task 2: 自定义命令
- 命令别名支持
- 命令组合
- 命令模板

### Task 3: Web 版（可选）
- Flask/FastAPI 后端
- WebSocket 终端支持
- 响应式前端

---

## 🧪 测试策略

### 单元测试
- 每个新模块都需要对应的单元测试
- 使用 pytest 框架
- 测试覆盖率目标: 80%+

### 集成测试
- 测试模块间的交互
- 端到端功能测试
- UI 自动化测试（可选）

### 性能测试
- 多连接内存占用测试
- 长时间运行稳定性测试
- 批量操作性能测试

---

## 📝 开发规范

### Git 提交规范
```
feat(version): description

例如:
feat(v1.5.0): add multi-tab terminal window support
fix(v1.5.0): fix connection memory leak
refactor(v1.5.0): extract connection manager from controller
docs(v1.5.0): update README for new features
test(v1.5.0): add tests for connection manager
```

### 代码规范
- 遵循 PEP 8
- 类型注解（使用 typing 模块）
- 文档字符串（Google 风格）
- 最大行长度: 100

### Review 流程
- 每个 Task 完成后提交
- 每个 version 完成后 Code Review
- 发布前进行完整测试

---

## ✅ 验证标准

### 功能验收标准
1. 所有计划功能实现完成
2. 所有测试通过
3. 文档更新完成
4. 无严重 Bug
5. 性能达标

### 发布准备
1. 更新版本号
2. 生成 CHANGELOG
3. 创建 Git Tag
4. 打包发布（如有需要）
5. 更新文档网站（如有）

---

**计划版本:** 1.0.0
**创建日期:** 2025-01-15
**计划方式:** writing-plans skill
**状态:** Ready for implementation

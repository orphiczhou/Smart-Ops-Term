"""
连接配置管理标签页组件
提供连接配置的增删改查、导入导出、测试连接功能

v1.6.1: 连接配置管理界面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QLabel,
                             QHeaderView, QMessageBox, QFileDialog,
                             QDialog, QFormLayout, QDialogButtonBox,
                             QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List, Optional
from models.connection_profile import ConnectionProfile
from managers.profile_manager import ProfileManager
import json


class ConnectionProfileDialog(QDialog):
    """
    添加/编辑连接配置的对话框
    """

    def __init__(self, profile: Optional[ConnectionProfile] = None, parent=None):
        """
        初始化对话框

        Args:
            profile: 现有配置（编辑模式），None 表示添加模式
            parent: 父窗口
        """
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("编辑配置" if profile else "添加配置")
        self._setup_ui()
        self._load_profile()

    def _setup_ui(self):
        """设置UI"""
        layout = QFormLayout()

        # 名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("生产服务器")
        layout.addRow("名称*:", self.name_input)

        # 主机
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.1.100")
        layout.addRow("主机*:", self.host_input)

        # 端口
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(22)
        layout.addRow("端口:", self.port_input)

        # 用户名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("root")
        layout.addRow("用户名:", self.username_input)

        # 密码
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("密码:", self.password_input)

        # 分组
        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("生产环境")
        layout.addRow("分组:", self.group_input)

        # 标签
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("linux,web,数据库 (逗号分隔)")
        layout.addRow("标签:", self.tags_input)

        # 描述
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("生产环境Web服务器")
        layout.addRow("描述:", self.description_input)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def _load_profile(self):
        """加载现有配置数据"""
        if self.profile:
            self.name_input.setText(self.profile.name)
            self.host_input.setText(self.profile.host)
            self.port_input.setValue(self.profile.port)
            self.username_input.setText(self.profile.username)
            self.password_input.setText(self.profile.password)
            if self.profile.group:
                self.group_input.setText(self.profile.group)
            if self.profile.tags:
                self.tags_input.setText(','.join(self.profile.tags))
            if self.profile.description:
                self.description_input.setText(self.profile.description)

            # 禁用名称编辑（配置名称不可改）
            self.name_input.setReadOnly(True)

    def get_profile(self) -> Optional[ConnectionProfile]:
        """
        获取用户输入的配置数据

        Returns:
            ConnectionProfile: 配置实例，验证失败返回 None
        """
        name = self.name_input.text().strip()
        host = self.host_input.text().strip()

        if not name or not host:
            QMessageBox.warning(self, "验证错误", "名称和主机为必填项")
            return None

        # 解析标签
        tags = [t.strip() for t in self.tags_input.text().split(',') if t.strip()]

        # 如果是编辑模式，保留 created_at 和 last_connected
        created_at = self.profile.created_at if self.profile else None
        last_connected = self.profile.last_connected if self.profile else None

        return ConnectionProfile(
            name=name,
            host=host,
            port=self.port_input.value(),
            username=self.username_input.text().strip(),
            password=self.password_input.text(),
            group=self.group_input.text().strip() or None,
            tags=tags,
            description=self.description_input.text().strip(),
            created_at=created_at,
            last_connected=last_connected
        )


class ConnectionProfilesTab(QWidget):
    """
    连接配置管理标签页

    提供配置列表和管理功能。
    """

    # 信号
    profile_selected = pyqtSignal(ConnectionProfile)  # 用户选择配置
    settings_changed = pyqtSignal()  # 配置变更

    def __init__(self, parent=None):
        """
        初始化标签页

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.profile_manager = ProfileManager()
        self._setup_ui()
        self._load_profiles()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()

        # 添加按钮
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.clicked.connect(self._add_profile)
        toolbar.addWidget(self.add_btn)

        # 编辑按钮
        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.clicked.connect(self._edit_profile)
        self.edit_btn.setEnabled(False)
        toolbar.addWidget(self.edit_btn)

        # 删除按钮
        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.clicked.connect(self._delete_profile)
        self.delete_btn.setEnabled(False)
        toolbar.addWidget(self.delete_btn)

        # 测试连接按钮
        self.test_btn = QPushButton("🔌 测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        self.test_btn.setEnabled(False)
        toolbar.addWidget(self.test_btn)

        toolbar.addStretch()

        # 导入按钮
        self.import_btn = QPushButton("📥 导入")
        self.import_btn.clicked.connect(self._import_profiles)
        toolbar.addWidget(self.import_btn)

        # 导出按钮
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.clicked.connect(self._export_profiles)
        toolbar.addWidget(self.export_btn)

        layout.addLayout(toolbar)

        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("按名称、主机或标签搜索...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # 配置列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "名称", "主机", "端口", "用户名", "分组", "标签", "最后连接"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        # 快速连接区域
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("快速连接:"))
        self.quick_connect_btn = QPushButton("连接到选中配置")
        self.quick_connect_btn.clicked.connect(self._quick_connect)
        self.quick_connect_btn.setEnabled(False)
        quick_layout.addWidget(self.quick_connect_btn)
        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        self.setLayout(layout)

    def _load_profiles(self, profiles: Optional[List[ConnectionProfile]] = None):
        """
        加载配置到表格

        Args:
            profiles: 配置列表，None 表示加载全部
        """
        if profiles is None:
            profiles = self.profile_manager.get_all_profiles()

        self.table.setRowCount(len(profiles))

        for row, profile in enumerate(profiles):
            # 名称
            self.table.setItem(row, 0, QTableWidgetItem(profile.name))
            # 主机
            self.table.setItem(row, 1, QTableWidgetItem(profile.host))
            # 端口
            self.table.setItem(row, 2, QTableWidgetItem(str(profile.port)))
            # 用户名
            self.table.setItem(row, 3, QTableWidgetItem(profile.username))
            # 分组
            self.table.setItem(row, 4, QTableWidgetItem(profile.group or "-"))
            # 标签
            tags_text = ', '.join(profile.tags) if profile.tags else "-"
            self.table.setItem(row, 5, QTableWidgetItem(tags_text))
            # 最后连接
            last_conn = profile.last_connected or "从未"
            self.table.setItem(row, 6, QTableWidgetItem(last_conn))

    def _on_selection_changed(self):
        """处理选择变化"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.test_btn.setEnabled(has_selection)
        self.quick_connect_btn.setEnabled(has_selection)

    def _on_double_click(self, item: QTableWidgetItem):
        """双击快速连接"""
        self._quick_connect()

    def _add_profile(self):
        """添加新配置"""
        dialog = ConnectionProfileDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile = dialog.get_profile()
            if profile:
                self.profile_manager.save_profile(profile)
                self._load_profiles()
                self.settings_changed.emit()
                QMessageBox.information(self, "成功", f"配置 '{profile.name}' 已添加")

    def _edit_profile(self):
        """编辑选中的配置"""
        row = self.table.currentRow()
        if row < 0:
            return

        # 从 ProfileManager 获取配置（确保数据最新）
        profile_name = self.table.item(row, 0).text()
        profile = self.profile_manager.get_profile(profile_name)

        if not profile:
            QMessageBox.warning(self, "错误", f"找不到配置: {profile_name}")
            return

        dialog = ConnectionProfileDialog(profile, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_profile = dialog.get_profile()
            if updated_profile:
                self.profile_manager.save_profile(updated_profile)
                self._load_profiles()
                self.settings_changed.emit()
                QMessageBox.information(self, "成功", f"配置 '{updated_profile.name}' 已更新")

    def _delete_profile(self):
        """删除选中的配置"""
        row = self.table.currentRow()
        if row < 0:
            return

        profile_name = self.table.item(row, 0).text()

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除配置 '{profile_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete_profile(profile_name)
            self._load_profiles()
            self.settings_changed.emit()
            QMessageBox.information(self, "成功", f"配置 '{profile_name}' 已删除")

    def _test_connection(self):
        """测试连接"""
        row = self.table.currentRow()
        if row < 0:
            return

        profile_name = self.table.item(row, 0).text()
        profile = self.profile_manager.get_profile(profile_name)

        if not profile:
            return

        # 显示测试对话框
        QMessageBox.information(
            self,
            "测试连接",
            f"正在测试连接到 {profile.host}:{profile.port}...\n\n"
            f"此功能需要集成 SSH 连接测试逻辑\n"
            f"(暂未实现)",
            QMessageBox.StandardButton.Ok
        )

    def _on_search(self, text: str):
        """
        搜索配置

        Args:
            text: 搜索关键词
        """
        if not text:
            self._load_profiles()
        else:
            results = self.profile_manager.search_profiles(text)
            self._load_profiles(results)

    def _import_profiles(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入配置",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 导入配置
                count = 0
                for name, profile_data in data.items():
                    profile = ConnectionProfile.from_dict(profile_data)
                    self.profile_manager.save_profile(profile)
                    count += 1

                self._load_profiles()
                self.settings_changed.emit()
                QMessageBox.information(self, "成功", f"已导入 {count} 个配置")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def _export_profiles(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出配置",
            "connections.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                # 从配置文件读取并导出（不包含密码）
                profiles = self.profile_manager.get_all_profiles()

                # 创建导出数据（移除密码）
                export_data = {}
                for profile in profiles:
                    profile_dict = profile.to_dict()
                    profile_dict['password'] = ""  # 不导出密码
                    export_data[profile.name] = profile_dict

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, "成功", f"已导出 {len(profiles)} 个配置")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def _quick_connect(self):
        """快速连接到选中的配置"""
        row = self.table.currentRow()
        if row < 0:
            return

        profile_name = self.table.item(row, 0).text()
        profile = self.profile_manager.get_profile(profile_name)

        if profile:
            # 发射信号，让主窗口处理连接
            self.profile_selected.emit(profile)

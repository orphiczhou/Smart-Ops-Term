"""
AI 配置管理标签页组件
提供 AI 配置的增删改查、设为默认功能

v1.6.1: 多 AI API 配置功能
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QLabel,
                             QHeaderView, QMessageBox, QDialog,
                             QFormLayout, QDialogButtonBox, QCheckBox, QComboBox,
                             QProgressDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List, Optional
from models.ai_profile import AIProfile
from managers.ai_profile_manager import AIProfileManager


class AIProfileDialog(QDialog):
    """
    添加/编辑 AI 配置的对话框

    支持预设模板和自定义配置。
    """

    # 预设模板
    PRESETS = {
        "自定义": None,
        "OpenAI GPT-4": {
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-4-turbo"
        },
        "OpenAI GPT-3.5": {
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo"
        },
        "DeepSeek": {
            "api_base": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "Claude (via OpenAI)": {
            "api_base": "https://api.anthropic.com/v1",
            "model": "claude-3-5-sonnet-20241022"
        }
    }

    def __init__(self, profile: Optional[AIProfile] = None, parent=None):
        """
        初始化对话框

        Args:
            profile: 现有配置（编辑模式），None 表示添加模式
            parent: 父窗口
        """
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("编辑 AI 配置" if profile else "添加 AI 配置")
        # v1.6.1: 对话框宽度加倍，以更好显示信息
        self.setMinimumWidth(600)  # 从默认约300增加到600
        self._setup_ui()
        self._load_profile()

    def _setup_ui(self):
        """设置UI"""
        layout = QFormLayout()

        # 名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("GPT-4")
        layout.addRow("配置名称*:", self.name_input)

        # 预设模板下拉框
        self.preset_combo = QComboBox()
        for preset_name in self.PRESETS.keys():
            self.preset_combo.addItem(preset_name, self.PRESETS[preset_name])
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        layout.addRow("预设模板:", self.preset_combo)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        layout.addRow("API Key*:", self.api_key_input)

        # API Base
        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("https://api.openai.com/v1")
        layout.addRow("API Base:", self.api_base_input)

        # Model
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("gpt-4-turbo")
        layout.addRow("模型:", self.model_input)

        # 设为默认
        self.default_check = QCheckBox("设为默认配置")
        layout.addRow("", self.default_check)

        # 描述
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("OpenAI GPT-4 Turbo")
        layout.addRow("描述:", self.description_input)

        # 测试按钮
        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("🔍 测试 API 连接")
        self.test_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_btn)
        test_layout.addStretch()
        layout.addRow("", test_layout)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def _on_preset_changed(self, index: int):
        """
        处理预设模板选择

        Args:
            index: 选中的索引
        """
        preset_data = self.preset_combo.currentData()
        if preset_data:
            self.api_base_input.setText(preset_data["api_base"])
            self.model_input.setText(preset_data["model"])

    def _load_profile(self):
        """加载现有配置数据"""
        if self.profile:
            self.name_input.setText(self.profile.name)
            self.api_key_input.setText(self.profile.api_key)
            self.api_base_input.setText(self.profile.api_base)
            self.model_input.setText(self.profile.model)
            self.default_check.setChecked(self.profile.is_default)
            if self.profile.description:
                self.description_input.setText(self.profile.description)

            # 禁用名称编辑（配置名称不可改）
            self.name_input.setReadOnly(True)

    def get_profile(self) -> Optional[AIProfile]:
        """
        获取用户输入的配置数据

        Returns:
            AIProfile: 配置实例，验证失败返回 None
        """
        name = self.name_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not name or not api_key:
            QMessageBox.warning(self, "验证错误", "配置名称和 API Key 为必填项")
            return None

        # 如果是编辑模式，保留 created_at
        created_at = self.profile.created_at if self.profile else None

        return AIProfile(
            name=name,
            api_key=api_key,
            api_base=self.api_base_input.text().strip() or "https://api.openai.com/v1",
            model=self.model_input.text().strip() or "gpt-4-turbo",
            is_default=self.default_check.isChecked(),
            description=self.description_input.text().strip(),
            created_at=created_at
        )

    def _test_connection(self):
        """
        测试 AI API 连接

        使用当前对话框中的配置信息进行测试。
        """
        import threading

        # 获取当前输入的配置
        api_key = self.api_key_input.text().strip()
        api_base = self.api_base_input.text().strip() or "https://api.openai.com/v1"
        model = self.model_input.text().strip() or "gpt-4-turbo"

        if not api_key:
            QMessageBox.warning(self, "测试失败", "请先输入 API Key")
            return

        # 创建测试对话框
        progress = QProgressDialog("正在测试 API 连接...", "取消", 0, 100, self)
        progress.setWindowTitle("测试 API")
        progress.setCancelButton(None)
        progress.show()

        # 在新线程中测试
        result = {'success': False, 'message': ''}

        def test_api_thread():
            try:
                # 直接使用 OpenAI SDK 测试
                from openai import OpenAI

                client = OpenAI(
                    api_key=api_key,
                    base_url=api_base
                )

                # 发送简单测试请求
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )

                result['success'] = True
                result['message'] = f"API 测试成功！\n模型: {model}\n响应: {response.choices[0].message.content}"

            except Exception as e:
                result['success'] = False
                result['message'] = f"API 测试失败:\n{str(e)}"

        thread = threading.Thread(target=test_api_thread)
        thread.start()
        thread.join(timeout=10)

        progress.close()

        # 显示结果
        if result['success']:
            QMessageBox.information(self, "测试成功", result['message'])
        else:
            QMessageBox.critical(self, "测试失败", result['message'])


class AIProfilesTab(QWidget):
    """
    AI 配置管理标签页

    提供配置列表和管理功能。
    """

    settings_changed = pyqtSignal()  # 配置变更信号

    def __init__(self, parent=None):
        """
        初始化标签页

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.profile_manager = AIProfileManager()
        self._setup_ui()
        self._load_profiles()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()

        # 添加按钮
        self.add_btn = QPushButton("➕ 添加配置")
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

        # 设为默认按钮
        self.set_default_btn = QPushButton("⭐ 设为默认")
        self.set_default_btn.clicked.connect(self._set_default)
        self.set_default_btn.setEnabled(False)
        toolbar.addWidget(self.set_default_btn)

        toolbar.addStretch()

        # 默认配置提示
        self.default_label = QLabel("默认配置: 无")
        self.default_label.setStyleSheet("color: gray; font-style: italic;")
        toolbar.addWidget(self.default_label)

        layout.addLayout(toolbar)

        # 配置列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "配置名称", "API Base", "模型", "默认", "描述"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self._update_default_label()

    def _load_profiles(self):
        """加载配置到表格"""
        profiles = self.profile_manager.get_all_profiles()
        self.table.setRowCount(len(profiles))

        for row, profile in enumerate(profiles):
            # 配置名称
            self.table.setItem(row, 0, QTableWidgetItem(profile.name))
            # API Base
            self.table.setItem(row, 1, QTableWidgetItem(profile.api_base))
            # 模型
            self.table.setItem(row, 2, QTableWidgetItem(profile.model))
            # 默认
            default_text = "⭐" if profile.is_default else ""
            default_item = QTableWidgetItem(default_text)
            if profile.is_default:
                default_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(row, 3, default_item)
            # 描述
            self.table.setItem(row, 4, QTableWidgetItem(profile.description or "-"))

    def _on_selection_changed(self):
        """处理选择变化"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.set_default_btn.setEnabled(has_selection)

    def _add_profile(self):
        """添加新配置"""
        dialog = AIProfileDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile = dialog.get_profile()
            if profile:
                self.profile_manager.save_profile(profile)
                self._load_profiles()
                self._update_default_label()
                self.settings_changed.emit()
                QMessageBox.information(self, "成功", f"AI 配置 '{profile.name}' 已添加")

    def _edit_profile(self):
        """编辑选中的配置"""
        row = self.table.currentRow()
        if row < 0:
            return

        profile_name = self.table.item(row, 0).text()
        profile = self.profile_manager.get_profile(profile_name)

        if not profile:
            QMessageBox.warning(self, "错误", f"找不到配置: {profile_name}")
            return

        dialog = AIProfileDialog(profile, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_profile = dialog.get_profile()
            if updated_profile:
                self.profile_manager.save_profile(updated_profile)
                self._load_profiles()
                self._update_default_label()
                self.settings_changed.emit()
                QMessageBox.information(self, "成功", f"AI 配置 '{updated_profile.name}' 已更新")

    def _delete_profile(self):
        """删除选中的配置"""
        row = self.table.currentRow()
        if row < 0:
            return

        profile_name = self.table.item(row, 0).text()

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 AI 配置 '{profile_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete_profile(profile_name)
            self._load_profiles()
            self._update_default_label()
            self.settings_changed.emit()
            QMessageBox.information(self, "成功", f"AI 配置 '{profile_name}' 已删除")

    def _set_default(self):
        """设置选中的配置为默认"""
        row = self.table.currentRow()
        if row < 0:
            return

        profile_name = self.table.item(row, 0).text()
        profile = self.profile_manager.get_profile(profile_name)

        if profile:
            profile.is_default = True
            self.profile_manager.save_profile(profile)
            self._load_profiles()
            self._update_default_label()
            self.settings_changed.emit()
            QMessageBox.information(self, "成功", f"已将 '{profile_name}' 设为默认 AI 配置")

    def _update_default_label(self):
        """更新默认配置标签"""
        default = self.profile_manager.get_default_profile()
        if default:
            self.default_label.setText(f"默认配置: {default.name} ({default.model})")
            self.default_label.setStyleSheet("color: #00aa00; font-weight: bold;")
        else:
            self.default_label.setText("默认配置: 无")
            self.default_label.setStyleSheet("color: gray; font-style: italic;")

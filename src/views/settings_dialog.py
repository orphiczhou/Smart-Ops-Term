"""
Settings dialog with tabbed interface.

Part of v1.6.0 configuration persistence feature.
v1.6.1: 添加 AI 配置管理和连接配置管理标签页
"""
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget,
                             QFormLayout, QLineEdit, QSpinBox, QCheckBox,
                             QDialogButtonBox, QColorDialog, QPushButton, QLabel,
                             QSlider, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from config.config_manager import ConfigManager
from config.settings import AppSettings


def _safe_print(*args, **kwargs):
    """安全打印，处理 Windows 控制台编码问题"""
    message = " ".join(str(arg) for arg in args)
    try:
        print(message, **kwargs)
    except UnicodeEncodeError:
        try:
            encoded = message.encode(sys.stdout.encoding, errors='replace')
            print(encoded.decode(sys.stdout.encoding), **kwargs)
        except:
            ascii_only = message.encode('ascii', errors='ignore').decode('ascii')
            print(ascii_only, **kwargs)


class SettingsDialog(QDialog):
    """应用设置对话框"""

    settings_applied = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager.get_instance()
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self._original_system_prompt = ""  # 保存原始系统提示词，用于比较
        # v1.6.1: 每次打开设置时重新加载配置，确保显示最新值
        self.config_manager.load()
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 添加各个设置页
        self.ai_tab = self._create_ai_tab()
        self.ai_profiles_tab = self._create_ai_profiles_tab()  # v1.6.1 新增
        self.terminal_tab = self._create_terminal_tab()
        self.ui_tab = self._create_ui_tab()
        self.connection_tab = self._create_connection_tab()
        self.profiles_tab = self._create_profiles_tab()  # v1.6.1 新增

        self.tab_widget.addTab(self.ai_tab, "AI Settings")
        self.tab_widget.addTab(self.ai_profiles_tab, "AI Profiles")  # v1.6.1 新增
        self.tab_widget.addTab(self.terminal_tab, "Terminal")
        self.tab_widget.addTab(self.ui_tab, "Interface")
        self.tab_widget.addTab(self.connection_tab, "Connection")
        self.tab_widget.addTab(self.profiles_tab, "Connection Profiles")  # v1.6.1 新增

        layout.addWidget(self.tab_widget)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Reset |
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)
        buttons.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset)
        buttons.accepted.connect(self._apply_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _create_ai_tab(self) -> QWidget:
        """创建AI设置页"""
        widget = QWidget()
        layout = QFormLayout()

        # Temperature - v1.6.1: 改为滑动条
        temp_layout = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 200)  # 0.0 - 2.0
        self.temperature_slider.setSingleStep(10)  # 0.1
        self.temperature_slider.setValue(70)  # 默认 0.7
        temp_layout.addWidget(self.temperature_slider)

        self.temperature_value_label = QLabel("0.70")
        self.temperature_value_label.setMinimumWidth(40)
        temp_layout.addWidget(self.temperature_value_label)

        # 连接滑动条值变化信号
        self.temperature_slider.valueChanged.connect(self._on_temperature_changed)

        layout.addRow("温度 (Temperature):", temp_layout)

        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 32000)
        self.max_tokens_spin.setSingleStep(500)
        layout.addRow("最大 Tokens (Max Tokens):", self.max_tokens_spin)

        # Max History
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(0, 50)
        layout.addRow("最大历史 (Max History):", self.max_history_spin)

        # System Prompt - 添加恢复默认按钮
        from PyQt6.QtWidgets import QPlainTextEdit, QPushButton, QGroupBox, QVBoxLayout
        prompt_group = QGroupBox("系统提示词 (System Prompt)")
        prompt_layout = QVBoxLayout()

        self.system_prompt_input = QPlainTextEdit()
        self.system_prompt_input.setMinimumHeight(150)
        self.system_prompt_input.setMaximumHeight(200)
        prompt_layout.addWidget(self.system_prompt_input)

        # 恢复默认按钮
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        self.reset_prompt_btn = QPushButton("🔄 恢复默认提示词")
        self.reset_prompt_btn.setToolTip("恢复到原始的完整系统提示词")
        self.reset_prompt_btn.clicked.connect(self._reset_system_prompt)
        reset_layout.addWidget(self.reset_prompt_btn)
        prompt_layout.addLayout(reset_layout)

        prompt_group.setLayout(prompt_layout)
        layout.addRow(prompt_group)

        widget.setLayout(layout)
        return widget

    def _create_terminal_tab(self) -> QWidget:
        """创建终端设置页"""
        widget = QWidget()
        layout = QFormLayout()

        # Font Family
        self.font_family_input = QLineEdit()
        layout.addRow("Font Family:", self.font_family_input)

        # Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        layout.addRow("Font Size:", self.font_size_spin)

        # Background Color
        bg_layout = QVBoxLayout()
        self.bg_color_input = QLineEdit()
        self.bg_color_input.setReadOnly(True)
        bg_btn = QPushButton("Choose Color")
        bg_btn.clicked.connect(self._choose_bg_color)
        bg_layout.addWidget(self.bg_color_input)
        bg_layout.addWidget(bg_btn)
        layout.addRow("Background:", bg_layout)

        # Text Color
        text_layout = QVBoxLayout()
        self.text_color_input = QLineEdit()
        self.text_color_input.setReadOnly(True)
        text_btn = QPushButton("Choose Color")
        text_btn.clicked.connect(self._choose_text_color)
        text_layout.addWidget(self.text_color_input)
        text_layout.addWidget(text_btn)
        layout.addRow("Text Color:", text_layout)

        # Cursor Blink
        self.cursor_blink_check = QCheckBox()
        layout.addRow("Cursor Blink:", self.cursor_blink_check)

        # Scroll on Output
        self.scroll_check = QCheckBox()
        layout.addRow("Scroll on Output:", self.scroll_check)

        # Max Lines
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(100, 2000)
        self.max_lines_spin.setSingleStep(100)
        layout.addRow("Max Lines:", self.max_lines_spin)

        widget.setLayout(layout)
        return widget

    def _create_ui_tab(self) -> QWidget:
        """创建界面设置页"""
        widget = QWidget()
        layout = QFormLayout()

        # Window Width
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        layout.addRow("Window Width:", self.window_width_spin)

        # Window Height
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        layout.addRow("Window Height:", self.window_height_spin)

        # Show Toolbar
        self.show_toolbar_check = QCheckBox()
        layout.addRow("Show Toolbar:", self.show_toolbar_check)

        # Show Statusbar
        self.show_statusbar_check = QCheckBox()
        layout.addRow("Show Statusbar:", self.show_statusbar_check)

        widget.setLayout(layout)
        return widget

    def _create_connection_tab(self) -> QWidget:
        """创建连接设置页"""
        widget = QWidget()
        layout = QFormLayout()

        # Timeout
        self.conn_timeout_spin = QSpinBox()
        self.conn_timeout_spin.setRange(5, 60)
        self.conn_timeout_spin.setSuffix(" sec")
        layout.addRow("Connection Timeout:", self.conn_timeout_spin)

        # Auto Save History
        self.auto_save_check = QCheckBox()
        layout.addRow("Auto Save History:", self.auto_save_check)

        # Max History Count
        self.max_history_count_spin = QSpinBox()
        self.max_history_count_spin.setRange(0, 50)
        layout.addRow("Max History Count:", self.max_history_count_spin)

        widget.setLayout(layout)
        return widget

    def _create_ai_profiles_tab(self) -> QWidget:
        """
        创建 AI 配置管理标签页

        v1.6.1: 多 AI API 配置管理
        """
        from views.ai_profiles_tab import AIProfilesTab

        widget = AIProfilesTab(self)
        widget.settings_changed.connect(self.settings_applied)  # 修复: settings_changed -> settings_applied
        return widget

    def _create_profiles_tab(self) -> QWidget:
        """
        创建连接配置管理标签页

        v1.6.1: 连接配置管理界面
        """
        from views.connection_profiles_tab import ConnectionProfilesTab

        widget = ConnectionProfilesTab(self)
        widget.settings_changed.connect(self.settings_applied)  # 修复: settings_changed -> settings_applied
        return widget

    def _load_current_settings(self):
        """加载当前设置到UI"""
        s = self.config_manager.settings

        # AI Settings
        # v1.6.1: 温度改为滑动条
        self.temperature_slider.setValue(int(s.ai.temperature * 100))
        self.temperature_value_label.setText(f"{s.ai.temperature:.2f}")
        self.max_tokens_spin.setValue(s.ai.max_tokens)
        self.max_history_spin.setValue(s.ai.max_history)
        # 系统提示词：v1.6.1 - 简化逻辑：只有空字符串才使用默认
        from ai.ai_client import AIClient
        self._original_system_prompt = s.ai.system_prompt  # 保存原始值

        # 正确的逻辑：
        # - 如果 system_prompt 为空字符串，使用默认提示词
        # - 任何非空字符串（不管多短）都是用户故意设置的自定义提示词
        if not s.ai.system_prompt:
            # 使用默认提示词
            prompt_to_show = AIClient.DEFAULT_SYSTEM_PROMPT
            _safe_print(f"[DEBUG SettingsDialog] 加载设置: 使用默认提示词 (保存为空)")
        else:
            # 使用保存的自定义提示词（不管多短，都是用户意图）
            prompt_to_show = s.ai.system_prompt
            _safe_print(f"[DEBUG SettingsDialog] 加载设置: 使用自定义提示词 (长度={len(s.ai.system_prompt)})")

        self.system_prompt_input.setPlainText(prompt_to_show)

        # Terminal Settings
        self.font_family_input.setText(s.terminal.font_family)
        self.font_size_spin.setValue(s.terminal.font_size)
        self.bg_color_input.setText(s.terminal.background_color)
        self.text_color_input.setText(s.terminal.text_color)
        self.cursor_blink_check.setChecked(s.terminal.cursor_blink)
        self.scroll_check.setChecked(s.terminal.scroll_on_output)
        self.max_lines_spin.setValue(s.terminal.max_lines)

        # UI Settings
        self.window_width_spin.setValue(s.ui.window_width)
        self.window_height_spin.setValue(s.ui.window_height)
        self.show_toolbar_check.setChecked(s.ui.show_toolbar)
        self.show_statusbar_check.setChecked(s.ui.show_statusbar)

        # Connection Settings
        self.conn_timeout_spin.setValue(s.connection.timeout)
        self.auto_save_check.setChecked(s.connection.auto_save_history)
        self.max_history_count_spin.setValue(s.connection.max_history_count)

    def _apply(self):
        """应用设置"""
        _safe_print(f"[DEBUG SettingsDialog] === 开始保存配置 ===")
        s = self.config_manager.settings

        # AI Settings
        # v1.6.1: 温度从滑动条读取
        s.ai.temperature = self.temperature_slider.value() / 100.0
        s.ai.max_tokens = self.max_tokens_spin.value()
        s.ai.max_history = self.max_history_spin.value()

        # 系统提示词：v1.6.1 简化逻辑 - 直接保存用户输入
        from ai.ai_client import AIClient
        current_prompt = self.system_prompt_input.toPlainText()

        _safe_print(f"[DEBUG SettingsDialog] 系统提示词输入: '{current_prompt[:50]}...' (长度: {len(current_prompt)})")

        # 简单直接的逻辑：
        # 1. 如果用户输入的是默认提示词（完整匹配），保存空字符串
        # 2. 否则，保存用户输入的内容（无论是什么，包括 "111"、空字符串等）
        if current_prompt == AIClient.DEFAULT_SYSTEM_PROMPT:
            s.ai.system_prompt = ""  # 标记使用默认
            _safe_print(f"[DEBUG SettingsDialog] -> 系统提示词: 保存为空（使用默认）")
        else:
            s.ai.system_prompt = current_prompt
            _safe_print(f"[DEBUG SettingsDialog] -> 系统提示词: 保存为自定义，长度: {len(s.ai.system_prompt)}")

        # 打印所有 AI 设置
        _safe_print(f"[DEBUG SettingsDialog] AI 设置预览:")
        _safe_print(f"[DEBUG SettingsDialog]   - temperature: {s.ai.temperature}")
        _safe_print(f"[DEBUG SettingsDialog]   - max_tokens: {s.ai.max_tokens}")
        _safe_print(f"[DEBUG SettingsDialog]   - max_history: {s.ai.max_history}")
        _safe_print(f"[DEBUG SettingsDialog]   - system_prompt: '{s.ai.system_prompt[:50]}...'")

        # Terminal Settings
        s.terminal.font_family = self.font_family_input.text()
        s.terminal.font_size = self.font_size_spin.value()
        s.terminal.background_color = self.bg_color_input.text()
        s.terminal.text_color = self.text_color_input.text()
        s.terminal.cursor_blink = self.cursor_blink_check.isChecked()
        s.terminal.scroll_on_output = self.scroll_check.isChecked()
        s.terminal.max_lines = self.max_lines_spin.value()

        # UI Settings
        s.ui.window_width = self.window_width_spin.value()
        s.ui.window_height = self.window_height_spin.value()
        s.ui.show_toolbar = self.show_toolbar_check.isChecked()
        s.ui.show_statusbar = self.show_statusbar_check.isChecked()

        # Connection Settings
        s.connection.timeout = self.conn_timeout_spin.value()
        s.connection.auto_save_history = self.auto_save_check.isChecked()
        s.connection.max_history_count = self.max_history_count_spin.value()

        # 保存前打印完整配置（预览前500字符）
        import json
        config_dict = self.config_manager.settings.to_dict()
        config_json = json.dumps(config_dict, indent=2, ensure_ascii=False)
        _safe_print(f"[DEBUG SettingsDialog] 完整配置预览 (前500字符):\n{config_json[:500]}...")

        # 保存
        _safe_print(f"[DEBUG SettingsDialog] 正在保存到: {self.config_manager._config_path}")
        result = self.config_manager.save()
        _safe_print(f"[DEBUG SettingsDialog] 保存结果: {result}")

        # 验证文件内容
        if self.config_manager._config_path.exists():
            with open(self.config_manager._config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                _safe_print(f"[DEBUG SettingsDialog] 文件内容预览 (前300字符):\n{content[:300]}...")
        else:
            _safe_print(f"[ERROR SettingsDialog] 保存后文件不存在！")

        self.settings_applied.emit()
        _safe_print(f"[DEBUG SettingsDialog] === 配置保存完成 ===")

    def _reset(self):
        """重置为默认值"""
        self.config_manager.reset_to_defaults()
        self._load_current_settings()

    def _apply_and_close(self):
        """应用并关闭"""
        self._apply()
        self.accept()

    def _choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color_input.setText(color.name())

    def _choose_text_color(self):
        """选择文本颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color_input.setText(color.name())

    def _on_temperature_changed(self, value: int):
        """
        处理温度滑动条值变化

        v1.6.1: 更新温度显示标签
        """
        temp_value = value / 100.0
        self.temperature_value_label.setText(f"{temp_value:.2f}")

    def _reset_system_prompt(self):
        """恢复系统提示词到默认值"""
        from ai.ai_client import AIClient
        self.system_prompt_input.setPlainText(AIClient.DEFAULT_SYSTEM_PROMPT)


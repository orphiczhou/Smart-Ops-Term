"""
SSH Connection dialog.

v1.6.1: 添加保存的连接配置选择功能
"""
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QDialogButtonBox, QComboBox, QPushButton, QWidget)
from PyQt6.QtCore import Qt

load_dotenv()


class ConnectionDialog(QDialog):
    """Dialog for collecting SSH connection information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Connection")
        self._setup_ui()
        # v1.6.1: 不加载默认值，保持中文占位符
        self._load_saved_profiles()
        self._load_ai_profiles()

    def _setup_ui(self):
        """Setup connection dialog UI."""
        layout = QVBoxLayout()

        # v1.6.1: 添加保存的配置选择区域
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("保存的配置:"))

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("-- 手动输入 --")
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
        profile_layout.addWidget(self.profile_combo)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("刷新配置列表")
        refresh_btn.clicked.connect(self._load_saved_profiles)
        profile_layout.addWidget(refresh_btn)

        layout.addLayout(profile_layout)

        # 分隔线
        from PyQt6.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        # Host
        layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("请输入主机地址")
        layout.addWidget(self.host_input)

        # Port
        layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("请输入端口号")
        layout.addWidget(self.port_input)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # v1.6.1: AI Profile 选择
        ai_layout = QHBoxLayout()
        ai_layout.addWidget(QLabel("AI 配置:"))

        self.ai_profile_combo = QComboBox()
        self.ai_profile_combo.addItem("使用默认 AI")
        ai_layout.addWidget(self.ai_profile_combo)

        layout.addLayout(ai_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _load_defaults(self):
        """Load default values from .env file."""
        default_host = os.getenv('DEFAULT_HOST', '')
        default_port = os.getenv('DEFAULT_PORT', '22')
        default_user = os.getenv('DEFAULT_USER', '')

        if default_host:
            self.host_input.setText(default_host)
        if default_port:
            self.port_input.setText(default_port)
        if default_user:
            self.username_input.setText(default_user)

    def get_connection_info(self) -> dict:
        """
        Return connection info as dictionary.

        v1.6.1: 包含 AI profile 选择
        """
        ai_profile = self.ai_profile_combo.currentData()
        return {
            'host': self.host_input.text().strip(),
            'port': int(self.port_input.text().strip() or "22"),
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),
            'ai_profile': ai_profile  # v1.6.1: 添加 AI profile
        }

    def set_connection_info(self, host: str, port: int, username: str, password: str = ""):
        """Set connection info fields programmatically."""
        self.host_input.setText(host)
        self.port_input.setText(str(port))
        self.username_input.setText(username)
        self.password_input.setText(password)

    def _clear_form(self):
        """
        清空连接表单

        v1.6.1: 新建连接时默认显示空表单
        """
        self.host_input.clear()
        self.port_input.setText("22")
        self.username_input.clear()
        self.password_input.clear()
        print(f"[DEBUG] Connection form cleared")

    def _load_saved_profiles(self):
        """
        加载保存的连接配置到下拉框

        v1.6.1: 从 ProfileManager 加载保存的配置
        """
        # 保存当前选择
        current_index = self.profile_combo.currentIndex()
        current_data = self.profile_combo.currentData() if current_index > 0 else None

        # 清除现有项（保留第一项）
        while self.profile_combo.count() > 1:
            self.profile_combo.removeItem(1)

        # 加载保存的配置
        try:
            from managers.profile_manager import ProfileManager
            manager = ProfileManager()
            profiles = manager.get_all_profiles()

            for profile in profiles:
                label = f"{profile.name} ({profile.host}:{profile.port})"
                self.profile_combo.addItem(label, profile.name)

            print(f"[DEBUG] Loaded {len(profiles)} saved profiles")
        except Exception as e:
            print(f"[DEBUG] Failed to load saved profiles: {e}")

        # 恢复选择
        if current_data:
            for i in range(1, self.profile_combo.count()):
                if self.profile_combo.itemData(i) == current_data:
                    self.profile_combo.setCurrentIndex(i)
                    break
        else:
            self.profile_combo.setCurrentIndex(0)

    def _on_profile_selected(self, index: int):
        """
        处理配置选择

        v1.6.1: 当用户选择保存的配置时，自动填充表单；选择手动输入时清空表单
        """
        if index <= 0:  # 第一项是手动输入
            # 清空表单，让用户手动输入
            self.host_input.clear()
            self.port_input.setText("22")
            self.username_input.clear()
            self.password_input.clear()
            print(f"[DEBUG] Cleared form for manual input")
            return

        profile_name = self.profile_combo.currentData()
        if not profile_name:
            return

        try:
            from managers.profile_manager import ProfileManager
            manager = ProfileManager()
            profile = manager.get_profile(profile_name)

            if profile:
                self.host_input.setText(profile.host)
                self.port_input.setText(str(profile.port))
                self.username_input.setText(profile.username)
                self.password_input.setText(profile.password)  # 密码已保存

                print(f"[DEBUG] Loaded profile: {profile_name}")
        except Exception as e:
            print(f"[DEBUG] Failed to load profile: {e}")

    def _load_ai_profiles(self):
        """
        加载可用的 AI profile 列表到下拉框

        v1.6.1: 添加 AI 配置选择功能
        """
        try:
            from managers.ai_profile_manager import AIProfileManager
            ai_manager = AIProfileManager()
            profiles = ai_manager.get_all_profiles()

            # 清除现有项（保留第一项"使用默认 AI"）
            while self.ai_profile_combo.count() > 1:
                self.ai_profile_combo.removeItem(1)

            if profiles:
                for profile in profiles:
                    # 显示 AI 配置名称和模型
                    label = f"{profile.name} ({profile.model})"
                    self.ai_profile_combo.addItem(label, profile.name)

                print(f"[DEBUG ConnectionDialog] Loaded {len(profiles)} AI profiles")
            else:
                print(f"[DEBUG ConnectionDialog] No AI profiles found")

        except Exception as e:
            print(f"[DEBUG ConnectionDialog] Failed to load AI profiles: {e}")

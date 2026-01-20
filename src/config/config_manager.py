"""
Configuration manager - Singleton pattern.
Manages loading, saving, and accessing application settings.

Part of v1.6.0 configuration persistence feature.
"""
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from config.settings import AppSettings
import sys


def _safe_print(*args, **kwargs):
    """安全打印，处理 Windows 控制台编码问题"""
    # 将所有参数转换为字符串
    message = " ".join(str(arg) for arg in args)
    try:
        print(message, **kwargs)
    except UnicodeEncodeError:
        # 如果编码失败，尝试使用 replace 模式
        try:
            encoded = message.encode(sys.stdout.encoding, errors='replace')
            print(encoded.decode(sys.stdout.encoding), **kwargs)
        except:
            # 最后的备选方案：移除所有非 ASCII 字符
            ascii_only = message.encode('ascii', errors='ignore').decode('ascii')
            print(ascii_only, **kwargs)


class ConfigManager(QObject):
    """
    单例配置管理器
    - 加载/保存配置文件
    - 提供全局访问点
    - 通知配置变更
    """
    _instance: Optional['ConfigManager'] = None

    # 信号定义
    settings_changed = pyqtSignal()  # 配置变更时发射

    def __init__(self):
        super().__init__()
        self._config_path = Path.home() / '.smartops' / 'app_config.json'
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings = AppSettings()

    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> bool:
        """从文件加载配置"""
        try:
            _safe_print(f"[DEBUG ConfigManager] 尝试从 {self._config_path} 加载配置")
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                    if data.strip():
                        import json
                        self._settings = AppSettings.from_dict(json.loads(data))
                        _safe_print(f"[DEBUG ConfigManager] 配置加载成功:")
                        _safe_print(f"[DEBUG ConfigManager]   - ai.system_prompt: '{self._settings.ai.system_prompt[:50]}...'")
                        _safe_print(f"[DEBUG ConfigManager]   - ai.temperature: {self._settings.ai.temperature}")
                        _safe_print(f"[DEBUG ConfigManager]   - ai.max_tokens: {self._settings.ai.max_tokens}")
                        _safe_print(f"[DEBUG ConfigManager]   - ai.max_history: {self._settings.ai.max_history}")
                        return True
            _safe_print(f"[DEBUG ConfigManager] 配置文件不存在或为空，使用默认值")
            return False
        except Exception as e:
            _safe_print(f"[ERROR ConfigManager] 加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save(self) -> bool:
        """保存配置到文件"""
        try:
            import json
            import traceback
            data = self._settings.to_dict()

            # 打印调用栈，找出是谁调用了 save()
            stack = traceback.extract_stack()
            caller = stack[-2] if len(stack) >= 2 else stack[-1]
            _safe_print(f"[DEBUG ConfigManager] === save() 被调用 ===")
            _safe_print(f"[DEBUG ConfigManager]   调用者: {caller.filename}:{caller.lineno} in {caller.name}")
            _safe_print(f"[DEBUG ConfigManager] 准备保存配置:")
            _safe_print(f"[DEBUG ConfigManager]   - ai.system_prompt: '{data['ai']['system_prompt'][:50]}...'")
            _safe_print(f"[DEBUG ConfigManager]   - ai.temperature: {data['ai']['temperature']}")
            _safe_print(f"[DEBUG ConfigManager]   - ai.max_tokens: {data['ai']['max_tokens']}")
            _safe_print(f"[DEBUG ConfigManager]   - ai.max_history: {data['ai']['max_history']}")

            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            _safe_print(f"[DEBUG ConfigManager] 配置已保存到 {self._config_path}")
            return True
        except Exception as e:
            _safe_print(f"[ERROR ConfigManager] 保存失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    @property
    def settings(self) -> AppSettings:
        """获取当前设置（只读访问）"""
        return self._settings

    def update_settings(self, **kwargs):
        """
        更新配置并保存

        Args:
            **kwargs: 配置键值对，支持嵌套访问
                     例如: ai_api_key="xxx", terminal_font_size=16
        """
        for key, value in kwargs.items():
            parts = key.split('_')
            if len(parts) == 2:
                section, attr = parts
                if hasattr(self._settings, section):
                    section_obj = getattr(self._settings, section)
                    if hasattr(section_obj, attr):
                        setattr(section_obj, attr, value)

        self.save()
        self.settings_changed.emit()

    def reset_to_defaults(self):
        """重置为默认配置"""
        self._settings = AppSettings()
        self.save()
        self.settings_changed.emit()

"""
Application settings data models.
Uses dataclasses for type safety and easy serialization.

Part of v1.6.0 configuration persistence feature.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AISettings:
    """AI client configuration"""
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4-turbo"
    timeout: int = 10
    max_history: int = 10
    temperature: float = 0.7
    max_tokens: int = 2000
    # 使用占位符作为默认值，实际加载时会使用 AIClient.DEFAULT_SYSTEM_PROMPT
    system_prompt: str = ""

    def to_dict(self) -> dict:
        return {
            'api_key': self.api_key,
            'api_base': self.api_base,
            'model': self.model,
            'timeout': self.timeout,
            'max_history': self.max_history,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'system_prompt': self.system_prompt
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AISettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class TerminalSettings:
    """Terminal appearance and behavior"""
    font_family: str = "Consolas"
    font_size: int = 14
    background_color: str = "#1e1e1e"
    text_color: str = "#00ff00"
    cursor_blink: bool = True
    scroll_on_output: bool = True
    max_lines: int = 500

    def to_dict(self) -> dict:
        return {
            'font_family': self.font_family,
            'font_size': self.font_size,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'cursor_blink': self.cursor_blink,
            'scroll_on_output': self.scroll_on_output,
            'max_lines': self.max_lines
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TerminalSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class UISettings:
    """Window and UI state"""
    window_width: int = 1200
    window_height: int = 700
    window_x: int = 100
    window_y: int = 100
    splitter_position: int = 600
    show_toolbar: bool = True
    show_statusbar: bool = True

    def to_dict(self) -> dict:
        return {
            'window_width': self.window_width,
            'window_height': self.window_height,
            'window_x': self.window_x,
            'window_y': self.window_y,
            'splitter_position': self.splitter_position,
            'show_toolbar': self.show_toolbar,
            'show_statusbar': self.show_statusbar
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UISettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ConnectionSettings:
    """SSH connection settings"""
    timeout: int = 10
    auto_save_history: bool = True
    max_history_count: int = 10

    def to_dict(self) -> dict:
        return {
            'timeout': self.timeout,
            'auto_save_history': self.auto_save_history,
            'max_history_count': self.max_history_count
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConnectionSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class AppSettings:
    """Main application settings container"""
    ai: AISettings = field(default_factory=AISettings)
    terminal: TerminalSettings = field(default_factory=TerminalSettings)
    ui: UISettings = field(default_factory=UISettings)
    connection: ConnectionSettings = field(default_factory=ConnectionSettings)

    def to_dict(self) -> dict:
        return {
            'ai': self.ai.to_dict(),
            'terminal': self.terminal.to_dict(),
            'ui': self.ui.to_dict(),
            'connection': self.connection.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AppSettings':
        return cls(
            ai=AISettings.from_dict(data.get('ai', {})),
            terminal=TerminalSettings.from_dict(data.get('terminal', {})),
            ui=UISettings.from_dict(data.get('ui', {})),
            connection=ConnectionSettings.from_dict(data.get('connection', {}))
        )

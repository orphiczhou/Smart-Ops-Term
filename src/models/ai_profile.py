"""
AI 配置文件数据模型
支持多个 AI API 配置（OpenAI、DeepSeek、Claude 等）

v1.6.1: 多 AI API 配置功能
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class AIProfile:
    """
    AI API 配置文件

    存储单个 AI API 的配置信息，支持多个配置文件同时存在。
    """
    name: str  # 配置名称，如 "GPT-4"、"DeepSeek"
    api_key: str  # API Key
    api_base: str  # API Base URL
    model: str  # 模型名称
    is_default: bool = False  # 是否为默认配置
    description: str = ""  # 描述
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """
        转换为字典（用于JSON序列化）

        Returns:
            dict: 包含所有配置信息的字典
        """
        return {
            'name': self.name,
            'api_key': self._encode_api_key(self.api_key),
            'api_base': self.api_base,
            'model': self.model,
            'is_default': self.is_default,
            'description': self.description,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AIProfile':
        """
        从字典创建实例

        Args:
            data: 包含配置信息的字典

        Returns:
            AIProfile: AI 配置实例
        """
        return cls(
            name=data['name'],
            api_key=cls._decode_api_key(data.get('api_key', '')),
            api_base=data.get('api_base', 'https://api.openai.com/v1'),
            model=data.get('model', 'gpt-4-turbo'),
            is_default=data.get('is_default', False),
            description=data.get('description', ''),
            created_at=data.get('created_at')
        )

    @staticmethod
    def _encode_api_key(api_key: str) -> str:
        """
        简单编码 API Key（base64）

        Args:
            api_key: 原始 API Key

        Returns:
            str: Base64 编码后的 API Key
        """
        if not api_key:
            return ""
        import base64
        return base64.b64encode(api_key.encode()).decode()

    @staticmethod
    def _decode_api_key(encoded: str) -> str:
        """
        解码 API Key

        Args:
            encoded: Base64 编码的 API Key

        Returns:
            str: 原始 API Key
        """
        if not encoded:
            return ""
        try:
            import base64
            return base64.b64decode(encoded.encode()).decode()
        except Exception:
            return ""

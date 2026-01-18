"""
Connection profile data model.
Represents a saved SSH connection configuration.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import base64


@dataclass
class ConnectionProfile:
    """SSH connection configuration data model."""
    name: str
    host: str
    port: int = 22
    username: str = ""
    password: str = ""
    group: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_connected: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self._encode_password(self.password),
            'group': self.group,
            'tags': self.tags,
            'description': self.description,
            'created_at': self.created_at,
            'last_connected': self.last_connected
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConnectionProfile':
        """Create instance from dictionary."""
        return cls(
            name=data['name'],
            host=data['host'],
            port=data.get('port', 22),
            username=data.get('username', ''),
            password=cls._decode_password(data.get('password', '')),
            group=data.get('group'),
            tags=data.get('tags', []),
            description=data.get('description', ''),
            created_at=data.get('created_at'),
            last_connected=data.get('last_connected')
        )

    @staticmethod
    def _encode_password(password: str) -> str:
        """Encode password using base64."""
        if not password:
            return ""
        return base64.b64encode(password.encode()).decode()

    @staticmethod
    def _decode_password(encoded: str) -> str:
        """Decode password from base64."""
        if not encoded:
            return ""
        try:
            return base64.b64decode(encoded.encode()).decode()
        except Exception:
            return ""

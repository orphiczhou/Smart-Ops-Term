"""
AI 配置文件管理器
管理多个 AI API 配置的持久化

v1.6.1: 多 AI API 配置功能
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from models.ai_profile import AIProfile


class AIProfileManager:
    """
    AI 配置文件持久化管理器

    负责保存、加载和管理多个 AI API 配置。
    配置存储在 ~/.smartops/ai_profiles.json
    """

    DEFAULT_CONFIG_PATH = Path.home() / '.smartops' / 'ai_profiles.json'

    def __init__(self, config_path: Optional[Path | str] = None):
        """
        初始化管理器

        Args:
            config_path: 配置文件路径，默认为 ~/.smartops/ai_profiles.json
        """
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, AIProfile] = {}
        self.load()

    def save_profile(self, profile: AIProfile) -> None:
        """
        保存 AI 配置文件

        如果设置为默认配置，会取消其他配置的默认状态。

        Args:
            profile: AI 配置实例
        """
        # 如果设置为默认，取消其他配置的默认状态
        if profile.is_default:
            for p in self.profiles.values():
                p.is_default = False

        self.profiles[profile.name] = profile
        self._save()
        print(f"[DEBUG] AI Profile saved: {profile.name}")

    def get_profile(self, name: str) -> Optional[AIProfile]:
        """
        获取指定名称的配置

        Args:
            name: 配置名称

        Returns:
            AIProfile: 如果找到返回配置，否则返回 None
        """
        return self.profiles.get(name)

    def get_default_profile(self) -> Optional[AIProfile]:
        """
        获取默认配置

        Returns:
            AIProfile: 默认配置，如果没有则返回第一个配置，都没有则返回 None
        """
        # 先查找标记为默认的配置
        for profile in self.profiles.values():
            if profile.is_default:
                return profile

        # 如果没有默认配置，返回第一个配置
        if self.profiles:
            return next(iter(self.profiles.values()))

        return None

    def delete_profile(self, name: str) -> None:
        """
        删除配置

        Args:
            name: 配置名称
        """
        if name in self.profiles:
            del self.profiles[name]
            self._save()
            print(f"[DEBUG] AI Profile deleted: {name}")

    def get_all_profiles(self) -> List[AIProfile]:
        """
        获取所有配置

        Returns:
            List[AIProfile]: 所有配置列表
        """
        return list(self.profiles.values())

    def load(self) -> None:
        """
        从文件加载配置

        如果配置文件不存在或加载失败，profiles 将为空字典。
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.profiles = {
                        name: AIProfile.from_dict(profile_data)
                        for name, profile_data in data.items()
                    }
                print(f"[DEBUG] Loaded {len(self.profiles)} AI profiles from {self.config_path}")
            except Exception as e:
                print(f"[ERROR] Failed to load AI profiles: {e}")
                self.profiles = {}
        else:
            print(f"[DEBUG] AI profiles file not found, starting with empty profiles")

    def _save(self) -> None:
        """
        保存配置到文件

        将所有配置序列化为 JSON 并保存到文件。
        """
        data = {
            name: profile.to_dict()
            for name, profile in self.profiles.items()
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] Saved {len(self.profiles)} AI profiles to {self.config_path}")

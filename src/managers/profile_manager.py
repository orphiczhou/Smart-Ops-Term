"""
Profile persistence manager.
Manages saving and loading connection profiles.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from models.connection_profile import ConnectionProfile


class ProfileManager:
    """Connection profile persistence manager."""

    DEFAULT_CONFIG_PATH = Path.home() / '.smartops' / 'connections.json'

    def __init__(self, config_path: Optional[Path | str] = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, ConnectionProfile] = {}
        self.load()

    def save_profile(self, profile: ConnectionProfile) -> None:
        """Save a connection profile."""
        self.profiles[profile.name] = profile
        self._save()

    def get_profile(self, name: str) -> Optional[ConnectionProfile]:
        """Get a profile by name."""
        return self.profiles.get(name)

    def delete_profile(self, name: str) -> None:
        """Delete a profile."""
        if name in self.profiles:
            del self.profiles[name]
            self._save()

    def search_profiles(self, query: str) -> List[ConnectionProfile]:
        """Search profiles by name, host, or tags."""
        query = query.lower()
        results = []
        for profile in self.profiles.values():
            if (query in profile.name.lower() or
                query in profile.host.lower() or
                any(query in tag.lower() for tag in profile.tags)):
                results.append(profile)
        return results

    def get_all_profiles(self) -> List[ConnectionProfile]:
        """Get all profiles."""
        return list(self.profiles.values())

    def load(self) -> None:
        """Load profiles from file."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.profiles = {
                    name: ConnectionProfile.from_dict(profile_data)
                    for name, profile_data in data.items()
                }

    def _save(self) -> None:
        """Save profiles to file."""
        data = {
            name: profile.to_dict()
            for name, profile in self.profiles.items()
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
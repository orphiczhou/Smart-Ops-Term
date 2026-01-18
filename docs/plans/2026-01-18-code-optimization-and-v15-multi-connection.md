# Smart Ops Term Code Optimization & v1.5.0 Multi-Connection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor existing code quality issues and implement multi-connection architecture for v1.5.0

**Architecture:**
- Phase 1: Fix critical code quality issues (hardcoded values, long methods, duplicate code, thread safety, resource leaks)
- Phase 2: Build multi-connection infrastructure (data models, connection pool, profile persistence, session controllers)

**Tech Stack:** Python 3.10+, PyQt6 6.7.0, Paramiko 3.4.0, OpenAI SDK >=1.50.0

---

## Phase 1: Code Quality Optimization

### Task 1: Create Centralized Constants Configuration

**Files:**
- Create: `src/config/__init__.py`
- Create: `src/config/constants.py`

**Step 1: Create config directory and __init__.py**

```bash
mkdir -p src/config
```

Create `src/config/__init__.py`:
```python
"""Configuration module for Smart Ops Term."""
```

**Step 2: Create constants.py with all hardcoded values**

Create `src/config/constants.py`:
```python
"""
Application-wide constants.
Centralized configuration to avoid magic numbers and hardcoded values.
"""

class AppConstants:
    """Application constants"""

    # AI Feedback Timing
    AI_FEEDBACK_DELAY_MS = 1000

    # SSH Connection
    SSH_DEFAULT_PORT = 22
    SSH_TIMEOUT_SECONDS = 10
    SSH_CHANNEL_RECV_SIZE = 4096
    SSH_READ_THREAD_SLEEP_SEC = 0.01
    SSH_INIT_DELAY_SEC = 0.2
    THREAD_JOIN_TIMEOUT_SECONDS = 2

    # Terminal
    TERMINAL_MAX_LINES = 500
    TERMINAL_MAX_CHARS = 3000
    DEFAULT_TERMINAL_FONT_FAMILY = 'Consolas'
    DEFAULT_TERMINAL_FONT_SIZE = 14
    DEFAULT_TERMINAL_BACKGROUND = '#1e1e1e'
    DEFAULT_TERMINAL_TEXT_COLOR = '#00ff00'

    # Messages
    MSG_CONNECTING = "Connecting to {host}..."
    MSG_CONNECTED = "Connected to {host}"
    MSG_DISCONNECTED = "Disconnected from server"
    MSG_CONNECTION_FAILED = "Connection failed"
    MSG_NOT_CONNECTED = "Not connected to server. Please connect first."
    MSG_ANALYZING_OUTPUT = "正在分析命令执行结果..."

    # Password Prompts (Regex Patterns)
    PASSWORD_PATTERNS = [
        r'password\s*:',
        r'password\s+for\s+\S+:',
        r'enter\s+password',
        r'\[sudo\]\s+password',
        r'密码\s*:',
        r'请输入密码',
    ]
```

**Step 3: Verify Python syntax**

Run: `python -m py_compile src/config/constants.py`
Expected: No syntax errors

**Step 4: Commit**

```bash
git add src/config/
git commit -m "refactor: add centralized constants configuration"
```

---

### Task 2: Fix Duplicate Code in main_window.py

**Files:**
- Modify: `src/views/main_window.py:244-253`

**Step 1: Read the file to identify duplicate code**

Run: `grep -n "_show_connection_dialog" src/views/main_window.py`
Expected: Found at lines 199 and 244

**Step 2: Delete duplicate method (lines 244-253)**

Open `src/views/main_window.py` and delete lines 244-253 (the duplicate `_show_connection_dialog` method)

**Step 3: Verify syntax**

Run: `python -m py_compile src/views/main_window.py`
Expected: No syntax errors

**Step 4: Run application to verify**

Run: `python src/main.py`
Expected: Application starts, File -> Connect works

**Step 5: Commit**

```bash
git add src/views/main_window.py
git commit -m "fix: remove duplicate _show_connection_dialog method"
```

---

### Task 3: Replace Hardcoded Values in app_controller.py

**Files:**
- Modify: `src/controllers/app_controller.py:1-361`

**Step 1: Add import for constants**

Add at line 12 (after existing imports):
```python
from config.constants import AppConstants
```

**Step 2: Replace password prompt patterns initialization (lines 30-37)**

Replace:
```python
self._password_prompt_patterns = [
    re.compile(r'password\s*:', re.IGNORECASE),
    re.compile(r'password\s+for\s+\S+:', re.IGNORECASE),
    re.compile(r'enter\s+password', re.IGNORECASE),
    re.compile(r'\[sudo\]\s+password', re.IGNORECASE),
    re.compile(r'密码\s*:', re.IGNORECASE),
    re.compile(r'请输入密码', re.IGNORECASE),
]
```

With:
```python
self._password_prompt_patterns = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in AppConstants.PASSWORD_PATTERNS
]
```

**Step 3: Replace hardcoded timeout (line 251)**

Find: `self._ai_feedback_timer.start(1000)`
Replace with: `self._ai_feedback_timer.start(AppConstants.AI_FEEDBACK_DELAY_MS)`

**Step 4: Replace hardcoded message (line 300)**

Find: `self.main_window.chat_widget.append_system_message("正在分析命令执行结果...")`
Replace with: `self.main_window.chat_widget.append_system_message(AppConstants.MSG_ANALYZING_OUTPUT)`

**Step 5: Verify syntax**

Run: `python -m py_compile src/controllers/app_controller.py`
Expected: No syntax errors

**Step 6: Test application**

Run: `python src/main.py`
- Connect to a server
- Execute a command from AI
- Verify AI feedback works

**Step 7: Commit**

```bash
git add src/controllers/app_controller.py
git commit -m "refactor: replace hardcoded values with constants"
```

---

### Task 4: Split Long Method _on_data_received

**Files:**
- Modify: `src/controllers/app_controller.py:214-256`

**Step 1: Read current method**

Current method at lines 214-256 is 42 lines, handles too many responsibilities.

**Step 2: Extract _display_data helper method**

Add after line 213 (before `_on_data_received`):
```python
def _display_data(self, data: str) -> None:
    """Display data to terminal with HTML formatting."""
    html_data = ansi_to_html(data)
    self.main_window.terminal_widget.append_output_html(html_data)
```

**Step 3: Extract _update_context helper method**

Add after `_display_data`:
```python
def _update_context(self, data: str) -> None:
    """Update terminal context manager."""
    clean_data = strip_ansi(data)
    self.terminal_context.append(clean_data)
```

**Step 4: Extract _check_password_prompt helper method**

Add after `_update_context`:
```python
def _check_password_prompt(self, data: str) -> None:
    """Check if data contains password prompt."""
    if self._waiting_for_password:
        return

    clean_data = strip_ansi(data)
    for pattern in self._password_prompt_patterns:
        if pattern.search(clean_data):
            self._handle_password_prompt()
            break
```

**Step 5: Extract _trigger_ai_feedback_if_needed helper method**

Add after `_check_password_prompt`:
```python
def _trigger_ai_feedback_if_needed(self) -> None:
    """Trigger AI feedback if waiting for command output."""
    if not self._waiting_for_ai_feedback:
        return

    if self._ai_feedback_timer:
        self._ai_feedback_timer.stop()

    self._ai_feedback_timer = QTimer()
    self._ai_feedback_timer.setSingleShot(True)
    self._ai_feedback_timer.timeout.connect(self._send_feedback_to_ai)
    self._ai_feedback_timer.start(AppConstants.AI_FEEDBACK_DELAY_MS)
```

**Step 6: Extract _handle_error helper method**

Add after `_trigger_ai_feedback_if_needed`:
```python
def _handle_error(self, location: str, error: Exception) -> None:
    """Handle and display error message."""
    error_msg = f"[ERROR] {location}: {str(error)}"
    self.main_window.chat_widget.append_system_message(error_msg)
```

**Step 7: Refactor _on_data_received to use helpers**

Replace entire `_on_data_received` method (lines 214-256) with:
```python
@pyqtSlot(str)
def _on_data_received(self, data: str) -> None:
    """
    Handle data received from SSH server.
    Enhanced with automatic AI feedback loop and password prompt detection.
    """
    try:
        self._display_data(data)
        self._update_context(data)
        self._check_password_prompt(data)
        self._trigger_ai_feedback_if_needed()
    except Exception as e:
        self._handle_error("_on_data_received", e)
```

**Step 8: Verify syntax**

Run: `python -m py_compile src/controllers/app_controller.py`
Expected: No syntax errors

**Step 9: Test all terminal functions**

Run: `python src/main.py`
- Connect to server
- Execute commands
- Check password prompt still works
- Check AI feedback still works

**Step 10: Commit**

```bash
git add src/controllers/app_controller.py
git commit -m "refactor: split _on_data_received into smaller methods"
```

---

### Task 5: Add Thread Safety to SSHHandler

**Files:**
- Modify: `src/models/ssh_handler.py:1-155`

**Step 1: Add threading import**

Add at line 6 (after existing imports):
```python
import threading
```

**Step 2: Add state lock in __init__**

Add at line 22 (after `self._stop_reading = False`):
```python
self._state_lock = threading.Lock()
```

**Step 3: Protect _connected in connect method**

Modify line 69:
Replace: `self._connected = True`
With:
```python
with self._state_lock:
    self._connected = True
```

**Step 4: Protect _connected in error handlers**

Modify lines 80, 83, 86:
Replace: `self._connected = False`
With:
```python
with self._state_lock:
    self._connected = False
```

**Step 5: Protect _connected in _read_output**

Modify lines 111-131:
```python
def _read_output(self):
    """
    Background thread to continuously read output from SSH channel.
    Emits data_received signal with new data.
    """
    while True:
        with self._state_lock:
            if not self._connected or self._stop_reading:
                should_exit = not self._connected
                if should_exit:
                    break

        try:
            with self._state_lock:
                if not self.channel or not self.channel.recv_ready():
                    continue

            if self.channel and self.channel.recv_ready():
                data = self.channel.recv(4096)
                if data:
                    text = data.decode('utf-8', errors='ignore')
                    self.data_received.emit(text)
            else:
                time.sleep(0.01)
        except Exception as e:
            with self._state_lock:
                if self._connected:
                    self.connection_lost.emit(f"Read error: {str(e)}")
                break

    with self._state_lock:
        if self._connected:
            self._connected = False
            self.connection_lost.emit("Connection closed")
```

**Step 6: Protect _connected in close method**

Modify line 136:
Replace: `self._stop_reading = True`
With:
```python
with self._state_lock:
    self._stop_reading = True
    self._connected = False
```

**Step 7: Verify syntax**

Run: `python -m py_compile src/models/ssh_handler.py`
Expected: No syntax errors

**Step 8: Test connection**

Run: `python src/main.py`
- Connect to server
- Execute commands
- Disconnect
- Repeat to ensure no race conditions

**Step 9: Commit**

```bash
git add src/models/ssh_handler.py
git commit -m "fix: add thread safety to SSHHandler state management"
```

---

### Task 6: Improve Resource Cleanup in AppController

**Files:**
- Modify: `src/controllers/app_controller.py:353-361`

**Step 1: Read current cleanup method**

Current method at lines 353-361.

**Step 2: Replace with improved cleanup**

Replace entire `cleanup` method with:
```python
def cleanup(self) -> None:
    """Cleanup all resources before exit."""
    # Stop and cleanup timer
    if self._ai_feedback_timer:
        self._ai_feedback_timer.stop()
        self._ai_feedback_timer.deleteLater()
        self._ai_feedback_timer = None

    # Close SSH connection
    if self.ssh_handler:
        self.ssh_handler.close()
        self.ssh_handler = None

    # Clear AI conversation history
    if self.ai_client:
        self.ai_client.clear_history()

    # Clear terminal context
    if self.terminal_context:
        self.terminal_context.clear()
```

**Step 3: Verify syntax**

Run: `python -m py_compile src/controllers/app_controller.py`
Expected: No syntax errors

**Step 4: Test cleanup**

Run: `python src/main.py`
- Connect to server
- Close application
- Verify no resource warnings in console

**Step 5: Commit**

```bash
git add src/controllers/app_controller.py
git commit -m "fix: improve resource cleanup in AppController"
```

---

## Phase 2: Multi-Connection Architecture

### Task 7: Create ConnectionProfile Data Model

**Files:**
- Create: `src/models/connection_profile.py`
- Create: `tests/test_connection_profile.py`

**Step 1: Write test for ConnectionProfile**

Create `tests/test_connection_profile.py`:
```python
"""
Tests for ConnectionProfile data model.
"""
import pytest
from models.connection_profile import ConnectionProfile


def test_connection_profile_creation():
    """Test creating a connection profile."""
    profile = ConnectionProfile(
        name="test-server",
        host="192.168.1.100",
        port=22,
        username="root",
        password="testpass"
    )
    assert profile.name == "test-server"
    assert profile.host == "192.168.1.100"
    assert profile.port == 22
    assert profile.username == "root"


def test_connection_profile_serialization():
    """Test serializing profile to dict."""
    profile = ConnectionProfile(
        name="test-server",
        host="192.168.1.100",
        port=22,
        username="root",
        password="testpass"
    )
    data = profile.to_dict()

    assert data['name'] == "test-server"
    assert data['host'] == "192.168.1.100"
    assert data['port'] == 22
    assert 'password' in data
    assert data['password'] != "testpass"  # Should be encoded


def test_connection_profile_deserialization():
    """Test deserializing profile from dict."""
    data = {
        'name': 'test-server',
        'host': '192.168.1.100',
        'port': 22,
        'username': 'root',
        'password': 'dGVzdHBhc3M=',  # base64 encoded "testpass"
        'group': 'production',
        'tags': ['web', 'db'],
        'description': 'Test server'
    }

    profile = ConnectionProfile.from_dict(data)
    assert profile.name == "test-server"
    assert profile.host == "192.168.1.100"
    assert profile.port == 22
    assert profile.username == "root"
    assert profile.password == "testpass"  # Should be decoded
    assert profile.group == "production"
    assert profile.tags == ['web', 'db']
    assert profile.description == "Test server"


def test_password_encoding_decoding():
    """Test password encoding and decoding."""
    original = "my_secret_password"
    encoded = ConnectionProfile._encode_password(original)
    decoded = ConnectionProfile._decode_password(encoded)

    assert original == decoded
    assert encoded != original
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_connection_profile.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'models.connection_profile'"

**Step 3: Create ConnectionProfile model**

Create `src/models/connection_profile.py`:
```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_connection_profile.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/connection_profile.py tests/test_connection_profile.py
git commit -m "feat(v1.5.0): add ConnectionProfile data model"
```

---

### Task 8: Create ProfileManager for Config Persistence

**Files:**
- Create: `src/managers/__init__.py`
- Create: `src/managers/profile_manager.py`
- Create: `tests/test_profile_manager.py`

**Step 1: Create managers directory**

```bash
mkdir -p src/managers
```

**Step 2: Write test for ProfileManager**

Create `tests/test_profile_manager.py`:
```python
"""
Tests for ProfileManager.
"""
import pytest
import tempfile
from pathlib import Path
from managers.profile_manager import ProfileManager
from models.connection_profile import ConnectionProfile


@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        yield Path(f.name)
    # Cleanup handled by tempfile


def test_save_and_load_profile(temp_config_file):
    """Test saving and loading a profile."""
    manager = ProfileManager(config_path=temp_config_file)

    profile = ConnectionProfile(
        name="test-server",
        host="192.168.1.100",
        username="root",
        password="testpass"
    )

    manager.save_profile(profile)
    loaded = manager.get_profile("test-server")

    assert loaded is not None
    assert loaded.name == "test-server"
    assert loaded.host == "192.168.1.100"


def test_search_profiles(temp_config_file):
    """Test searching profiles."""
    manager = ProfileManager(config_path=temp_config_file)

    manager.save_profile(ConnectionProfile(name="prod-web", host="192.168.1.1"))
    manager.save_profile(ConnectionProfile(name="prod-db", host="192.168.1.2"))
    manager.save_profile(ConnectionProfile(name="test-server", host="10.0.0.1"))

    results = manager.search_profiles("prod")
    assert len(results) == 2

    results = manager.search_profiles("192.168.1.1")
    assert len(results) == 1


def test_delete_profile(temp_config_file):
    """Test deleting a profile."""
    manager = ProfileManager(config_path=temp_config_file)

    profile = ConnectionProfile(name="test", host="192.168.1.1")
    manager.save_profile(profile)

    assert manager.get_profile("test") is not None

    manager.delete_profile("test")
    assert manager.get_profile("test") is None
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_profile_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'managers.profile_manager'"

**Step 4: Create __init__.py for managers**

Create `src/managers/__init__.py`:
```python
"""Connection and profile managers."""
```

**Step 5: Create ProfileManager implementation**

Create `src/managers/profile_manager.py`:
```python
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

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
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
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_profile_manager.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/managers/ tests/test_profile_manager.py
git commit -m "feat(v1.5.0): add ProfileManager for config persistence"
```

---

### Task 9: Add ConnectionStatus Enum to ConnectionHandler

**Files:**
- Modify: `src/models/connection_handler.py:1-50`

**Step 1: Add enum import**

Add at line 4:
```python
from enum import Enum
```

**Step 2: Add ConnectionStatus enum**

Add after imports (before ConnectionHandler class):
```python
class ConnectionStatus(Enum):
    """Connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
```

**Step 3: Add status tracking to ConnectionHandler**

Add after line 10 (in `__init__` method):
```python
self._connection_id: Optional[str] = None
self._status = ConnectionStatus.DISCONNECTED
```

**Step 4: Add status_changed signal**

Add to signal declarations (around line 8):
```python
status_changed = pyqtSignal(str)
```

**Step 5: Add status properties and methods**

Add at end of class:
```python
@property
def status(self) -> ConnectionStatus:
    """Get current connection status."""
    return self._status

@property
def connection_id(self) -> Optional[str]:
    """Get connection ID."""
    return self._connection_id

def set_connection_id(self, conn_id: str) -> None:
    """Set connection ID."""
    self._connection_id = conn_id

def _set_status(self, status: ConnectionStatus) -> None:
    """Set status and emit signal."""
    if self._status != status:
        self._status = status
        self.status_changed.emit(status.value)
```

**Step 6: Verify syntax**

Run: `python -m py_compile src/models/connection_handler.py`
Expected: No syntax errors

**Step 7: Test with SSHHandler**

Run: `python -c "from models.ssh_handler import SSHHandler; from models.connection_handler import ConnectionStatus; h = SSHHandler(); print(h.status)"`
Expected: `ConnectionStatus.DISCONNECTED`

**Step 8: Commit**

```bash
git add src/models/connection_handler.py
git commit -m "refactor(v1.5.0): add ConnectionStatus enum to ConnectionHandler"
```

---

### Task 10: Create ConnectionManager for Multi-Connection Support

**Files:**
- Create: `src/managers/connection_manager.py`
- Create: `tests/test_connection_manager.py`

**Step 1: Write test for ConnectionManager**

Create `tests/test_connection_manager.py`:
```python
"""
Tests for ConnectionManager.
"""
import pytest
from unittest.mock import Mock, MagicMock
from managers.connection_manager import ConnectionManager
from models.connection_profile import ConnectionProfile


@pytest.fixture
def mock_ssh_handler():
    """Create a mock SSH handler."""
    handler = Mock()
    handler.is_connected = True
    handler.set_connection_id = Mock()
    handler.status_changed = Mock()
    handler.connect = Mock(return_value=(True, "Connected"))
    handler.close = Mock()
    return handler


def test_create_connection(mock_ssh_handler, monkeypatch):
    """Test creating a new connection."""
    # Mock SSHHandler creation
    monkeypatch.setattr("models.ssh_handler.SSHHandler", lambda: mock_ssh_handler)

    manager = ConnectionManager()
    profile = ConnectionProfile(
        name="test",
        host="192.168.1.1",
        username="root"
    )

    conn_id = manager.create_connection(profile)

    assert conn_id == "conn_1"
    assert conn_id in manager.get_all_connections()


def test_remove_connection(mock_ssh_handler, monkeypatch):
    """Test removing a connection."""
    monkeypatch.setattr("models.ssh_handler.SSHHandler", lambda: mock_ssh_handler)

    manager = ConnectionManager()
    profile = ConnectionProfile(name="test", host="192.168.1.1", username="root")

    conn_id = manager.create_connection(profile)
    manager.remove_connection(conn_id)

    assert conn_id not in manager.get_all_connections()


def test_get_active_connections(mock_ssh_handler, monkeypatch):
    """Test getting active connections."""
    monkeypatch.setattr("models.ssh_handler.SSHHandler", lambda: mock_ssh_handler)

    manager = ConnectionManager()
    profile = ConnectionProfile(name="test", host="192.168.1.1", username="root")

    conn_id = manager.create_connection(profile)
    active = manager.get_active_connections()

    assert conn_id in active
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_connection_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'managers.connection_manager'"

**Step 3: Create ConnectionManager implementation**

Create `src/managers/connection_manager.py`:
```python
"""
Connection pool manager.
Manages multiple SSH connections lifecycle.
"""
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from models.ssh_handler import SSHHandler
from models.connection_profile import ConnectionProfile
from config.constants import AppConstants


class ConnectionManager(QObject):
    """Connection pool manager for multiple SSH connections."""

    connection_added = pyqtSignal(str)
    connection_removed = pyqtSignal(str)
    connection_status_changed = pyqtSignal(str, str)
    connection_error = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._connections: Dict[str, SSHHandler] = {}
        self._connection_info: Dict[str, dict] = {}
        self._next_conn_id = 1

    def create_connection(self, profile: ConnectionProfile) -> str:
        """Create a new connection and return connection ID."""
        conn_id = f"conn_{self._next_conn_id}"
        self._next_conn_id += 1

        ssh_handler = SSHHandler()
        ssh_handler.set_connection_id(conn_id)

        ssh_handler.status_changed.connect(
            lambda status: self.connection_status_changed.emit(conn_id, status)
        )

        success, message = ssh_handler.connect(
            host=profile.host,
            port=profile.port,
            username=profile.username,
            password=profile.password,
            timeout=AppConstants.SSH_TIMEOUT_SECONDS
        )

        if success:
            self._connections[conn_id] = ssh_handler
            self._connection_info[conn_id] = profile.to_dict()
            self.connection_added.emit(conn_id)
            return conn_id
        else:
            raise ConnectionError(f"Connection failed: {message}")

    def get_connection(self, conn_id: str) -> Optional[SSHHandler]:
        """Get a specific connection."""
        return self._connections.get(conn_id)

    def remove_connection(self, conn_id: str) -> None:
        """Remove a connection and cleanup resources."""
        if conn_id in self._connections:
            handler = self._connections[conn_id]
            handler.close()
            del self._connections[conn_id]
            del self._connection_info[conn_id]
            self.connection_removed.emit(conn_id)

    def get_all_connections(self) -> Dict[str, SSHHandler]:
        """Get all active connections."""
        return self._connections.copy()

    def get_active_connections(self) -> Dict[str, SSHHandler]:
        """Get connected active connections."""
        return {
            conn_id: handler
            for conn_id, handler in self._connections.items()
            if handler.is_connected
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_connection_manager.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/managers/connection_manager.py tests/test_connection_manager.py
git commit -m "feat(v1.5.0): add ConnectionManager for multi-connection support"
```

---

## Verification Checklist

### Phase 1 Verification
- [ ] All constants in one file
- [ ] No duplicate code in main_window.py
- [ ] No hardcoded values in app_controller.py
- [ ] _on_data_received split into helper methods
- [ ] SSHHandler has thread safety
- [ ] AppController cleanup properly releases resources
- [ ] All tests pass
- [ ] Application starts and runs without errors

### Phase 2 Verification
- [ ] ConnectionProfile can serialize/deserialize
- [ ] ProfileManager saves/loads to JSON file
- [ ] ConnectionStatus enum defined and used
- [ ] ConnectionManager can create/remove connections
- [ ] All new tests pass

---

## Time Estimates

| Phase | Task | Estimated Time |
|-------|------|----------------|
| Phase 1 | Task 1: Constants | 30 min |
| Phase 1 | Task 2: Duplicate Code | 15 min |
| Phase 1 | Task 3: Replace Hardcoded | 45 min |
| Phase 1 | Task 4: Split Methods | 90 min |
| Phase 1 | Task 5: Thread Safety | 60 min |
| Phase 1 | Task 6: Resource Cleanup | 30 min |
| **Phase 1 Total** | | **4.5 hours** |
| Phase 2 | Task 7: Data Model | 60 min |
| Phase 2 | Task 8: Profile Manager | 60 min |
| Phase 2 | Task 9: Status Enum | 30 min |
| Phase 2 | Task 10: Connection Manager | 90 min |
| **Phase 2 Total** | | **4 hours** |
| **Grand Total** | | **8.5 hours** |

---

**Plan complete and saved to `docs/plans/2026-01-18-code-optimization-and-v15-multi-connection.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**

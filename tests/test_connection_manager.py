"""
Tests for ConnectionManager.
"""
import pytest
from PyQt6.QtCore import QObject, pyqtSignal
from managers.connection_manager import ConnectionManager
from models.connection_profile import ConnectionProfile
from models.ssh_handler import SSHHandler


class TestConnectionManager:
    """Test suite for ConnectionManager."""

    def test_initialization(self, qtbot):
        """Test ConnectionManager initializes correctly."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        assert manager.get_connection_count() == 0
        assert manager.get_active_count() == 0
        assert len(manager.get_all_connections()) == 0

    def test_create_connection_success(self, qtbot, mocker):
        """Test successful connection creation."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        # Mock SSHHandler to avoid actual SSH connection
        mock_handler = mocker.Mock(spec=SSHHandler)
        mock_handler.is_connected = True
        mock_handler.connection_id = "conn_1"

        # Mock the connect method
        mock_handler.connect.return_value = (True, "Connected successfully")
        mock_handler.status_changed = pyqtSignal(str)

        # Create a test profile
        profile = ConnectionProfile(
            name="test-server",
            host="192.168.1.10",
            port=22,
            username="testuser",
            password="testpass"
        )

        # Mock SSHHandler constructor
        mocker.patch('managers.connection_manager.SSHHandler', return_value=mock_handler)

        # Track signal emissions
        with qtbot.wait_signal(manager.connection_added, timeout=1000):
            conn_id = manager.create_connection(profile)

        assert conn_id == "conn_1"
        assert manager.has_connection(conn_id)
        assert manager.get_connection_count() == 1
        assert manager.get_active_count() == 1
        assert manager.get_connection(conn_id) == mock_handler

    def test_create_connection_failure(self, qtbot, mocker):
        """Test connection creation failure handling."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        # Mock SSHHandler to simulate connection failure
        mock_handler = mocker.Mock(spec=SSHHandler)
        mock_handler.is_connected = False
        mock_handler.connect.return_value = (False, "Authentication failed")
        mock_handler.status_changed = pyqtSignal(str)

        mocker.patch('managers.connection_manager.SSHHandler', return_value=mock_handler)

        profile = ConnectionProfile(
            name="test-server",
            host="192.168.1.10",
            port=22,
            username="testuser",
            password="wrongpass"
        )

        # Should raise ConnectionError
        with pytest.raises(ConnectionError, match="Connection failed"):
            manager.create_connection(profile)

        # No connection should be added
        assert manager.get_connection_count() == 0

    def test_get_connection_info(self, qtbot, mocker):
        """Test retrieving connection metadata."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        mock_handler = mocker.Mock(spec=SSHHandler)
        mock_handler.is_connected = True
        mock_handler.connect.return_value = (True, "Connected")
        mock_handler.status_changed = pyqtSignal(str)

        mocker.patch('managers.connection_manager.SSHHandler', return_value=mock_handler)

        profile = ConnectionProfile(
            name="production-server",
            host="10.0.0.1",
            port=2222,
            username="admin",
            password="secret",
            group="production",
            tags=["linux", "web"]
        )

        conn_id = manager.create_connection(profile)
        info = manager.get_connection_info(conn_id)

        assert info is not None
        assert info['name'] == "production-server"
        assert info['host'] == "10.0.0.1"
        assert info['port'] == 2222
        assert info['username'] == "admin"
        assert info['group'] == "production"
        assert info['tags'] == ["linux", "web"]

    def test_remove_connection(self, qtbot, mocker):
        """Test removing a connection."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        mock_handler = mocker.Mock(spec=SSHHandler)
        mock_handler.is_connected = True
        mock_handler.connect.return_value = (True, "Connected")
        mock_handler.status_changed = pyqtSignal(str)
        mock_handler.close = mocker.Mock()

        mocker.patch('managers.connection_manager.SSHHandler', return_value=mock_handler)

        profile = ConnectionProfile(
            name="test-server",
            host="192.168.1.10",
            username="testuser"
        )

        conn_id = manager.create_connection(profile)
        assert manager.has_connection(conn_id)

        # Track removal signal
        with qtbot.wait_signal(manager.connection_removed, timeout=1000):
            manager.remove_connection(conn_id)

        assert not manager.has_connection(conn_id)
        assert manager.get_connection_count() == 0
        mock_handler.close.assert_called_once()

    def test_get_active_connections(self, qtbot, mocker):
        """Test filtering active connections."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        # Create first active connection
        active_handler = mocker.Mock(spec=SSHHandler)
        active_handler.is_connected = True
        active_handler.connect.return_value = (True, "Connected")
        active_handler.status_changed = pyqtSignal(str)

        # Create second inactive connection
        inactive_handler = mocker.Mock(spec=SSHHandler)
        inactive_handler.is_connected = False
        inactive_handler.connect.return_value = (False, "Failed")
        inactive_handler.status_changed = pyqtSignal(str)

        mocker.patch('managers.connection_manager.SSHHandler', side_effect=[active_handler, inactive_handler])

        profile1 = ConnectionProfile(name="server1", host="192.168.1.1", username="user")
        profile2 = ConnectionProfile(name="server2", host="192.168.1.2", username="user")

        conn_id1 = manager.create_connection(profile1)
        conn_id2 = manager.create_connection(profile2)

        active_conns = manager.get_active_connections()
        assert len(active_conns) == 1
        assert conn_id1 in active_conns
        assert conn_id2 not in active_conns

    def test_close_all(self, qtbot, mocker):
        """Test closing all connections."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        # Create multiple mock handlers
        handlers = []
        for i in range(3):
            handler = mocker.Mock(spec=SSHHandler)
            handler.is_connected = True
            handler.connect.return_value = (True, "Connected")
            handler.status_changed = pyqtSignal(str)
            handlers.append(handler)

        mocker.patch('managers.connection_manager.SSHHandler', side_effect=handlers)

        # Create 3 connections
        for i in range(3):
            profile = ConnectionProfile(
                name=f"server{i}",
                host=f"192.168.1.{i}",
                username="user"
            )
            manager.create_connection(profile)

        assert manager.get_connection_count() == 3

        # Close all
        manager.close_all()

        assert manager.get_connection_count() == 0
        for handler in handlers:
            handler.close.assert_called_once()

    def test_connection_id_generation(self, qtbot, mocker):
        """Test that connection IDs are generated sequentially."""
        manager = ConnectionManager()
        qtbot.addWidget(manager)

        mocker.patch('managers.connection_manager.SSHHandler')

        profile = ConnectionProfile(name="test", host="192.168.1.1", username="user")

        conn_ids = []
        for i in range(5):
            conn_id = manager.create_connection(profile)
            conn_ids.append(conn_id)

        assert conn_ids == ["conn_1", "conn_2", "conn_3", "conn_4", "conn_5"]

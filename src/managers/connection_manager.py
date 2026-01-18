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
    """
    Connection pool manager for managing multiple SSH connections.
    Provides connection lifecycle management, status tracking, and signal notifications.
    """

    # Signals
    connection_added = pyqtSignal(str)           # conn_id - New connection added
    connection_removed = pyqtSignal(str)         # conn_id - Connection removed
    connection_status_changed = pyqtSignal(str, str)  # conn_id, status - Status changed
    connection_error = pyqtSignal(str, str)      # conn_id, error_msg - Connection error

    def __init__(self, parent=None):
        """
        Initialize connection manager.

        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        self._connections: Dict[str, SSHHandler] = {}
        self._connection_info: Dict[str, dict] = {}
        self._next_conn_id = 1

    def create_connection(self, profile: ConnectionProfile) -> str:
        """
        Create a new SSH connection from a profile.

        Args:
            profile: ConnectionProfile with connection details

        Returns:
            str: Connection ID (e.g., "conn_1", "conn_2")

        Raises:
            ConnectionError: If connection fails
        """
        conn_id = f"conn_{self._next_conn_id}"
        self._next_conn_id += 1

        # Create SSH handler
        ssh_handler = SSHHandler()
        ssh_handler.set_connection_id(conn_id)

        # Connect status change signal
        ssh_handler.status_changed.connect(
            lambda status, cid=conn_id: self.connection_status_changed.emit(cid, status)
        )

        # Establish connection
        success, message = ssh_handler.connect(
            host=profile.host,
            port=profile.port,
            username=profile.username,
            password=profile.password,
            timeout=AppConstants.SSH_TIMEOUT_SECONDS
        )

        if success:
            self._connections[conn_id] = ssh_handler
            self._connection_info[conn_id] = {
                'name': profile.name,
                'host': profile.host,
                'port': profile.port,
                'username': profile.username,
                'group': profile.group,
                'tags': profile.tags
            }
            self.connection_added.emit(conn_id)
            return conn_id
        else:
            raise ConnectionError(f"Connection failed: {message}")

    def get_connection(self, conn_id: str) -> Optional[SSHHandler]:
        """
        Get a specific connection by ID.

        Args:
            conn_id: Connection ID

        Returns:
            SSHHandler if found, None otherwise
        """
        return self._connections.get(conn_id)

    def get_connection_info(self, conn_id: str) -> Optional[dict]:
        """
        Get connection metadata by ID.

        Args:
            conn_id: Connection ID

        Returns:
            dict with connection info if found, None otherwise
        """
        return self._connection_info.get(conn_id)

    def remove_connection(self, conn_id: str) -> None:
        """
        Remove a connection and cleanup resources.

        Args:
            conn_id: Connection ID to remove
        """
        if conn_id in self._connections:
            handler = self._connections[conn_id]
            handler.close()
            del self._connections[conn_id]
            del self._connection_info[conn_id]
            self.connection_removed.emit(conn_id)

    def get_all_connections(self) -> Dict[str, SSHHandler]:
        """
        Get all connections (active and inactive).

        Returns:
            Dict mapping conn_id to SSHHandler
        """
        return self._connections.copy()

    def get_active_connections(self) -> Dict[str, SSHHandler]:
        """
        Get only active (connected) connections.

        Returns:
            Dict mapping conn_id to SSHHandler for connected sessions
        """
        return {
            conn_id: handler
            for conn_id, handler in self._connections.items()
            if handler.is_connected
        }

    def get_connection_count(self) -> int:
        """
        Get total number of connections.

        Returns:
            int: Total connection count
        """
        return len(self._connections)

    def get_active_count(self) -> int:
        """
        Get number of active connections.

        Returns:
            int: Active connection count
        """
        return len(self.get_active_connections())

    def has_connection(self, conn_id: str) -> bool:
        """
        Check if a connection exists.

        Args:
            conn_id: Connection ID

        Returns:
            bool: True if connection exists
        """
        return conn_id in self._connections

    def close_all(self) -> None:
        """
        Close all connections and cleanup resources.
        Useful for application shutdown.
        """
        for conn_id in list(self._connections.keys()):
            self.remove_connection(conn_id)

"""
Base class for connection handlers.
Note: This is a conceptual base class. Subclasses must implement the abstract methods.
"""
from PyQt6.QtCore import QObject, pyqtSignal


class ConnectionHandler(QObject):
    """
    Base class for SSH and Telnet connections.
    Subclasses must implement: connect(), send_command(), and close() methods.
    """

    # Signals
    data_received = pyqtSignal(str)  # Emitted when data is received from server
    connection_lost = pyqtSignal(str)  # Emitted when connection is lost
    connection_established = pyqtSignal()  # Emitted when connection is successful

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False

    def connect(self, host, port, username, password=None, timeout=10):
        """
        Establish connection to remote server.
        Must be implemented by subclass.

        Args:
            host: Server hostname or IP
            port: Server port
            username: Login username
            password: Login password (optional for key-based auth)
            timeout: Connection timeout in seconds
        """
        raise NotImplementedError("Subclasses must implement connect()")

    def send_command(self, command):
        """
        Send command to remote server.
        Must be implemented by subclass.

        Args:
            command: Command string to send
        """
        raise NotImplementedError("Subclasses must implement send_command()")

    def close(self):
        """
        Close the connection.
        Must be implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement close()")

    @property
    def is_connected(self):
        """Check if connection is active."""
        return self._connected

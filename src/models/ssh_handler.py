"""
SSH connection handler using Paramiko.
"""
import paramiko
import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal
from models.connection_handler import ConnectionHandler


class SSHHandler(ConnectionHandler):
    """
    SSH connection handler that wraps Paramiko SSHClient.
    Handles SSH connections, command execution, and real-time output streaming.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = None
        self.channel = None
        self._read_thread = None
        self._stop_reading = False
        self._state_lock = threading.Lock()

    def connect(self, host, port, username, password=None, timeout=10):
        """
        Establish SSH connection to remote server.

        Args:
            host: Server hostname or IP
            port: SSH port (default 22)
            username: Login username
            password: Login password
            timeout: Connection timeout in seconds
        """
        try:
            # Create SSH client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to server
            self.client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                look_for_keys=False,
                allow_agent=False
            )

            # Create interactive shell channel
            # Set environment variable for PTY to get colors
            self.channel = self.client.invoke_shell()
            self.channel.setblocking(0)  # Non-blocking mode

            # Immediately send environment setup commands
            # These must be sent before shell prompt appears
            import time
            time.sleep(0.2)  # Wait for shell to initialize

            # Set all color-related environment variables
            self.channel.send('export TERM=xterm-256color\n')
            self.channel.send('export COLORTERM=256color\n')
            self.channel.send('export FORCE_COLOR=1\n')
            self.channel.send('alias ls="ls --color=always"\n')  # Force ls to use colors
            self.channel.send('alias grep="grep --color=always"\n')  # Force grep to use colors
            self.channel.send('clear\n')  # Clear screen to clean up initialization messages

            with self._state_lock:
                self._connected = True
            self.connection_established.emit()

            # Start reading thread
            self._stop_reading = False
            self._read_thread = threading.Thread(target=self._read_output, daemon=True)
            self._read_thread.start()

            return True, "Connected successfully"

        except paramiko.AuthenticationException:
            with self._state_lock:
                self._connected = False
            return False, "Authentication failed. Please check your credentials."
        except paramiko.SSHException as e:
            with self._state_lock:
                self._connected = False
            return False, f"SSH connection failed: {str(e)}"
        except Exception as e:
            with self._state_lock:
                self._connected = False
            return False, f"Connection error: {str(e)}"

    def send_command(self, command):
        """
        Send command to SSH server.

        Args:
            command: Command string to send
        """
        if not self._connected or not self.channel:
            return False, "Not connected to server"

        try:
            # Send command with newline
            self.channel.send(command + '\n')
            return True, "Command sent"
        except Exception as e:
            return False, f"Failed to send command: {str(e)}"

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
                if self.channel and self.channel.recv_ready():
                    # Read data from channel
                    data = self.channel.recv(4096)
                    if data:
                        # Decode and emit signal
                        text = data.decode('utf-8', errors='ignore')
                        self.data_received.emit(text)
                else:
                    # Small sleep to prevent busy waiting
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

    def close(self):
        """Close SSH connection."""
        with self._state_lock:
            self._stop_reading = True
            self._connected = False

        if self.channel:
            try:
                self.channel.close()
            except:
                pass
            self.channel = None

        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None

        # Wait for read thread to finish
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2)

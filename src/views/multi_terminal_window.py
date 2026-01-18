"""
Multi-tab terminal window for v1.5.0.
Supports multiple SSH connections in tabbed interface.
"""
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget,
                             QHBoxLayout, QMessageBox, QToolBar, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
from views.terminal_widget import TerminalWidget
from views.chat_widget import AIChatWidget
from views.connection_dialog import ConnectionDialog
from controllers.session_controller import SessionController
from ai.ai_client import AIClient
from config.constants import AppConstants


class MultiTerminalWindow(QMainWindow):
    """
    Multi-tab terminal window for managing multiple SSH connections.
    v1.5.0 feature: Each tab is an independent SSH session with its own terminal and AI chat.
    """

    # Signals
    window_closing = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sessions = {}  # session_id -> SessionController
        self.next_session_id = 1
        self.ai_client = None

        self._setup_ui()
        self._setup_shortcuts()
        self._init_ai_client()

    def _setup_ui(self):
        """Setup multi-terminal window UI."""
        self.setWindowTitle("Smart-Ops-Term - Multi Session (v1.5.0)")
        self.setMinimumSize(1200, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        from PyQt6.QtWidgets import QVBoxLayout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Create toolbar
        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget)

        # Status bar
        self.statusBar().showMessage("Ready. Press Ctrl+T for new connection, Ctrl+K for quick connect.")

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar with connection buttons."""
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # New connection button
        new_conn_action = QAction("🔌 New Connection", self)
        new_conn_action.setShortcut(QKeySequence.StandardKey.AddTab)
        new_conn_action.setToolTip("Create new SSH connection (Ctrl+T)")
        new_conn_action.triggered.connect(self.new_connection)
        toolbar.addAction(new_conn_action)

        toolbar.addSeparator()

        # Session counter label
        self.session_label = QLabel("Sessions: 0")
        toolbar.addWidget(self.session_label)

        toolbar.addSeparator()

        # Quick connect button
        quick_action = QAction("🔍 Quick Connect", self)
        quick_action.setShortcut(QKeySequence("Ctrl+K"))
        quick_action.setToolTip("Quick connect to saved servers (Ctrl+K)")
        quick_action.triggered.connect(self.quick_connect)
        toolbar.addAction(quick_action)

        return toolbar

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+T: New connection
        shortcut_new = QShortcut(QKeySequence.StandardKey.AddTab, self)
        shortcut_new.activated.connect(self.new_connection)

        # Ctrl+W: Close current tab
        shortcut_close = QShortcut(QKeySequence.StandardKey.Close, self)
        shortcut_close.activated.connect(self.close_current_tab)

        # Ctrl+Tab: Next tab
        shortcut_next = QShortcut(QKeySequence("Ctrl+Tab"), self)
        shortcut_next.activated.connect(self._next_tab)

        # Ctrl+Shift+Tab: Previous tab
        shortcut_prev = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        shortcut_prev.activated.connect(self._previous_tab)

    def _init_ai_client(self):
        """Initialize shared AI client for all sessions."""
        self.ai_client = AIClient()

    def new_connection(self, conn_info=None) -> str:
        """
        Create a new SSH connection tab.

        Args:
            conn_info: Optional connection info dict. If None, shows connection dialog.

        Returns:
            str: Session ID if successful, None otherwise
        """
        # Show connection dialog if no info provided
        if conn_info is None:
            dialog = ConnectionDialog(self)
            if dialog.exec() != 1:  # QDialog.DialogCode.Accepted == 1
                return None
            conn_info = dialog.get_connection_info()

            # Validate
            if not conn_info['host'] or not conn_info['username']:
                QMessageBox.warning(self, "Connection Error",
                                   "Please provide host and username.")
                return None

        # Create session ID
        session_id = f"session_{self.next_session_id}"
        self.next_session_id += 1

        # Create UI components for this session
        session_widget = QWidget()
        session_layout = QHBoxLayout(session_widget)
        session_layout.setContentsMargins(0, 0, 0, 0)

        # Terminal and Chat widgets
        terminal = TerminalWidget()
        chat = AIChatWidget()

        # Create splitter for resizable panes
        from PyQt6.QtWidgets import QSplitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(terminal)
        splitter.addWidget(chat)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        session_layout.addWidget(splitter)

        # Create session controller
        ssh_handler = None
        try:
            from models.ssh_handler import SSHHandler
            ssh_handler = SSHHandler()
            controller = SessionController(session_id, terminal, chat, self.ai_client, self)
            controller.initialize(ssh_handler)

            # Connect terminal connect button to re-connect in this session
            terminal.connect_requested.connect(lambda: self._handle_session_reconnect(session_id))

            # Store session
            self.sessions[session_id] = {
                'controller': controller,
                'ssh_handler': ssh_handler,
                'terminal': terminal,
                'chat': chat,
                'widget': session_widget,
                'conn_info': conn_info
            }

            # Add tab
            tab_name = f"{conn_info['host']}:{conn_info['port']}"
            index = self.tab_widget.addTab(session_widget, tab_name)
            self.tab_widget.setCurrentIndex(index)

            # Auto-connect
            success = controller.connect_to_server(conn_info)
            if not success:
                # Connection failed but keep the tab open
                terminal.append_output(f"\n=== Connection to {conn_info['host']} failed ===\n")
                terminal.append_output("You can try connecting again using the Connect button.\n")

            self._update_session_count()

            return session_id

        except Exception as e:
            import traceback
            error_msg = f"Failed to create session: {str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Error", error_msg)
            # Cleanup
            if ssh_handler:
                try:
                    ssh_handler.close()
                except:
                    pass
            return None

    def quick_connect(self):
        """Show quick connect dialog (for future use with saved profiles)."""
        # For now, just show regular connection dialog
        # TODO: Implement quick connect with saved profiles
        self.new_connection()

    def close_tab(self, index: int):
        """
        Close a tab by index.

        Args:
            index: Tab index to close
        """
        if index < 0:
            return

        # Find session ID for this tab
        session_id = None
        for sid, info in self.sessions.items():
            tab_widget = info['widget']
            # Find the tab index for this widget
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == tab_widget:
                    if i == index:
                        session_id = sid
                        break
            if session_id:
                break

        if session_id:
            self._close_session(session_id)

    def close_current_tab(self):
        """Close the current tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)

    def _close_session(self, session_id: str):
        """
        Close and cleanup a session.

        Args:
            session_id: Session ID to close
        """
        if session_id not in self.sessions:
            return

        session_info = self.sessions[session_id]

        # Cleanup controller (this will disconnect AI signals)
        controller = session_info['controller']
        controller.cleanup()

        # Remove tab
        tab_widget = session_info['widget']
        index = self.tab_widget.indexOf(tab_widget)
        if index >= 0:
            self.tab_widget.removeTab(index)

        # Remove from sessions dict
        del self.sessions[session_id]

        self._update_session_count()

    def _handle_session_reconnect(self, session_id: str):
        """Handle re-connect button click in terminal."""
        if session_id not in self.sessions:
            return

        session_info = self.sessions[session_id]
        controller = session_info['controller']
        conn_info = session_info['conn_info']

        # Try to reconnect
        success = controller.connect_to_server(conn_info)
        if not success:
            session_info['terminal'].append_output(f"\n=== Reconnection failed ===\n")

    def _on_tab_changed(self, index: int):
        """Handle tab change event."""
        pass

    def _next_tab(self):
        """Switch to next tab."""
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 0:
            next_index = (current + 1) % count
            self.tab_widget.setCurrentIndex(next_index)

    def _previous_tab(self):
        """Switch to previous tab."""
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 0:
            prev_index = (current - 1) % count
            self.tab_widget.setCurrentIndex(prev_index)

    def _update_session_count(self):
        """Update session counter in toolbar."""
        self.session_label.setText(f"Sessions: {len(self.sessions)}")

    def get_session_count(self) -> int:
        """Get current number of sessions."""
        return len(self.sessions)

    def closeEvent(self, event):
        """Handle window close event."""
        # Cleanup all sessions
        for session_id in list(self.sessions.keys()):
            self._close_session(session_id)

        # Clear AI history
        if self.ai_client:
            self.ai_client.clear_history()

        self.window_closing.emit()
        event.accept()

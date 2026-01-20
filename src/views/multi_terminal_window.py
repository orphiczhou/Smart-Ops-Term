"""
Multi-tab terminal window for v1.5.0.
Supports multiple SSH connections in tabbed interface.
"""
import json
import os
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget,
                             QHBoxLayout, QMessageBox, QToolBar, QLabel,
                             QToolButton, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
from views.terminal_widget import TerminalWidget
from views.chat_widget import AIChatWidget
from views.connection_dialog import ConnectionDialog
from controllers.session_controller import SessionController
from ai.ai_client import AIClient
from config.constants import AppConstants
from config.config_manager import ConfigManager


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
        self.connection_history = []  # Store connection history
        self._load_connection_history()

        self._setup_ui()
        self._setup_shortcuts()
        self._init_ai_client()
        self._load_window_state()

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

        # New connection button with dropdown
        self.new_conn_button = QToolButton(self)
        self.new_conn_button.setText("🔌 New Connection")
        self.new_conn_button.setShortcut(QKeySequence.StandardKey.AddTab)
        self.new_conn_button.setToolTip("Create new SSH connection (Ctrl+T)")
        self.new_conn_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.new_conn_button.clicked.connect(self._safe_new_connection)

        # Create dropdown menu for connection history
        self.history_menu = QMenu(self)
        self._update_history_menu()
        self.new_conn_button.setMenu(self.history_menu)

        toolbar.addWidget(self.new_conn_button)

        toolbar.addSeparator()

        # Session counter label
        self.session_label = QLabel("Sessions: 0")
        toolbar.addWidget(self.session_label)

        toolbar.addSeparator()

        # Settings button (v1.6.0)
        self.settings_button = QToolButton(self)
        self.settings_button.setText("⚙️ Settings")
        self.settings_button.setToolTip("Open settings dialog")
        self.settings_button.clicked.connect(self._open_settings_dialog)
        toolbar.addWidget(self.settings_button)

        return toolbar

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+T: New connection
        shortcut_new = QShortcut(QKeySequence.StandardKey.AddTab, self)
        shortcut_new.activated.connect(self._safe_new_connection)

        # Ctrl+W: Close current tab
        shortcut_close = QShortcut(QKeySequence.StandardKey.Close, self)
        shortcut_close.activated.connect(self.close_current_tab)

        # Ctrl+Tab: Next tab
        shortcut_next = QShortcut(QKeySequence("Ctrl+Tab"), self)
        shortcut_next.activated.connect(self._next_tab)

        # Ctrl+Shift+Tab: Previous tab
        shortcut_prev = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        shortcut_prev.activated.connect(self._previous_tab)

    def _safe_new_connection(self):
        """Safe wrapper for new_connection with exception handling."""
        try:
            print("[DEBUG] _safe_new_connection called", flush=True)
            result = self.new_connection()
            print(f"[DEBUG] _safe_new_connection completed: {result}", flush=True)
        except Exception as e:
            print(f"[ERROR] Exception in new_connection: {e}", flush=True)
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error",
                                f"Failed to create new connection:\n{str(e)}")

    def _init_ai_client(self):
        """Initialize AI client (note: each session will have its own instance)."""
        # No longer using a shared AI client - each session gets its own
        pass

    def _load_connection_history(self):
        """Load connection history from file."""
        history_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     'data', 'connection_history.json')
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.connection_history = json.load(f)
                print(f"[DEBUG] Loaded {len(self.connection_history)} connections from history")
        except Exception as e:
            print(f"[DEBUG] Failed to load connection history: {e}")
            self.connection_history = []

    def _save_connection_history(self):
        """Save connection history to file."""
        history_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     'data', 'connection_history.json')
        try:
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(self.connection_history, f, indent=2)
            print(f"[DEBUG] Saved {len(self.connection_history)} connections to history")
        except Exception as e:
            print(f"[DEBUG] Failed to save connection history: {e}")

    def _add_to_history(self, conn_info: dict):
        """Add connection to history and save."""
        # Create a simplified entry for history (without password)
        entry = {
            'host': conn_info['host'],
            'port': conn_info['port'],
            'username': conn_info['username']
        }

        # Remove duplicates and add to front
        self.connection_history = [e for e in self.connection_history
                                   if not (e['host'] == entry['host'] and
                                          e['port'] == entry['port'] and
                                          e['username'] == entry['username'])]
        self.connection_history.insert(0, entry)

        # Keep only last 10 connections
        self.connection_history = self.connection_history[:10]

        # Save to file
        self._save_connection_history()

        # Update menu
        self._update_history_menu()

    def _update_history_menu(self):
        """Update the connection history dropdown menu."""
        self.history_menu.clear()

        if not self.connection_history:
            no_history_action = self.history_menu.addAction("No recent connections")
            no_history_action.setEnabled(False)
        else:
            for i, entry in enumerate(self.connection_history):
                label = f"{entry['username']}@{entry['host']}:{entry['port']}"
                action = self.history_menu.addAction(label)
                # Store connection info in action data
                action.setData(entry)
                action.triggered.connect(lambda checked, e=entry: self._connect_from_history(e))

            self.history_menu.addSeparator()
            clear_action = self.history_menu.addAction("Clear History")
            clear_action.triggered.connect(self._clear_history)

    def _connect_from_history(self, entry: dict):
        """Connect using a connection from history."""
        print(f"[DEBUG] Connecting from history: {entry}")
        # Need to show dialog to enter password since we don't store it
        dialog = ConnectionDialog(self)
        dialog.set_connection_info(entry['host'], entry['port'], entry['username'], '')
        result = dialog.exec()
        if result == 1:
            conn_info = dialog.get_connection_info()
            self.new_connection(conn_info)

    def _clear_history(self):
        """Clear connection history."""
        self.connection_history = []
        self._save_connection_history()
        self._update_history_menu()
        print("[DEBUG] Connection history cleared")

    def new_connection(self, conn_info=None, ai_profile_name=None) -> str:
        """
        Create a new SSH connection tab.

        v1.6.1: 添加 AI 配置选择功能

        Args:
            conn_info: Optional connection info dict. If None, shows connection dialog.
            ai_profile_name: Optional AI profile name to use for this session.

        Returns:
            str: Session ID if successful, None otherwise
        """
        print("[DEBUG] new_connection called")

        # Show connection dialog if no info provided
        if conn_info is None:
            print("[DEBUG] No conn_info provided, showing dialog")
            dialog = ConnectionDialog(self)
            result = dialog.exec()
            print(f"[DEBUG] Dialog result: {result} (1=Accepted, 0=Rejected)")
            if result != 1:  # QDialog.DialogCode.Accepted == 1
                print("[DEBUG] Dialog rejected, returning None")
                return None
            conn_info = dialog.get_connection_info()
            print(f"[DEBUG] Got conn_info from dialog: {conn_info}")

            # Validate
            if not conn_info['host'] or not conn_info['username']:
                QMessageBox.warning(self, "Connection Error",
                                   "Please provide host and username.")
                return None

            # v1.6.1: 从对话框获取选择的 AI profile
            ai_profile_name = conn_info.pop('ai_profile', None)
            if ai_profile_name:
                print(f"[DEBUG] Using AI profile from dialog: {ai_profile_name}")
            else:
                # 如果没有选择，使用默认配置
                try:
                    from managers.ai_profile_manager import AIProfileManager
                    ai_manager = AIProfileManager()
                    ai_profile = ai_manager.get_default_profile()
                    if ai_profile:
                        ai_profile_name = ai_profile.name
                        print(f"[DEBUG] Using default AI profile: {ai_profile_name}")
                except Exception as e:
                    print(f"[DEBUG] Failed to load AI profiles: {e}")
        elif ai_profile_name is None:
            # v1.6.1: 如果有多个 AI 配置且未指定，自动使用默认配置
            try:
                from managers.ai_profile_manager import AIProfileManager
                ai_manager = AIProfileManager()
                ai_profile = ai_manager.get_default_profile()
                if ai_profile:
                    ai_profile_name = ai_profile.name
                    print(f"[DEBUG] Using default AI profile: {ai_profile_name}")
            except Exception as e:
                print(f"[DEBUG] Failed to load AI profiles: {e}")

        print(f"[DEBUG] Proceeding with connection to {conn_info.get('host')}:{conn_info.get('port', 22)}")

        # Create session ID
        session_id = f"session_{self.next_session_id}"
        self.next_session_id += 1
        print(f"[DEBUG] Created session_id: {session_id}")

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

            # Debug: Print before creating SSH handler
            print(f"[DEBUG] Creating SSHHandler for session {session_id}...")
            ssh_handler = SSHHandler()
            print(f"[DEBUG] SSHHandler created: {ssh_handler}")

            # Create independent AI client for this session
            print(f"[DEBUG] Creating AIClient for session {session_id}...")
            ai_client = AIClient()
            print(f"[DEBUG] AIClient created: {ai_client}")

            # v1.6.1: 如果指定了 AI 配置，设置到客户端
            if ai_profile_name:
                ai_client.set_profile(ai_profile_name)
                print(f"[DEBUG] Set AI profile: {ai_profile_name}")

            print(f"[DEBUG] Creating SessionController...")
            controller = SessionController(session_id, terminal, chat, ai_client, ai_profile_name, self)
            print(f"[DEBUG] SessionController created: {controller}")

            print(f"[DEBUG] Initializing controller with ssh_handler...")
            controller.initialize(ssh_handler)
            print(f"[DEBUG] Controller initialized")

            # Connect terminal connect button to re-connect in this session
            terminal.connect_requested.connect(lambda: self._handle_session_reconnect(session_id))

            # Connect chat signals to controller
            chat.message_sent.connect(controller.on_chat_message)
            chat.command_execute_requested.connect(controller.on_command_execute)
            # v1.6.1: 连接 AI profile 切换信号
            chat.ai_profile_changed.connect(controller.on_ai_profile_changed)

            # Store session
            self.sessions[session_id] = {
                'controller': controller,
                'ssh_handler': ssh_handler,
                'terminal': terminal,
                'chat': chat,
                'widget': session_widget,
                'conn_info': conn_info,
                'ai_client': ai_client,  # Store AI client for cleanup
                'ai_profile_name': ai_profile_name  # v1.6.1: 存储 AI 配置名称
            }

            # Add to connection history
            self._add_to_history(conn_info)

            # Add tab - v1.6.1: 在标签名上显示 AI 配置
            tab_name = f"{conn_info['host']}:{conn_info['port']}"
            if ai_profile_name:
                tab_name += f" [{ai_profile_name}]"
            index = self.tab_widget.addTab(session_widget, tab_name)
            self.tab_widget.setCurrentIndex(index)

            # v1.6.1: 加载 AI profiles 到下拉框
            chat.load_ai_profiles(ai_profile_name)

            # Auto-connect
            print(f"[DEBUG] Attempting to connect to {conn_info['host']}:{conn_info['port']}...")
            print(f"[DEBUG] conn_info: {conn_info}")
            print(f"[DEBUG] controller.ssh_handler before connect: {controller.ssh_handler}")

            success = controller.connect_to_server(conn_info)
            print(f"[DEBUG] Connection result: {success}")

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

        # Cleanup this session's AI client (clear conversation history)
        ai_client = session_info.get('ai_client')
        if ai_client:
            ai_client.clear_history()

        # Remove tab
        tab_widget = session_info['widget']
        index = self.tab_widget.indexOf(tab_widget)
        if index >= 0:
            self.tab_widget.removeTab(index)

        # Remove from sessions dict
        del self.sessions[session_id]

        self._update_session_count()

    def _handle_session_reconnect(self, session_id: str):
        """Handle Connect/Disconnect/Reconnect button click in terminal."""
        if session_id not in self.sessions:
            return

        session_info = self.sessions[session_id]
        controller = session_info['controller']
        ssh_handler = session_info['ssh_handler']
        conn_info = session_info['conn_info']
        terminal = session_info['terminal']

        # Check if currently connected
        if ssh_handler and ssh_handler.is_connected:
            # Currently connected - disconnect
            print(f"[DEBUG] Disconnecting session {session_id}")
            controller.disconnect()
        else:
            # Currently disconnected - reconnect
            print(f"[DEBUG] Reconnecting session {session_id}")
            success = controller.reconnect(conn_info)
            if not success:
                terminal.append_output(f"\n=== Reconnection failed ===\n")

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
        # Save window state before closing
        self._save_window_state()

        # Cleanup all sessions (each will clear its own AI history)
        for session_id in list(self.sessions.keys()):
            self._close_session(session_id)

        self.window_closing.emit()
        event.accept()

    # ========== v1.6.0 Configuration Persistence Methods ==========

    def _open_settings_dialog(self):
        """Open settings dialog"""
        try:
            from views.settings_dialog import SettingsDialog

            print(f"[DEBUG] Creating SettingsDialog...", flush=True)
            dialog = SettingsDialog(self)
            dialog.settings_applied.connect(self._on_settings_changed)
            print(f"[DEBUG] Showing SettingsDialog...", flush=True)
            dialog.exec()
            print(f"[DEBUG] SettingsDialog closed", flush=True)
        except Exception as e:
            import traceback
            print(f"[ERROR] Failed to open settings dialog: {e}", flush=True)
            traceback.print_exc()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"无法打开设置对话框:\n{str(e)}")

    def _on_settings_changed(self):
        """Handle settings changed"""
        print("[DEBUG] Settings changed, reloading configuration", flush=True)
        # Note: AI client settings will take effect on new connections
        # Terminal settings can be applied immediately in the future

    def _save_window_state(self):
        """Save window geometry and state"""
        config_manager = ConfigManager.get_instance()
        geometry = self.geometry()
        config_manager.settings.ui.window_x = geometry.x()
        config_manager.settings.ui.window_y = geometry.y()
        config_manager.settings.ui.window_width = geometry.width()
        config_manager.settings.ui.window_height = geometry.height()
        config_manager.save()
        print("[DEBUG] Window state saved", flush=True)

    def _load_window_state(self):
        """Restore window geometry and state"""
        config_manager = ConfigManager.get_instance()
        # Load config first
        config_manager.load()

        ui = config_manager.settings.ui
        self.resize(ui.window_width, ui.window_height)
        self.move(ui.window_x, ui.window_y)
        print(f"[DEBUG] Window state loaded: {ui.window_width}x{ui.window_height} at ({ui.window_x}, {ui.window_y})", flush=True)

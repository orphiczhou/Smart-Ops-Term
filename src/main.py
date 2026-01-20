"""
Smart-Ops-Term - AI Assisted Remote Terminal
Main entry point for the application.
v1.5.0: Multi-tab terminal window.
"""
import sys
import os
import traceback
import threading

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, qInstallMessageHandler, QtMsgType
from views.multi_terminal_window import MultiTerminalWindow


def migrate_env_to_config():
    """
    Migrate existing .env settings to new ConfigManager system.
    v1.6.1: 只在配置文件不存在时才迁移，避免覆盖已有配置
    """
    try:
        from config.config_manager import ConfigManager
        from dotenv import load_dotenv
        from pathlib import Path

        config_manager = ConfigManager.get_instance()

        # v1.6.1: 只在配置文件不存在时才进行迁移
        # 如果配置文件已存在，跳过迁移，保留用户配置
        if config_manager._config_path.exists():
            print("[DEBUG] Config file exists, skipping migration")
            # 先加载现有配置
            config_manager.load()
            return

        # Load .env file
        load_dotenv()

        changed = False

        # Check if we need to migrate (if config file doesn't exist or is empty/default)
        if not config_manager.settings.ai.api_key:
            api_key = os.getenv('OPENAI_API_KEY', '')
            if api_key:
                config_manager.settings.ai.api_key = api_key
                changed = True

        if not config_manager.settings.ai.api_base or config_manager.settings.ai.api_base == "https://api.openai.com/v1":
            api_base = os.getenv('OPENAI_API_BASE', '')
            if api_base:
                config_manager.settings.ai.api_base = api_base
                changed = True

        if not config_manager.settings.ai.model or config_manager.settings.ai.model == "gpt-4-turbo":
            model = os.getenv('OPENAI_MODEL', '')
            if model:
                config_manager.settings.ai.model = model
                changed = True

        if changed:
            config_manager.save()
            print("[INFO] Migrated settings from .env to config file (~/.smartops/app_config.json)")
        else:
            print("[DEBUG] No migration needed, using existing config")

    except Exception as e:
        print(f"[WARNING] Failed to migrate .env settings: {e}")


def qt_message_handler(mode, context, message):
    """Qt message handler to catch Qt-level errors."""
    log_file = open("qt_debug.log", "a")
    mode_str = {
        QtMsgType.QtDebugMsg: "Debug",
        QtMsgType.QtInfoMsg: "Info",
        QtMsgType.QtWarningMsg: "Warning",
        QtMsgType.QtCriticalMsg: "Critical",
        QtMsgType.QtFatalMsg: "Fatal",
    }.get(mode, "Unknown")

    log_file.write(f"[{mode_str}] {message}\n")
    if context.file:
        log_file.write(f"  File: {context.file}, Line: {context.line}\n")
    if context.function:
        log_file.write(f"  Function: {context.function}\n")
    log_file.write(f"\n")
    log_file.flush()

    # Also print to console
    print(f"[QT {mode_str}] {message}", flush=True)
    if mode == QtMsgType.QtFatalMsg:
        traceback.print_stack()


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to catch all unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log_file = open("error_log.txt", "a")
    log_file.write("=" * 80 + "\n")
    log_file.write("UNHANDLED EXCEPTION:\n")
    log_file.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    log_file.write("=" * 80 + "\n\n")
    log_file.flush()

    # Also print to console
    print("\n" + "=" * 80, file=sys.stderr, flush=True)
    print("UNHANDLED EXCEPTION:", file=sys.stderr, flush=True)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("=" * 80 + "\n", file=sys.stderr, flush=True)


def main():
    """
    Main entry point for Smart-Ops-Term application.
    """
    # Install global exception handler
    sys.excepthook = handle_exception

    # Install Qt message handler
    qInstallMessageHandler(qt_message_handler)

    # Handle threading exceptions
    threading.excepthook = handle_exception

    print("[DEBUG] Application starting...", flush=True)

    # v1.6.0: Migrate .env settings to ConfigManager
    print("[DEBUG] Checking for .env migration...", flush=True)
    migrate_env_to_config()

    try:
        # Enable high DPI scaling
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        print("[DEBUG] Creating QApplication...", flush=True)

        # Create application instance
        app = QApplication(sys.argv)
        app.setApplicationName("Smart-Ops-Term")
        app.setOrganizationName("SmartOps")

        print("[DEBUG] Creating MultiTerminalWindow...", flush=True)

        # Create multi-terminal window
        window = MultiTerminalWindow()

        print("[DEBUG] Showing window...", flush=True)
        window.show()

        print("[DEBUG] Starting event loop...", flush=True)

        # Run event loop
        exit_code = app.exec()

        print(f"[DEBUG] Event loop ended with exit code: {exit_code}", flush=True)

        sys.exit(exit_code)

    except Exception as e:
        print(f"[CRITICAL ERROR] {e}", file=sys.stderr, flush=True)
        traceback.print_exc()
        with open("critical_error.txt", "w") as f:
            f.write(f"Critical error during startup:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main()

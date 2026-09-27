#!/usr/bin/env python3
"""
WiFi File Transfer — Cross-platform launcher.
Works on macOS, Windows, and Linux.

Usage:
    python run.py              # Interactive menu
    python run.py start        # Start the server
    python run.py stop         # Stop the server
    python run.py restart      # Restart the server
    python run.py status       # Check server status
    python run.py install      # Install dependencies only
"""

import subprocess
import sys
import os
import signal
import time
import platform
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────
APP_FILE = "app.py"
PID_FILE = ".server.pid"
LOG_FILE = "server.log"
REQUIREMENTS = "requirements.txt"
PROJECT_DIR = Path(__file__).parent


def find_venv_python() -> Path | None:
    """Find the Python executable inside a virtual environment."""
    for venv_name in (".venv", "venv", "env"):
        venv_dir = PROJECT_DIR / venv_name
        if not venv_dir.is_dir():
            continue
        if platform.system() == "Windows":
            python = venv_dir / "Scripts" / "python.exe"
        else:
            python = venv_dir / "bin" / "python"
        if python.exists():
            return python
    return None


def create_venv() -> Path:
    """Create a virtual environment and return the Python path."""
    venv_dir = PROJECT_DIR / ".venv"
    print("📦 Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    python = find_venv_python()
    if python is None:
        print("❌ Failed to create virtual environment.")
        sys.exit(1)
    print(f"✅ Virtual environment created at {venv_dir}")
    return python


def install_dependencies(python: Path):
    """Install dependencies from requirements.txt."""
    req_file = PROJECT_DIR / REQUIREMENTS
    if not req_file.exists():
        print("⚠️  No requirements.txt found, skipping dependency install.")
        return
    print("📦 Installing dependencies...")
    subprocess.run(
        [str(python), "-m", "pip", "install", "-r", str(req_file), "-q"],
        check=True,
    )
    print("✅ Dependencies installed.")


def get_streamlit_cmd(python: Path) -> list[str]:
    """Return the command to run Streamlit using the venv Python."""
    return [str(python), "-m", "streamlit", "run", str(PROJECT_DIR / APP_FILE)]


def read_pid() -> int | None:
    """Read the PID from the PID file."""
    pid_path = PROJECT_DIR / PID_FILE
    if not pid_path.exists():
        return None
    try:
        pid = int(pid_path.read_text().strip())
        return pid
    except (ValueError, OSError):
        return None


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True,
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def kill_process(pid: int):
    """Kill a process by PID."""
    if platform.system() == "Windows":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                       capture_output=True)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass


def start():
    """Start the Streamlit server."""
    # Check if already running
    pid = read_pid()
    if pid and is_process_running(pid):
        print(f"⚡ Server is already running (PID {pid}).")
        return

    # Clean up stale PID file
    pid_path = PROJECT_DIR / PID_FILE
    if pid_path.exists():
        pid_path.unlink()

    # Find or create venv
    python = find_venv_python()
    if python is None:
        python = create_venv()
        install_dependencies(python)
    else:
        # Quick check: is streamlit installed?
        result = subprocess.run(
            [str(python), "-c", "import streamlit"],
            capture_output=True,
        )
        if result.returncode != 0:
            install_dependencies(python)

    # Start the server
    print("🚀 Starting WiFi File Transfer server...")
    log_path = PROJECT_DIR / LOG_FILE
    cmd = get_streamlit_cmd(python)

    if platform.system() == "Windows":
        # Windows: use CREATE_NEW_PROCESS_GROUP for background process
        with open(log_path, "w") as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS,
            )
    else:
        # macOS / Linux
        with open(log_path, "w") as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

    # Save PID
    pid_path.write_text(str(proc.pid))
    print(f"✅ Server started (PID {proc.pid}).")
    print(f"📝 Logs: {log_path}")

    # Wait a moment and show the URL
    time.sleep(3)
    if log_path.exists():
        content = log_path.read_text()
        for line in content.splitlines():
            if "Network URL" in line or "Local URL" in line:
                print(f"   {line.strip()}")


def stop():
    """Stop the Streamlit server."""
    pid = read_pid()
    pid_path = PROJECT_DIR / PID_FILE

    if pid is None:
        print("ℹ️  Server is not running (no PID file).")
        return

    if is_process_running(pid):
        print(f"🛑 Stopping server (PID {pid})...")
        kill_process(pid)
        time.sleep(1)
        # Force kill if still running
        if is_process_running(pid):
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True)
            else:
                try:
                    os.kill(pid, signal.SIGKILL)
                except (OSError, ProcessLookupError):
                    pass
        print("✅ Server stopped.")
    else:
        print("ℹ️  Server was not running (stale PID file).")

    if pid_path.exists():
        pid_path.unlink()


def status():
    """Check the server status."""
    pid = read_pid()
    if pid and is_process_running(pid):
        print(f"✅ Server is running (PID {pid}).")
        log_path = PROJECT_DIR / LOG_FILE
        if log_path.exists():
            content = log_path.read_text()
            for line in content.splitlines():
                if "Network URL" in line or "Local URL" in line:
                    print(f"   {line.strip()}")
    else:
        print("❌ Server is not running.")
        if (PROJECT_DIR / PID_FILE).exists():
            (PROJECT_DIR / PID_FILE).unlink()


def restart():
    """Restart the server."""
    stop()
    time.sleep(2)
    start()


def install():
    """Install dependencies into the virtual environment."""
    python = find_venv_python()
    if python is None:
        python = create_venv()
    install_dependencies(python)


def interactive_menu():
    """Show an interactive menu."""
    actions = {
        "1": ("Start Server", start),
        "2": ("Stop Server", stop),
        "3": ("Check Status", status),
        "4": ("Restart Server", restart),
        "5": ("Install Dependencies", install),
        "6": ("Quit", None),
    }

    print("\n📡 WiFi File Transfer")
    print("=" * 30)
    for key, (label, _) in actions.items():
        print(f"  {key}. {label}")
    print()

    choice = input("Enter your choice (1-6): ").strip()
    if choice in actions:
        label, func = actions[choice]
        if func is None:
            print("👋 Bye!")
            sys.exit(0)
        func()
    else:
        print("❌ Invalid choice.")


def main():
    os.chdir(PROJECT_DIR)

    if len(sys.argv) < 2:
        interactive_menu()
        return

    command = sys.argv[1].lower()
    commands = {
        "start": start,
        "stop": stop,
        "status": status,
        "restart": restart,
        "install": install,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python run.py {{start|stop|status|restart|install}}")
        print("Or run without arguments for an interactive menu.")
        sys.exit(1)


if __name__ == "__main__":
    main()

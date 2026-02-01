"""
Windows Control Module
======================
Utility functions for controlling windows, launching apps, and managing the IDE.

Usage:
    from utils.windows_control import open_antigravity, maximize_window, open_project
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional

import pyautogui
import pygetwindow as gw


# ----- Configuration -----
# Common paths for AntiGravity IDE (adjust if needed)
ANTIGRAVITY_PATHS = [
    r"C:\Users\%USERNAME%\AppData\Local\Programs\antigravity\AntiGravity.exe",
    r"C:\Program Files\AntiGravity\AntiGravity.exe",
    r"C:\Program Files (x86)\AntiGravity\AntiGravity.exe",
]

# Expand environment variables
ANTIGRAVITY_PATHS = [os.path.expandvars(p) for p in ANTIGRAVITY_PATHS]


def find_antigravity_exe() -> Optional[str]:
    """Find the AntiGravity executable on the system."""
    for path in ANTIGRAVITY_PATHS:
        if os.path.exists(path):
            return path
    
    # Try to find via 'where' command
    try:
        result = subprocess.run(
            ["where", "antigravity"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except Exception:
        pass
    
    return None


def open_antigravity(project_path: Optional[str] = None) -> bool:
    """
    Launch AntiGravity IDE, optionally opening a specific project folder.
    
    Args:
        project_path: Optional path to a project folder to open
        
    Returns:
        True if launched successfully, False otherwise
    """
    exe_path = find_antigravity_exe()
    
    if not exe_path:
        print("[ERROR] AntiGravity executable not found!")
        return False
    
    try:
        if project_path:
            # Open with specific project
            subprocess.Popen([exe_path, project_path])
            print(f"[INFO] Launching AntiGravity with project: {project_path}")
        else:
            # Just open the IDE
            subprocess.Popen([exe_path])
            print("[INFO] Launching AntiGravity...")
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to launch AntiGravity: {e}")
        return False


def find_window(title_pattern: str) -> Optional[gw.Window]:
    """
    Find a window by partial title match.
    
    Args:
        title_pattern: Substring to search for in window titles
        
    Returns:
        Window object if found, None otherwise
    """
    windows = gw.getAllWindows()
    for win in windows:
        if title_pattern.lower() in win.title.lower():
            return win
    return None


def maximize_window(title_pattern: str = "AntiGravity") -> bool:
    """
    Find and maximize a window by title.
    
    Args:
        title_pattern: Substring to search for in window titles
        
    Returns:
        True if successful, False otherwise
    """
    window = find_window(title_pattern)
    
    if not window:
        print(f"[ERROR] Window '{title_pattern}' not found!")
        return False
    
    try:
        window.maximize()
        window.activate()
        print(f"[INFO] Maximized window: {window.title}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to maximize: {e}")
        return False


def minimize_window(title_pattern: str = "AntiGravity") -> bool:
    """Minimize a window by title."""
    window = find_window(title_pattern)
    
    if not window:
        print(f"[ERROR] Window '{title_pattern}' not found!")
        return False
    
    try:
        window.minimize()
        print(f"[INFO] Minimized window: {window.title}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to minimize: {e}")
        return False


def restore_window(title_pattern: str = "AntiGravity") -> bool:
    """Restore a minimized window."""
    window = find_window(title_pattern)
    
    if not window:
        print(f"[ERROR] Window '{title_pattern}' not found!")
        return False
    
    try:
        window.restore()
        window.activate()
        print(f"[INFO] Restored window: {window.title}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to restore: {e}")
        return False


def focus_window(title_pattern: str = "AntiGravity") -> bool:
    """Bring a window to the foreground."""
    window = find_window(title_pattern)
    
    if not window:
        print(f"[ERROR] Window '{title_pattern}' not found!")
        return False
    
    try:
        window.activate()
        print(f"[INFO] Focused window: {window.title}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to focus: {e}")
        return False


def open_project(project_path: str) -> bool:
    """
    Open a project folder in AntiGravity.
    If IDE is already running, uses keyboard shortcut.
    Otherwise launches IDE with the project.
    
    Args:
        project_path: Absolute path to the project folder
        
    Returns:
        True if successful, False otherwise
    """
    path = Path(project_path)
    if not path.exists():
        print(f"[ERROR] Project path does not exist: {project_path}")
        return False
    
    # Check if AntiGravity is already running
    window = find_window("AntiGravity")
    
    if window:
        # IDE is running - use Ctrl+O to open folder
        try:
            window.activate()
            time.sleep(0.5)
            
            # Ctrl+K, Ctrl+O is common for "Open Folder" in VS Code-like IDEs
            pyautogui.hotkey("ctrl", "k")
            time.sleep(0.2)
            pyautogui.hotkey("ctrl", "o")
            time.sleep(1)
            
            # Type the path
            pyautogui.typewrite(str(path), interval=0.02)
            time.sleep(0.3)
            
            # Press Enter to confirm
            pyautogui.press("enter")
            
            print(f"[INFO] Opening project in running IDE: {project_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to open project: {e}")
            return False
    else:
        # IDE not running - launch with project
        return open_antigravity(str(path))


def list_open_windows() -> list:
    """List all visible windows with their titles."""
    windows = gw.getAllWindows()
    visible = [w for w in windows if w.visible and w.title.strip()]
    return [(w.title, w.isMaximized, w.isMinimized) for w in visible]


def close_window(title_pattern: str) -> bool:
    """Close a window by title (use with caution!)."""
    window = find_window(title_pattern)
    
    if not window:
        print(f"[ERROR] Window '{title_pattern}' not found!")
        return False
    
    try:
        window.close()
        print(f"[INFO] Closed window: {window.title}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to close: {e}")
        return False


# ----- CLI Interface -----
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
Windows Control Module
======================

Commands:
    python windows_control.py open [project_path]  - Open AntiGravity (optionally with project)
    python windows_control.py max [window_title]   - Maximize a window
    python windows_control.py min [window_title]   - Minimize a window
    python windows_control.py focus [window_title] - Focus a window
    python windows_control.py list                 - List all open windows
    python windows_control.py project <path>       - Open a project in AntiGravity
""")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    
    if command == "open":
        open_antigravity(arg)
    elif command == "max":
        maximize_window(arg or "AntiGravity")
    elif command == "min":
        minimize_window(arg or "AntiGravity")
    elif command == "focus":
        focus_window(arg or "AntiGravity")
    elif command == "restore":
        restore_window(arg or "AntiGravity")
    elif command == "list":
        windows = list_open_windows()
        print("\nOpen Windows:")
        for title, is_max, is_min in windows:
            state = "MAX" if is_max else ("MIN" if is_min else "")
            print(f"  [{state:3}] {title[:60]}")
    elif command == "project":
        if not arg:
            print("Usage: python windows_control.py project <path>")
        else:
            open_project(arg)
    elif command == "close":
        if not arg:
            print("Usage: python windows_control.py close <window_title>")
        else:
            close_window(arg)
    else:
        print(f"Unknown command: {command}")

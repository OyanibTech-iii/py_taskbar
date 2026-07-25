#!/usr/bin/env python3
"""
AppTracker — Native Python Desktop Application
Minimalist Gray & White UI for tracking running desktop apps, CPU/RAM usage, and focus duration.

Run on any desktop OS (Windows, macOS, Linux):
    python3 desktop_app.py
"""

import os
import json
import tkinter as tk

from auth import AuthManager, build_auth_ui, AUTH_CONFIG_PATH
from gui import DesktopAppGUI
from theme import apply_config


def main():
    config = {}
    if os.path.exists(AUTH_CONFIG_PATH):
        try:
            with open(AUTH_CONFIG_PATH) as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                config = cfg
        except Exception:
            pass

    apply_config(config)

    root = tk.Tk()
    auth = AuthManager()

    def on_auth():
        for w in root.winfo_children():
            w.destroy()
        DesktopAppGUI(root)

    build_auth_ui(root, auth, on_auth)
    root.mainloop()


if __name__ == '__main__':
    main()

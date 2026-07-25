import platform
import tkinter.font as tkfont

THEMES = {
    "Minimal Light": {
        "bg_main": "#f8fafc",
        "bg_card": "#ffffff",
        "bg_secondary": "#f1f5f9",
        "bg_dark": "#0f172a",
        "border": "#e2e8f0",
        "text_primary": "#0f172a",
        "text_secondary": "#64748b",
        "text_muted": "#94a3b8",
        "accent_green": "#10b981",
        "accent_amber": "#f59e0b",
    },
    "Dark Slate": {
        "bg_main": "#0f172a",
        "bg_card": "#1e293b",
        "bg_secondary": "#334155",
        "bg_dark": "#020617",
        "border": "#475569",
        "text_primary": "#f1f5f9",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",
        "accent_green": "#34d399",
        "accent_amber": "#fbbf24",
    },
    "Nord": {
        "bg_main": "#2e3440",
        "bg_card": "#3b4252",
        "bg_secondary": "#434c5e",
        "bg_dark": "#1a1e28",
        "border": "#4c566a",
        "text_primary": "#eceff4",
        "text_secondary": "#d8dee9",
        "text_muted": "#81a1c1",
        "accent_green": "#a3be8c",
        "accent_amber": "#ebcb8b",
    },
    "Dracula": {
        "bg_main": "#282a36",
        "bg_card": "#44475a",
        "bg_secondary": "#383a4a",
        "bg_dark": "#191a21",
        "border": "#6272a4",
        "text_primary": "#f8f8f2",
        "text_secondary": "#bd93f9",
        "text_muted": "#6272a4",
        "accent_green": "#50fa7b",
        "accent_amber": "#ffb86c",
    },
    "Solarized Light": {
        "bg_main": "#fdf6e3",
        "bg_card": "#eee8d5",
        "bg_secondary": "#eee8d5",
        "bg_dark": "#073642",
        "border": "#93a1a1",
        "text_primary": "#073642",
        "text_secondary": "#586e75",
        "text_muted": "#93a1a1",
        "accent_green": "#859900",
        "accent_amber": "#b58900",
    },
}

THEME = dict(THEMES["Minimal Light"])
THEME["font_family"] = "Segoe UI" if platform.system() == "Windows" else "Helvetica"
THEME["font_mono"] = "Consolas" if platform.system() == "Windows" else "Courier"


def list_installed_fonts():
    return sorted(tkfont.families())


def apply_config(config):
    theme_name = config.get("theme_name", "Minimal Light")
    if theme_name in THEMES:
        THEME.update(THEMES[theme_name])
    ff = config.get("font_family", "")
    fm = config.get("font_mono", "")
    if ff:
        THEME["font_family"] = ff
    if fm:
        THEME["font_mono"] = fm

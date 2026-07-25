import os
import json
import hashlib
import tkinter as tk
from theme import THEME

AUTH_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".apptracker_config.json")


class AuthManager:
    def __init__(self):
        self.config_path = AUTH_CONFIG_PATH
        self.config = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)

    def is_first_run(self):
        return "pin_hash" not in self.config

    def set_pin(self, pin):
        self.config["pin_hash"] = hashlib.sha256(pin.encode()).hexdigest()
        self.save()

    def verify_pin(self, pin):
        return hashlib.sha256(pin.encode()).hexdigest() == self.config.get("pin_hash", "")

    def reset(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.config = {}


def _round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    pts = [
        x1+r, y1, x2-r, y1,
        x2, y1, x2, y1+r,
        x2, y2-r, x2, y2,
        x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r,
        x1, y1+r, x1, y1
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


def _make_round_btn(parent, text, command, bg, fg, font, width=200, height=42):
    frame = tk.Frame(parent, bg=THEME["bg_main"], width=width, height=height)
    frame.pack_propagate(False)
    canvas = tk.Canvas(frame, width=width, height=height, highlightthickness=0, bg=THEME["bg_main"])
    canvas.place(x=0, y=0)
    r = 12
    _round_rect(canvas, 2, 2, width-2, height-2, r, fill=bg, outline="", tags="bg")
    canvas.create_text(width//2, height//2, text=text, fill=fg, font=font, tags="txt")
    def on_enter(_):
        canvas.itemconfig("bg", fill="#1e293b" if bg == THEME["bg_dark"] else bg)
    def on_leave(_):
        canvas.itemconfig("bg", fill=bg)
    def on_click(_):
        command()
    canvas.bind("<Button-1>", on_click)
    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    frame.bind("<Button-1>", on_click)
    return frame


def _make_round_entry(parent, textvariable, show, width=200):
    frame = tk.Frame(parent, bg=THEME["bg_main"])
    canvas = tk.Canvas(frame, width=width, height=40, highlightthickness=0, bg=THEME["bg_main"])
    canvas.pack()
    _round_rect(canvas, 2, 2, width-2, 38, 12, fill=THEME["bg_card"], outline=THEME["border"], width=2)
    entry = tk.Entry(frame, textvariable=textvariable, show=show, width=16,
                     font=(THEME["font_family"], 11), justify="center",
                     bd=0, highlightthickness=0, bg=THEME["bg_card"])
    canvas.create_window(width//2, 20, window=entry, width=width-16, height=32)
    return frame


def build_auth_ui(root, auth, on_success):
    root.title("AppTracker — Authentication")
    root.geometry("1024x680")
    root.minsize(800, 500)
    root.configure(bg=THEME["bg_main"])
    try:
        root.iconbitmap("at/favicon.ico")
    except Exception:
        pass
    root.update_idletasks()
    wx = (root.winfo_screenwidth() - 1024) // 2
    wy = (root.winfo_screenheight() - 680) // 2
    root.geometry(f"+{wx}+{wy}")

    container = tk.Frame(root, bg=THEME["bg_main"])
    container.pack(fill="both", expand=True)

    btn_font = (THEME["font_family"], 11, "bold")
    btn_bg = THEME["bg_dark"]
    btn_fg = "#ffffff"

    def clear():
        for w in container.winfo_children():
            w.destroy()

    def show_page(title, subtitle, body_builder, btn_text, btn_cmd):
        clear()
        logo_img = None
        try:
            from PIL import Image, ImageTk
            img = Image.open("at_logo.png").resize((64, 64), Image.LANCZOS)
            logo_img = ImageTk.PhotoImage(img)
        except Exception:
            pass
        logo = tk.Label(container, image=logo_img, bg=THEME["bg_main"] if logo_img else THEME["bg_dark"],
                        text="" if logo_img else "AT", fg="#ffffff",
                        font=(THEME["font_mono"], 22, "bold"), width=3 if not logo_img else 0,
                        height=1 if not logo_img else 0)
        logo.image = logo_img
        logo.pack(pady=(50, 12))
        tk.Label(container, text=title, bg=THEME["bg_main"],
                 fg=THEME["text_primary"], font=(THEME["font_family"], 18, "bold")).pack()
        if subtitle:
            tk.Label(container, text=subtitle, bg=THEME["bg_main"],
                     fg=THEME["text_secondary"], font=(THEME["font_family"], 10)).pack(pady=(4, 16))
        err_lbl = tk.Label(container, text="", bg=THEME["bg_main"], fg="#dc2626",
                           font=(THEME["font_family"], 9))
        err_lbl.pack()
        def set_err(msg):
            err_lbl.config(text=msg)
        body_builder(container, set_err)
        _make_round_btn(container, btn_text, btn_cmd, btn_bg, btn_fg, btn_font, width=200, height=42).pack()

    def do_welcome():
        def body(parent, set_err):
            tk.Label(parent, text="Desktop Application Monitor", bg=THEME["bg_main"],
                     fg=THEME["text_muted"], font=(THEME["font_family"], 10)).pack()
            features = ("Track processes  ·  CPU & RAM  ·  Real-time radar\n"
                        "Security scan  ·  Top consumers  ·  Export reports")
            tk.Label(parent, text=features, bg=THEME["bg_main"],
                     fg=THEME["text_muted"], font=(THEME["font_family"], 9),
                     justify="center").pack(pady=(16, 0))
        show_page("AppTracker Desktop", None, body, "Get Started",
                  lambda: show_pin_setup() if auth.is_first_run() else show_unlock())

    def show_pin_setup():
        pin_var = tk.StringVar()
        confirm_var = tk.StringVar()
        _set_err = [None]
        def body(parent, set_err):
            _set_err[0] = set_err
            tk.Label(parent, text="Create a 4–6 digit PIN to secure the app",
                     bg=THEME["bg_main"], fg=THEME["text_muted"],
                     font=(THEME["font_family"], 9)).pack(pady=(0, 10))
            f1 = tk.Frame(parent, bg=THEME["bg_main"])
            f1.pack(pady=4)
            tk.Label(f1, text="PIN:", bg=THEME["bg_main"], fg=THEME["text_primary"],
                     font=(THEME["font_family"], 10), width=10, anchor="e").pack(side="left")
            _make_round_entry(f1, pin_var, "•", width=180).pack(side="left", padx=8)
            f2 = tk.Frame(parent, bg=THEME["bg_main"])
            f2.pack(pady=4)
            tk.Label(f2, text="Confirm:", bg=THEME["bg_main"], fg=THEME["text_primary"],
                     font=(THEME["font_family"], 10), width=10, anchor="e").pack(side="left")
            _make_round_entry(f2, confirm_var, "•", width=180).pack(side="left", padx=8)
        def on_set():
            pin = pin_var.get()
            confirm = confirm_var.get()
            if len(pin) < 4 or len(pin) > 6 or not pin.isdigit():
                _set_err[0]("PIN must be 4–6 digits")
                return
            if pin != confirm:
                _set_err[0]("PINs do not match")
                return
            auth.set_pin(pin)
            show_unlock()
        show_page("Set Your PIN", "First-time setup", body, "Set PIN", on_set)

    def show_unlock():
        pin_var = tk.StringVar()
        attempts = [0]
        _set_err = [None]
        def body(parent, set_err):
            _set_err[0] = set_err
            tk.Label(parent, text="Enter your PIN to unlock the application",
                     bg=THEME["bg_main"], fg=THEME["text_muted"],
                     font=(THEME["font_family"], 9)).pack(pady=(0, 14))
            _make_round_entry(parent, pin_var, "•", width=220).pack()
            pin_var.trace_add("write", lambda *_: _set_err[0](""))
        def on_unlock():
            pin = pin_var.get()
            if not pin:
                _set_err[0]("Enter your PIN")
                return
            if auth.verify_pin(pin):
                root.resizable(True, True)
                on_success()
            else:
                attempts[0] += 1
                remaining = 3 - attempts[0]
                if remaining <= 0:
                    auth.reset()
                    _set_err[0]("Too many attempts — config reset. Restart to set new PIN.")
                else:
                    plural = "s" if remaining != 1 else ""
                    _set_err[0](f"Incorrect PIN ({remaining} attempt{plural} left)")
        show_page("Welcome Back", "Enter your PIN", body, "Unlock", on_unlock)

    do_welcome()

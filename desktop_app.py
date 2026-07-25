#!/usr/bin/env python3
"""
AppTracker — Native Python Desktop Application
Minimalist Gray & White UI for tracking running desktop apps, CPU/RAM usage, and focus duration.

Run on any desktop OS (Windows, macOS, Linux):
    python3 desktop_app.py
"""

import sys
import os
import time
import json
import threading
import platform
import subprocess
from datetime import datetime

# GUI Framework (Tkinter is built into standard Python)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Attempt psutil import for rich process monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Minimalist Gray & White Color Palette
THEME = {
    "bg_main": "#f8fafc",        # Clean off-white background
    "bg_card": "#ffffff",        # White container cards
    "bg_secondary": "#f1f5f9",   # Soft gray accent
    "bg_dark": "#0f172a",        # Deep slate/black for primary buttons
    "border": "#e2e8f0",         # Subtle light border
    "text_primary": "#0f172a",   # Dark primary text
    "text_secondary": "#64748b", # Muted gray label text
    "text_muted": "#94a3b8",     # Light gray text
    "accent_green": "#10b981",   # Emerald indicator for active
    "accent_amber": "#f59e0b",   # Amber for paused
    "font_family": "Segoe UI" if platform.system() == "Windows" else "Helvetica",
    "font_mono": "Consolas" if platform.system() == "Windows" else "Courier"
}


class AppTrackerEngine:
    """Background engine that gathers processes and tracks active durations."""
    def __init__(self):
        self.is_tracking = True
        self.polling_interval = 3.0
        self.processes = []
        self.app_durations = {}  # {app_name: {'seconds': int, 'cpu_sum': float, 'ram_sum': float, 'samples': int}}
        self.activity_logs = []
        self.active_app = "Desktop"
        self.start_time = time.time()
        
        # Default Category Rules
        self.category_rules = [
            {"pattern": "code", "category": "Development"},
            {"pattern": "cursor", "category": "Development"},
            {"pattern": "python", "category": "Development"},
            {"pattern": "terminal", "category": "Development"},
            {"pattern": "bash", "category": "Development"},
            {"pattern": "chrome", "category": "Browser"},
            {"pattern": "firefox", "category": "Browser"},
            {"pattern": "slack", "category": "Communication"},
            {"pattern": "discord", "category": "Communication"},
            {"pattern": "figma", "category": "Design"},
            {"pattern": "spotify", "category": "Entertainment"},
        ]

    def categorize(self, app_name):
        name_lower = app_name.lower()
        for rule in self.category_rules:
            if rule["pattern"].lower() in name_lower:
                return rule["category"]
        if "win" in name_lower or "sys" in name_lower or "daemon" in name_lower:
            return "System"
        return "Productivity"

    def fetch_processes(self):
        if not self.is_tracking:
            return

        procs = []
        if HAS_PSUTIL:
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'username']):
                try:
                    info = p.info
                    mem_mb = round((info['memory_info'].rss if info['memory_info'] else 0) / (1024 * 1024), 1)
                    cpu_pct = round(info['cpu_percent'] or 0.0, 1)
                    name = info['name'] or f"PID-{info['pid']}"
                    
                    procs.append({
                        'pid': info['pid'],
                        'name': name,
                        'cpu': cpu_pct,
                        'memory_mb': mem_mb,
                        'user': info['username'] or 'user',
                        'category': self.categorize(name)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        else:
            # Fallback for systems without psutil
            try:
                if platform.system() in ["Linux", "Darwin"]:
                    cmd = ["ps", "-eo", "pid,pcpu,rss,comm,user"]
                    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
                    lines = output.strip().split('\n')
                    for line in lines[1:40]:
                        parts = line.split(None, 4)
                        if len(parts) >= 5:
                            pid = int(parts[0])
                            cpu = float(parts[1])
                            rss_kb = float(parts[2])
                            comm = parts[3].split('/')[-1]
                            user = parts[4]
                            procs.append({
                                'pid': pid,
                                'name': comm,
                                'cpu': cpu,
                                'memory_mb': round(rss_kb / 1024.0, 1),
                                'user': user,
                                'category': self.categorize(comm)
                            })
            except Exception:
                pass

        # Sort by CPU / Memory
        procs.sort(key=lambda x: (x['cpu'], x['memory_mb']), reverse=True)
        self.processes = procs[:50]

        # Update active app
        if procs:
            top_app = procs[0]['name']
            if self.active_app != top_app:
                self.active_app = top_app
                self.log_event("app_switch", top_app, f"Focus shifted to {top_app}")

        # Accumulate metrics
        for p in procs[:20]:
            name = p['name']
            if name not in self.app_durations:
                self.app_durations[name] = {'seconds': 30, 'cpu_sum': p['cpu'], 'ram_sum': p['memory_mb'], 'samples': 1}
            else:
                self.app_durations[name]['seconds'] += int(self.polling_interval)
                self.app_durations[name]['cpu_sum'] += p['cpu']
                self.app_durations[name]['ram_sum'] += p['memory_mb']
                self.app_durations[name]['samples'] += 1

    def log_event(self, evt_type, app_name, details):
        self.activity_logs.insert(0, {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'type': evt_type,
            'app_name': app_name,
            'details': details
        })
        if len(self.activity_logs) > 100:
            self.activity_logs.pop()


class DesktopAppGUI:
    """Tkinter Native Desktop Application Interface."""
    def __init__(self, root):
        self.root = root
        self.engine = AppTrackerEngine()
        
        self.root.title("AppTracker — Desktop Application Monitor")
        self.root.geometry("1024x680")
        self.root.minsize(800, 500)
        self.root.configure(bg=THEME["bg_main"])
        
        # Configure TTK Styles for Minimalist Gray & White Look
        self.setup_styles()
        
        # Build UI layout
        self.build_header()
        self.build_body()
        self.build_statusbar()
        
        # Start background polling thread
        self.start_background_thread()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors & Fonts
        self.style.configure('.', background=THEME["bg_main"], foreground=THEME["text_primary"], font=(THEME["font_family"], 10))
        self.style.configure('TNotebook', background=THEME["bg_main"], borderwidth=0)
        self.style.configure('TNotebook.Tab', background=THEME["bg_secondary"], foreground=THEME["text_secondary"], padding=[12, 6], font=(THEME["font_family"], 9, "bold"))
        self.style.map('TNotebook.Tab', background=[('selected', THEME["bg_card"])], foreground=[('selected', THEME["text_primary"])])
        
        # Treeview styling
        self.style.configure('Treeview', background=THEME["bg_card"], fieldbackground=THEME["bg_card"], foreground=THEME["text_primary"], rowheight=28, borderwidth=1, relief="flat")
        self.style.configure('Treeview.Heading', background=THEME["bg_secondary"], foreground=THEME["text_primary"], font=(THEME["font_family"], 9, "bold"), relief="flat")
        self.style.map('Treeview', background=[('selected', THEME["bg_dark"])], foreground=[('selected', "#ffffff")])

    def build_header(self):
        header_frame = tk.Frame(self.root, bg=THEME["bg_card"], bd=1, relief="solid", highlightbackground=THEME["border"])
        header_frame.pack(fill="x", padx=0, pady=0)

        inner = tk.Frame(header_frame, bg=THEME["bg_card"])
        inner.pack(fill="x", padx=20, pady=12)

        # Title / Brand
        brand_frame = tk.Frame(inner, bg=THEME["bg_card"])
        brand_frame.pack(side="left")

        logo_box = tk.Label(brand_frame, text="AT", bg=THEME["bg_dark"], fg="#ffffff", font=(THEME["font_mono"], 11, "bold"), width=3, height=1)
        logo_box.pack(side="left", padx=(0, 10))

        title_label = tk.Label(brand_frame, text="AppTracker Desktop", bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_family"], 13, "bold"))
        title_label.pack(anchor="w")

        self.status_lbl = tk.Label(brand_frame, text="● Python Engine Active", bg=THEME["bg_card"], fg=THEME["accent_green"], font=(THEME["font_mono"], 9))
        self.status_lbl.pack(anchor="w")

        # System Metrics (CPU/RAM)
        metrics_frame = tk.Frame(inner, bg=THEME["bg_card"])
        metrics_frame.pack(side="right")

        self.cpu_meter = tk.Label(metrics_frame, text="CPU: 0.0%", bg=THEME["bg_secondary"], fg=THEME["text_primary"], font=(THEME["font_mono"], 9, "bold"), padx=10, pady=4)
        self.cpu_meter.pack(side="left", padx=4)

        self.ram_meter = tk.Label(metrics_frame, text="RAM: 0 MB", bg=THEME["bg_secondary"], fg=THEME["text_primary"], font=(THEME["font_mono"], 9, "bold"), padx=10, pady=4)
        self.ram_meter.pack(side="left", padx=4)

        self.btn_pause = tk.Button(
            metrics_frame, text="Pause Engine", bg=THEME["bg_dark"], fg="#ffffff",
            activebackground="#334155", activeforeground="#ffffff",
            relief="flat", font=(THEME["font_family"], 9, "bold"), padx=12, pady=3,
            command=self.toggle_tracking
        )
        self.btn_pause.pack(side="left", padx=8)

    def build_body(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=15)

        # Tab 1: Live Processes
        self.tab_processes = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_processes, text="Live Processes")
        self.build_processes_tab()

        # Tab 2: Analytics & Usage
        self.tab_analytics = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_analytics, text="Analytics & Focus")
        self.build_analytics_tab()

        # Tab 3: Category Rules
        self.tab_rules = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_rules, text="Category Rules")
        self.build_rules_tab()

        # Tab 4: Activity Log Stream
        self.tab_logs = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_logs, text="Activity Logs")
        self.build_logs_tab()

    def build_processes_tab(self):
        # Search Bar
        search_frame = tk.Frame(self.tab_processes, bg=THEME["bg_main"])
        search_frame.pack(fill="x", pady=8)

        tk.Label(search_frame, text="Filter:", bg=THEME["bg_main"], fg=THEME["text_secondary"], font=(THEME["font_mono"], 9)).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_tree())
        entry = tk.Entry(search_frame, textvariable=self.search_var, bg=THEME["bg_card"], fg=THEME["text_primary"], relief="solid", bd=1, font=(THEME["font_mono"], 9))
        entry.pack(side="left", fill="x", expand=True, ipady=3)

        btn_export = tk.Button(search_frame, text="Export CSV", bg=THEME["bg_secondary"], fg=THEME["text_primary"],
                               relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2,
                               command=lambda: self.export_tree_to_csv(self.tree, "processes"))
        btn_export.pack(side="right", padx=(8, 0))

        # Treeview Table
        cols = ("PID", "Application Name", "CPU %", "Memory (MB)", "Category", "User")
        self.tree = ttk.Treeview(self.tab_processes, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("PID", text="PID")
        self.tree.heading("Application Name", text="Application Name")
        self.tree.heading("CPU %", text="CPU %")
        self.tree.heading("Memory (MB)", text="Memory (MB)")
        self.tree.heading("Category", text="Category")
        self.tree.heading("User", text="User")

        self.tree.column("PID", width=70, anchor="center")
        self.tree.column("Application Name", width=260, anchor="w")
        self.tree.column("CPU %", width=90, anchor="e")
        self.tree.column("Memory (MB)", width=110, anchor="e")
        self.tree.column("Category", width=120, anchor="center")
        self.tree.column("User", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(self.tab_processes, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def build_analytics_tab(self):
        frame = tk.Frame(self.tab_analytics, bg=THEME["bg_card"], bd=1, relief="solid", highlightbackground=THEME["border"])
        frame.pack(fill="both", expand=True, pady=10, padx=5)

        header_row = tk.Frame(frame, bg=THEME["bg_card"])
        header_row.pack(fill="x", padx=15, pady=10)
        tk.Label(header_row, text="Application Duration Breakdown", bg=THEME["bg_card"], fg=THEME["text_primary"],
                 font=(THEME["font_family"], 11, "bold")).pack(side="left")
        btn_export = tk.Button(header_row, text="Export CSV", bg=THEME["bg_secondary"], fg=THEME["text_primary"],
                               relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2,
                               command=lambda: self.export_tree_to_csv(self.tree_analytics, "analytics"))
        btn_export.pack(side="right")

        cols = ("App", "Category", "Duration", "Avg CPU", "Avg RAM")
        self.tree_analytics = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree_analytics.heading(c, text=c)
            self.tree_analytics.column(c, width=150, anchor="center")
        self.tree_analytics.pack(fill="both", expand=True, padx=15, pady=10)

    def build_rules_tab(self):
        frame = tk.Frame(self.tab_rules, bg=THEME["bg_card"], bd=1, relief="solid", highlightbackground=THEME["border"])
        frame.pack(fill="both", expand=True, pady=10, padx=5)

        header_row = tk.Frame(frame, bg=THEME["bg_card"])
        header_row.pack(fill="x", padx=15, pady=10)
        tk.Label(header_row, text="Category Mapping Rules", bg=THEME["bg_card"], fg=THEME["text_primary"],
                 font=(THEME["font_family"], 11, "bold")).pack(side="left")
        btn_export = tk.Button(header_row, text="Export CSV", bg=THEME["bg_secondary"], fg=THEME["text_primary"],
                               relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2,
                               command=lambda: self.export_tree_to_csv(self.tree_rules, "category_rules"))
        btn_export.pack(side="right")

        cols = ("Process Match Pattern", "Mapped Category")
        self.tree_rules = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree_rules.heading(c, text=c)
            self.tree_rules.column(c, width=250, anchor="center")
        self.tree_rules.pack(fill="both", expand=True, padx=15, pady=10)

        # Add Rule Form
        form = tk.Frame(frame, bg=THEME["bg_card"])
        form.pack(fill="x", padx=15, pady=10)

        tk.Label(form, text="Process Pattern:", bg=THEME["bg_card"]).pack(side="left")
        self.ent_pattern = tk.Entry(form, width=20, bg=THEME["bg_secondary"], relief="solid", bd=1)
        self.ent_pattern.pack(side="left", padx=5)

        tk.Label(form, text="Category:", bg=THEME["bg_card"]).pack(side="left", padx=(10, 0))
        self.ent_cat = tk.Entry(form, width=15, bg=THEME["bg_secondary"], relief="solid", bd=1)
        self.ent_cat.insert(0, "Productivity")
        self.ent_cat.pack(side="left", padx=5)

        btn_add = tk.Button(form, text="Add Rule", bg=THEME["bg_dark"], fg="#fff", relief="flat", command=self.add_rule)
        btn_add.pack(side="left", padx=10)

        self.refresh_rules_tree()

    def build_logs_tab(self):
        frame = tk.Frame(self.tab_logs, bg=THEME["bg_card"], bd=1, relief="solid", highlightbackground=THEME["border"])
        frame.pack(fill="both", expand=True, pady=10, padx=5)

        header_row = tk.Frame(frame, bg=THEME["bg_card"])
        header_row.pack(fill="x", padx=15, pady=(10, 0))
        tk.Label(header_row, text="Activity Log Stream", bg=THEME["bg_card"], fg=THEME["text_primary"],
                 font=(THEME["font_family"], 11, "bold")).pack(side="left")
        btn_export = tk.Button(header_row, text="Export Logs", bg=THEME["bg_secondary"], fg=THEME["text_primary"],
                               relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2,
                               command=self.export_logs_to_file)
        btn_export.pack(side="right")

        self.txt_logs = tk.Text(frame, bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_mono"], 9), bd=0)
        self.txt_logs.pack(fill="both", expand=True, padx=10, pady=10)

    def build_statusbar(self):
        sb = tk.Frame(self.root, bg=THEME["bg_secondary"], bd=1, relief="solid", highlightbackground=THEME["border"])
        sb.pack(fill="x", side="bottom")

        self.sb_label = tk.Label(sb, text="Engine running • Python " + platform.python_version(), bg=THEME["bg_secondary"], fg=THEME["text_secondary"], font=(THEME["font_mono"], 8))
        self.sb_label.pack(side="left", padx=10, pady=4)

    def toggle_tracking(self):
        self.engine.is_tracking = not self.engine.is_tracking
        if self.engine.is_tracking:
            self.btn_pause.config(text="Pause Engine", bg=THEME["bg_dark"])
            self.status_lbl.config(text="● Python Engine Active", fg=THEME["accent_green"])
        else:
            self.btn_pause.config(text="Resume Engine", bg=THEME["accent_amber"])
            self.status_lbl.config(text="PAUSED", fg=THEME["accent_amber"])

    def add_rule(self):
        pat = self.ent_pattern.get().strip()
        cat = self.ent_cat.get().strip()
        if pat and cat:
            self.engine.category_rules.append({"pattern": pat, "category": cat})
            self.ent_pattern.delete(0, "end")
            self.refresh_rules_tree()

    def refresh_rules_tree(self):
        for item in self.tree_rules.get_children():
            self.tree_rules.delete(item)
        for r in self.engine.category_rules:
            self.tree_rules.insert("", "end", values=(r["pattern"], r["category"]))

    def refresh_tree(self):
        filter_text = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in self.engine.processes:
            if filter_text in p['name'].lower() or filter_text in str(p['pid']) or filter_text in p['category'].lower():
                self.tree.insert("", "end", values=(p['pid'], p['name'], f"{p['cpu']}%", f"{p['memory_mb']} MB", p['category'], p['user']))

    def refresh_analytics(self):
        for item in self.tree_analytics.get_children():
            self.tree_analytics.delete(item)

        for name, stats in self.engine.app_durations.items():
            mins = stats['seconds'] // 60
            secs = stats['seconds'] % 60
            avg_cpu = round(stats['cpu_sum'] / max(1, stats['samples']), 1)
            avg_ram = round(stats['ram_sum'] / max(1, stats['samples']), 1)
            cat = self.engine.categorize(name)
            self.tree_analytics.insert("", "end", values=(name, cat, f"{mins}m {secs}s", f"{avg_cpu}%", f"{avg_ram} MB"))

    def refresh_logs(self):
        self.txt_logs.delete("1.0", "end")
        for log in self.engine.activity_logs:
            self.txt_logs.insert("end", f"[{log['timestamp']}] [{log['type'].upper()}] {log['app_name']} - {log['details']}\n")

    def export_tree_to_csv(self, tree, default_name="export"):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{default_name}.csv"
        )
        if not path:
            return
        cols = [tree.heading(c)["text"] for c in tree["columns"]]
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write(",".join(f'"{c}"' for c in cols) + "\n")
            for item in tree.get_children():
                values = tree.item(item, "values")
                f.write(",".join(f'"{v}"' for v in values) + "\n")

    def export_logs_to_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="activity_logs.txt"
        )
        if not path:
            return
        content = self.txt_logs.get("1.0", "end-1c")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def start_background_thread(self):
        def loop():
            while True:
                self.engine.fetch_processes()
                
                # Calculate totals
                cpu_total = sum(p['cpu'] for p in self.engine.processes)
                ram_total = sum(p['memory_mb'] for p in self.engine.processes)

                # Update UI elements safely on main thread
                self.root.after(0, lambda: self.cpu_meter.config(text=f"CPU: {cpu_total:.1f}%"))
                self.root.after(0, lambda: self.ram_meter.config(text=f"RAM: {ram_total:.1f} MB"))
                self.root.after(0, self.refresh_tree)
                self.root.after(0, self.refresh_analytics)
                self.root.after(0, self.refresh_logs)

                time.sleep(self.engine.polling_interval)

        t = threading.Thread(target=loop, daemon=True)
        t.start()


def main():
    root = tk.Tk()
    gui = DesktopAppGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()

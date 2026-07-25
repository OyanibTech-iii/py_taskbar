import time
import json
import math
import threading
import platform
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog

from theme import THEME, THEMES, list_installed_fonts, apply_config
from engine import AppTrackerEngine


class DesktopAppGUI:
    def __init__(self, root):
        self.root = root
        self.engine = AppTrackerEngine()

        self.root.title("AppTracker — Desktop Application Monitor")
        self.root.geometry("1024x680")
        self.root.minsize(800, 500)
        self.root.configure(bg=THEME["bg_main"])

        self.setup_styles()
        self.build_header()
        self.build_body()
        self.build_statusbar()
        self.start_background_thread()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background=THEME["bg_main"], foreground=THEME["text_primary"], font=(THEME["font_family"], 10))
        self.style.configure('TNotebook', background=THEME["bg_main"], borderwidth=0)
        self.style.configure('TNotebook.Tab', background=THEME["bg_secondary"], foreground=THEME["text_secondary"], padding=[12, 6], font=(THEME["font_family"], 9, "bold"))
        self.style.map('TNotebook.Tab', background=[('selected', THEME["bg_card"])], foreground=[('selected', THEME["text_primary"])])
        self.style.configure('Treeview', background=THEME["bg_card"], fieldbackground=THEME["bg_card"], foreground=THEME["text_primary"], rowheight=28, borderwidth=1, relief="flat")
        self.style.configure('Treeview.Heading', background=THEME["bg_secondary"], foreground=THEME["text_primary"], font=(THEME["font_family"], 9, "bold"), relief="flat")
        self.style.map('Treeview', background=[('selected', THEME["bg_dark"])], foreground=[('selected', "#ffffff")])

    def build_header(self):
        header_frame = tk.Frame(self.root, bg=THEME["bg_card"], bd=1, relief="solid", highlightbackground=THEME["border"])
        header_frame.pack(fill="x", padx=0, pady=0)
        inner = tk.Frame(header_frame, bg=THEME["bg_card"])
        inner.pack(fill="x", padx=20, pady=12)
        brand_frame = tk.Frame(inner, bg=THEME["bg_card"])
        brand_frame.pack(side="left")
        logo_box = tk.Label(brand_frame, text="AT", bg=THEME["bg_dark"], fg="#ffffff", font=(THEME["font_mono"], 11, "bold"), width=3, height=1)
        logo_box.pack(side="left", padx=(0, 10))
        title_label = tk.Label(brand_frame, text="AppTracker Desktop", bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_family"], 13, "bold"))
        title_label.pack(anchor="w")
        self.status_lbl = tk.Label(brand_frame, text="● Python Engine Active", bg=THEME["bg_card"], fg=THEME["accent_green"], font=(THEME["font_mono"], 9))
        self.status_lbl.pack(anchor="w")
        metrics_frame = tk.Frame(inner, bg=THEME["bg_card"])
        metrics_frame.pack(side="right")
        self.cpu_meter = tk.Label(metrics_frame, text="CPU: 0.0%", bg=THEME["bg_secondary"], fg=THEME["text_primary"], font=(THEME["font_mono"], 9, "bold"), padx=10, pady=4)
        self.cpu_meter.pack(side="left", padx=4)
        self.ram_meter = tk.Label(metrics_frame, text="RAM: 0 MB", bg=THEME["bg_secondary"], fg=THEME["text_primary"], font=(THEME["font_mono"], 9, "bold"), padx=10, pady=4)
        self.ram_meter.pack(side="left", padx=4)
        self.btn_settings = tk.Button(metrics_frame, text="⚙", bg=THEME["bg_secondary"], fg=THEME["text_primary"], activebackground=THEME["bg_dark"], activeforeground="#ffffff", relief="flat", font=(THEME["font_family"], 12), padx=6, pady=0, command=self.open_settings)
        self.btn_settings.pack(side="left", padx=(0, 4))
        self.btn_pause = tk.Button(metrics_frame, text="Pause Engine", bg=THEME["bg_dark"], fg="#ffffff", activebackground="#334155", activeforeground="#ffffff", relief="flat", font=(THEME["font_family"], 9, "bold"), padx=12, pady=3, command=self.toggle_tracking)
        self.btn_pause.pack(side="left", padx=8)

    def build_body(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=15)
        self.tab_processes = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_processes, text="Live Processes")
        self.build_processes_tab()
        self.tab_analytics = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_analytics, text="Analytics & Focus")
        self.build_analytics_tab()
        self.tab_rules = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_rules, text="Category Rules")
        self.build_rules_tab()
        self.tab_logs = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_logs, text="Activity Logs")
        self.build_logs_tab()
        self.tab_radar = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_radar, text="Real-time Radar")
        self.build_realtime_tab()
        self.tab_security = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_security, text="Security Scan")
        self.build_security_tab()
        self.tab_consumers = tk.Frame(self.notebook, bg=THEME["bg_main"])
        self.notebook.add(self.tab_consumers, text="Top Consumers")
        self.build_top_consumers_tab()

    def build_processes_tab(self):
        search_frame = tk.Frame(self.tab_processes, bg=THEME["bg_main"])
        search_frame.pack(fill="x", pady=8)
        tk.Label(search_frame, text="Filter:", bg=THEME["bg_main"], fg=THEME["text_secondary"], font=(THEME["font_mono"], 9)).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_tree())
        entry = tk.Entry(search_frame, textvariable=self.search_var, bg=THEME["bg_card"], fg=THEME["text_primary"], relief="solid", bd=1, font=(THEME["font_mono"], 9))
        entry.pack(side="left", fill="x", expand=True, ipady=3)
        btn_export = tk.Button(search_frame, text="Export CSV", bg=THEME["bg_secondary"], fg=THEME["text_primary"], relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2, command=lambda: self.export_tree_to_csv(self.tree, "processes"))
        btn_export.pack(side="right", padx=(8, 0))
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
        tk.Label(header_row, text="Application Duration Breakdown", bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_family"], 11, "bold")).pack(side="left")
        btn_export = tk.Button(header_row, text="Export CSV", bg=THEME["bg_secondary"], fg=THEME["text_primary"], relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2, command=lambda: self.export_tree_to_csv(self.tree_analytics, "analytics"))
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
        tk.Label(header_row, text="Category Mapping Rules", bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_family"], 11, "bold")).pack(side="left")
        btn_export = tk.Button(header_row, text="Export CSV", bg=THEME["bg_secondary"], fg=THEME["text_primary"], relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2, command=lambda: self.export_tree_to_csv(self.tree_rules, "category_rules"))
        btn_export.pack(side="right")
        cols = ("Process Match Pattern", "Mapped Category")
        self.tree_rules = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree_rules.heading(c, text=c)
            self.tree_rules.column(c, width=250, anchor="center")
        self.tree_rules.pack(fill="both", expand=True, padx=15, pady=10)
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
        tk.Label(header_row, text="Activity Log Stream", bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_family"], 11, "bold")).pack(side="left")
        btn_export = tk.Button(header_row, text="Export Logs", bg=THEME["bg_secondary"], fg=THEME["text_primary"], relief="flat", font=(THEME["font_family"], 9, "bold"), padx=10, pady=2, command=self.export_logs_to_file)
        btn_export.pack(side="right")
        self.txt_logs = tk.Text(frame, bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_mono"], 9), bd=0)
        self.txt_logs.pack(fill="both", expand=True, padx=10, pady=10)

    def build_realtime_tab(self):
        container = tk.Frame(self.tab_radar, bg=THEME["bg_main"])
        container.pack(fill="both", expand=True)
        header_row = tk.Frame(container, bg=THEME["bg_main"])
        header_row.pack(fill="x", pady=(12, 0))
        tk.Label(header_row, text="Real-time Radar & Monitoring", bg=THEME["bg_main"], fg=THEME["text_primary"], font=(THEME["font_family"], 12, "bold")).pack(side="left", padx=20)
        btn_report = tk.Button(header_row, text="Export Report", bg=THEME["bg_dark"], fg="#ffffff", relief="flat", font=(THEME["font_family"], 9, "bold"), padx=12, pady=3, command=self.export_radar_report)
        btn_report.pack(side="right", padx=20)
        content = tk.Frame(container, bg=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=10)
        self.radar_labels = ["CPU Load", "RAM Usage", "Processes", "Uptime", "Focus"]
        self.radar_maxes = [100, 100, 100, 100, 100]
        chart_frame = tk.Frame(content, bg=THEME["bg_card"], bd=1, relief="solid", highlightbackground=THEME["border"])
        chart_frame.pack(side="left", fill="both", expand=True)
        self.radar_canvas = tk.Canvas(chart_frame, bg=THEME["bg_card"], highlightthickness=0)
        self.radar_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        right_panel = tk.Frame(content, bg=THEME["bg_card"], bd=1, relief="solid", highlightbackground=THEME["border"], width=260)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)
        tk.Label(right_panel, text="Live Metrics", bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_family"], 11, "bold")).pack(anchor="w", padx=15, pady=(12, 8))
        self.metric_widgets = {}
        metric_defs = [("cpu", "CPU Total"), ("ram", "RAM Total"), ("procs", "Processes"), ("uptime", "Uptime"), ("top_app", "Top App"), ("tracking", "Tracking")]
        for key, label in metric_defs:
            row = tk.Frame(right_panel, bg=THEME["bg_card"])
            row.pack(fill="x", padx=15, pady=3)
            tk.Label(row, text=label, bg=THEME["bg_card"], fg=THEME["text_secondary"], font=(THEME["font_family"], 9)).pack(side="left")
            val_lbl = tk.Label(row, text="--", bg=THEME["bg_card"], fg=THEME["text_primary"], font=(THEME["font_mono"], 9, "bold"))
            val_lbl.pack(side="right")
            self.metric_widgets[key] = val_lbl
        self.root.after(200, self.refresh_radar)

    def get_radar_values(self):
        cpu = min(100, sum(p['cpu'] for p in self.engine.processes))
        ram_mb = sum(p['memory_mb'] for p in self.engine.processes)
        ram = min(100, ram_mb / 16.384)
        procs = min(100, len(self.engine.processes) * 2)
        elapsed = time.time() - self.engine.start_time
        uptime = min(100, elapsed / 36.0)
        focus = 85 if self.engine.is_tracking else 30
        return [cpu, ram, procs, uptime, focus]

    def refresh_radar(self):
        c = self.radar_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        cx, cy = w // 2, h // 2
        radius = min(cx, cy) - 40
        if radius < 20:
            return
        n = 5
        angles = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
        def point(r, a):
            return cx + r * math.cos(a), cy + r * math.sin(a)
        for level in [20, 40, 60, 80, 100]:
            r = radius * level / 100
            pts = []
            for a in angles:
                x, y = point(r, a)
                pts.extend([x, y])
            c.create_polygon(pts, outline=THEME["border"], fill="", width=1)
        for a, lbl in zip(angles, self.radar_labels):
            x, y = point(radius, a)
            c.create_line(cx, cy, x, y, fill=THEME["border"], width=1)
            lx, ly = point(radius + 18, a)
            c.create_text(lx, ly, text=lbl, fill=THEME["text_secondary"], font=(THEME["font_mono"], 8))
        vals = self.get_radar_values()
        pts = []
        for v, a in zip(vals, angles):
            r = radius * v / 100
            x, y = point(r, a)
            pts.extend([x, y])
        c.create_polygon(pts, outline=THEME["accent_green"], fill=THEME["accent_green"], stipple="gray25", width=2)
        for i in range(0, len(pts), 2):
            c.create_oval(pts[i] - 3, pts[i + 1] - 3, pts[i] + 3, pts[i + 1] + 3, fill=THEME["accent_green"], outline="")
        self.metric_widgets["cpu"].config(text=f"{vals[0]:.1f}%")
        self.metric_widgets["ram"].config(text=f"{sum(p['memory_mb'] for p in self.engine.processes):.1f} MB")
        self.metric_widgets["procs"].config(text=str(len(self.engine.processes)))
        elapsed = time.time() - self.engine.start_time
        mins, secs = int(elapsed // 60), int(elapsed % 60)
        self.metric_widgets["uptime"].config(text=f"{mins}m {secs}s")
        self.metric_widgets["top_app"].config(text=self.engine.active_app[:18])
        self.metric_widgets["tracking"].config(text="Active" if self.engine.is_tracking else "Paused")

    def export_radar_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], initialfile="radar_report.json")
        if not path:
            return
        vals = self.get_radar_values()
        elapsed = time.time() - self.engine.start_time
        mins, secs = int(elapsed // 60), int(elapsed % 60)
        report = {
            "timestamp": datetime.now().isoformat(),
            "tracking_active": self.engine.is_tracking,
            "active_app": self.engine.active_app,
            "uptime": f"{mins}m {secs}s",
            "radar_metrics": {self.radar_labels[i]: vals[i] for i in range(len(self.radar_labels))},
            "processes": [{"name": p["name"], "cpu": p["cpu"], "memory_mb": p["memory_mb"], "category": p["category"]} for p in self.engine.processes[:20]],
            "app_durations": {name: {"duration_sec": d["seconds"], "avg_cpu": round(d["cpu_sum"] / max(1, d["samples"]), 1), "avg_ram_mb": round(d["ram_sum"] / max(1, d["samples"]), 1)} for name, d in self.engine.app_durations.items()}
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    def export_threats_to_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], initialfile="threat_scan.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write('"Risk Score","Process Name","PID","Indicators","CPU %","Memory MB","User","Category"\n')
            for t in self.engine.threats:
                ind = "; ".join(t["indicators"])
                f.write(f'{t["risk_score"]},"{t["name"]}",{t["pid"]},"{ind}",{t["cpu"]},{t["memory_mb"]},"{t["user"]}","{t["category"]}"\n')

    def build_security_tab(self):
        container = tk.Frame(self.tab_security, bg=THEME["bg_main"])
        container.pack(fill="both", expand=True)
        header = tk.Frame(container, bg=THEME["bg_main"])
        header.pack(fill="x", pady=(12, 0))
        tk.Label(header, text="Hidden Apps & Threat Detection", bg=THEME["bg_main"], fg=THEME["text_primary"], font=(THEME["font_family"], 12, "bold")).pack(side="left", padx=20)
        tk.Label(header, text="Heuristic scan — may produce false positives", bg=THEME["bg_main"], fg=THEME["text_muted"], font=(THEME["font_mono"], 8)).pack(side="left", padx=(8, 0))
        btn_export = tk.Button(header, text="Export CSV", bg=THEME["bg_dark"], fg="#ffffff", relief="flat", font=(THEME["font_family"], 9, "bold"), padx=12, pady=3, command=self.export_threats_to_csv)
        btn_export.pack(side="right", padx=20)
        summary = tk.Frame(container, bg=THEME["bg_main"])
        summary.pack(fill="x", padx=20, pady=(8, 0))
        self.threat_count_lbl = tk.Label(summary, text="Scanning...", bg=THEME["bg_main"], fg=THEME["text_secondary"], font=(THEME["font_family"], 10))
        self.threat_count_lbl.pack(side="left")
        cols = ("Risk Score", "Process Name", "PID", "Indicators", "CPU %", "Memory (MB)", "User")
        self.tree_threats = ttk.Treeview(container, columns=cols, show="headings", selectmode="browse")
        col_widths = [90, 220, 70, 320, 70, 100, 100]
        for c, w in zip(cols, col_widths):
            self.tree_threats.heading(c, text=c)
            self.tree_threats.column(c, width=w, anchor="center")
        self.tree_threats.column("Process Name", anchor="w")
        self.tree_threats.column("Indicators", anchor="w")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree_threats.yview)
        self.tree_threats.configure(yscroll=scrollbar.set)
        self.tree_threats.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=10)
        self.refresh_threats()

    def refresh_threats(self):
        for item in self.tree_threats.get_children():
            self.tree_threats.delete(item)
        threats = self.engine.threats
        if not threats:
            self.threat_count_lbl.config(text="No threats detected — system appears clean")
            return
        high = sum(1 for t in threats if t["risk_score"] >= 50)
        med = sum(1 for t in threats if 20 <= t["risk_score"] < 50)
        self.threat_count_lbl.config(text=f"{len(threats)} flagged  ·  {high} high risk  ·  {med} medium risk")
        for t in threats:
            ind = "; ".join(t["indicators"])
            tag = "high" if t["risk_score"] >= 50 else "medium" if t["risk_score"] >= 20 else "low"
            self.tree_threats.insert("", "end", values=(t["risk_score"], t["name"], t["pid"], ind, f"{t['cpu']}%", f"{t['memory_mb']} MB", t["user"]), tags=(tag,))
        self.tree_threats.tag_configure("high", foreground="#dc2626")
        self.tree_threats.tag_configure("medium", foreground="#d97706")
        self.tree_threats.tag_configure("low", foreground="#64748b")

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
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], initialfile=f"{default_name}.csv")
        if not path:
            return
        cols = [tree.heading(c)["text"] for c in tree["columns"]]
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write(",".join(f'"{c}"' for c in cols) + "\n")
            for item in tree.get_children():
                values = tree.item(item, "values")
                f.write(",".join(f'"{v}"' for v in values) + "\n")

    def export_logs_to_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], initialfile="activity_logs.txt")
        if not path:
            return
        content = self.txt_logs.get("1.0", "end-1c")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def build_top_consumers_tab(self):
        container = tk.Frame(self.tab_consumers, bg=THEME["bg_main"])
        container.pack(fill="both", expand=True)
        header = tk.Frame(container, bg=THEME["bg_main"])
        header.pack(fill="x", pady=(12, 0))
        tk.Label(header, text="Top Resource Consumers — ranked by CPU usage", bg=THEME["bg_main"], fg=THEME["text_primary"], font=(THEME["font_family"], 12, "bold")).pack(side="left", padx=20)
        btn = tk.Button(header, text="Export CSV", bg=THEME["bg_dark"], fg="#ffffff", relief="flat", font=(THEME["font_family"], 9, "bold"), padx=12, pady=3, command=self.export_consumers_csv)
        btn.pack(side="right", padx=20)
        cols = ("Rank", "Process Name", "CPU %", "RAM (MB)", "Category", "Analysis")
        self.tree_consumers = ttk.Treeview(container, columns=cols, show="headings", selectmode="browse")
        widths = [60, 240, 80, 90, 120, 350]
        for c, w in zip(cols, widths):
            self.tree_consumers.heading(c, text=c)
            self.tree_consumers.column(c, width=w, anchor="w")
        self.tree_consumers.column("Rank", anchor="center")
        self.tree_consumers.column("CPU %", anchor="e")
        self.tree_consumers.column("RAM (MB)", anchor="e")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree_consumers.yview)
        self.tree_consumers.configure(yscroll=scrollbar.set)
        self.tree_consumers.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=15)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=15)
        self.consumer_summary = tk.Label(container, text="", bg=THEME["bg_main"], fg=THEME["text_secondary"], font=(THEME["font_family"], 10))
        self.consumer_summary.pack(padx=20, pady=(0, 12), anchor="w")
        self.refresh_top_consumers()

    def refresh_top_consumers(self):
        for item in self.tree_consumers.get_children():
            self.tree_consumers.delete(item)
        procs = sorted(self.engine.processes, key=lambda p: p['cpu'], reverse=True)[:10]
        if not procs:
            self.consumer_summary.config(text="No process data available")
            return
        total_cpu = sum(p['cpu'] for p in self.engine.processes)
        total_ram = sum(p['memory_mb'] for p in self.engine.processes)
        avg_cpu_top10 = sum(p['cpu'] for p in procs) / max(len(procs), 1)
        for rank, p in enumerate(procs, 1):
            analysis = []
            cpu_share = (p['cpu'] / max(total_cpu, 1)) * 100
            ram_share = (p['memory_mb'] / max(total_ram, 1)) * 100
            if cpu_share > 30:
                analysis.append(f"Dominant CPU: {cpu_share:.0f}% of all processes")
            elif p['cpu'] > avg_cpu_top10 * 1.2:
                analysis.append(f"Above avg CPU ({avg_cpu_top10:.1f}% avg)")
            if p['memory_mb'] > 500:
                analysis.append(f"High RAM footprint ({p['memory_mb']:.0f} MB)")
            if ram_share > 25:
                analysis.append(f"RAM-heavy: {ram_share:.0f}% of total")
            if p['cpu'] < 1 and p['category'] in ("System", "Productivity"):
                analysis.append("Background process, idle CPU")
            if p['category'] in ("Browser", "Development", "Entertainment"):
                analysis.append(f"Expected high-use category ({p['category']})")
            if not analysis:
                analysis.append("Moderate resource usage")
            self.tree_consumers.insert("", "end", values=(f"#{rank}", p['name'], f"{p['cpu']}%", f"{p['memory_mb']:.0f}", p['category'], "; ".join(analysis[:3])))
        self.consumer_summary.config(text=f"Top 10 account for {sum(p['cpu'] for p in procs):.1f}% CPU  ·  {sum(p['memory_mb'] for p in procs):.0f} MB RAM  ·  {len([p for p in procs if p['cpu'] > 20])} processes above 20% CPU")

    def export_consumers_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], initialfile="top_consumers.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write('"Rank","Process Name","CPU %","RAM (MB)","Category","Analysis"\n')
            for item in self.tree_consumers.get_children():
                vals = self.tree_consumers.item(item, "values")
                f.write(','.join(f'"{v}"' for v in vals) + '\n')

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("AppTracker — Settings")
        win.geometry("500x400")
        win.resizable(False, False)
        win.configure(bg=THEME["bg_main"])
        win.transient(self.root)
        win.grab_set()

        main = tk.Frame(win, bg=THEME["bg_main"], padx=20, pady=20)
        main.pack(fill="both", expand=True)

        fonts = list_installed_fonts()
        theme_names = list(THEMES.keys())

        cur_family = THEME["font_family"]
        cur_mono = THEME["font_mono"]
        cur_theme = next((n for n in theme_names if THEMES[n]["bg_main"] == THEME["bg_main"]), theme_names[0])

        tk.Label(main, text="Settings", bg=THEME["bg_main"], fg=THEME["text_primary"],
                 font=(THEME["font_family"], 14, "bold")).pack(anchor="w", pady=(0, 16))

        tk.Label(main, text="Theme", bg=THEME["bg_main"], fg=THEME["text_secondary"],
                 font=(THEME["font_family"], 10)).pack(anchor="w")
        theme_var = tk.StringVar(value=cur_theme)
        theme_menu = ttk.Combobox(main, textvariable=theme_var, values=theme_names, state="readonly", width=30)
        theme_menu.pack(anchor="w", pady=(2, 14))

        tk.Label(main, text="Interface Font", bg=THEME["bg_main"], fg=THEME["text_secondary"],
                 font=(THEME["font_family"], 10)).pack(anchor="w")
        family_var = tk.StringVar(value=cur_family if cur_family in fonts else fonts[0])
        fam_menu = ttk.Combobox(main, textvariable=family_var, values=fonts, state="readonly", width=30)
        fam_menu.pack(anchor="w", pady=(2, 14))

        tk.Label(main, text="Monospace Font (code, logs, metrics)", bg=THEME["bg_main"], fg=THEME["text_secondary"],
                 font=(THEME["font_family"], 10)).pack(anchor="w")
        mono_var = tk.StringVar(value=cur_mono if cur_mono in fonts else fonts[0])
        mono_menu = ttk.Combobox(main, textvariable=mono_var, values=fonts, state="readonly", width=30)
        mono_menu.pack(anchor="w", pady=(2, 20))

        bar = tk.Frame(main, bg=THEME["bg_main"])
        bar.pack(fill="x")
        btn_close = tk.Button(bar, text="Cancel", bg=THEME["bg_secondary"], fg=THEME["text_primary"],
                              font=(THEME["font_family"], 10), padx=16, pady=4, relief="flat", command=win.destroy)
        btn_close.pack(side="right", padx=(8, 0))

        def do_apply():
            from auth import AUTH_CONFIG_PATH
            import json, os, sys, subprocess
            config = {}
            if os.path.exists(AUTH_CONFIG_PATH):
                try:
                    with open(AUTH_CONFIG_PATH) as f:
                        config = json.load(f)
                    if not isinstance(config, dict):
                        config = {}
                except Exception:
                    config = {}
            config["theme_name"] = theme_var.get()
            config["font_family"] = family_var.get()
            config["font_mono"] = mono_var.get()
            with open(AUTH_CONFIG_PATH, "w") as f:
                json.dump(config, f)
            win.destroy()
            subprocess.Popen([sys.executable, sys.argv[0]])
            self.root.quit()

        btn_apply = tk.Button(bar, text="Save", bg=THEME["bg_dark"], fg="#ffffff",
                              font=(THEME["font_family"], 10, "bold"), padx=20, pady=4,
                              relief="flat", command=do_apply)
        btn_apply.pack(side="right")

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 500) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        win.geometry(f"+{x}+{y}")

    def start_background_thread(self):
        def loop():
            while True:
                self.engine.fetch_processes()
                cpu_total = sum(p['cpu'] for p in self.engine.processes)
                ram_total = sum(p['memory_mb'] for p in self.engine.processes)
                self.root.after(0, lambda: self.cpu_meter.config(text=f"CPU: {cpu_total:.1f}%"))
                self.root.after(0, lambda: self.ram_meter.config(text=f"RAM: {ram_total:.1f} MB"))
                self.root.after(0, self.refresh_tree)
                self.root.after(0, self.refresh_analytics)
                self.root.after(0, self.refresh_logs)
                self.root.after(0, self.refresh_radar)
                self.root.after(0, self.refresh_threats)
                self.root.after(0, self.refresh_top_consumers)
                time.sleep(self.engine.polling_interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

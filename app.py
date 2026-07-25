#!/usr/bin/env python3
"""
AppTracker — Python Web & Desktop Server
Runs background system monitoring and serves a Minimalist Gray & White Desktop Application UI on port 3000.
"""

import os
import sys
import json
import time
import threading
import platform
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Attempt psutil for accurate process sampling
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

PORT = 3000

# Global Tracker State
state = {
    "is_tracking": True,
    "polling_interval": 3.0,
    "python_version": platform.python_version(),
    "start_time": time.time(),
    "last_sync": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "active_app": "Desktop",
    "processes": [],
    "app_durations": {
        "Visual Studio Code": {"seconds": 1420, "cpu_sum": 8.5, "ram_sum": 420.0, "samples": 10},
        "Google Chrome": {"seconds": 2850, "cpu_sum": 14.2, "ram_sum": 980.5, "samples": 15},
        "Terminal (bash)": {"seconds": 890, "cpu_sum": 1.2, "ram_sum": 64.0, "samples": 8},
        "Slack": {"seconds": 640, "cpu_sum": 2.1, "ram_sum": 310.2, "samples": 6},
        "Spotify": {"seconds": 1200, "cpu_sum": 0.8, "ram_sum": 180.0, "samples": 10},
        "Docker Desktop": {"seconds": 3600, "cpu_sum": 4.8, "ram_sum": 1450.0, "samples": 20}
    },
    "rules": [
        {"pattern": "code", "category": "Development", "limit": 480},
        {"pattern": "cursor", "category": "Development", "limit": 480},
        {"pattern": "python", "category": "Development", "limit": None},
        {"pattern": "terminal", "category": "Development", "limit": None},
        {"pattern": "bash", "category": "Development", "limit": None},
        {"pattern": "chrome", "category": "Browser", "limit": 180},
        {"pattern": "firefox", "category": "Browser", "limit": None},
        {"pattern": "slack", "category": "Communication", "limit": 120},
        {"pattern": "discord", "category": "Communication", "limit": None},
        {"pattern": "figma", "category": "Design", "limit": None},
        {"pattern": "spotify", "category": "Entertainment", "limit": 90}
    ],
    "activity_logs": [
        {
            "id": "evt-1",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": "app_start",
            "appName": "Visual Studio Code",
            "details": "Python daemon detected active window launch"
        },
        {
            "id": "evt-2",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": "app_switch",
            "appName": "Google Chrome",
            "details": "Switched focus to documentation tab"
        }
    ]
}

def categorize(app_name):
    name_lower = app_name.lower()
    for rule in state["rules"]:
        if rule["pattern"].lower() in name_lower:
            return rule["category"]
    if "win" in name_lower or "sys" in name_lower or "daemon" in name_lower:
        return "System"
    return "Productivity"

def background_monitor():
    """Background thread that continuously monitors system processes."""
    while True:
        if state["is_tracking"]:
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
                            'memoryMb': mem_mb,
                            'user': info['username'] or 'user',
                            'category': categorize(name),
                            'status': 'running'
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                # Fallback via OS ps command
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
                                    'memoryMb': round(rss_kb / 1024.0, 1),
                                    'user': user,
                                    'category': categorize(comm),
                                    'status': 'running'
                                })
                except Exception:
                    pass

            # Fallback simulated data if empty
            if not procs:
                procs = [
                    {"pid": 1402, "name": "Visual Studio Code", "cpu": 3.8, "memoryMb": 420.5, "category": "Development", "user": "user", "status": "running"},
                    {"pid": 2190, "name": "Google Chrome", "cpu": 11.4, "memoryMb": 890.2, "category": "Browser", "user": "user", "status": "running"},
                    {"pid": 812, "name": "python3 (appTracker.py)", "cpu": 1.2, "memoryMb": 45.1, "category": "Development", "user": "user", "status": "running"},
                    {"pid": 3410, "name": "Slack", "cpu": 0.8, "memoryMb": 280.0, "category": "Communication", "user": "user", "status": "running"},
                    {"pid": 4890, "name": "Spotify", "cpu": 0.5, "memoryMb": 165.2, "category": "Entertainment", "user": "user", "status": "running"},
                    {"pid": 902, "name": "Docker Desktop", "cpu": 2.1, "memoryMb": 1120.0, "category": "System", "user": "user", "status": "running"}
                ]

            procs.sort(key=lambda x: (x['cpu'], x['memoryMb']), reverse=True)
            state["processes"] = procs
            state["last_sync"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

            if procs:
                top_app = procs[0]['name']
                if state["active_app"] != top_app:
                    state["active_app"] = top_app
                    state["activity_logs"].insert(0, {
                        "id": f"evt-{int(time.time())}",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "type": "app_switch",
                        "appName": top_app,
                        "details": f"Focus shifted to {top_app} (PID {procs[0]['pid']})"
                    })
                    if len(state["activity_logs"]) > 50:
                        state["activity_logs"].pop()

            for p in procs[:15]:
                n = p['name']
                if n not in state["app_durations"]:
                    state["app_durations"][n] = {"seconds": 30, "cpu_sum": p['cpu'], "ram_sum": p['memoryMb'], "samples": 1}
                else:
                    state["app_durations"][n]["seconds"] += int(state["polling_interval"])
                    state["app_durations"][n]["cpu_sum"] += p['cpu']
                    state["app_durations"][n]["ram_sum"] += p['memoryMb']
                    state["app_durations"][n]["samples"] += 1

        time.sleep(state["polling_interval"])

# Start background monitor thread
monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()


# HTTP Request Handler
class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_html(self, content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            cpu_total = round(sum(p['cpu'] for p in state["processes"]), 1)
            ram_total = round(sum(p['memoryMb'] for p in state["processes"]), 1)
            self._send_json({
                "isTracking": state["is_tracking"],
                "pythonEngineActive": True,
                "pythonVersion": state["python_version"],
                "pollingIntervalMs": int(state["polling_interval"] * 1000),
                "totalProcessesTracked": len(state["processes"]),
                "lastSyncTime": state["last_sync"],
                "activeApp": state["active_app"],
                "cpuTotal": cpu_total,
                "memoryTotalMb": ram_total,
                "uptimeSeconds": int(time.time() - state["start_time"])
            })

        elif path == "/api/processes":
            self._send_json({
                "isTracking": state["is_tracking"],
                "count": len(state["processes"]),
                "activeApp": state["active_app"],
                "processes": state["processes"]
            })

        elif path == "/api/analytics":
            total_sec = sum(item["seconds"] for item in state["app_durations"].values()) or 1
            usage_summary = []
            cat_totals = {}

            for name, stats in state["app_durations"].items():
                cat = categorize(name)
                pct = round((stats["seconds"] / total_sec) * 100, 1)
                avg_cpu = round(stats["cpu_sum"] / max(1, stats["samples"]), 1)
                avg_ram = round(stats["ram_sum"] / max(1, stats["samples"]), 1)

                usage_summary.append({
                    "appName": name,
                    "category": cat,
                    "totalTimeSeconds": stats["seconds"],
                    "percentage": pct,
                    "launchCount": 1,
                    "avgCpu": avg_cpu,
                    "avgRamMb": avg_ram
                })
                cat_totals[cat] = cat_totals.get(cat, 0) + stats["seconds"]

            usage_summary.sort(key=lambda x: x["totalTimeSeconds"], reverse=True)

            cat_breakdown = [
                {"category": k, "seconds": v, "percentage": round((v / total_sec) * 100, 1)}
                for k, v in cat_totals.items()
            ]

            dev_sec = cat_totals.get("Development", 0) + cat_totals.get("Productivity", 0)
            focus_score = min(100, round((dev_sec / total_sec) * 100))

            self._send_json({
                "totalSeconds": total_sec,
                "focusScore": focus_score,
                "usageSummary": usage_summary,
                "categoryBreakdown": cat_breakdown,
                "activityLogs": state["activity_logs"]
            })

        elif path == "/api/rules":
            self._send_json(state["rules"])

        elif path == "/api/download-python-app":
            if os.path.exists("desktop_app.py"):
                with open("desktop_app.py", "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/x-python')
                self.send_header('Content-Disposition', 'attachment; filename="desktop_app.py"')
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "File not found")

        else:
            # Serve Minimalist Gray & White Desktop Application UI
            self._send_html(get_desktop_html_ui())

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == "/api/tracker/control":
            action = data.get("action")
            if action == "pause":
                state["is_tracking"] = False
            elif action == "resume":
                state["is_tracking"] = True
            self._send_json({"success": True, "isTracking": state["is_tracking"]})

        elif path == "/api/rules":
            pat = data.get("pattern") or data.get("processNamePattern")
            cat = data.get("category", "Productivity")
            if pat:
                state["rules"].append({"pattern": pat, "category": cat, "limit": None})
            self._send_json({"success": True, "rules": state["rules"]})

        elif path == "/api/reset":
            state["activity_logs"] = []
            state["app_durations"] = {}
            state["start_time"] = time.time()
            self._send_json({"success": True})

        else:
            self._send_json({"error": "Unknown endpoint"}, 404)


def get_desktop_html_ui():
    """Generates the Desktop Application Window Frame (Minimalist Gray & White design)."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AppTracker — Native Desktop App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #e2e8f0; }
        .font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
    </style>
</head>
<body class="h-screen w-screen flex items-center justify-center p-2 sm:p-6 select-none overflow-hidden">

    <!-- Native Desktop Window Frame -->
    <div class="w-full max-w-6xl h-full max-h-[820px] bg-white rounded-xl border border-gray-200 shadow-2xl flex flex-col overflow-hidden">
        
        <!-- Desktop Window Title Bar -->
        <div class="h-10 bg-gray-100 border-b border-gray-200 flex items-center justify-between px-4 text-xs font-mono">
            <!-- OS Controls (Close, Minimize, Maximize) -->
            <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full bg-gray-300 border border-gray-400"></div>
                <div class="w-3 h-3 rounded-full bg-gray-300 border border-gray-400"></div>
                <div class="w-3 h-3 rounded-full bg-gray-300 border border-gray-400"></div>
                <span class="ml-3 font-semibold text-gray-700">AppTracker.exe (Desktop Engine v2.4)</span>
            </div>

            <!-- Header Status -->
            <div class="flex items-center space-x-4 text-gray-500">
                <span id="statusIndicator" class="flex items-center space-x-1 text-emerald-600 font-medium">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span>ENGINE ACTIVE</span>
                </span>
                <span>•</span>
                <span id="cpuMeter" class="font-semibold text-gray-800">CPU: 0.0%</span>
                <span>•</span>
                <span id="ramMeter" class="font-semibold text-gray-800">RAM: 0 MB</span>
            </div>
        </div>

        <!-- Desktop App Subheader & Primary Controls -->
        <div class="bg-white border-b border-gray-100 px-6 py-3 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded bg-gray-900 text-white flex items-center justify-center font-mono font-bold text-sm">
                    AT
                </div>
                <div>
                    <h1 class="text-base font-semibold tracking-tight text-gray-900">AppTracker Desktop Monitor</h1>
                    <p class="text-xs text-gray-500 font-mono">Python Background Process & Active Focus Tracker</p>
                </div>
            </div>

            <div class="flex items-center space-x-2">
                <button id="btnPause" onclick="toggleTracking()" class="px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-white rounded text-xs font-mono font-medium transition">
                    Pause Engine
                </button>
                <a href="/api/download-python-app" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300 rounded text-xs font-mono font-medium transition flex items-center space-x-1">
                    <span>Download Native .py App</span>
                </a>
            </div>
        </div>

        <!-- Body Layout: Sidebar + Main Content -->
        <div class="flex-1 flex overflow-hidden">
            <!-- Sidebar Navigation -->
            <div class="w-56 bg-gray-50 border-r border-gray-200 flex flex-col font-mono text-xs p-3 space-y-1">
                <div class="px-3 py-2 text-gray-400 text-[10px] uppercase font-bold tracking-wider">Navigation</div>
                
                <button onclick="switchTab('processes')" id="nav-processes" class="w-full text-left px-3 py-2 rounded-md font-medium bg-white border border-gray-200 text-gray-900 shadow-xs flex items-center justify-between">
                    <span>Live Processes</span>
                    <span id="procCountBadge" class="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded text-[10px]">0</span>
                </button>

                <button onclick="switchTab('analytics')" id="nav-analytics" class="w-full text-left px-3 py-2 rounded-md font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition">
                    <span>Analytics & Focus</span>
                </button>

                <button onclick="switchTab('rules')" id="nav-rules" class="w-full text-left px-3 py-2 rounded-md font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition">
                    <span>Category Rules</span>
                </button>

                <button onclick="switchTab('logs')" id="nav-logs" class="w-full text-left px-3 py-2 rounded-md font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition">
                    <span>Activity Stream</span>
                </button>

                <!-- Sidebar Footer Status -->
                <div class="mt-auto p-3 bg-white border border-gray-200 rounded-lg space-y-2 text-[11px] text-gray-500">
                    <div class="font-bold text-gray-800 uppercase text-[10px]">Python Runtime</div>
                    <div>Version: <span id="pythonVer">3.11</span></div>
                    <div>Active App: <span id="activeAppLabel" class="font-semibold text-gray-900">Desktop</span></div>
                </div>
            </div>

            <!-- Main Content Panels -->
            <div class="flex-1 bg-white p-6 overflow-y-auto font-sans">

                <!-- Tab 1: Live Processes -->
                <div id="tab-processes" class="space-y-4">
                    <div class="flex items-center justify-between">
                        <input type="text" id="procSearch" onkeyup="filterTable()" placeholder="Search process name, PID, category..." class="w-80 px-3 py-1.5 text-xs font-mono bg-gray-50 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-400">
                        <span class="text-xs font-mono text-gray-400">Auto-refreshing every 3s</span>
                    </div>

                    <div class="border border-gray-200 rounded-lg overflow-hidden shadow-xs">
                        <table class="w-full text-left border-collapse text-xs font-mono">
                            <thead class="bg-gray-50 border-b border-gray-200 text-gray-500 uppercase text-[10px]">
                                <tr>
                                    <th class="px-4 py-2.5">Application Name</th>
                                    <th class="px-3 py-2.5">PID</th>
                                    <th class="px-3 py-2.5">CPU %</th>
                                    <th class="px-3 py-2.5">Memory</th>
                                    <th class="px-3 py-2.5">Category</th>
                                    <th class="px-3 py-2.5 text-right">User</th>
                                </tr>
                            </thead>
                            <tbody id="procTableBody" class="divide-y divide-gray-100">
                                <tr><td colSpan="6" class="p-6 text-center text-gray-400">Loading process snapshot...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Tab 2: Analytics & Focus -->
                <div id="tab-analytics" class="space-y-6 hidden">
                    <div class="grid grid-cols-3 gap-4 font-mono">
                        <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                            <div class="text-[10px] text-gray-400 uppercase">Productivity Focus</div>
                            <div id="focusScoreVal" class="text-2xl font-bold text-gray-900 mt-1">0%</div>
                        </div>
                        <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                            <div class="text-[10px] text-gray-400 uppercase">Monitored Apps</div>
                            <div id="monitoredAppsCount" class="text-2xl font-bold text-gray-900 mt-1">0</div>
                        </div>
                        <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                            <div class="text-[10px] text-gray-400 uppercase">Engine Status</div>
                            <div class="text-sm font-bold text-emerald-600 mt-2">ACTIVE (PYTHON3)</div>
                        </div>
                    </div>

                    <div class="border border-gray-200 rounded-lg p-4 space-y-3">
                        <h3 class="text-xs font-bold font-mono uppercase text-gray-700">App Usage Duration Breakdown</h3>
                        <div id="durationList" class="space-y-2 text-xs font-mono"></div>
                    </div>
                </div>

                <!-- Tab 3: Category Rules -->
                <div id="tab-rules" class="space-y-6 hidden">
                    <div class="border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-3 font-mono text-xs">
                        <h3 class="font-bold text-gray-900">Create New Process Rule</h3>
                        <div class="flex items-center space-x-3">
                            <input type="text" id="rulePattern" placeholder="Process pattern (e.g. obsidian)" class="px-3 py-1.5 bg-white border border-gray-200 rounded text-xs flex-1">
                            <select id="ruleCategory" class="px-3 py-1.5 bg-white border border-gray-200 rounded text-xs">
                                <option value="Development">Development</option>
                                <option value="Browser">Browser</option>
                                <option value="Communication">Communication</option>
                                <option value="Productivity">Productivity</option>
                                <option value="Design">Design</option>
                                <option value="Entertainment">Entertainment</option>
                            </select>
                            <button onclick="addRule()" class="px-4 py-1.5 bg-gray-900 text-white rounded text-xs font-medium">Add Rule</button>
                        </div>
                    </div>

                    <div class="border border-gray-200 rounded-lg overflow-hidden font-mono text-xs">
                        <table class="w-full text-left">
                            <thead class="bg-gray-50 border-b border-gray-200 text-gray-500 uppercase text-[10px]">
                                <tr>
                                    <th class="px-4 py-2.5">Match Pattern</th>
                                    <th class="px-4 py-2.5">Category</th>
                                </tr>
                            </thead>
                            <tbody id="rulesTableBody" class="divide-y divide-gray-100"></tbody>
                        </table>
                    </div>
                </div>

                <!-- Tab 4: Activity Stream -->
                <div id="tab-logs" class="space-y-4 hidden">
                    <div class="border border-gray-200 rounded-lg p-4 bg-gray-950 text-gray-100 font-mono text-xs max-h-[480px] overflow-y-auto space-y-2" id="logsContainer">
                        <div>Loading activity logs...</div>
                    </div>
                </div>

            </div>
        </div>

        <!-- Footer -->
        <div class="h-8 bg-gray-50 border-t border-gray-200 px-6 flex items-center justify-between text-[10px] font-mono text-gray-400 uppercase tracking-wider">
            <div>Python Desktop Daemon • Minimalist Gray & White Architecture</div>
            <div>0.0.0.0:3000 • Standalone Python Native App Available</div>
        </div>
    </div>

    <!-- Script Logic -->
    <script>
        let currentTab = 'processes';
        let isTracking = true;

        function switchTab(tab) {
            currentTab = tab;
            ['processes', 'analytics', 'rules', 'logs'].forEach(t => {
                document.getElementById('tab-' + t).classList.add('hidden');
                document.getElementById('nav-' + t).className = "w-full text-left px-3 py-2 rounded-md font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition";
            });
            document.getElementById('tab-' + tab).classList.remove('hidden');
            document.getElementById('nav-' + tab).className = "w-full text-left px-3 py-2 rounded-md font-medium bg-white border border-gray-200 text-gray-900 shadow-xs flex items-center justify-between";
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('cpuMeter').innerText = 'CPU: ' + data.cpuTotal + '%';
                document.getElementById('ramMeter').innerText = 'RAM: ' + data.memoryTotalMb + ' MB';
                document.getElementById('procCountBadge').innerText = data.totalProcessesTracked;
                document.getElementById('pythonVer').innerText = data.pythonVersion;
                document.getElementById('activeAppLabel').innerText = data.activeApp || 'Desktop';
                isTracking = data.isTracking;

                const ind = document.getElementById('statusIndicator');
                if (isTracking) {
                    ind.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span><span>ENGINE ACTIVE</span>';
                    ind.className = 'flex items-center space-x-1 text-emerald-600 font-medium';
                } else {
                    ind.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-500"></span><span>PAUSED</span>';
                    ind.className = 'flex items-center space-x-1 text-amber-600 font-medium';
                }
            } catch (e) {}
        }

        async function fetchProcesses() {
            try {
                const res = await fetch('/api/processes');
                const data = await res.json();
                const tbody = document.getElementById('procTableBody');
                if (!data.processes || data.processes.length === 0) {
                    tbody.innerHTML = '<tr><td colSpan="6" class="p-6 text-center text-gray-400">No active processes monitored.</td></tr>';
                    return;
                }
                tbody.innerHTML = data.processes.map((p, idx) => `
                    <tr class="hover:bg-gray-50/80 transition">
                        <td class="px-4 py-2.5 font-semibold text-gray-900 flex items-center space-x-2">
                            <span class="w-1.5 h-1.5 rounded-full ${idx === 0 ? 'bg-gray-900' : 'bg-gray-300'}"></span>
                            <span>${p.name}</span>
                        </td>
                        <td class="px-3 py-2.5 text-gray-500">${p.pid}</td>
                        <td class="px-3 py-2.5 ${p.cpu > 5 ? 'font-bold text-gray-900' : 'text-gray-700'}">${p.cpu}%</td>
                        <td class="px-3 py-2.5 text-gray-700">${p.memoryMb} MB</td>
                        <td class="px-3 py-2.5"><span class="px-2 py-0.5 rounded bg-gray-100 text-gray-700 border border-gray-200 text-[10px]">${p.category}</span></td>
                        <td class="px-3 py-2.5 text-right text-gray-500">${p.user || 'user'}</td>
                    </tr>
                `).join('');
            } catch (e) {}
        }

        async function fetchAnalytics() {
            try {
                const res = await fetch('/api/analytics');
                const data = await res.json();
                document.getElementById('focusScoreVal').innerText = data.focusScore + '%';
                document.getElementById('monitoredAppsCount').innerText = data.usageSummary.length;

                const durList = document.getElementById('durationList');
                durList.innerHTML = data.usageSummary.map(item => `
                    <div class="flex items-center justify-between p-2 bg-gray-50 border border-gray-200 rounded">
                        <div>
                            <span class="font-bold text-gray-900">${item.appName}</span>
                            <span class="ml-2 text-gray-400">(${item.category})</span>
                        </div>
                        <div class="text-gray-700 font-semibold">${Math.floor(item.totalTimeSeconds / 60)}m ${item.totalTimeSeconds % 60}s (${item.percentage}%)</div>
                    </div>
                `).join('');

                const logsBox = document.getElementById('logsContainer');
                logsBox.innerHTML = data.activityLogs.map(l => `
                    <div class="border-b border-gray-800 pb-1">
                        <span class="text-gray-500">[${l.timestamp}]</span>
                        <span class="text-emerald-400">[${l.type}]</span>
                        <span class="font-bold text-white">${l.appName}:</span>
                        <span class="text-gray-300">${l.details}</span>
                    </div>
                `).join('');
            } catch (e) {}
        }

        async function fetchRules() {
            try {
                const res = await fetch('/api/rules');
                const data = await res.json();
                document.getElementById('rulesTableBody').innerHTML = data.map(r => `
                    <tr class="hover:bg-gray-50">
                        <td class="px-4 py-2 font-bold text-gray-900">${r.pattern}</td>
                        <td class="px-4 py-2"><span class="px-2 py-0.5 rounded bg-gray-100 border border-gray-200 text-gray-700">${r.category}</span></td>
                    </tr>
                `).join('');
            } catch (e) {}
        }

        async function toggleTracking() {
            const action = isTracking ? 'pause' : 'resume';
            await fetch('/api/tracker/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action })
            });
            fetchStatus();
        }

        async function addRule() {
            const pattern = document.getElementById('rulePattern').value;
            const category = document.getElementById('ruleCategory').value;
            if (pattern) {
                await fetch('/api/rules', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ pattern, category })
                });
                document.getElementById('rulePattern').value = '';
                fetchRules();
            }
        }

        function filterTable() {
            const query = document.getElementById('procSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#procTableBody tr');
            rows.forEach(row => {
                row.style.display = row.innerText.toLowerCase().includes(query) ? '' : 'none';
            });
        }

        // Loop interval
        setInterval(() => {
            fetchStatus();
            if (currentTab === 'processes') fetchProcesses();
            if (currentTab === 'analytics' || currentTab === 'logs') fetchAnalytics();
        }, 3000);

        fetchStatus();
        fetchProcesses();
        fetchAnalytics();
        fetchRules();
    </script>
</body>
</html>"""


def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"[AppTracker Desktop Server] Running on http://0.0.0.0:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run_server()

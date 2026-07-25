import time
import json
import platform
import subprocess
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class AppTrackerEngine:
    def __init__(self):
        self.is_tracking = True
        self.polling_interval = 3.0
        self.processes = []
        self.threats = []
        self.app_durations = {}
        self.activity_logs = []
        self.active_app = "Desktop"
        self.start_time = time.time()

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
                    try:
                        exe = p.exe() or ""
                    except Exception:
                        exe = ""
                    try:
                        ppid = p.ppid()
                    except Exception:
                        ppid = 0

                    procs.append({
                        'pid': info['pid'],
                        'name': name,
                        'cpu': cpu_pct,
                        'memory_mb': mem_mb,
                        'user': info['username'] or 'user',
                        'category': self.categorize(name),
                        'exe': exe,
                        'ppid': ppid
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        else:
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
                                'category': self.categorize(comm),
                                'exe': "",
                                'ppid': 0
                            })
            except Exception:
                pass

        procs.sort(key=lambda x: (x['cpu'], x['memory_mb']), reverse=True)
        self.processes = procs[:50]

        if procs:
            top_app = procs[0]['name']
            if self.active_app != top_app:
                self.active_app = top_app
                self.log_event("app_switch", top_app, f"Focus shifted to {top_app}")

        for p in procs[:20]:
            name = p['name']
            if name not in self.app_durations:
                self.app_durations[name] = {'seconds': 30, 'cpu_sum': p['cpu'], 'ram_sum': p['memory_mb'], 'samples': 1}
            else:
                self.app_durations[name]['seconds'] += int(self.polling_interval)
                self.app_durations[name]['cpu_sum'] += p['cpu']
                self.app_durations[name]['ram_sum'] += p['memory_mb']
                self.app_durations[name]['samples'] += 1

        self.analyze_threats()

    def analyze_threats(self):
        threats = []
        cpu_vals = [p['cpu'] for p in self.processes]
        avg_cpu = sum(cpu_vals) / max(len(cpu_vals), 1)

        suspicious_names_known = [
            "mimikatz", "nc.exe", "netcat", "psexec", "payload.dll", "payload.exe",
            "winlogin.exe", "svchosts.exe", "scvhost.exe", "windows.exe",
            "rundll32.exe", "regsvr32.exe", "mshta.exe", "cscript.exe", "wscript.exe",
            "powershell_ise.exe", "cmd.exe", "explorer.exe"
        ]
        known_system = {"svchost.exe", "csrss.exe", "wininit.exe", "lsass.exe",
                        "services.exe", "winlogon.exe", "smss.exe", "system",
                        "system idle process", "registry", "memory compression"}

        for p in self.processes:
            indicators = []
            score = 0
            name_lower = p['name'].lower()
            clean_name = ''.join(c for c in p['name'] if c.isalnum())

            if clean_name.isdigit():
                indicators.append("Numeric-only process name")
                score += 35
            if len(p['name']) <= 2 and p['name'].lower() not in known_system:
                indicators.append("Suspiciously short name")
                score += 30
            if p['name'].count('.') > 2:
                indicators.append("Multiple extensions")
                score += 25

            for sn in suspicious_names_known:
                if sn in name_lower and name_lower not in known_system:
                    indicators.append(f"Matches known threat vector: {sn}")
                    score += 45
                    break

            if avg_cpu > 1 and p['cpu'] > avg_cpu * 6 and p['cpu'] > 30:
                indicators.append("Anomalous CPU spike")
                score += 20
            if p['memory_mb'] > 800 and p['category'] == "Productivity":
                indicators.append("Uncategorized high memory usage")
                score += 15

            exe_lower = p.get('exe', '').lower()
            temp_paths = ['\\temp\\', '\\tmp\\', '\\downloads\\', '\\appdata\\local\\temp\\']
            if exe_lower and any(tp in exe_lower for tp in temp_paths):
                indicators.append("Running from temp directory")
                score += 35

            ppid = p.get('ppid', 0)
            if ppid == 0 or ppid == 4:
                indicators.append("Orphaned or unusual parent")
                score += 15

            if score > 0:
                threats.append({
                    'pid': p['pid'],
                    'name': p['name'],
                    'risk_score': min(score, 99),
                    'indicators': indicators,
                    'cpu': p['cpu'],
                    'memory_mb': p['memory_mb'],
                    'user': p['user'],
                    'category': p['category'],
                    'exe': p.get('exe', '')
                })

        threats.sort(key=lambda x: x['risk_score'], reverse=True)
        self.threats = threats

    def log_event(self, evt_type, app_name, details):
        self.activity_logs.insert(0, {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'type': evt_type,
            'app_name': app_name,
            'details': details
        })
        if len(self.activity_logs) > 100:
            self.activity_logs.pop()

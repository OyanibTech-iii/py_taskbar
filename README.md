# AppTracker Desktop

![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/platform-win%20%7C%20macos%20%7C%20linux-lightgrey)
![Tkinter](https://img.shields.io/badge/GUI-tkinter-ff69b4)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

A 100% Python native desktop application monitor with a minimalist gray & white UI. Tracks running processes, CPU/RAM usage, application durations, category rules, and includes real-time radar charts, threat heuristics, and resource hotspot analysis.

---

## Project Structure

```
app-tracker-desktop/
├── desktop_app.py          # Entry point — auth flow then launches GUI
├── auth.py                 # AuthManager (PIN hashing, config) + auth UI
├── gui.py                  # DesktopAppGUI — 7-tab tkinter interface
├── engine.py               # AppTrackerEngine — process polling, threat analysis
├── theme.py                # THEME color/font constants
├── app.py                  # Web server mode on port 3000
├── python_tracker.py       # Background CLI daemon script
├── README.md
└── .gitignore
```

---

## How to Run

### 1. Install Dependencies (optional)

The app runs with Python's standard library only. For richer process data, install psutil:

```bash
pip install psutil
```

### 2. Launch the Desktop GUI

```bash
python desktop_app.py
```

Opens a native window with 7 tabs (see Features below).

### 3. Web Server Mode (port 3000)

```bash
python app.py
```

Serves the monitoring UI over HTTP at `http://localhost:3000`.

### 4. CLI Daemon (JSON output)

```bash
python python_tracker.py
```

Outputs process snapshots as JSON to stdout.

---

## Features

| Tab | Description |
|-----|-------------|
| **Live Processes** | Real-time PID, CPU%, memory, user, category with search filter & CSV export |
| **Analytics & Focus** | App duration breakdown, avg CPU/RAM per process, CSV export |
| **Category Rules** | Add/edit pattern-to-category mapping rules, CSV export |
| **Activity Logs** | Timestamped event stream (app switches, status changes), text export |
| **Real-time Radar** | Canvas-drawn 5-axis radar chart (CPU, RAM, processes, uptime, focus) + live metrics panel & JSON report export |
| **Security Scan** | Heuristic threat detection (suspicious names, temp paths, orphaned processes, CPU anomalies) with color-coded risk scoring & CSV export |
| **Top Consumers** | Ranked #1–10 by CPU usage with auto-generated analysis per process, summary stats & CSV export |

### Detection Heuristics (Security Scan)
- Numeric-only or suspiciously short process names
- Known malware vectors (mimikatz, psexec, etc.)
- Processes running from `\temp\`, `\downloads\`, `\AppData\Local\Temp\`
- Anomalous CPU spikes (>6x average)
- Uncategorized processes with high memory (>800 MB)
- Orphaned processes (pid 0 or 4)

---

## Badges (above)

- ![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python)
- ![Platform](https://img.shields.io/badge/platform-win%20%7C%20macos%20%7C%20linux-lightgrey)
- ![Tkinter](https://img.shields.io/badge/GUI-tkinter-ff69b4)
- ![License](https://img.shields.io/badge/license-MIT-green)
- ![Status](https://img.shields.io/badge/status-active-brightgreen)

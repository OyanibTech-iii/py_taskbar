# AppTracker — Native Python Desktop Application

AppTracker is a 100% Python native desktop application monitor with a minimalist gray & white UI. It tracks running system processes, CPU/RAM utilization, application duration, focus metrics, and custom category mapping rules.

---

## Architecture Overview (Pure Python)

1. **Native Python Desktop GUI (`desktop_app.py`)**
   - Built with Python's standard `tkinter` / `ttk` library.
   - Minimalist gray & white design with native window controls, CPU/RAM meters, process table, duration analytics, category rules manager, and activity log stream.
   - Run directly on Windows, macOS, or Linux using `python3 desktop_app.py`.

2. **Python Web & Desktop Server (`app.py`)**
   - Runs on `0.0.0.0:3000` using Python's standard `http.server`.
   - Serves an interactive Desktop Application Window simulator in browser preview while running background system tracking.

---

## How to Run

### 1. Run Native Python Desktop GUI (Local Desktop OS)
To open the standalone Python desktop GUI window on your machine:

```bash
python3 desktop_app.py
```

### 2. Run Python Server Mode (Port 3000)
To run the background monitoring engine and server on port 3000:

```bash
python3 app.py
```

---

## Features
- **Zero TypeScript / No Web Framework dependencies**: Built strictly with Python.
- **Minimalist Palette**: Clean off-white background (`#f8fafc`), white cards (`#ffffff`), dark primary slate text (`#0f172a`), and subtle border accents (`#e2e8f0`).
- **Live Process Monitor**: Real-time PID, CPU %, Memory RSS, User context, and Category tags.
- **Focus & Analytics**: Tracks application durations, top apps, category percentages, and productivity score.
- **Category Rules**: Define process matching patterns (e.g., `code` -> `Development`).

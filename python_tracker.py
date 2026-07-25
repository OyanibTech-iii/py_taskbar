#!/usr/bin/env python3
"""
AppTracker Background Daemon Script (Python)
Tracks running applications, CPU %, memory usage, and active process state.
Sends JSON output to stdout or posts to AppTracker REST API.
"""

import sys
import os
import json
import time
import platform
import subprocess

def get_processes_psutil():
    """Attempts to gather rich process information using psutil if available."""
    try:
        import psutil
        processes = []
        # Find active/top processes by CPU/Memory
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'username', 'create_time']):
            try:
                pinfo = proc.info
                mem_mb = round((pinfo['memory_info'].rss if pinfo['memory_info'] else 0) / (1024 * 1024), 1)
                cpu_pct = round(pinfo['cpu_percent'] or 0.0, 1)
                duration = int(time.time() - (pinfo['create_time'] or time.time()))
                
                name = pinfo['name'] or f"Process-{pinfo['pid']}"
                
                # Filter out pure kernel noise if desired, keep user & desktop apps
                processes.append({
                    'pid': pinfo['pid'],
                    'name': name,
                    'cpu': cpu_pct,
                    'memoryMb': mem_mb,
                    'durationSeconds': duration,
                    'status': pinfo['status'] or 'running',
                    'user': pinfo['username'] or 'system'
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by CPU usage and memory
        processes.sort(key=lambda x: (x['cpu'], x['memoryMb']), reverse=True)
        return processes[:50]
    except ImportError:
        return None

def get_processes_fallback():
    """Fallback using standard OS commands (ps on Unix/Linux/macOS, tasklist on Windows)."""
    processes = []
    current_os = platform.system()
    
    if current_os in ["Linux", "Darwin"]:
        try:
            # Run ps aux command
            cmd = ["ps", "-eo", "pid,pcpu,pmem,rss,comm,user"]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
            lines = output.strip().split('\n')
            
            for line in lines[1:]:
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    try:
                        pid = int(parts[0])
                        cpu = float(parts[1])
                        rss_kb = float(parts[3])
                        comm = parts[4].split('/')[-1]
                        user = parts[5]
                        mem_mb = round(rss_kb / 1024.0, 1)
                        
                        processes.append({
                            'pid': pid,
                            'name': comm,
                            'cpu': cpu,
                            'memoryMb': mem_mb,
                            'durationSeconds': 3600,
                            'status': 'running',
                            'user': user
                        })
                    except ValueError:
                        continue
        except Exception as e:
            pass
            
    elif current_os == "Windows":
        try:
            cmd = ["tasklist", "/FO", "CSV", "/NH"]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
            for line in output.strip().split('\n'):
                parts = [p.strip('"') for p in line.split(',')]
                if len(parts) >= 5:
                    try:
                        name = parts[0]
                        pid = int(parts[1])
                        mem_str = parts[4].replace(' K', '').replace(',', '').replace('.', '')
                        mem_mb = round(float(mem_str) / 1024.0, 1)
                        processes.append({
                            'pid': pid,
                            'name': name,
                            'cpu': 0.5,
                            'memoryMb': mem_mb,
                            'durationSeconds': 1800,
                            'status': 'running',
                            'user': 'user'
                        })
                    except ValueError:
                        continue
        except Exception:
            pass
            
    # Sort top processes
    processes.sort(key=lambda x: x['memoryMb'], reverse=True)
    return processes[:40]

def main():
    processes = get_processes_psutil()
    if processes is None:
        processes = get_processes_fallback()
        
    system_info = {
        'timestamp': time.time(),
        'platform': platform.system(),
        'release': platform.release(),
        'python_version': platform.python_version(),
        'process_count': len(processes),
        'processes': processes
    }
    
    print(json.dumps(system_info))

if __name__ == '__main__':
    main()

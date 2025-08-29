"""
Server monitoring system for Analyzator application
"""

import psutil
import json
import os
from datetime import datetime, timedelta
import time
import threading
from typing import Dict, List, Optional
import streamlit as st


class ServerMonitor:
    """Trieda pre monitoring server resources v reálnom čase"""
    
    def __init__(self, data_file: str = "logs/server_metrics.json"):
        self.data_file = data_file
        self.monitoring = False
        self.monitor_thread = None
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Zabezpečí že existuje súbor pre metrics"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"metrics": []}, f)
    
    def get_current_metrics(self) -> Dict:
        """Získa aktuálne server metrics"""
        try:
            # CPU informácie
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # RAM informácie
            memory = psutil.virtual_memory()
            
            # Disk informácie
            disk = psutil.disk_usage('/')
            
            # Network informácie
            net_io = psutil.net_io_counters()
            
            # Process informácie
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] is not None and proc_info['cpu_percent'] > 0.1:
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Zoradenie procesov podľa CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_processes = processes[:10]  # Top 10 procesov
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": round(cpu_percent, 1),
                    "count": cpu_count,
                    "frequency_mhz": round(cpu_freq.current, 0) if cpu_freq else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": round(memory.percent, 1)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 1)
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "top_processes": top_processes
            }
            
            return metrics
            
        except Exception as e:
            return {"error": f"Chyba pri získavaní metrics: {str(e)}"}
    
    def save_metrics(self, metrics: Dict):
        """Uloží metrics do súboru"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            data["metrics"].append(metrics)
            
            # Zachovaj len posledných 24 hodín dát (jeden záznam každé 2 minúty = 720 záznamov)
            if len(data["metrics"]) > 720:
                data["metrics"] = data["metrics"][-720:]
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Chyba pri ukladaní metrics: {e}")
    
    def get_historical_metrics(self, hours: int = 24) -> List[Dict]:
        """Získa historické metrics za posledné hodiny"""
        try:
            # Skontroluj či súbor existuje a nie je prázdny
            if not os.path.exists(self.data_file) or os.path.getsize(self.data_file) == 0:
                print("Metrics súbor neexistuje alebo je prázdny, vytváranie nového...")
                self._ensure_data_file()
                return []
            
            with open(self.data_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    print("Prázdny metrics súbor, vytváranie nového...")
                    self._ensure_data_file()
                    return []
                
                data = json.loads(content)
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            filtered_metrics = []
            for metric in data.get("metrics", []):
                try:
                    metric_time = datetime.fromisoformat(metric["timestamp"])
                    if metric_time > cutoff_time:
                        filtered_metrics.append(metric)
                except Exception as parse_error:
                    print(f"Chyba pri parsovaní metric timestamp: {parse_error}")
                    continue
            
            return filtered_metrics
            
        except json.JSONDecodeError as e:
            print(f"Chyba pri načítavaní historických metrics - JSON decode error: {e}")
            print("Obnovujem metrics súbor...")
            self._ensure_data_file()
            return []
        except Exception as e:
            print(f"Chyba pri načítavaní historických metrics: {e}")
            return []
    
    def get_daily_growth_stats(self) -> Dict:
        """Získa štatistiky rastu za posledný deň"""
        metrics_24h = self.get_historical_metrics(24)
        
        if len(metrics_24h) < 2:
            return {"error": "Nedostatok dát pre výpočet rastu"}
        
        first_metric = metrics_24h[0]
        last_metric = metrics_24h[-1]
        
        try:
            memory_growth = last_metric["memory"]["used_gb"] - first_metric["memory"]["used_gb"]
            disk_growth = last_metric["disk"]["used_gb"] - first_metric["disk"]["used_gb"]
            
            avg_cpu = sum(m["cpu"]["usage_percent"] for m in metrics_24h) / len(metrics_24h)
            avg_memory = sum(m["memory"]["usage_percent"] for m in metrics_24h) / len(metrics_24h)
            
            return {
                "period_hours": 24,
                "memory_growth_gb": round(memory_growth, 3),
                "disk_growth_gb": round(disk_growth, 3),
                "avg_cpu_percent": round(avg_cpu, 1),
                "avg_memory_percent": round(avg_memory, 1),
                "data_points": len(metrics_24h)
            }
            
        except Exception as e:
            return {"error": f"Chyba pri výpočte štatistík: {str(e)}"}
    
    def start_monitoring(self, interval_seconds: int = 120):
        """Spustí monitoring na pozadí"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Zastaví monitoring"""
        self.monitoring = False
    
    def _monitor_loop(self, interval_seconds: int):
        """Hlavný monitoring loop"""
        while self.monitoring:
            try:
                metrics = self.get_current_metrics()
                if "error" not in metrics:
                    self.save_metrics(metrics)
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                print(f"Chyba v monitoring loop: {e}")
                time.sleep(interval_seconds)


# Globálny monitor instance
server_monitor = ServerMonitor()

def get_server_monitor() -> ServerMonitor:
    """Získa globálnu instanciu server monitor-u"""
    return server_monitor

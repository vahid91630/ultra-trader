#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم پیشرفته ثبت رویدادها و مانیتورینگ
Enhanced Telemetry Logging System for Ultra-Trader
"""

import os
import json
import time
import psutil
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from collections import defaultdict, deque


class MetricType(Enum):
    """انواع متریک‌ها"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """سطوح هشدار"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """ساختار داده‌های متریک"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["metric_type"] = self.metric_type.value
        return data


@dataclass
class SystemHealth:
    """وضعیت سلامت سیستم"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_connections: int
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class TelemetryLogger:
    """سیستم پیشرفته ثبت رویدادها و مانیتورینگ"""
    
    def __init__(self, 
                 db_path: str = "monitoring/telemetry.db",
                 retention_days: int = 30,
                 collection_interval: int = 60):
        self.db_path = db_path
        self.retention_days = retention_days
        self.collection_interval = collection_interval
        
        # متریک‌های محلی
        self.metrics_buffer = deque(maxlen=10000)
        self.error_counts = defaultdict(int)
        self.performance_history = deque(maxlen=1000)
        
        # تنظیمات لاگینگ
        self._setup_logging()
        
        # ایجاد دیتابیس
        self._initialize_database()
        
        # شروع جمع‌آوری خودکار
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._continuous_monitoring)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("🔧 سیستم تلمتری فعال شد")
    
    def _setup_logging(self):
        """تنظیم سیستم لاگینگ پیشرفته"""
        # ایجاد دایرکتوری لاگ
        os.makedirs("monitoring/logs", exist_ok=True)
        
        # فرمت پیشرفته لاگ
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
        )
        
        # لاگر اصلی
        self.logger = logging.getLogger("TelemetryLogger")
        self.logger.setLevel(logging.INFO)
        
        # فایل هندلر برای لاگ‌های عمومی
        file_handler = logging.FileHandler(
            "monitoring/logs/telemetry.log", encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # فایل هندلر برای خطاها
        error_handler = logging.FileHandler(
            "monitoring/logs/errors.log", encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # کنسول هندلر
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _initialize_database(self):
        """ایجاد جداول دیتابیس"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول متریک‌ها
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                metric_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول سلامت سیستم
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                network_connections INTEGER,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول خطاها
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                component TEXT,
                stacktrace TEXT,
                timestamp TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول رویدادها
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                data TEXT,
                severity TEXT,
                component TEXT,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ایندکس‌ها برای بهینه‌سازی
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_errors_level ON errors(level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        
        conn.commit()
        conn.close()
    
    def _continuous_monitoring(self):
        """مانیتورینگ مداوم"""
        while self.monitoring_active:
            try:
                # جمع‌آوری سلامت سیستم
                health = self.collect_system_health()
                
                if health:
                    # بررسی آستانه‌های هشدار
                    self._check_health_thresholds(health)
                
                # انتظار تا جمع‌آوری بعدی
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"خطا در مانیتورینگ مداوم: {e}")
                time.sleep(60)  # انتظار بیشتر در صورت خطا
    
    def collect_system_health(self) -> SystemHealth:
        """جمع‌آوری اطلاعات سلامت سیستم"""
        try:
            # استفاده از psutil برای جمع‌آوری اطلاعات سیستم
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network_connections = len(psutil.net_connections())
            
            health = SystemHealth(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_connections=network_connections,
                timestamp=datetime.now()
            )
            
            # ذخیره در دیتابیس
            self._save_system_health(health)
            
            # ثبت متریک‌ها
            self.record_metric("system.cpu_percent", cpu_percent)
            self.record_metric("system.memory_percent", memory.percent)
            self.record_metric("system.disk_percent", disk.percent)
            self.record_metric("system.network_connections", network_connections)
            
            return health
            
        except Exception as e:
            self.logger.error(f"خطا در جمع‌آوری سلامت سیستم: {e}")
            return None
    
    def _save_system_health(self, health: SystemHealth):
        """ذخیره اطلاعات سلامت سیستم"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_health 
                (cpu_percent, memory_percent, disk_percent, network_connections, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                health.cpu_percent,
                health.memory_percent,
                health.disk_percent,
                health.network_connections,
                health.timestamp.isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"خطا در ذخیره سلامت سیستم: {e}")
    
    def _check_health_thresholds(self, health: SystemHealth):
        """بررسی آستانه‌های سلامت سیستم"""
        # آستانه‌های هشدار
        cpu_warning = 80
        cpu_critical = 95
        memory_warning = 85
        memory_critical = 95
        disk_warning = 85
        disk_critical = 95
        
        # بررسی CPU
        if health.cpu_percent >= cpu_critical:
            self.record_error(
                AlertLevel.CRITICAL,
                f"استفاده از CPU بحرانی: {health.cpu_percent:.1f}%",
                "SystemMonitor"
            )
        elif health.cpu_percent >= cpu_warning:
            self.record_error(
                AlertLevel.WARNING,
                f"استفاده از CPU بالا: {health.cpu_percent:.1f}%",
                "SystemMonitor"
            )
        
        # بررسی Memory
        if health.memory_percent >= memory_critical:
            self.record_error(
                AlertLevel.CRITICAL,
                f"استفاده از حافظه بحرانی: {health.memory_percent:.1f}%",
                "SystemMonitor"
            )
        elif health.memory_percent >= memory_warning:
            self.record_error(
                AlertLevel.WARNING,
                f"استفاده از حافظه بالا: {health.memory_percent:.1f}%",
                "SystemMonitor"
            )
        
        # بررسی Disk
        if health.disk_percent >= disk_critical:
            self.record_error(
                AlertLevel.CRITICAL,
                f"استفاده از دیسک بحرانی: {health.disk_percent:.1f}%",
                "SystemMonitor"
            )
        elif health.disk_percent >= disk_warning:
            self.record_error(
                AlertLevel.WARNING,
                f"استفاده از دیسک بالا: {health.disk_percent:.1f}%",
                "SystemMonitor"
            )
    
    def record_metric(self, 
                     name: str, 
                     value: float, 
                     metric_type: MetricType = MetricType.GAUGE,
                     tags: Dict[str, str] = None):
        """ثبت متریک جدید"""
        metric = MetricData(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        # اضافه به بافر محلی
        self.metrics_buffer.append(metric)
        
        # ذخیره در دیتابیس
        self._save_metric_to_db(metric)
        
        self.logger.debug(f"📊 متریک ثبت شد: {name}={value}")
    
    def _save_metric_to_db(self, metric: MetricData):
        """ذخیره متریک در دیتابیس"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO metrics (name, value, metric_type, timestamp, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metric.name,
                metric.value,
                metric.metric_type.value,
                metric.timestamp.isoformat(),
                json.dumps(metric.tags) if metric.tags else None
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"خطا در ذخیره متریک: {e}")
    
    def record_error(self, 
                    level: AlertLevel,
                    message: str,
                    component: str = None,
                    stacktrace: str = None):
        """ثبت خطا"""
        self.error_counts[level.value] += 1
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # بررسی وجود خطای مشابه
            cursor.execute("""
                SELECT id, count FROM errors 
                WHERE message = ? AND component = ? AND level = ?
                AND datetime(timestamp) > datetime('now', '-1 hour')
            """, (message, component, level.value))
            
            existing = cursor.fetchone()
            
            if existing:
                # افزایش تعداد خطای موجود
                cursor.execute("""
                    UPDATE errors SET count = count + 1, timestamp = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), existing[0]))
            else:
                # ثبت خطای جدید
                cursor.execute("""
                    INSERT INTO errors (level, message, component, stacktrace, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    level.value,
                    message,
                    component,
                    stacktrace,
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            # لاگ خطا
            if level == AlertLevel.CRITICAL:
                self.logger.critical(f"🚨 {component}: {message}")
            elif level == AlertLevel.ERROR:
                self.logger.error(f"❌ {component}: {message}")
            elif level == AlertLevel.WARNING:
                self.logger.warning(f"⚠️ {component}: {message}")
            else:
                self.logger.info(f"ℹ️ {component}: {message}")
                
        except Exception as e:
            self.logger.error(f"خطا در ثبت خطا: {e}")
    
    def generate_health_report(self) -> Dict[str, Any]:
        """تولید گزارش سلامت سیستم"""
        try:
            # آخرین وضعیت سلامت
            latest_health = self.collect_system_health()
            
            # خلاصه خطاها
            error_summary = self.get_error_summary(24)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_health': latest_health.to_dict() if latest_health else None,
                'error_summary_24h': error_summary,
                'total_errors_24h': sum(error_summary.values()),
                'monitoring_status': 'active' if self.monitoring_active else 'inactive',
                'database_size': self._get_database_size()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"خطا در تولید گزارش: {e}")
            return {'error': str(e)}
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, int]:
        """خلاصه خطاهای اخیر"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT level, SUM(count) FROM errors 
                WHERE timestamp > ?
                GROUP BY level
            """, (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            return {row[0]: row[1] for row in results}
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت خلاصه خطاها: {e}")
            return {}
    
    def _get_database_size(self) -> int:
        """اندازه دیتابیس به بایت"""
        try:
            return os.path.getsize(self.db_path)
        except:
            return 0
    
    def stop_monitoring(self):
        """توقف مانیتورینگ"""
        self.monitoring_active = False
        self.logger.info("🛑 مانیتورینگ متوقف شد")


# نمونه سازی global
telemetry = TelemetryLogger()

if __name__ == "__main__":
    print("🧪 تست سیستم تلمتری...")
    
    # تست ثبت متریک‌ها
    for i in range(5):
        telemetry.record_metric(f"test.metric_{i}", float(i * 10))
    
    # تست ثبت خطا
    telemetry.record_error(
        AlertLevel.WARNING,
        "تست خطای آزمایشی",
        "TestComponent"
    )
    
    # تولید گزارش
    report = telemetry.generate_health_report()
    print("📊 گزارش سلامت سیستم:")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    print("✅ تست کامل شد")


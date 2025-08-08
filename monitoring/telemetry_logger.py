#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم لاگ تله‌متری با گزارشدهی فارسی
جمع‌آوری و گزارش‌دهی اطلاعات عملکرد سیستم
"""

import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
try:
    from persian_reporter import PersianReporter, SystemComponent
    from persiantools import digits
except ImportError:
    # Fallback for standalone execution
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class PersianReporter:
        def __init__(self, *args, **kwargs):
            pass
        def success(self, title, message, data=None):
            print(f"✅ {title}: {message}")
        def info(self, title, message, data=None):
            print(f"ℹ️ {title}: {message}")
        def warning(self, title, message, data=None):
            print(f"⚠️ {title}: {message}")
        def error(self, title, message, data=None):
            print(f"❌ {title}: {message}")
    
    class SystemComponent:
        TELEMETRY = "تله‌متری"
    
    def digits_en_to_fa(text):
        return str(text).replace('0','۰').replace('1','۱').replace('2','۲').replace('3','۳').replace('4','۴').replace('5','۵').replace('6','۶').replace('7','۷').replace('8','۸').replace('9','۹')


class PersianTelemetryLogger:
    """سیستم لاگ تله‌متری فارسی"""
    
    def __init__(self, collection_interval: int = 60):
        self.reporter = PersianReporter(
            SystemComponent.TELEMETRY,
            log_file="monitoring/logs/telemetry_fa.log"
        )
        
        self.collection_interval = collection_interval
        self.metrics_history = deque(maxlen=1440)  # 24 ساعت (هر دقیقه)
        self.running = True
        
        # معیارهای عملکرد
        self.performance_thresholds = {
            'cpu_warning': 70,
            'cpu_critical': 85,
            'memory_warning': 75,
            'memory_critical': 90,
            'disk_warning': 80,
            'disk_critical': 95
        }
        
        # شروع جمع‌آوری
        self.collection_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        self.collection_thread.start()
        
        self.reporter.success(
            "راه‌اندازی تله‌متری",
            f"سیستم تله‌متری شروع شد - بازه جمع‌آوری: {collection_interval} ثانیه"
        )
    
    def _collect_metrics(self):
        """جمع‌آوری مداوم معیارها"""
        while self.running:
            try:
                metrics = self._gather_system_metrics()
                self.metrics_history.append(metrics)
                
                # بررسی آستانه‌ها
                self._check_thresholds(metrics)
                
                # انتظار برای چرخه بعد
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.reporter.error(
                    "خطا در جمع‌آوری",
                    f"خطا در جمع‌آوری معیارها: {str(e)}"
                )
                time.sleep(self.collection_interval)
    
    def _gather_system_metrics(self) -> Dict:
        """جمع‌آوری معیارهای سیستم"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Network (basic)
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'persian_datetime': self._format_persian_datetime(),
                'cpu': {
                    'usage_percent': round(cpu_percent, 2),
                    'cores': cpu_count
                },
                'memory': {
                    'usage_percent': round(memory_percent, 2),
                    'available_gb': round(memory_available_gb, 2),
                    'total_gb': round(memory.total / (1024**3), 2)
                },
                'disk': {
                    'usage_percent': round(disk_percent, 2),
                    'free_gb': round(disk_free_gb, 2),
                    'total_gb': round(disk.total / (1024**3), 2)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                'processes': process_count
            }
            
            return metrics
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': f"خطا در جمع‌آوری: {str(e)}"
            }
    
    def _format_persian_datetime(self) -> str:
        """فرمت فارسی تاریخ و زمان"""
        try:
            import jdatetime
            dt = datetime.now()
            jalali_dt = jdatetime.datetime.fromgregorian(datetime=dt)
            persian_date = jalali_dt.strftime('%Y/%m/%d - %H:%M:%S')
            try:
                from persiantools import digits
                return digits.en_to_fa(persian_date)
            except ImportError:
                return digits_en_to_fa(persian_date)
        except ImportError:
            # Fallback to regular datetime
            dt = datetime.now()
            formatted = dt.strftime('%Y/%m/%d - %H:%M:%S')
            try:
                from persiantools import digits
                return digits.en_to_fa(formatted)
            except ImportError:
                return digits_en_to_fa(formatted)
    
    def _check_thresholds(self, metrics: Dict):
        """بررسی آستانه‌های عملکرد"""
        if 'error' in metrics:
            return
        
        # بررسی CPU
        cpu_usage = metrics['cpu']['usage_percent']
        if cpu_usage >= self.performance_thresholds['cpu_critical']:
            self.reporter.error(
                "CPU بحرانی",
                f"استفاده از CPU به {self._format_number(cpu_usage)}% رسیده",
                {'cpu_usage': cpu_usage}
            )
        elif cpu_usage >= self.performance_thresholds['cpu_warning']:
            self.reporter.warning(
                "CPU بالا",
                f"استفاده از CPU: {self._format_number(cpu_usage)}%",
                {'cpu_usage': cpu_usage}
            )
        
        # بررسی Memory
        memory_usage = metrics['memory']['usage_percent']
        if memory_usage >= self.performance_thresholds['memory_critical']:
            self.reporter.error(
                "حافظه بحرانی",
                f"استفاده از حافظه به {self._format_number(memory_usage)}% رسیده",
                {'memory_usage': memory_usage}
            )
        elif memory_usage >= self.performance_thresholds['memory_warning']:
            self.reporter.warning(
                "حافظه بالا",
                f"استفاده از حافظه: {self._format_number(memory_usage)}%",
                {'memory_usage': memory_usage}
            )
        
        # بررسی Disk
        disk_usage = metrics['disk']['usage_percent']
        if disk_usage >= self.performance_thresholds['disk_critical']:
            self.reporter.error(
                "دیسک بحرانی",
                f"استفاده از دیسک به {self._format_number(disk_usage)}% رسیده",
                {'disk_usage': disk_usage}
            )
        elif disk_usage >= self.performance_thresholds['disk_warning']:
            self.reporter.warning(
                "دیسک پر",
                f"استفاده از دیسک: {self._format_number(disk_usage)}%",
                {'disk_usage': disk_usage}
            )
    
    def _format_number(self, number: float) -> str:
        """تبدیل عدد به فرمت فارسی"""
        try:
            from persiantools import digits
            return digits.en_to_fa(str(round(number, 2)))
        except ImportError:
            return digits_en_to_fa(round(number, 2))
    
    def get_current_metrics(self) -> Dict:
        """دریافت آخرین معیارها"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return {}
    
    def get_performance_summary(self) -> Dict:
        """خلاصه عملکرد سیستم"""
        if not self.metrics_history:
            return {'error': 'هیچ داده‌ای جمع‌آوری نشده'}
        
        recent_metrics = list(self.metrics_history)[-60:]  # آخرین ساعت
        
        # محاسبه میانگین‌ها
        avg_cpu = sum(m.get('cpu', {}).get('usage_percent', 0) for m in recent_metrics if 'error' not in m) / len(recent_metrics)
        avg_memory = sum(m.get('memory', {}).get('usage_percent', 0) for m in recent_metrics if 'error' not in m) / len(recent_metrics)
        avg_disk = sum(m.get('disk', {}).get('usage_percent', 0) for m in recent_metrics if 'error' not in m) / len(recent_metrics)
        
        # وضعیت سلامت
        health_status = "سالم"
        if avg_cpu > 85 or avg_memory > 90 or avg_disk > 95:
            health_status = "بحرانی"
        elif avg_cpu > 70 or avg_memory > 75 or avg_disk > 80:
            health_status = "نیاز به توجه"
        
        current = self.get_current_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'persian_datetime': self._format_persian_datetime(),
            'health_status': health_status,
            'current_metrics': {
                'cpu': self._format_number(current.get('cpu', {}).get('usage_percent', 0)) + '%',
                'memory': self._format_number(current.get('memory', {}).get('usage_percent', 0)) + '%',
                'disk': self._format_number(current.get('disk', {}).get('usage_percent', 0)) + '%',
                'processes': self._format_number(current.get('processes', 0))
            },
            'hourly_averages': {
                'cpu': self._format_number(avg_cpu) + '%',
                'memory': self._format_number(avg_memory) + '%',
                'disk': self._format_number(avg_disk) + '%'
            },
            'data_points_collected': self._format_number(len(self.metrics_history))
        }
    
    def export_metrics(self, filename: str = None, hours: int = 24) -> str:
        """صادرات معیارها"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"telemetry_metrics_{timestamp}.json"
        
        # فیلتر کردن ساعات مشخص شده
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        export_data = {
            'metadata': {
                'export_time': self._format_persian_datetime(),
                'hours_covered': self._format_number(hours),
                'total_data_points': self._format_number(len(filtered_metrics))
            },
            'performance_summary': self.get_performance_summary(),
            'raw_metrics': filtered_metrics
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        self.reporter.success(
            "صادرات معیارها",
            f"معیارهای {self._format_number(hours)} ساعت گذشته در {filename} ذخیره شد"
        )
        
        return filename
    
    def stop(self):
        """توقف سیستم تله‌متری"""
        self.running = False
        self.reporter.info("توقف تله‌متری", "سیستم تله‌متری متوقف شد")


# نمونه استفاده
if __name__ == "__main__":
    # ایجاد سیستم تله‌متری
    telemetry = PersianTelemetryLogger(collection_interval=5)  # هر 5 ثانیه
    
    try:
        # اجرای نمونه
        print("📊 سیستم تله‌متری در حال اجرا...")
        print("برای توقف Ctrl+C را فشار دهید\n")
        
        # نمایش وضعیت هر 30 ثانیه
        while True:
            time.sleep(30)
            
            summary = telemetry.get_performance_summary()
            print(f"\n📋 خلاصه عملکرد - {summary.get('persian_datetime', '')}")
            print(f"وضعیت سلامت: {summary.get('health_status', 'نامشخص')}")
            
            current = summary.get('current_metrics', {})
            print(f"CPU: {current.get('cpu', '0%')}")
            print(f"حافظه: {current.get('memory', '0%')}")
            print(f"دیسک: {current.get('disk', '0%')}")
            print(f"پروسه‌ها: {current.get('processes', '0')}")
            
    except KeyboardInterrupt:
        print("\n🛑 توقف سیستم...")
        
        # صادرات معیارها قبل از خروج
        telemetry.export_metrics()
        telemetry.stop()
        
        print("✅ سیستم تله‌متری متوقف شد")

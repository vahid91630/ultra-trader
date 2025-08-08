#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
داشبورد سریع با گزارشدهی فارسی
نمایش وضعیت سیستم‌های مانیتورینگ به زبان فارسی
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any
try:
    from monitoring.persian_reporter import PersianReporter, SystemComponent
    from persiantools import digits
except ImportError:
    # Fallback for standalone execution
    import logging
    logging.basicConfig(level=logging.INFO)
    print("⚠️ برخی ماژول‌ها در دسترس نیستند - اجرا در حالت محدود")
    
    def digits_en_to_fa(text):
        return str(text).replace('0','۰').replace('1','۱').replace('2','۲').replace('3','۳').replace('4','۴').replace('5','۵').replace('6','۶').replace('7','۷').replace('8','۸').replace('9','۹')


class PersianDashboard:
    """داشبورد فارسی سیستم مانیتورینگ"""
    
    def __init__(self):
        print("🚀 راه‌اندازی داشبورد فارسی...")
        
        try:
            self.reporter = PersianReporter(
                SystemComponent.DASHBOARD,
                log_file="monitoring/logs/dashboard_fa.log"
            )
        except:
            self.reporter = None
            
        self.start_time = datetime.now()
        self.refresh_interval = 30  # ثانیه
        
        if self.reporter:
            self.reporter.success(
                "راه‌اندازی داشبورد",
                "داشبورد فارسی با موفقیت راه‌اندازی شد"
            )
    
    def format_persian_number(self, number) -> str:
        """تبدیل عدد به فرمت فارسی"""
        try:
            from persiantools import digits
            return digits.en_to_fa(str(number))
        except ImportError:
            return digits_en_to_fa(number)
    
    def format_persian_datetime(self) -> str:
        """فرمت فارسی تاریخ و زمان"""
        try:
            import jdatetime
            dt = datetime.now()
            jalali_dt = jdatetime.datetime.fromgregorian(datetime=dt)
            persian_date = jalali_dt.strftime('%Y/%m/%d - %H:%M:%S')
            return self.format_persian_number(persian_date)
        except ImportError:
            dt = datetime.now()
            formatted = dt.strftime('%Y/%m/%d - %H:%M:%S')
            return self.format_persian_number(formatted)
    
    def get_system_status(self) -> Dict:
        """دریافت وضعیت کلی سیستم"""
        status = {
            'uptime': self._calculate_uptime(),
            'persian_datetime': self.format_persian_datetime(),
            'news_monitoring': self._get_news_status(),
            'telemetry': self._get_telemetry_status()
        }
        
        return status
    
    def _calculate_uptime(self) -> str:
        """محاسبه زمان فعالیت داشبورد"""
        uptime = datetime.now() - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60
        
        uptime_fa = f"{self.format_persian_number(hours)}:{self.format_persian_number(minutes):0>2}:{self.format_persian_number(seconds):0>2}"
        return uptime_fa
    
    def _get_news_status(self) -> Dict:
        """وضعیت سرویس پایش اخبار"""
        try:
            if os.path.exists('news_monitoring_status.json'):
                with open('news_monitoring_status.json', 'r', encoding='utf-8') as f:
                    status = json.load(f)
                return {
                    'status': 'فعال',
                    'total_analyses': self.format_persian_number(status.get('total_analyses', 0)),
                    'active_signals': self.format_persian_number(status.get('current_signals', 0))
                }
            return {'status': 'غیر فعال'}
        except:
            return {'status': 'خطا'}
    
    def _get_telemetry_status(self) -> Dict:
        """وضعیت سیستم تله‌متری"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                'status': 'فعال',
                'cpu_usage': self.format_persian_number(round(cpu_percent, 1)) + '%',
                'memory_usage': self.format_persian_number(round(memory.percent, 1)) + '%'
            }
        except ImportError:
            return {'status': 'محدود', 'message': 'ماژول psutil در دسترس نیست'}
    
    def display_status(self, status: Dict):
        """نمایش وضعیت"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 60)
        print("🚀 داشبورد مانیتورینگ فارسی 🚀".center(60))
        print("=" * 60)
        print(f"زمان: {status['persian_datetime']}")
        print(f"مدت فعالیت: {status['uptime']}")
        print("-" * 60)
        
        # پایش اخبار
        news = status['news_monitoring']
        print(f"📰 پایش اخبار: {news['status']}")
        if news['status'] == 'فعال':
            print(f"   تحلیل‌ها: {news.get('total_analyses', '۰')}")
            print(f"   سیگنال‌ها: {news.get('active_signals', '۰')}")
        
        # تله‌متری
        telemetry = status['telemetry']
        print(f"📡 تله‌متری: {telemetry['status']}")
        if telemetry['status'] == 'فعال':
            print(f"   CPU: {telemetry.get('cpu_usage', '۰%')}")
            print(f"   حافظه: {telemetry.get('memory_usage', '۰%')}")
        
        print("-" * 60)
        print(f"🔄 بروزرسانی در {self.format_persian_number(self.refresh_interval)} ثانیه | Ctrl+C برای خروج")
    
    def run_dashboard(self):
        """اجرای داشبورد"""
        try:
            while True:
                status = self.get_system_status()
                self.display_status(status)
                time.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 خروج از داشبورد...")
            if self.reporter:
                self.reporter.info("توقف داشبورد", "داشبورد فارسی متوقف شد")


# اجرای داشبورد
if __name__ == "__main__":
    dashboard = PersianDashboard()
    dashboard.run_dashboard()

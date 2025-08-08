#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم گزارشدهی فارسی مرکزی برای مانیتورینگ
ارائه گزارشهای یکپارچه و قابل خواندن به زبان فارسی
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import jdatetime
from persiantools import digits


class ReportLevel(Enum):
    """سطوح گزارشدهی"""
    INFO = "اطلاع"
    SUCCESS = "موفق"
    WARNING = "هشدار"
    ERROR = "خطا"
    CRITICAL = "بحرانی"


class SystemComponent(Enum):
    """اجزای سیستم"""
    NEWS_MONITORING = "پایش اخبار"
    DATA_COLLECTION = "جمع‌آوری داده"
    TRADING_ENGINE = "موتور معاملات"
    ALERT_SYSTEM = "سیستم هشدار"
    DASHBOARD = "داشبورد"
    DATABASE = "پایگاه داده"
    API_INTEGRATION = "یکپارچگی API"


class PersianReporter:
    """گزارشگر فارسی مرکزی"""
    
    def __init__(self, component: SystemComponent, log_file: str = None):
        self.component = component
        self.reports_history = []
        
        # تنظیم لاگر
        self.logger = logging.getLogger(f"persian_reporter_{component.name}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            if log_file:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(console_formatter)
                self.logger.addHandler(file_handler)
    
    def _format_persian_datetime(self, dt: datetime = None) -> str:
        """تبدیل تاریخ و زمان به فرمت فارسی"""
        if dt is None:
            dt = datetime.now()
        
        # تبدیل به تاریخ شمسی
        jalali_dt = jdatetime.datetime.fromgregorian(datetime=dt)
        
        # فرمت فارسی
        persian_date = jalali_dt.strftime('%Y/%m/%d')
        persian_time = jalali_dt.strftime('%H:%M:%S')
        
        # تبدیل اعداد به فارسی
        persian_date = digits.en_to_fa(persian_date)
        persian_time = digits.en_to_fa(persian_time)
        
        return f"{persian_date} - {persian_time}"
    
    def _format_numbers(self, text: str) -> str:
        """تبدیل اعداد انگلیسی به فارسی در متن"""
        return digits.en_to_fa(str(text))
    
    def report(self, level: ReportLevel, title: str, message: str, 
               data: Dict = None, tags: List[str] = None) -> Dict:
        """ثبت گزارش جدید"""
        
        # تبدیل اعداد به فارسی
        title = self._format_numbers(title)
        message = self._format_numbers(message)
        
        # ایجاد گزارش
        report = {
            'timestamp': datetime.now().isoformat(),
            'persian_datetime': self._format_persian_datetime(),
            'component': self.component.value,
            'level': level.value,
            'title': title,
            'message': message,
            'data': data or {},
            'tags': tags or []
        }
        
        # ذخیره در تاریخچه
        self.reports_history.append(report)
        
        # نمایش در لاگ
        formatted_message = self._format_log_message(report)
        
        if level == ReportLevel.INFO:
            self.logger.info(formatted_message)
        elif level == ReportLevel.SUCCESS:
            self.logger.info(formatted_message)
        elif level == ReportLevel.WARNING:
            self.logger.warning(formatted_message)
        elif level == ReportLevel.ERROR:
            self.logger.error(formatted_message)
        elif level == ReportLevel.CRITICAL:
            self.logger.critical(formatted_message)
        
        return report
    
    def _format_log_message(self, report: Dict) -> str:
        """فرمت‌بندی پیام لاگ"""
        emoji_map = {
            "اطلاع": "ℹ️",
            "موفق": "✅",
            "هشدار": "⚠️",
            "خطا": "❌",
            "بحرانی": "🚨"
        }
        
        emoji = emoji_map.get(report['level'], "📋")
        component = report['component']
        title = report['title']
        message = report['message']
        
        return f"{emoji} [{component}] {title}: {message}"
    
    def success(self, title: str, message: str, data: Dict = None) -> Dict:
        """گزارش موفقیت"""
        return self.report(ReportLevel.SUCCESS, title, message, data)
    
    def info(self, title: str, message: str, data: Dict = None) -> Dict:
        """گزارش اطلاعاتی"""
        return self.report(ReportLevel.INFO, title, message, data)
    
    def warning(self, title: str, message: str, data: Dict = None) -> Dict:
        """گزارش هشدار"""
        return self.report(ReportLevel.WARNING, title, message, data)
    
    def error(self, title: str, message: str, data: Dict = None) -> Dict:
        """گزارش خطا"""
        return self.report(ReportLevel.ERROR, title, message, data)
    
    def critical(self, title: str, message: str, data: Dict = None) -> Dict:
        """گزارش بحرانی"""
        return self.report(ReportLevel.CRITICAL, title, message, data)
    
    def create_status_report(self) -> Dict:
        """ایجاد گزارش وضعیت جامع"""
        now = datetime.now()
        
        # آمار کلی
        total_reports = len(self.reports_history)
        recent_reports = [r for r in self.reports_history 
                         if (now - datetime.fromisoformat(r['timestamp'])).seconds < 3600]
        
        # آمار بر اساس سطح
        level_stats = {}
        for level in ReportLevel:
            count = len([r for r in self.reports_history if r['level'] == level.value])
            level_stats[level.value] = count
        
        # آخرین گزارشها
        latest_reports = self.reports_history[-5:] if self.reports_history else []
        
        status_report = {
            'timestamp': now.isoformat(),
            'persian_datetime': self._format_persian_datetime(now),
            'component': self.component.value,
            'title': 'گزارش وضعیت سیستم',
            'statistics': {
                'total_reports': self._format_numbers(str(total_reports)),
                'recent_reports_1h': self._format_numbers(str(len(recent_reports))),
                'level_breakdown': {k: self._format_numbers(str(v)) for k, v in level_stats.items()}
            },
            'latest_reports': latest_reports,
            'system_health': self._assess_system_health(level_stats)
        }
        
        return status_report
    
    def _assess_system_health(self, level_stats: Dict) -> str:
        """ارزیابی سلامت سیستم"""
        error_count = level_stats.get("خطا", 0) + level_stats.get("بحرانی", 0)
        warning_count = level_stats.get("هشدار", 0)
        total_issues = error_count + warning_count
        
        if error_count > 5:
            return "بحرانی - نیاز به بررسی فوری"
        elif error_count > 0:
            return "مشکل‌دار - نیاز به توجه"
        elif warning_count > 10:
            return "هشدار - نظارت مداوم"
        elif total_issues == 0:
            return "سالم - عملکرد عادی"
        else:
            return "پایدار - عملکرد قابل قبول"
    
    def export_reports(self, filename: str = None, format: str = 'json') -> str:
        """صادرات گزارشها"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"persian_reports_{self.component.name}_{timestamp}.{format}"
        
        if format == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'component': self.component.value,
                        'export_time': self._format_persian_datetime(),
                        'total_reports': len(self.reports_history)
                    },
                    'reports': self.reports_history
                }, f, ensure_ascii=False, indent=2)
        
        self.success("صادرات گزارشها", f"گزارشها با موفقیت در {filename} ذخیره شدند")
        return filename
    
    def clear_old_reports(self, hours: int = 24) -> int:
        """پاکسازی گزارشهای قدیمی"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        initial_count = len(self.reports_history)
        self.reports_history = [
            r for r in self.reports_history 
            if datetime.fromisoformat(r['timestamp']).timestamp() > cutoff_time
        ]
        
        removed_count = initial_count - len(self.reports_history)
        if removed_count > 0:
            self.info(
                "پاکسازی گزارشها", 
                f"{self._format_numbers(str(removed_count))} گزارش قدیمی حذف شد"
            )
        
        return removed_count


# نمونه استفاده
if __name__ == "__main__":
    # ایجاد گزارشگر برای پایش اخبار
    reporter = PersianReporter(
        SystemComponent.NEWS_MONITORING,
        log_file="monitoring/logs/news_monitoring_fa.log"
    )
    
    # نمونه گزارشها
    reporter.success(
        "شروع سرویس", 
        "سرویس پایش اخبار با موفقیت راه‌اندازی شد",
        {"apis_count": 3, "update_interval": 30}
    )
    
    reporter.info(
        "تحلیل اخبار", 
        "تحلیل 25 خبر جدید انجام شد",
        {"crypto_sentiment": 0.75, "stock_sentiment": 0.62}
    )
    
    reporter.warning(
        "کاهش احساسات", 
        "احساسات بازار کریپتو در 2 ساعت گذشته کاهش یافته",
        {"previous": 0.80, "current": 0.65}
    )
    
    # ایجاد گزارش وضعیت
    status = reporter.create_status_report()
    print("\n📊 گزارش وضعیت:")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    
    # صادرات گزارشها
    reporter.export_reports()
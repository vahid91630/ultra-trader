#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم هشدار با گزارشدهی فارسی
مدیریت و ارسال هشدارهای سیستم به زبان فارسی
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
try:
    from persian_reporter import PersianReporter, SystemComponent, ReportLevel
    from persiantools import digits
except ImportError:
    # Fallback for standalone execution
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class ReportLevel:
        INFO = "اطلاع"
        ERROR = "خطا"
        
    def digits_en_to_fa(text):
        return str(text).replace('0','۰').replace('1','۱').replace('2','۲').replace('3','۳').replace('4','۴').replace('5','۵').replace('6','۶').replace('7','۷').replace('8','۸').replace('9','۹')


class AlertPriority(Enum):
    """اولویت هشدارها"""
    LOW = "کم"
    MEDIUM = "متوسط"
    HIGH = "بالا"
    CRITICAL = "بحرانی"


class AlertType(Enum):
    """انواع هشدارها"""
    SYSTEM_ERROR = "خطای سیستم"
    PERFORMANCE_ISSUE = "مشکل عملکرد"
    TRADING_ANOMALY = "ناهنجاری معاملات"
    API_FAILURE = "خرابی API"


class PersianAlertSystem:
    """سیستم هشدار با گزارشدهی فارسی"""
    
    def __init__(self):
        self.active_alerts = []
        self.alert_history = []
        self.alert_rules = []
        
        # تنظیمات پیش‌فرض
        self.max_active_alerts = 100
        
        print("✅ سیستم هشدار فارسی فعال شد")
    
    def trigger_alert(self, title: str, message: str, priority: AlertPriority,
                      alert_type: AlertType, data: Dict = None) -> Dict:
        """ایجاد هشدار جدید"""
        
        alert = {
            'id': len(self.alert_history) + 1,
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'message': message,
            'priority': priority.value,
            'type': alert_type.value,
            'data': data or {},
            'status': 'فعال'
        }
        
        # افزودن به لیست فعال
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # گزارش
        print(f"🚨 هشدار {priority.value}: {title} - {message}")
        
        return alert
    
    def get_alert_statistics(self) -> Dict:
        """آمار هشدارها"""
        try:
            total_alerts = len(self.alert_history)
            active_count = len(self.active_alerts)
            
            # تبدیل اعداد به فارسی
            try:
                from persiantools import digits
                total_fa = digits.en_to_fa(str(total_alerts))
                active_fa = digits.en_to_fa(str(active_count))
            except ImportError:
                total_fa = digits_en_to_fa(total_alerts)
                active_fa = digits_en_to_fa(active_count)
            
            return {
                'total_alerts': total_fa,
                'active_alerts': active_fa,
                'persian_datetime': datetime.now().strftime('%Y/%m/%d - %H:%M:%S')
            }
        except Exception as e:
            return {
                'error': f"خطا در محاسبه آمار: {str(e)}",
                'total_alerts': '0',
                'active_alerts': '0'
            }


# نمونه استفاده
if __name__ == "__main__":
    alert_system = PersianAlertSystem()
    
    # تست هشدار
    alert_system.trigger_alert(
        title="CPU بالا",
        message="استفاده از CPU به ۹۵% رسیده است",
        priority=AlertPriority.HIGH,
        alert_type=AlertType.PERFORMANCE_ISSUE,
        data={"cpu_usage": 95}
    )
    
    # نمایش آمار
    stats = alert_system.get_alert_statistics()
    print("\n📊 آمار هشدارها:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

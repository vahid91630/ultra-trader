#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم هشدار پیشرفته در زمان واقعی
Real-time Advanced Alert System for Ultra-Trader
"""

import os
import json
import time
import smtplib
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from monitoring.telemetry_logger import AlertLevel, telemetry


class AlertType(Enum):
    """انواع هشدار"""
    SYSTEM_HEALTH = "system_health"
    ERROR_SPIKE = "error_spike"
    PERFORMANCE = "performance"
    TRADING = "trading"
    CUSTOM = "custom"


class NotificationChannel(Enum):
    """کانال‌های اطلاع‌رسانی"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    TELEGRAM = "telegram"
    LOG = "log"


@dataclass
class AlertRule:
    """قانون هشدار"""
    id: str
    name: str
    alert_type: AlertType
    condition: str  # شرط هشدار (مثل: cpu_percent > 80)
    severity: AlertLevel
    channels: List[NotificationChannel]
    cooldown_minutes: int = 5  # فاصله بین هشدارهای مشابه
    enabled: bool = True
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        data['channels'] = [c.value for c in self.channels]
        return data


@dataclass
class Alert:
    """هشدار"""
    id: str
    rule_id: str
    title: str
    message: str
    severity: AlertLevel
    alert_type: AlertType
    data: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['severity'] = self.severity.value
        data['alert_type'] = self.alert_type.value
        data['timestamp'] = self.timestamp.isoformat()
        data['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
        return data


class AlertSystem:
    """سیستم هشدار پیشرفته"""
    
    def __init__(self, db_path: str = "monitoring/alerts.db"):
        self.db_path = db_path
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        
        # تنظیمات لاگینگ
        self.logger = logging.getLogger("AlertSystem")
        
        # تنظیمات اطلاع‌رسانی
        self.email_config = self._load_email_config()
        self.webhook_config = self._load_webhook_config()
        self.telegram_config = self._load_telegram_config()
        
        # ایجاد دیتابیس
        self._initialize_database()
        
        # بارگذاری قوانین
        self._load_default_rules()
        
        # شروع مانیتورینگ
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_alerts)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("🚨 سیستم هشدار فعال شد")
    
    def _load_email_config(self) -> Dict[str, str]:
        """بارگذاری تنظیمات ایمیل"""
        return {
            'smtp_server': os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.environ.get('EMAIL_SMTP_PORT', '587')),
            'username': os.environ.get('EMAIL_USERNAME', ''),
            'password': os.environ.get('EMAIL_PASSWORD', ''),
            'from_email': os.environ.get('EMAIL_FROM', ''),
            'to_emails': os.environ.get('EMAIL_TO', '').split(',')
        }
    
    def _load_webhook_config(self) -> Dict[str, str]:
        """بارگذاری تنظیمات وب‌هوک"""
        return {
            'url': os.environ.get('WEBHOOK_URL', ''),
            'headers': json.loads(os.environ.get('WEBHOOK_HEADERS', '{}'))
        }
    
    def _load_telegram_config(self) -> Dict[str, str]:
        """بارگذاری تنظیمات تلگرام"""
        return {
            'bot_token': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': os.environ.get('TELEGRAM_CHAT_ID', '')
        }
    
    def _initialize_database(self):
        """ایجاد جداول دیتابیس"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول قوانین هشدار
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                condition_text TEXT NOT NULL,
                severity TEXT NOT NULL,
                channels TEXT NOT NULL,
                cooldown_minutes INTEGER,
                enabled BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول هشدارها
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                rule_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                data TEXT,
                timestamp TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0,
                resolved_at TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ایندکس‌ها
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)")
        
        conn.commit()
        conn.close()
    
    def _load_default_rules(self):
        """بارگذاری قوانین پیش‌فرض"""
        default_rules = [
            AlertRule(
                id="cpu_high",
                name="استفاده بالای CPU",
                alert_type=AlertType.SYSTEM_HEALTH,
                condition="cpu_percent > 80",
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.LOG],
                cooldown_minutes=5
            ),
            AlertRule(
                id="memory_high",
                name="استفاده بالای حافظه",
                alert_type=AlertType.SYSTEM_HEALTH,
                condition="memory_percent > 85",
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.LOG],
                cooldown_minutes=5
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule):
        """اضافه کردن قانون هشدار"""
        self.rules[rule.id] = rule
        self.logger.info(f"➕ قانون هشدار اضافه شد: {rule.name}")
    
    def _monitor_alerts(self):
        """مانیتورینگ مداوم برای تشخیص هشدارها"""
        while self.monitoring_active:
            try:
                # بررسی سلامت سیستم
                self._check_system_health_alerts()
                
                # انتظار
                time.sleep(30)  # بررسی هر 30 ثانیه
                
            except Exception as e:
                self.logger.error(f"خطا در مانیتورینگ هشدارها: {e}")
                time.sleep(60)
    
    def _check_system_health_alerts(self):
        """بررسی هشدارهای سلامت سیستم"""
        try:
            # دریافت آخرین وضعیت سلامت
            health = telemetry.collect_system_health()
            if not health:
                return
            
            # بررسی قوانین سلامت سیستم
            for rule in self.rules.values():
                if (rule.alert_type == AlertType.SYSTEM_HEALTH and 
                    rule.enabled and 
                    self._should_check_rule(rule)):
                    
                    if self._evaluate_condition(rule.condition, health.to_dict()):
                        self._trigger_alert(rule, health.to_dict())
                        
        except Exception as e:
            self.logger.error(f"خطا در بررسی هشدارهای سلامت: {e}")
    
    def _should_check_rule(self, rule: AlertRule) -> bool:
        """بررسی اینکه آیا زمان بررسی قانون رسیده"""
        if rule.id in self.last_alert_times:
            time_since_last = datetime.now() - self.last_alert_times[rule.id]
            if time_since_last.total_seconds() < rule.cooldown_minutes * 60:
                return False
        return True
    
    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """ارزیابی شرط هشدار"""
        try:
            # جایگزینی متغیرها در شرط
            for key, value in data.items():
                condition = condition.replace(key, str(value))
            
            # ارزیابی شرط
            result = eval(condition)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی شرط: {condition}, {e}")
            return False
    
    def _trigger_alert(self, rule: AlertRule, data: Dict[str, Any]):
        """فعال‌سازی هشدار"""
        try:
            alert_id = f"{rule.id}_{int(time.time())}"
            
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                title=f"هشدار: {rule.name}",
                message=self._generate_alert_message(rule, data),
                severity=rule.severity,
                alert_type=rule.alert_type,
                data=data,
                timestamp=datetime.now()
            )
            
            # ذخیره هشدار
            self.active_alerts[alert_id] = alert
            self.last_alert_times[rule.id] = alert.timestamp
            
            # ارسال اطلاع‌رسانی
            self._send_notifications(alert, rule.channels)
            
            self.logger.warning(f"🚨 هشدار فعال شد: {alert.title}")
            
        except Exception as e:
            self.logger.error(f"خطا در فعال‌سازی هشدار: {e}")
    
    def _generate_alert_message(self, rule: AlertRule, data: Dict[str, Any]) -> str:
        """تولید متن هشدار"""
        message = f"هشدار {rule.severity.value.upper()}: {rule.name}\n\n"
        message += f"زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"شرط: {rule.condition}\n\n"
        message += "اطلاعات:\n"
        
        for key, value in data.items():
            if isinstance(value, dict):
                message += f"  {key}:\n"
                for k, v in value.items():
                    message += f"    {k}: {v}\n"
            else:
                message += f"  {key}: {value}\n"
        
        return message
    
    def _send_notifications(self, alert: Alert, channels: List[NotificationChannel]):
        """ارسال اطلاع‌رسانی‌ها"""
        for channel in channels:
            try:
                if channel == NotificationChannel.LOG:
                    self._send_log_notification(alert)
                    
            except Exception as e:
                self.logger.error(f"خطا در ارسال اطلاع‌رسانی {channel.value}: {e}")
    
    def _send_log_notification(self, alert: Alert):
        """ارسال اطلاع‌رسانی لاگ"""
        self.logger.warning(f"📢 {alert.title}: {alert.message}")
    
    def get_active_alerts(self) -> List[Dict]:
        """دریافت هشدارهای فعال"""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def stop_monitoring(self):
        """توقف مانیتورینگ"""
        self.monitoring_active = False
        self.logger.info("🛑 مانیتورینگ هشدار متوقف شد")


# نمونه سازی global
alert_system = AlertSystem()

if __name__ == "__main__":
    print("🚨 تست سیستم هشدار...")
    
    # انتظار کوتاه برای اجرای تست
    time.sleep(3)
    
    # نمایش هشدارهای فعال
    active_alerts = alert_system.get_active_alerts()
    print(f"📋 هشدارهای فعال: {len(active_alerts)}")
    
    print("✅ تست کامل شد")

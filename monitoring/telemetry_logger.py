#!/usr/bin/env python3
"""
سیستم ثبت لاگ و نظارت بر عملکرد
"""

import json
import os
import sqlite3
from datetime import datetime
import logging

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TelemetryLogger:
    """سیستم ثبت داده‌های عملکرد و نظارت"""
    
    def __init__(self):
        self.db_path = 'system_logs.db'
        self.init_database()
    
    def init_database(self):
        """ایجاد دیتابیس لاگ‌ها"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    source TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("دیتابیس لاگ‌ها آماده شد")
            
        except Exception as e:
            logger.error(f"خطا در ایجاد دیتابیس: {e}")
    
    def log_event(self, level, category, message, details=None, source=None):
        """ثبت رویداد در لاگ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_logs (timestamp, level, category, message, details, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                level,
                category,
                message,
                json.dumps(details) if details else None,
                source
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"خطا در ثبت لاگ: {e}")

# نمونه سراسری
telemetry = TelemetryLogger()

if __name__ == "__main__":
    telemetry.log_event('INFO', 'SYSTEM', 'سیستم لاگینگ راه‌اندازی شد')
    print("سیستم لاگینگ آماده است")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سرویس بکاپ خودکار روزانه ULTRA_PLUS_BOT
اجرای مداوم بکاپ‌گیری از تمام داده‌ها
"""

import os
import time
import logging
import threading
from datetime import datetime
from comprehensive_backup_system import ComprehensiveBackupSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedBackupService:
    """سرویس خودکار بکاپ‌گیری"""
    
    def __init__(self):
        self.backup_system = ComprehensiveBackupSystem()
        self.running = True
        self.backup_interval = 86400  # 24 ساعت
        self.last_backup = None
        self.total_backups = 0
        
    def run_backup_cycle(self):
        """اجرای یک چرخه بکاپ"""
        try:
            logger.info("🔄 شروع بکاپ‌گیری خودکار...")
            
            # ایجاد بکاپ
            backup_info = self.backup_system.create_daily_backup()
            self.total_backups += 1
            self.last_backup = datetime.now()
            
            # حذف بکاپ‌های قدیمی (بیش از 7 روز)
            self.backup_system.cleanup_old_backups(keep_days=7)
            
            # ذخیره وضعیت سرویس
            self.save_service_status(backup_info)
            
            logger.info(f"✅ بکاپ شماره {self.total_backups} کامل شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در بکاپ‌گیری: {e}")
    
    def save_service_status(self, latest_backup):
        """ذخیره وضعیت سرویس بکاپ"""
        backups = self.backup_system.get_backup_list()
        
        status = {
            'service': 'automated_backup',
            'status': 'active',
            'last_backup': self.last_backup.isoformat() if self.last_backup else None,
            'total_backups': self.total_backups,
            'latest_backup_id': latest_backup['id'],
            'latest_backup_size_mb': latest_backup['total_size_mb'],
            'total_backup_size_mb': sum(b['size_mb'] for b in backups),
            'backup_count': len(backups),
            'oldest_backup_days': max(b['age_days'] for b in backups) if backups else 0
        }
        
        with open('backup_service_status.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(status, f, ensure_ascii=False, indent=2)
    
    def continuous_backup(self):
        """بکاپ‌گیری مداوم"""
        logger.info("🚀 سرویس بکاپ خودکار شروع به کار کرد")
        logger.info(f"⏰ بکاپ هر 24 ساعت یکبار")
        
        # اجرای اولین بکاپ
        self.run_backup_cycle()
        
        while self.running:
            try:
                # انتظار تا بکاپ بعدی
                time.sleep(self.backup_interval)
                
                # اجرای بکاپ
                self.run_backup_cycle()
                
            except KeyboardInterrupt:
                logger.info("❌ توقف سرویس بکاپ")
                break
            except Exception as e:
                logger.error(f"خطا در سرویس: {e}")
                time.sleep(3600)  # انتظار 1 ساعت در صورت خطا
    
    def quick_backup(self):
        """ایجاد بکاپ فوری"""
        logger.info("⚡ ایجاد بکاپ فوری...")
        self.run_backup_cycle()
    
    def stop(self):
        """توقف سرویس"""
        self.running = False
        logger.info("🛑 دستور توقف سرویس صادر شد")

def main():
    """اجرای سرویس بکاپ خودکار"""
    service = AutomatedBackupService()
    
    # ایجاد بکاپ فوری در ابتدا
    service.quick_backup()
    
    # شروع بکاپ‌گیری مداوم در thread جداگانه
    backup_thread = threading.Thread(target=service.continuous_backup)
    backup_thread.daemon = True
    backup_thread.start()
    
    logger.info("✅ سرویس بکاپ خودکار فعال شد")
    logger.info("📦 بکاپ از تمام داده‌ها هر 24 ساعت")
    
    try:
        # نمایش وضعیت هر 5 دقیقه
        while True:
            time.sleep(300)  # 5 دقیقه
            
            # نمایش وضعیت
            if os.path.exists('backup_service_status.json'):
                import json
                with open('backup_service_status.json', 'r') as f:
                    status = json.load(f)
                    print(f"\n📊 وضعیت بکاپ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   آخرین بکاپ: {status.get('last_backup', 'ندارد')}")
                    print(f"   تعداد بکاپ‌ها: {status['backup_count']}")
                    print(f"   حجم کل: {status['total_backup_size_mb']:.2f} MB")
                    print(f"   قدیمی‌ترین: {status['oldest_backup_days']} روز قبل")
            
    except KeyboardInterrupt:
        logger.info("🛑 توقف سرویس...")
        service.stop()

if __name__ == "__main__":
    main()
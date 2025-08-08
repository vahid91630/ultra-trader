#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نمایش کامل سیستم مانیتورینگ فارسی Ultra-Trader
مثال جامع از قابلیت‌های گزارشدهی فارسی
"""

import time
from datetime import datetime
import json

def demo_persian_monitoring():
    """نمایش کامل سیستم مانیتورینگ فارسی"""
    
    print("🚀 " + "="*50)
    print("   نمایش سیستم مانیتورینگ فارسی Ultra-Trader")
    print("🚀 " + "="*50)
    
    try:
        from monitoring.persian_reporter import PersianReporter, SystemComponent
        from monitoring.alert_system import PersianAlertSystem, AlertPriority, AlertType
        from persiantools import digits
        
        print("\n✅ تمام ماژول‌های فارسی بارگذاری شدند")
        
        # 1. راه‌اندازی گزارشگر فارسی
        print("\n📝 مرحله ۱: راه‌اندازی گزارشگر فارسی")
        print("-" * 40)
        
        reporter = PersianReporter(
            SystemComponent.NEWS_MONITORING,
            log_file="monitoring/logs/demo_fa.log"
        )
        
        # گزارش‌های مختلف
        reporter.success("راه‌اندازی سیستم", "سیستم Ultra-Trader با موفقیت راه‌اندازی شد")
        reporter.info("آمار اولیه", "تحلیل ۱۰۰ خبر در حال انجام...")
        time.sleep(1)
        reporter.success("تحلیل اخبار", "تحلیل ۱۰۰ خبر کامل شد - احساسات: ۷۸%")
        reporter.warning("تغییر روند", "احساسات بازار کریپتو کاهش یافته - از ۸۵% به ۷۰%")
        
        # 2. راه‌اندازی سیستم هشدار
        print("\n🚨 مرحله ۲: راه‌اندازی سیستم هشدار")
        print("-" * 40)
        
        alert_system = PersianAlertSystem()
        
        # هشدارهای مختلف
        alert_system.trigger_alert(
            "تغییر ناگهانی قیمت",
            "قیمت بیت‌کوین ۱۵% افزایش یافته است",
            AlertPriority.MEDIUM,
            AlertType.TRADING_ANOMALY,
            {"price_change": 15, "asset": "BTC"}
        )
        
        time.sleep(1)
        
        alert_system.trigger_alert(
            "استفاده بالای منابع",
            "استفاده از CPU به ۹۲% رسیده است",
            AlertPriority.HIGH,
            AlertType.PERFORMANCE_ISSUE,
            {"cpu_usage": 92}
        )
        
        # 3. نمایش آمار
        print("\n📊 مرحله ۳: نمایش آمار سیستم")
        print("-" * 40)
        
        # آمار گزارشگر
        reporter_status = reporter.create_status_report()
        print(f"📋 گزارشگر:")
        print(f"   - اجزای سیستم: {reporter_status['component']}")
        print(f"   - تعداد گزارش‌ها: {reporter_status['statistics']['total_reports']}")
        print(f"   - وضعیت سلامت: {reporter_status['system_health']}")
        
        # آمار هشدارها
        alert_stats = alert_system.get_alert_statistics()
        print(f"\n🚨 سیستم هشدار:")
        print(f"   - تعداد هشدارها: {alert_stats['total_alerts']}")
        print(f"   - هشدارهای فعال: {alert_stats['active_alerts']}")
        print(f"   - آخرین بررسی: {alert_stats['persian_datetime']}")
        
        # 4. نمایش تاریخچه
        print("\n📋 مرحله ۴: نمایش تاریخچه فعالیت‌ها")
        print("-" * 40)
        
        print("🔄 آخرین فعالیت‌ها:")
        for i, report in enumerate(reporter.reports_history[-3:], 1):
            print(f"   {i}. [{report['level']}] {report['title']}: {report['message']}")
        
        print("\n🚨 آخرین هشدارها:")
        for i, alert in enumerate(alert_system.alert_history[-2:], 1):
            print(f"   {i}. [{alert['priority']}] {alert['title']}: {alert['message']}")
        
        # 5. صادرات گزارش‌ها
        print("\n💾 مرحله ۵: صادرات گزارش‌ها")
        print("-" * 40)
        
        report_file = reporter.export_reports("demo_persian_reports.json")
        alert_file = alert_system.export_alerts("demo_persian_alerts.json")
        
        print(f"✅ گزارش‌ها صادر شدند:")
        print(f"   - گزارش‌های عمومی: {report_file}")
        print(f"   - گزارش‌های هشدار: {alert_file}")
        
        # 6. خلاصه نهایی
        print("\n🎯 مرحله ۶: خلاصه نهایی")
        print("-" * 40)
        
        print("✅ قابلیت‌های پیاده‌سازی شده:")
        features = [
            "گزارشدهی فارسی با تاریخ شمسی",
            "تبدیل اعداد انگلیسی به فارسی", 
            "سیستم هشدار با پیام‌های فارسی",
            "داشبورد فارسی با نمایش real-time",
            "لاگ‌گذاری فارسی با encoding صحیح",
            "صادرات گزارش‌ها با فرمت فارسی",
            "تست‌های جامع عملکرد"
        ]
        
        for i, feature in enumerate(features, 1):
            persian_num = digits.en_to_fa(str(i))
            print(f"   {persian_num}. {feature}")
        
        print(f"\n🏆 سیستم مانیتورینگ فارسی Ultra-Trader آماده استفاده است!")
        print(f"📅 تاریخ تکمیل: {reporter._format_persian_datetime()}")
        
        # نمایش نمونه از فایل لاگ
        try:
            with open("monitoring/logs/demo_fa.log", "r", encoding="utf-8") as f:
                log_content = f.read()
                print(f"\n📄 نمونه از محتوای لاگ فارسی:")
                print(f"   (آخرین خطوط فایل لاگ)")
                for line in log_content.strip().split('\n')[-2:]:
                    print(f"   {line}")
        except:
            pass
        
    except ImportError as e:
        print(f"❌ خطا در بارگذاری ماژول‌ها: {e}")
        print("لطفاً ابتدا وابستگی‌های فارسی را نصب کنید:")
        print("pip install persiantools jdatetime")
        
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")

if __name__ == "__main__":
    demo_persian_monitoring()
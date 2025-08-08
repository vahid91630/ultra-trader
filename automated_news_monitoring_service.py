#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سرویس پایش خودکار اخبار بازارهای مالی
بروزرسانی مداوم احساسات بازار و افزایش هوش ربات
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from news_api_integration import NewsAPIIntegration, update_intelligence_with_news

# اضافه کردن سیستم مانیتورینگ پیشرفته
try:
    from monitoring.telemetry_logger import telemetry, log_function_performance, AlertLevel, MetricType
    from monitoring.alert_system import alert_system, AlertRule, AlertType, NotificationChannel
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    def log_function_performance(func):
        return func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedNewsMonitoringService:
    """سرویس خودکار پایش اخبار"""
    
    def __init__(self):
        self.news_system = NewsAPIIntegration()
        self.running = True
        self.analysis_interval = 1800  # هر 30 دقیقه
        self.last_analysis = None
        self.total_analyses = 0
        self.market_signals = []
        
        # متریک‌های عملکردی
        self.success_count = 0
        self.error_count = 0
        self.api_response_times = []
        
        # اگر مانیتورینگ فعال است، قوانین هشدار اضافه کن
        if MONITORING_ENABLED:
            self._setup_monitoring()
        
    def _setup_monitoring(self):
        """تنظیم سیستم مانیتورینگ برای سرویس اخبار"""
        try:
            # قانون هشدار برای خطاهای زیاد در تحلیل اخبار
            news_error_rule = AlertRule(
                id="news_analysis_errors",
                name="خطاهای زیاد در تحلیل اخبار",
                alert_type=AlertType.CUSTOM,
                condition="error_rate > 0.2",  # بیش از 20% خطا
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.LOG],
                cooldown_minutes=10
            )
            alert_system.add_rule(news_error_rule)
            
            # قانون هشدار برای کاهش کیفیت API
            api_performance_rule = AlertRule(
                id="news_api_slow",
                name="کندی در API های اخبار",
                alert_type=AlertType.PERFORMANCE,
                condition="avg_response_time > 10.0",  # بیش از 10 ثانیه
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.LOG],
                cooldown_minutes=15
            )
            alert_system.add_rule(api_performance_rule)
            
            logger.info("🔧 مانیتورینگ پیشرفته برای سرویس اخبار فعال شد")
            
        except Exception as e:
            logger.error(f"خطا در تنظیم مانیتورینگ: {e}")
    
    @log_function_performance
    def run_analysis_cycle(self):
        """اجرای یک چرخه تحلیل"""
        start_time = time.time()
        
        try:
            if MONITORING_ENABLED:
                telemetry.record_event(
                    "news_analysis_started",
                    {"cycle": self.total_analyses + 1},
                    "info",
                    "NewsMonitoring"
                )
            
            logger.info("🔄 شروع چرخه جدید تحلیل اخبار...")
            
            # تحلیل بازارها
            result = self.news_system.analyze_all_markets()
            self.total_analyses += 1
            self.last_analysis = datetime.now()
            self.success_count += 1
            
            # ثبت زمان پاسخ
            response_time = time.time() - start_time
            self.api_response_times.append(response_time)
            
            # حفظ حداکثر 100 زمان آخر
            if len(self.api_response_times) > 100:
                self.api_response_times.pop(0)
            
            # ثبت متریک‌ها
            if MONITORING_ENABLED:
                telemetry.record_metric("news.analysis_cycle_time", response_time, MetricType.TIMER)
                telemetry.record_metric("news.total_analyses", self.total_analyses, MetricType.COUNTER)
                telemetry.record_metric("news.success_rate", self._calculate_success_rate(), MetricType.GAUGE)
                
                if self.api_response_times:
                    avg_response_time = sum(self.api_response_times) / len(self.api_response_times)
                    telemetry.record_metric("news.avg_response_time", avg_response_time, MetricType.GAUGE)
            
            # بروزرسانی سطح هوش
            update_intelligence_with_news()
            
            # تولید سیگنال‌های معاملاتی
            self.generate_trading_signals(result)
            
            # ذخیره وضعیت سرویس
            self.save_service_status(result)
            
            # بررسی کیفیت عملکرد برای هشدارها
            if MONITORING_ENABLED:
                self._check_performance_alerts()
            
            logger.info(f"✅ چرخه تحلیل {self.total_analyses} کامل شد در {response_time:.2f} ثانیه")
            
        except Exception as e:
            self.error_count += 1
            error_rate = self._calculate_error_rate()
            
            if MONITORING_ENABLED:
                telemetry.record_error(
                    AlertLevel.ERROR,
                    f"خطا در چرخه تحلیل اخبار: {str(e)}",
                    "NewsMonitoring",
                    str(e)
                )
                telemetry.record_metric("news.error_rate", error_rate, MetricType.GAUGE)
                telemetry.record_metric("news.total_errors", self.error_count, MetricType.COUNTER)
            
            logger.error(f"❌ خطا در چرخه تحلیل: {e}")
    
    def _calculate_success_rate(self) -> float:
        """محاسبه نرخ موفقیت"""
        total = self.success_count + self.error_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def _calculate_error_rate(self) -> float:
        """محاسبه نرخ خطا"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.error_count / total
    
    def _check_performance_alerts(self):
        """بررسی شرایط هشدار عملکرد"""
        try:
            error_rate = self._calculate_error_rate()
            avg_response_time = sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else 0
            
            # بررسی نرخ خطا
            if error_rate > 0.2:  # بیش از 20% خطا
                telemetry.record_error(
                    AlertLevel.WARNING,
                    f"نرخ خطای بالا در تحلیل اخبار: {error_rate:.1%}",
                    "NewsMonitoring"
                )
            
            # بررسی زمان پاسخ
            if avg_response_time > 10.0:  # بیش از 10 ثانیه
                telemetry.record_error(
                    AlertLevel.WARNING,
                    f"زمان پاسخ بالای API اخبار: {avg_response_time:.2f} ثانیه",
                    "NewsMonitoring"
                )
                
        except Exception as e:
            logger.error(f"خطا در بررسی هشدارهای عملکرد: {e}")
    
    @log_function_performance
    def generate_trading_signals(self, analysis_result):
        """تولید سیگنال‌های معاملاتی بر اساس اخبار"""
        signals = []
        
        crypto_sentiment = analysis_result.get('crypto_sentiment', 0.5)
        stock_sentiment = analysis_result.get('stock_sentiment', 0.5)
        
        # ثبت احساسات در متریک‌ها
        if MONITORING_ENABLED:
            telemetry.record_metric("news.crypto_sentiment", crypto_sentiment, MetricType.GAUGE)
            telemetry.record_metric("news.stock_sentiment", stock_sentiment, MetricType.GAUGE)
        
        # سیگنال‌های کریپتو
        if crypto_sentiment > 0.75:
            signals.append({
                'market': 'crypto',
                'action': 'BUY',
                'strength': 'قوی',
                'sentiment': crypto_sentiment,
                'reason': 'احساسات بسیار مثبت در اخبار'
            })
        elif crypto_sentiment < 0.25:
            signals.append({
                'market': 'crypto',
                'action': 'SELL',
                'strength': 'قوی',
                'sentiment': crypto_sentiment,
                'reason': 'احساسات بسیار منفی در اخبار'
            })
        
        # سیگنال‌های سهام
        if stock_sentiment > 0.75:
            signals.append({
                'market': 'stocks',
                'action': 'BUY',
                'strength': 'قوی',
                'sentiment': stock_sentiment,
                'reason': 'اخبار مثبت بازار سهام'
            })
        elif stock_sentiment < 0.25:
            signals.append({
                'market': 'stocks',
                'action': 'SELL',
                'strength': 'قوی',
                'sentiment': stock_sentiment,
                'reason': 'اخبار منفی بازار سهام'
            })
        
        # ذخیره سیگنال‌ها
        if signals:
            self.market_signals = signals
            with open('news_trading_signals.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'signals': signals,
                    'total_signals': len(signals)
                }, f, ensure_ascii=False, indent=2)
            
            # ثبت متریک تعداد سیگنال‌ها
            if MONITORING_ENABLED:
                telemetry.record_metric("news.trading_signals", len(signals), MetricType.GAUGE)
                telemetry.record_event(
                    "trading_signals_generated",
                    {"count": len(signals), "signals": signals},
                    "info",
                    "NewsMonitoring"
                )
            
            logger.info(f"🎯 {len(signals)} سیگنال معاملاتی تولید شد")
    
    def save_service_status(self, latest_result):
        """ذخیره وضعیت سرویس"""
        status = {
            'service': 'news_monitoring',
            'status': 'active',
            'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None,
            'total_analyses': self.total_analyses,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self._calculate_success_rate(),
            'error_rate': self._calculate_error_rate(),
            'avg_response_time': sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else 0,
            'active_apis': latest_result.get('active_apis', 0),
            'intelligence_boost': latest_result.get('intelligence_boost', 0),
            'current_signals': len(self.market_signals),
            'crypto_sentiment': latest_result.get('crypto_sentiment', 0.5),
            'stock_sentiment': latest_result.get('stock_sentiment', 0.5),
            'news_analyzed': latest_result.get('total_news_analyzed', 0),
            'monitoring_enabled': MONITORING_ENABLED
        }
        
        with open('news_monitoring_status.json', 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    
    def continuous_monitoring(self):
        """پایش مداوم"""
        logger.info("🚀 سرویس پایش اخبار شروع به کار کرد")
        logger.info(f"⏰ بروزرسانی هر {self.analysis_interval // 60} دقیقه")
        logger.info(f"🔧 مانیتورینگ پیشرفته: {'فعال' if MONITORING_ENABLED else 'غیرفعال'}")
        
        # اجرای اولین تحلیل
        self.run_analysis_cycle()
        
        while self.running:
            try:
                # انتظار تا چرخه بعد
                time.sleep(self.analysis_interval)
                
                # اجرای تحلیل
                self.run_analysis_cycle()
                
            except KeyboardInterrupt:
                logger.info("❌ توقف سرویس پایش اخبار")
                break
            except Exception as e:
                self.error_count += 1
                if MONITORING_ENABLED:
                    telemetry.record_error(
                        AlertLevel.ERROR,
                        f"خطا در سرویس پایش اخبار: {str(e)}",
                        "NewsMonitoring",
                        str(e)
                    )
                logger.error(f"خطا در سرویس: {e}")
                time.sleep(60)  # انتظار 1 دقیقه در صورت خطا
    
    def stop(self):
        """توقف سرویس"""
        self.running = False
        logger.info("🛑 دستور توقف سرویس صادر شد")

def integrate_with_trading_systems():
    """اتصال سیگنال‌های اخبار به سیستم‌های معاملاتی"""
    try:
        # خواندن سیگنال‌های اخبار
        if os.path.exists('news_trading_signals.json'):
            with open('news_trading_signals.json', 'r') as f:
                news_signals = json.load(f)
                
            # ارسال به سیستم معاملاتی
            if news_signals.get('signals'):
                # این قسمت می‌تواند به سیستم‌های معاملاتی متصل شود
                logger.info(f"📡 {len(news_signals['signals'])} سیگنال به سیستم معاملاتی ارسال شد")
                
                # نمونه: ذخیره برای استفاده سایر سیستم‌ها
                with open('integrated_trading_signals.json', 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'news_signals': news_signals['signals'],
                        'integration_status': 'active'
                    }, f, indent=2)
                    
    except Exception as e:
        if MONITORING_ENABLED:
            telemetry.record_error(
                AlertLevel.ERROR,
                f"خطا در اتصال به سیستم معاملاتی: {str(e)}",
                "NewsMonitoring",
                str(e)
            )
        logger.error(f"خطا در اتصال به سیستم معاملاتی: {e}")

def main():
    """اجرای سرویس پایش اخبار"""
    service = AutomatedNewsMonitoringService()
    
    # شروع پایش در thread جداگانه
    monitor_thread = threading.Thread(target=service.continuous_monitoring)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    logger.info("✅ سرویس پایش اخبار فعال شد")
    logger.info("📰 در حال دریافت و تحلیل اخبار از منابع مختلف...")
    
    try:
        # اجرای مداوم
        while True:
            # بروزرسانی اتصال با سیستم‌های معاملاتی
            integrate_with_trading_systems()
            
            # نمایش وضعیت
            if os.path.exists('news_monitoring_status.json'):
                with open('news_monitoring_status.json', 'r') as f:
                    status = json.load(f)
                    print(f"\n📊 وضعیت سرویس - {datetime.now().strftime('%H:%M:%S')}")
                    print(f"   تحلیل‌های انجام شده: {status['total_analyses']}")
                    print(f"   نرخ موفقیت: {status['success_rate']:.1%}")
                    print(f"   نرخ خطا: {status['error_rate']:.1%}")
                    print(f"   میانگین زمان پاسخ: {status['avg_response_time']:.2f}s")
                    print(f"   API های فعال: {status['active_apis']}")
                    print(f"   سیگنال‌های فعال: {status['current_signals']}")
                    print(f"   احساسات کریپتو: {status['crypto_sentiment']:.2%}")
                    print(f"   احساسات سهام: {status['stock_sentiment']:.2%}")
                    print(f"   مانیتورینگ پیشرفته: {status['monitoring_enabled']}")
            
            # انتظار 5 دقیقه
            time.sleep(300)
            
    except KeyboardInterrupt:
        logger.info("🛑 توقف سرویس...")
        service.stop()

if __name__ == "__main__":
    main()
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
from monitoring.persian_reporter import PersianReporter, SystemComponent, ReportLevel

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
        
        # ایجاد گزارشگر فارسی
        self.reporter = PersianReporter(
            SystemComponent.NEWS_MONITORING,
            log_file="monitoring/logs/news_monitoring_fa.log"
        )
        
        self.reporter.success(
            "راه‌اندازی سرویس",
            "سرویس پایش اخبار با گزارشدهی فارسی آماده شد"
        )
        
    def run_analysis_cycle(self):
        """اجرای یک چرخه تحلیل"""
        try:
            self.reporter.info("چرخه تحلیل", "شروع چرخه جدید تحلیل اخبار...")
            
            # تحلیل بازارها
            result = self.news_system.analyze_all_markets()
            self.total_analyses += 1
            self.last_analysis = datetime.now()
            
            # بروزرسانی سطح هوش
            update_intelligence_with_news()
            
            # تولید سیگنال‌های معاملاتی
            self.generate_trading_signals(result)
            
            # ذخیره وضعیت سرویس
            self.save_service_status(result)
            
            self.reporter.success(
                "تکمیل تحلیل",
                f"چرخه تحلیل شماره {self.total_analyses} با موفقیت انجام شد",
                {
                    'cycle_number': self.total_analyses,
                    'analysis_time': self.last_analysis.isoformat(),
                    'signals_generated': len(self.market_signals)
                }
            )
            
        except Exception as e:
            self.reporter.error(
                "خطا در تحلیل",
                f"خطا در چرخه تحلیل: {str(e)}",
                {'error_type': type(e).__name__, 'cycle_number': self.total_analyses}
            )
    
    def generate_trading_signals(self, analysis_result):
        """تولید سیگنال‌های معاملاتی بر اساس اخبار"""
        signals = []
        
        crypto_sentiment = analysis_result.get('crypto_sentiment', 0.5)
        stock_sentiment = analysis_result.get('stock_sentiment', 0.5)
        
        # سیگنال‌های کریپتو
        if crypto_sentiment > 0.75:
            signal = {
                'market': 'crypto',
                'action': 'BUY',
                'strength': 'قوی',
                'sentiment': crypto_sentiment,
                'reason': 'احساسات بسیار مثبت در اخبار'
            }
            signals.append(signal)
            self.reporter.success(
                "سیگنال خرید کریپتو",
                f"سیگنال خرید قوی تولید شد - احساسات: {crypto_sentiment:.2%}",
                signal
            )
        elif crypto_sentiment < 0.25:
            signal = {
                'market': 'crypto',
                'action': 'SELL',
                'strength': 'قوی',
                'sentiment': crypto_sentiment,
                'reason': 'احساسات بسیار منفی در اخبار'
            }
            signals.append(signal)
            self.reporter.warning(
                "سیگنال فروش کریپتو",
                f"سیگنال فروش قوی تولید شد - احساسات: {crypto_sentiment:.2%}",
                signal
            )
        
        # سیگنال‌های سهام
        if stock_sentiment > 0.75:
            signal = {
                'market': 'stocks',
                'action': 'BUY',
                'strength': 'قوی',
                'sentiment': stock_sentiment,
                'reason': 'اخبار مثبت بازار سهام'
            }
            signals.append(signal)
            self.reporter.success(
                "سیگنال خرید سهام",
                f"سیگنال خرید قوی برای سهام - احساسات: {stock_sentiment:.2%}",
                signal
            )
        elif stock_sentiment < 0.25:
            signal = {
                'market': 'stocks',
                'action': 'SELL',
                'strength': 'قوی',
                'sentiment': stock_sentiment,
                'reason': 'اخبار منفی بازار سهام'
            }
            signals.append(signal)
            self.reporter.warning(
                "سیگنال فروش سهام",
                f"سیگنال فروش قوی برای سهام - احساسات: {stock_sentiment:.2%}",
                signal
            )
        
        # ذخیره سیگنال‌ها
        if signals:
            self.market_signals = signals
            with open('news_trading_signals.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'signals': signals,
                    'total_signals': len(signals)
                }, f, ensure_ascii=False, indent=2)
            
            self.reporter.info(
                "ذخیره سیگنال‌ها",
                f"{len(signals)} سیگنال معاملاتی تولید و ذخیره شد",
                {'signals_count': len(signals), 'signals': signals}
            )
        else:
            self.reporter.info(
                "عدم تولید سیگنال",
                "شرایط بازار مناسب تولید سیگنال نبود",
                {'crypto_sentiment': crypto_sentiment, 'stock_sentiment': stock_sentiment}
            )
    
    def save_service_status(self, latest_result):
        """ذخیره وضعیت سرویس"""
        status = {
            'service': 'news_monitoring',
            'status': 'active',
            'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None,
            'total_analyses': self.total_analyses,
            'active_apis': latest_result.get('active_apis', 0),
            'intelligence_boost': latest_result.get('intelligence_boost', 0),
            'current_signals': len(self.market_signals),
            'crypto_sentiment': latest_result.get('crypto_sentiment', 0.5),
            'stock_sentiment': latest_result.get('stock_sentiment', 0.5),
            'news_analyzed': latest_result.get('total_news_analyzed', 0)
        }
        
        with open('news_monitoring_status.json', 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    
    def continuous_monitoring(self):
        """پایش مداوم"""
        logger.info("🚀 سرویس پایش اخبار شروع به کار کرد")
        logger.info(f"⏰ بروزرسانی هر {self.analysis_interval // 60} دقیقه")
        
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
                logger.error(f"خطا در سرویس: {e}")
                time.sleep(60)  # انتظار 1 دقیقه در صورت خطا
    
    def stop(self):
        """توقف سرویس"""
        self.running = False
        self.reporter.info("توقف سرویس", "دستور توقف سرویس صادر شد")
        logger.info("🛑 دستور توقف سرویس صادر شد")
    
    def create_comprehensive_report(self):
        """ایجاد گزارش جامع عملکرد سرویس"""
        try:
            report_data = {
                'total_analyses': self.total_analyses,
                'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None,
                'active_signals': len(self.market_signals),
                'service_status': 'فعال' if self.running else 'متوقف',
                'analysis_interval_minutes': self.analysis_interval // 60
            }
            
            # خواندن آخرین وضعیت
            try:
                with open('news_monitoring_status.json', 'r', encoding='utf-8') as f:
                    status = json.load(f)
                    report_data.update(status)
            except FileNotFoundError:
                pass
            
            self.reporter.info(
                "گزارش جامع سرویس",
                f"تحلیل‌های انجام شده: {self.total_analyses}، سیگنال‌های فعال: {len(self.market_signals)}",
                report_data
            )
            
            return report_data
            
        except Exception as e:
            self.reporter.error(
                "خطا در گزارش",
                f"خطا در ایجاد گزارش جامع: {str(e)}"
            )
            return {}

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
                    print(f"   API های فعال: {status['active_apis']}")
                    print(f"   سیگنال‌های فعال: {status['current_signals']}")
                    print(f"   احساسات کریپتو: {status['crypto_sentiment']:.2%}")
                    print(f"   احساسات سهام: {status['stock_sentiment']:.2%}")
            
            # انتظار 5 دقیقه
            time.sleep(300)
            
    except KeyboardInterrupt:
        logger.info("🛑 توقف سرویس...")
        service.stop()

if __name__ == "__main__":
    main()
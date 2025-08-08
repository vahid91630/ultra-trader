#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم جمع‌آوری و تحلیل داده‌های روزانه با انتقال شبانه به MongoDB
"""

import os
import json
import sqlite3
from datetime import datetime, time, timedelta
import schedule
import threading
import logging
import time as time_module
from typing import Dict, List, Any
import numpy as np
from openai import OpenAI

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

class DailyDataCollectionSystem:
    def __init__(self):
        self.temp_db = 'temp_daily_data.db'
        self.analysis_db = 'daily_analysis.db'
        self.mongodb_queue = 'mongodb_queue.json'
        
        # ساعت انتقال به MongoDB (23:30)
        self.transfer_time = time(23, 30)
        
        # امتیازدهی و وزن‌ها
        self.scoring_weights = {
            'price_movement': 0.25,
            'volume': 0.20,
            'news_sentiment': 0.20,
            'technical_indicators': 0.15,
            'ai_prediction': 0.20
        }
        
        # متریک‌های عملکردی
        self.data_collection_count = 0
        self.analysis_count = 0
        self.mongodb_transfers = 0
        self.last_collection_errors = []
        self.database_sizes = {}
        
        # مقداردهی اولیه
        self._initialize_databases()
        self.openai_client = OpenAI() if os.environ.get('OPENAI_API_KEY') else None
        
        # تنظیم مانیتورینگ
        if MONITORING_ENABLED:
            self._setup_monitoring()
    
    def _setup_monitoring(self):
        """تنظیم سیستم مانیتورینگ برای جمع‌آوری داده‌ها"""
        try:
            # قانون هشدار برای اندازه بالای دیتابیس
            db_size_rule = AlertRule(
                id="database_size_warning",
                name="اندازه بالای دیتابیس",
                alert_type=AlertType.CUSTOM,
                condition="temp_db_size_mb > 100",  # بیش از 100 مگابایت
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.LOG],
                cooldown_minutes=60
            )
            alert_system.add_rule(db_size_rule)
            
            # قانون هشدار برای خطاهای جمع‌آوری
            collection_error_rule = AlertRule(
                id="data_collection_errors",
                name="خطاهای زیاد در جمع‌آوری داده",
                alert_type=AlertType.CUSTOM,
                condition="collection_error_rate > 0.1",  # بیش از 10% خطا
                severity=AlertLevel.ERROR,
                channels=[NotificationChannel.LOG],
                cooldown_minutes=30
            )
            alert_system.add_rule(collection_error_rule)
            
            # قانون هشدار برای عدم انتقال MongoDB
            mongodb_transfer_rule = AlertRule(
                id="mongodb_transfer_failed",
                name="مشکل در انتقال به MongoDB",
                alert_type=AlertType.CUSTOM,
                condition="hours_since_last_transfer > 25",  # بیش از 25 ساعت
                severity=AlertLevel.CRITICAL,
                channels=[NotificationChannel.LOG],
                cooldown_minutes=120
            )
            alert_system.add_rule(mongodb_transfer_rule)
            
            logger.info("🔧 مانیتورینگ پیشرفته برای جمع‌آوری داده‌ها فعال شد")
            
        except Exception as e:
            logger.error(f"خطا در تنظیم مانیتورینگ: {e}")
    
    def _initialize_databases(self):
        """ایجاد جداول موقت برای داده‌های روزانه"""
        # دیتابیس موقت روزانه
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        # جدول داده‌های خام
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                data_type TEXT,
                market TEXT,
                symbol TEXT,
                data JSON,
                processed BOOLEAN DEFAULT 0
            )
        ''')
        
        # جدول تحلیل‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                analysis_type TEXT,
                score REAL,
                details JSON
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # دیتابیس تحلیل‌های نهایی
        conn = sqlite3.connect(self.analysis_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                symbol TEXT,
                final_score REAL,
                recommendation TEXT,
                analysis JSON,
                transferred_to_mongodb BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @log_function_performance
    def collect_market_data(self, symbol: str, market: str) -> Dict:
        """جمع‌آوری داده‌های بازار"""
        start_time = time_module.time()
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'market': market,
                'price': np.random.uniform(100, 50000),  # شبیه‌سازی قیمت
                'volume': np.random.uniform(1000, 100000),
                'change_24h': np.random.uniform(-10, 10),
                'high_24h': np.random.uniform(100, 51000),
                'low_24h': np.random.uniform(99, 49000)
            }
            
            # ذخیره در دیتابیس موقت
            conn = sqlite3.connect(self.temp_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO raw_data (timestamp, data_type, market, symbol, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data['timestamp'],
                'market_data',
                market,
                symbol,
                json.dumps(data)
            ))
            
            conn.commit()
            conn.close()
            
            # شمارش موفق
            self.data_collection_count += 1
            collection_time = time_module.time() - start_time
            
            # ثبت متریک‌ها
            if MONITORING_ENABLED:
                telemetry.record_metric("data_collection.count", self.data_collection_count, MetricType.COUNTER)
                telemetry.record_metric("data_collection.time", collection_time, MetricType.TIMER)
                telemetry.record_metric(f"market_data.{market}.{symbol}.price", data['price'], MetricType.GAUGE)
                telemetry.record_metric(f"market_data.{market}.{symbol}.volume", data['volume'], MetricType.GAUGE)
                
                # بررسی اندازه دیتابیس
                self._check_database_sizes()
            
            logger.info(f"📊 داده بازار جمع‌آوری شد: {symbol} - قیمت: ${data['price']:.2f}")
            return data
            
        except Exception as e:
            # ثبت خطا
            self.last_collection_errors.append({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'market': market,
                'error': str(e)
            })
            
            # حفظ حداکثر 100 خطای اخیر
            if len(self.last_collection_errors) > 100:
                self.last_collection_errors.pop(0)
            
            if MONITORING_ENABLED:
                telemetry.record_error(
                    AlertLevel.ERROR,
                    f"خطا در جمع‌آوری داده {symbol}: {str(e)}",
                    "DataCollection",
                    str(e)
                )
                
                # بررسی نرخ خطا
                error_rate = len(self.last_collection_errors) / max(self.data_collection_count, 1)
                telemetry.record_metric("data_collection.error_rate", error_rate, MetricType.GAUGE)
            
            logger.error(f"خطا در جمع‌آوری داده {symbol}: {e}")
            raise
    
    def _check_database_sizes(self):
        """بررسی اندازه دیتابیس‌ها"""
        try:
            temp_db_size = os.path.getsize(self.temp_db) if os.path.exists(self.temp_db) else 0
            analysis_db_size = os.path.getsize(self.analysis_db) if os.path.exists(self.analysis_db) else 0
            
            self.database_sizes = {
                'temp_db_size_bytes': temp_db_size,
                'temp_db_size_mb': temp_db_size / (1024 * 1024),
                'analysis_db_size_bytes': analysis_db_size,
                'analysis_db_size_mb': analysis_db_size / (1024 * 1024)
            }
            
            # ثبت متریک‌ها
            telemetry.record_metric("database.temp_size_mb", self.database_sizes['temp_db_size_mb'], MetricType.GAUGE)
            telemetry.record_metric("database.analysis_size_mb", self.database_sizes['analysis_db_size_mb'], MetricType.GAUGE)
            
            # بررسی هشدار اندازه
            if self.database_sizes['temp_db_size_mb'] > 100:
                telemetry.record_error(
                    AlertLevel.WARNING,
                    f"اندازه دیتابیس موقت بالا است: {self.database_sizes['temp_db_size_mb']:.1f} MB",
                    "DataCollection"
                )
                
        except Exception as e:
            logger.error(f"خطا در بررسی اندازه دیتابیس: {e}")
    
    @log_function_performance
    def analyze_and_score(self, symbol: str) -> Dict:
        """تحلیل و امتیازدهی داده‌ها"""
        try:
            conn = sqlite3.connect(self.temp_db)
            cursor = conn.cursor()
            
            # دریافت داده‌های خام امروز
            cursor.execute('''
                SELECT data FROM raw_data 
                WHERE symbol = ? AND DATE(timestamp) = DATE('now')
                AND processed = 0
            ''', (symbol,))
            
            raw_data = cursor.fetchall()
            
            if not raw_data:
                return {}
            
            # محاسبه امتیازات
            scores = {
                'price_movement': self._calculate_price_score(raw_data),
                'volume': self._calculate_volume_score(raw_data),
                'news_sentiment': self._calculate_news_sentiment(symbol),
                'technical_indicators': self._calculate_technical_score(raw_data),
                'ai_prediction': self._get_ai_prediction_score(symbol, raw_data)
            }
            
            # محاسبه امتیاز نهایی
            final_score = sum(
                scores[key] * self.scoring_weights[key] 
                for key in scores
            )
            
            # تعیین توصیه
            if final_score >= 80:
                recommendation = "خرید قوی"
            elif final_score >= 65:
                recommendation = "خرید"
            elif final_score >= 50:
                recommendation = "نگهداری"
            elif final_score >= 35:
                recommendation = "فروش"
            else:
                recommendation = "فروش قوی"
            
            analysis_result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'scores': scores,
                'final_score': final_score,
                'recommendation': recommendation,
                'data_points_analyzed': len(raw_data)
            }
            
            # ذخیره نتیجه تحلیل
            cursor.execute('''
                INSERT INTO analysis_results (timestamp, symbol, analysis_type, score, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                analysis_result['timestamp'],
                symbol,
                'comprehensive',
                final_score,
                json.dumps(analysis_result)
            ))
            
            # علامت‌گذاری داده‌های پردازش شده
            cursor.execute('''
                UPDATE raw_data SET processed = 1 
                WHERE symbol = ? AND DATE(timestamp) = DATE('now')
            ''', (symbol,))
            
            conn.commit()
            conn.close()
            
            # شمارش تحلیل‌ها
            self.analysis_count += 1
            
            # ثبت متریک‌ها
            if MONITORING_ENABLED:
                telemetry.record_metric("analysis.count", self.analysis_count, MetricType.COUNTER)
                telemetry.record_metric(f"analysis.{symbol}.final_score", final_score, MetricType.GAUGE)
                telemetry.record_metric("analysis.data_points", len(raw_data), MetricType.GAUGE)
                
                telemetry.record_event(
                    "analysis_completed",
                    {
                        "symbol": symbol,
                        "final_score": final_score,
                        "recommendation": recommendation,
                        "data_points": len(raw_data)
                    },
                    "info",
                    "DataAnalysis"
                )
            
            logger.info(f"✅ تحلیل {symbol}: امتیاز {final_score:.1f} - {recommendation}")
            return analysis_result
            
        except Exception as e:
            if MONITORING_ENABLED:
                telemetry.record_error(
                    AlertLevel.ERROR,
                    f"خطا در تحلیل {symbol}: {str(e)}",
                    "DataAnalysis",
                    str(e)
                )
            logger.error(f"خطا در تحلیل {symbol}: {e}")
            return {}
    
    def _calculate_price_score(self, raw_data: List) -> float:
        """محاسبه امتیاز حرکت قیمت"""
        prices = []
        for row in raw_data:
            data = json.loads(row[0])
            prices.append(data['price'])
        
        if len(prices) < 2:
            return 50
        
        # محاسبه روند
        price_change = (prices[-1] - prices[0]) / prices[0] * 100
        
        # امتیازدهی بر اساس روند
        if price_change > 5:
            return 90
        elif price_change > 2:
            return 75
        elif price_change > -2:
            return 50
        elif price_change > -5:
            return 25
        else:
            return 10
    
    def _calculate_volume_score(self, raw_data: List) -> float:
        """محاسبه امتیاز حجم معاملات"""
        volumes = []
        for row in raw_data:
            data = json.loads(row[0])
            volumes.append(data['volume'])
        
        if not volumes:
            return 50
        
        # میانگین حجم
        avg_volume = np.mean(volumes)
        recent_volume = volumes[-1] if volumes else 0
        
        # امتیازدهی بر اساس حجم
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio > 2:
            return 95
        elif volume_ratio > 1.5:
            return 80
        elif volume_ratio > 1:
            return 60
        elif volume_ratio > 0.7:
            return 40
        else:
            return 20
    
    def _calculate_news_sentiment(self, symbol: str) -> float:
        """محاسبه احساسات خبری"""
        # شبیه‌سازی احساسات خبری
        # در حالت واقعی از NewsAPI استفاده می‌شود
        return np.random.uniform(30, 80)
    
    def _calculate_technical_score(self, raw_data: List) -> float:
        """محاسبه امتیاز اندیکاتورهای تکنیکال"""
        if not raw_data:
            return 50
        
        # محاسبه RSI, MACD, etc.
        # فعلاً شبیه‌سازی
        return np.random.uniform(40, 85)
    
    def _get_ai_prediction_score(self, symbol: str, raw_data: List) -> float:
        """دریافت امتیاز پیش‌بینی AI"""
        if not self.openai_client or not raw_data:
            return 50
        
        try:
            # آماده‌سازی داده‌ها برای AI
            recent_data = json.loads(raw_data[-1][0]) if raw_data else {}
            
            prompt = f"""
            بر اساس داده‌های زیر برای {symbol}، یک امتیاز از 0 تا 100 برای احتمال رشد قیمت بده:
            - قیمت فعلی: ${recent_data.get('price', 0):.2f}
            - تغییر 24 ساعته: {recent_data.get('change_24h', 0):.2f}%
            - حجم معاملات: {recent_data.get('volume', 0):.0f}
            
            فقط عدد را برگردان.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            
            score = float(response.choices[0].message.content.strip())
            return min(max(score, 0), 100)
        except:
            return 50
    
    @log_function_performance
    def transfer_to_mongodb(self):
        """انتقال داده‌ها به MongoDB در پایان شب"""
        logger.info("🌙 شروع انتقال داده‌ها به MongoDB...")
        
        # بررسی اتصال MongoDB
        mongodb_uri = os.environ.get('MONGODB_URI')
        if not mongodb_uri:
            logger.warning("⚠️ MongoDB URI تنظیم نشده - ذخیره در صف")
            self._save_to_queue()
            return
        
        try:
            from pymongo import MongoClient
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            db = client['ultra_plus_bot']
            
            # انتقال خلاصه‌های روزانه
            conn = sqlite3.connect(self.analysis_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM daily_summaries
                WHERE transferred_to_mongodb = 0
            ''')
            
            summaries = cursor.fetchall()
            
            if summaries:
                # تبدیل به فرمت MongoDB
                documents = []
                for summary in summaries:
                    doc = {
                        '_id': f"{summary[1]}_{summary[2]}",  # date_symbol
                        'date': summary[1],
                        'symbol': summary[2],
                        'final_score': summary[3],
                        'recommendation': summary[4],
                        'analysis': json.loads(summary[5]),
                        'created_at': datetime.now()
                    }
                    documents.append(doc)
                
                # درج در MongoDB
                collection = db['daily_analysis']
                result = collection.insert_many(documents, ordered=False)
                
                # علامت‌گذاری انتقال موفق
                for summary in summaries:
                    cursor.execute('''
                        UPDATE daily_summaries SET transferred_to_mongodb = 1
                        WHERE id = ?
                    ''', (summary[0],))
                
                conn.commit()
                
                # شمارش انتقال‌ها
                self.mongodb_transfers += 1
                
                # ثبت متریک‌ها
                if MONITORING_ENABLED:
                    telemetry.record_metric("mongodb.transfers", self.mongodb_transfers, MetricType.COUNTER)
                    telemetry.record_metric("mongodb.documents_transferred", len(result.inserted_ids), MetricType.GAUGE)
                    
                    telemetry.record_event(
                        "mongodb_transfer_completed",
                        {
                            "documents_count": len(result.inserted_ids),
                            "transfer_number": self.mongodb_transfers
                        },
                        "info",
                        "DataTransfer"
                    )
                
                logger.info(f"✅ {len(result.inserted_ids)} سند به MongoDB منتقل شد")
            
            # پاکسازی داده‌های موقت
            self._cleanup_temp_data()
            
            client.close()
            conn.close()
            
        except Exception as e:
            if MONITORING_ENABLED:
                telemetry.record_error(
                    AlertLevel.ERROR,
                    f"خطا در انتقال به MongoDB: {str(e)}",
                    "DataTransfer",
                    str(e)
                )
            logger.error(f"❌ خطا در انتقال به MongoDB: {e}")
            self._save_to_queue()
    
    def _save_to_queue(self):
        """ذخیره در صف برای انتقال بعدی"""
        conn = sqlite3.connect(self.analysis_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_summaries
            WHERE transferred_to_mongodb = 0
        ''')
        
        summaries = cursor.fetchall()
        
        queue_data = []
        for summary in summaries:
            queue_data.append({
                'date': summary[1],
                'symbol': summary[2],
                'final_score': summary[3],
                'recommendation': summary[4],
                'analysis': json.loads(summary[5])
            })
        
        # ذخیره در فایل JSON
        with open(self.mongodb_queue, 'w', encoding='utf-8') as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 {len(queue_data)} رکورد در صف MongoDB ذخیره شد")
        conn.close()
    
    def _cleanup_temp_data(self):
        """پاکسازی داده‌های موقت"""
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        # پاک کردن داده‌های پردازش شده بیش از 1 روز
        cursor.execute('''
            DELETE FROM raw_data 
            WHERE processed = 1 AND 
            datetime(timestamp) < datetime('now', '-1 day')
        ''')
        
        cursor.execute('''
            DELETE FROM analysis_results
            WHERE datetime(timestamp) < datetime('now', '-1 day')
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("🧹 داده‌های موقت پاکسازی شد")
    
    def prepare_daily_summary(self):
        """آماده‌سازی خلاصه روزانه برای انتقال به MongoDB"""
        conn_temp = sqlite3.connect(self.temp_db)
        conn_analysis = sqlite3.connect(self.analysis_db)
        
        cursor_temp = conn_temp.cursor()
        cursor_analysis = conn_analysis.cursor()
        
        # دریافت تمام تحلیل‌های امروز
        cursor_temp.execute('''
            SELECT DISTINCT symbol FROM analysis_results
            WHERE DATE(timestamp) = DATE('now')
        ''')
        
        symbols = cursor_temp.fetchall()
        
        for (symbol,) in symbols:
            # دریافت آخرین تحلیل هر سمبل
            cursor_temp.execute('''
                SELECT score, details FROM analysis_results
                WHERE symbol = ? AND DATE(timestamp) = DATE('now')
                ORDER BY timestamp DESC LIMIT 1
            ''', (symbol,))
            
            result = cursor_temp.fetchone()
            if result:
                score, details = result
                
                # ذخیره خلاصه روزانه
                cursor_analysis.execute('''
                    INSERT INTO daily_summaries (date, symbol, final_score, recommendation, analysis)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().date().isoformat(),
                    symbol,
                    score,
                    json.loads(details).get('recommendation', ''),
                    details
                ))
        
        conn_analysis.commit()
        conn_temp.close()
        conn_analysis.close()
        
        logger.info("📋 خلاصه روزانه آماده شد")
    
    def get_system_status(self) -> Dict[str, Any]:
        """دریافت وضعیت سیستم"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'data_collection_count': self.data_collection_count,
            'analysis_count': self.analysis_count,
            'mongodb_transfers': self.mongodb_transfers,
            'recent_errors_count': len(self.last_collection_errors),
            'database_sizes': self.database_sizes,
            'monitoring_enabled': MONITORING_ENABLED,
            'openai_available': self.openai_client is not None,
            'last_mongodb_transfer': None  # TODO: track this
        }
        
        # محاسبه نرخ خطا
        if self.data_collection_count > 0:
            status['error_rate'] = len(self.last_collection_errors) / self.data_collection_count
        else:
            status['error_rate'] = 0
        
        return status
    
    def start_collection_cycle(self):
        """شروع چرخه جمع‌آوری و تحلیل"""
        logger.info("🚀 سیستم جمع‌آوری داده‌های روزانه فعال شد")
        logger.info(f"🔧 مانیتورینگ پیشرفته: {'فعال' if MONITORING_ENABLED else 'غیرفعال'}")
        
        # برنامه‌ریزی جمع‌آوری داده‌ها (هر 5 دقیقه)
        schedule.every(5).minutes.do(self._collect_all_markets)
        
        # برنامه‌ریزی تحلیل (هر 30 دقیقه)
        schedule.every(30).minutes.do(self._analyze_all_symbols)
        
        # برنامه‌ریزی خلاصه روزانه (ساعت 23:00)
        schedule.every().day.at("23:00").do(self.prepare_daily_summary)
        
        # برنامه‌ریزی انتقال به MongoDB (ساعت 23:30)
        schedule.every().day.at("23:30").do(self.transfer_to_mongodb)
        
        # اجرای اولیه
        self._collect_all_markets()
        
        # حلقه اصلی
        while True:
            schedule.run_pending()
            time_module.sleep(60)
    
    def _collect_all_markets(self):
        """جمع‌آوری از تمام بازارها"""
        markets = [
            ('BTC/USDT', 'crypto'),
            ('ETH/USDT', 'crypto'),
            ('AAPL', 'stock'),
            ('GOOGL', 'stock'),
            ('EUR/USD', 'forex'),
            ('GOLD', 'commodity')
        ]
        
        for symbol, market in markets:
            try:
                self.collect_market_data(symbol, market)
            except Exception as e:
                logger.error(f"خطا در جمع‌آوری {symbol}: {e}")
    
    def _analyze_all_symbols(self):
        """تحلیل تمام سمبل‌ها"""
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT symbol FROM raw_data WHERE processed = 0')
        symbols = cursor.fetchall()
        
        for (symbol,) in symbols:
            try:
                self.analyze_and_score(symbol)
            except Exception as e:
                logger.error(f"خطا در تحلیل {symbol}: {e}")
        
        conn.close()

# نمونه استفاده
if __name__ == "__main__":
    collector = DailyDataCollectionSystem()
    
    # تست جمع‌آوری و تحلیل
    try:
        collector.collect_market_data('BTC/USDT', 'crypto')
        result = collector.analyze_and_score('BTC/USDT')
        
        if result:
            print(f"\n📊 نتیجه تحلیل {result['symbol']}:")
            print(f"امتیاز نهایی: {result['final_score']:.1f}")
            print(f"توصیه: {result['recommendation']}")
        
        # نمایش وضعیت سیستم
        status = collector.get_system_status()
        print(f"\n🔧 وضعیت سیستم:")
        print(f"   جمع‌آوری داده‌ها: {status['data_collection_count']}")
        print(f"   تحلیل‌ها: {status['analysis_count']}")
        print(f"   نرخ خطا: {status['error_rate']:.1%}")
        print(f"   مانیتورینگ پیشرفته: {status['monitoring_enabled']}")
        
    except Exception as e:
        logger.error(f"خطا در تست: {e}")
    
    # برای اجرای کامل:
    # collector.start_collection_cycle()
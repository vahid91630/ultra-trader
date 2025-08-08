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
        
        # مقداردهی اولیه
        self._initialize_databases()
        self.openai_client = OpenAI() if os.environ.get('OPENAI_API_KEY') else None
    
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
    
    def collect_market_data(self, symbol: str, market: str) -> Dict:
        """جمع‌آوری داده‌های بازار"""
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
        
        logger.info(f"📊 داده بازار جمع‌آوری شد: {symbol} - قیمت: ${data['price']:.2f}")
        return data
    
    def analyze_and_score(self, symbol: str) -> Dict:
        """تحلیل و امتیازدهی داده‌ها"""
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
        
        logger.info(f"✅ تحلیل {symbol}: امتیاز {final_score:.1f} - {recommendation}")
        return analysis_result
    
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
    
    def transfer_to_mongodb(self):
        """انتقال داده‌ها به MongoDB در پایان شب با مدیریت بهتر خطا"""
        logger.info("🌙 شروع انتقال داده‌ها به MongoDB...")
        
        # بررسی اتصال MongoDB
        mongodb_uri = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')
        if not mongodb_uri:
            logger.error("❌ هیچ‌کدام از متغیرهای MONGODB_URI یا MONGO_URI تنظیم نشده")
            logger.info("💡 برای تنظیم متغیر محیطی:")
            logger.info("   - MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database")
            logger.info("   - یا MONGO_URI=mongodb://localhost:27017/ultra_trader")
            logger.info("   - یا در فایل .env تنظیم کنید")
            self._save_to_queue("متغیر محیطی MongoDB تنظیم نشده")
            return
        
        try:
            from pymongo import MongoClient
            from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
            
            logger.info("🔌 در حال اتصال به MongoDB...")
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
            
            # تست اتصال
            client.admin.command('ping')
            logger.info("✅ اتصال MongoDB برقرار شد")
            
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
                        'created_at': datetime.now(),
                        'transfer_timestamp': datetime.now().isoformat()
                    }
                    documents.append(doc)
                
                # درج در MongoDB
                collection = db['daily_analysis']
                try:
                    result = collection.insert_many(documents, ordered=False)
                    logger.info(f"✅ {len(result.inserted_ids)} سند به MongoDB منتقل شد")
                    
                    # علامت‌گذاری انتقال موفق
                    for summary in summaries:
                        cursor.execute('''
                            UPDATE daily_summaries SET transferred_to_mongodb = 1
                            WHERE id = ?
                        ''', (summary[0],))
                    
                    conn.commit()
                    
                except Exception as insert_error:
                    logger.error(f"❌ خطا در درج داده‌ها: {insert_error}")
                    self._save_to_queue(f"خطا در درج: {str(insert_error)}")
            else:
                logger.info("ℹ️ هیچ داده‌ای برای انتقال موجود نیست")
            
            # پاکسازی داده‌های موقت
            self._cleanup_temp_data()
            
            client.close()
            conn.close()
            
        except ImportError:
            logger.error("❌ کتابخانه pymongo نصب نیست")
            logger.info("💡 برای نصب: pip install pymongo")
            self._save_to_queue("pymongo نصب نیست")
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"🕐 Timeout در اتصال به MongoDB: {e}")
            logger.info("💡 بررسی کنید:")
            logger.info("   - اتصال اینترنت")
            logger.info("   - دسترسی به سرور MongoDB")
            logger.info("   - صحت آدرس سرور")
            self._save_to_queue(f"Timeout اتصال: {str(e)}")
            
        except ConfigurationError as e:
            logger.error(f"⚙️ خطای پیکربندی MongoDB: {e}")
            logger.info("💡 بررسی کنید:")
            logger.info("   - فرمت URI صحیح باشد")
            logger.info("   - نام کاربری و رمز عبور")
            self._save_to_queue(f"خطای پیکربندی: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره در انتقال به MongoDB: {e}")
            logger.info(f"🔧 جزئیات: نوع خطا {type(e).__name__}")
            self._save_to_queue(f"خطای غیرمنتظره: {str(e)}")
    
    def _save_to_queue(self, error_reason="خطای نامشخص"):
        """ذخیره در صف برای انتقال بعدی با اطلاعات بیشتر"""
        logger.info(f"💾 ذخیره داده‌ها در صف (دلیل: {error_reason})")
        
        conn = sqlite3.connect(self.analysis_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_summaries
            WHERE transferred_to_mongodb = 0
        ''')
        
        summaries = cursor.fetchall()
        
        queue_data = {
            'error_reason': error_reason,
            'timestamp': datetime.now().isoformat(),
            'retry_count': 0,
            'data': []
        }
        
        for summary in summaries:
            queue_data['data'].append({
                'date': summary[1],
                'symbol': summary[2],
                'final_score': summary[3],
                'recommendation': summary[4],
                'analysis': json.loads(summary[5])
            })
        
        # خواندن صف قدیمی و اضافه کردن به آن
        try:
            with open(self.mongodb_queue, 'r', encoding='utf-8') as f:
                existing_queue = json.load(f)
                if isinstance(existing_queue, list):
                    # فرمت قدیمی - تبدیل به فرمت جدید
                    queue_data['data'].extend(existing_queue)
                elif isinstance(existing_queue, dict):
                    # فرمت جدید - اضافه کردن داده‌ها
                    queue_data['data'].extend(existing_queue.get('data', []))
                    queue_data['retry_count'] = existing_queue.get('retry_count', 0) + 1
        except (FileNotFoundError, json.JSONDecodeError):
            # فایل وجود ندارد یا فرمت اشتباه - ادامه با داده‌های جدید
            pass
        
        # ذخیره صف بروزرسانی شده
        with open(self.mongodb_queue, 'w', encoding='utf-8') as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 {len(queue_data['data'])} رکورد در صف MongoDB ذخیره شد (تلاش #{queue_data['retry_count']})")
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
    
    def start_collection_cycle(self):
        """شروع چرخه جمع‌آوری و تحلیل"""
        logger.info("🚀 سیستم جمع‌آوری داده‌های روزانه فعال شد")
        
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
            self.collect_market_data(symbol, market)
    
    def _analyze_all_symbols(self):
        """تحلیل تمام سمبل‌ها"""
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT symbol FROM raw_data WHERE processed = 0')
        symbols = cursor.fetchall()
        
        for (symbol,) in symbols:
            self.analyze_and_score(symbol)
        
        conn.close()

# نمونه استفاده
if __name__ == "__main__":
    collector = DailyDataCollectionSystem()
    
    # تست جمع‌آوری و تحلیل
    collector.collect_market_data('BTC/USDT', 'crypto')
    result = collector.analyze_and_score('BTC/USDT')
    
    if result:
        print(f"\n📊 نتیجه تحلیل {result['symbol']}:")
        print(f"امتیاز نهایی: {result['final_score']:.1f}")
        print(f"توصیه: {result['recommendation']}")
        
    # برای اجرای کامل:
    # collector.start_collection_cycle()
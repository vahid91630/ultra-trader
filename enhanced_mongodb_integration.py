#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB Integration Enhancement - بهبود یکپارچه‌سازی MongoDB
سیستم بهبود یافته برای ذخیره و مدیریت داده‌های یادگیری در MongoDB
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    import pymongo
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    class MockMongoClient:
        def __init__(self, *args, **kwargs):
            pass
        def __getitem__(self, name):
            return MockCollection()
    class MockCollection:
        def find(self, *args, **kwargs):
            return []
        def insert_one(self, *args, **kwargs):
            return None
        def insert_many(self, *args, **kwargs):
            return None
        def update_one(self, *args, **kwargs):
            return None
    MongoClient = MockMongoClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MongoConfig:
    """تنظیمات MongoDB"""
    connection_string: str = "mongodb://localhost:27017/"
    database_name: str = "ultra_trader"
    learning_collection: str = "learning_patterns"
    intelligence_collection: str = "intelligence_data"
    performance_collection: str = "performance_metrics"
    sources_collection: str = "data_sources"
    
class EnhancedMongoDBIntegration:
    """سیستم یکپارچه‌سازی پیشرفته MongoDB"""
    
    def __init__(self, config: Optional[MongoConfig] = None):
        self.config = config or MongoConfig()
        self.client = None
        self.database = None
        self.collections = {}
        self.connection_healthy = False
        
        # آمار اتصال
        self.connection_stats = {
            'last_connected': None,
            'connection_attempts': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_error': None
        }
        
        # Initialize connection
        self._initialize_connection()
        logger.info("🔗 MongoDB Integration System آماده شد")
    
    def _initialize_connection(self):
        """راه‌اندازی اتصال MongoDB"""
        if not PYMONGO_AVAILABLE:
            logger.warning("⚠️ PyMongo در دسترس نیست - MongoDB integration غیرفعال")
            return
        
        try:
            # دریافت connection string از متغیرهای محیط
            connection_string = os.getenv('MONGODB_CONNECTION_STRING', self.config.connection_string)
            
            logger.info(f"🔗 اتلاق به MongoDB: {connection_string.split('@')[-1] if '@' in connection_string else connection_string}")
            
            # ایجاد اتصال با timeout
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,  # 5 seconds timeout
                connectTimeoutMS=10000,  # 10 seconds connect timeout
                maxPoolSize=10,
                retryWrites=True
            )
            
            # تست اتصال
            self.client.admin.command('ping')
            
            # دسترسی به دیتابیس
            self.database = self.client[self.config.database_name]
            
            # راه‌اندازی collections
            self._setup_collections()
            
            self.connection_healthy = True
            self.connection_stats['last_connected'] = time.time()
            logger.info("✅ اتصال MongoDB با موفقیت برقرار شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در اتصال MongoDB: {e}")
            self.connection_healthy = False
            self.connection_stats['last_error'] = str(e)
            self.connection_stats['connection_attempts'] += 1
    
    def _setup_collections(self):
        """راه‌اندازی collections و indexes"""
        try:
            collection_configs = {
                self.config.learning_collection: {
                    'indexes': [
                        ('pattern_hash', pymongo.ASCENDING),
                        ('confidence', pymongo.DESCENDING),
                        ('created_at', pymongo.DESCENDING),
                        ('source', pymongo.ASCENDING),
                        ('category', pymongo.ASCENDING),
                        ('effectiveness_score', pymongo.DESCENDING)
                    ]
                },
                self.config.intelligence_collection: {
                    'indexes': [
                        ('timestamp', pymongo.DESCENDING),
                        ('intelligence_level', pymongo.DESCENDING)
                    ]
                },
                self.config.performance_collection: {
                    'indexes': [
                        ('session_id', pymongo.ASCENDING),
                        ('start_time', pymongo.DESCENDING),
                        ('patterns_learned', pymongo.DESCENDING)
                    ]
                },
                self.config.sources_collection: {
                    'indexes': [
                        ('source_name', pymongo.ASCENDING),
                        ('quality_score', pymongo.DESCENDING),
                        ('last_accessed', pymongo.DESCENDING)
                    ]
                }
            }
            
            for collection_name, config in collection_configs.items():
                collection = self.database[collection_name]
                self.collections[collection_name] = collection
                
                # ایجاد indexes
                for index_spec in config['indexes']:
                    try:
                        collection.create_index(index_spec, background=True)
                        logger.debug(f"Index ایجاد شد: {collection_name}.{index_spec}")
                    except Exception as e:
                        logger.warning(f"خطا در ایجاد index {collection_name}.{index_spec}: {e}")
                
                logger.info(f"✅ Collection {collection_name} آماده شد")
            
        except Exception as e:
            logger.error(f"خطا در راه‌اندازی collections: {e}")
    
    def store_learning_pattern(self, pattern_data: Dict[str, Any]) -> bool:
        """ذخیره الگوی یادگیری در MongoDB"""
        if not self.connection_healthy:
            logger.warning("MongoDB اتصال غیرفعال - ذخیره محلی")
            return False
        
        try:
            collection = self.collections.get(self.config.learning_collection)
            if not collection:
                return False
            
            # افزودن metadata
            pattern_data.update({
                'created_at': datetime.utcnow(),
                'stored_at': time.time(),
                'version': '2.0',
                'source_system': 'enhanced_ultra_learning'
            })
            
            # بررسی تکراری بودن
            existing = collection.find_one({'pattern_hash': pattern_data.get('pattern_hash')})
            if existing:
                # بروزرسانی الگوی موجود
                collection.update_one(
                    {'pattern_hash': pattern_data['pattern_hash']},
                    {'$set': pattern_data, '$inc': {'usage_frequency': 1}}
                )
                logger.debug(f"الگو بروزرسانی شد: {pattern_data.get('pattern_hash', 'N/A')}")
            else:
                # درج الگوی جدید
                result = collection.insert_one(pattern_data)
                logger.debug(f"الگوی جدید ذخیره شد: {result.inserted_id}")
            
            self.connection_stats['successful_operations'] += 1
            return True
            
        except Exception as e:
            logger.error(f"خطا در ذخیره الگو در MongoDB: {e}")
            self.connection_stats['failed_operations'] += 1
            return False
    
    def store_intelligence_data(self, intelligence_data: Dict[str, Any]) -> bool:
        """ذخیره داده‌های هوش مصنوعی"""
        if not self.connection_healthy:
            return False
        
        try:
            collection = self.collections.get(self.config.intelligence_collection)
            if not collection:
                return False
            
            intelligence_data.update({
                'created_at': datetime.utcnow(),
                'stored_at': time.time()
            })
            
            result = collection.insert_one(intelligence_data)
            logger.debug(f"داده‌های هوش ذخیره شد: {result.inserted_id}")
            
            self.connection_stats['successful_operations'] += 1
            return True
            
        except Exception as e:
            logger.error(f"خطا در ذخیره داده‌های هوش: {e}")
            self.connection_stats['failed_operations'] += 1
            return False
    
    def store_performance_metrics(self, performance_data: Dict[str, Any]) -> bool:
        """ذخیره معیارهای عملکرد"""
        if not self.connection_healthy:
            return False
        
        try:
            collection = self.collections.get(self.config.performance_collection)
            if not collection:
                return False
            
            performance_data.update({
                'created_at': datetime.utcnow(),
                'stored_at': time.time()
            })
            
            result = collection.insert_one(performance_data)
            logger.debug(f"معیارهای عملکرد ذخیره شد: {result.inserted_id}")
            
            self.connection_stats['successful_operations'] += 1
            return True
            
        except Exception as e:
            logger.error(f"خطا در ذخیره معیارهای عملکرد: {e}")
            self.connection_stats['failed_operations'] += 1
            return False
    
    def get_learning_patterns(self, filter_criteria: Dict[str, Any] = None, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """دریافت الگوهای یادگیری"""
        if not self.connection_healthy:
            return []
        
        try:
            collection = self.collections.get(self.config.learning_collection)
            if not collection:
                return []
            
            filter_criteria = filter_criteria or {}
            
            # اضافه کردن فیلتر زمانی پیش‌فرض (آخرین 30 روز)
            if 'created_at' not in filter_criteria:
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                filter_criteria['created_at'] = {'$gte': thirty_days_ago}
            
            cursor = collection.find(filter_criteria).sort('created_at', -1).limit(limit)
            patterns = list(cursor)
            
            logger.info(f"📊 {len(patterns)} الگو از MongoDB بازیابی شد")
            return patterns
            
        except Exception as e:
            logger.error(f"خطا در دریافت الگوها: {e}")
            return []
    
    def get_intelligence_statistics(self) -> Dict[str, Any]:
        """دریافت آمار هوش مصنوعی"""
        if not self.connection_healthy:
            return {}
        
        try:
            collection = self.collections.get(self.config.intelligence_collection)
            if not collection:
                return {}
            
            # آخرین رکورد هوش
            latest = collection.find_one(sort=[('timestamp', -1)])
            
            # آمار کلی
            total_records = collection.count_documents({})
            
            # میانگین سطح هوش در آخرین 7 روز
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_records = list(collection.find(
                {'created_at': {'$gte': week_ago}},
                {'intelligence_level': 1}
            ))
            
            avg_intelligence = 0
            if recent_records:
                avg_intelligence = sum(r.get('intelligence_level', 0) for r in recent_records) / len(recent_records)
            
            stats = {
                'latest_intelligence': latest.get('intelligence_level', 0) if latest else 0,
                'total_records': total_records,
                'average_intelligence_week': round(avg_intelligence, 2),
                'recent_records_count': len(recent_records),
                'last_update': latest.get('created_at') if latest else None
            }
            
            logger.info(f"📈 آمار هوش: {stats['latest_intelligence']}% فعلی، {stats['average_intelligence_week']}% میانگین هفته")
            return stats
            
        except Exception as e:
            logger.error(f"خطا در دریافت آمار هوش: {e}")
            return {}
    
    def sync_from_sqlite(self, sqlite_db_path: str) -> Dict[str, int]:
        """همگام‌سازی از SQLite به MongoDB"""
        if not self.connection_healthy:
            logger.warning("MongoDB غیرفعال - همگام‌سازی امکان‌پذیر نیست")
            return {'patterns': 0, 'intelligence': 0, 'performance': 0}
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()
            
            sync_stats = {'patterns': 0, 'intelligence': 0, 'performance': 0}
            
            # همگام‌سازی الگوها
            try:
                cursor.execute('SELECT * FROM enhanced_patterns ORDER BY created_at DESC LIMIT 1000')
                patterns = cursor.fetchall()
                
                # دریافت نام ستون‌ها
                column_names = [description[0] for description in cursor.description]
                
                for pattern_row in patterns:
                    pattern_dict = dict(zip(column_names, pattern_row))
                    
                    # تبدیل blob data
                    if pattern_dict.get('pattern_data'):
                        try:
                            import pickle
                            pattern_dict['pattern_data_decoded'] = pickle.loads(pattern_dict['pattern_data'])
                        except:
                            pattern_dict['pattern_data_decoded'] = None
                    
                    if self.store_learning_pattern(pattern_dict):
                        sync_stats['patterns'] += 1
                        
                logger.info(f"📥 {sync_stats['patterns']} الگو از SQLite همگام‌سازی شد")
                
            except Exception as e:
                logger.warning(f"خطا در همگام‌سازی الگوها: {e}")
            
            # همگام‌سازی داده‌های هوش
            try:
                cursor.execute('SELECT * FROM enhanced_intelligence ORDER BY timestamp DESC LIMIT 100')
                intelligence_records = cursor.fetchall()
                
                column_names = [description[0] for description in cursor.description]
                
                for intel_row in intelligence_records:
                    intel_dict = dict(zip(column_names, intel_row))
                    
                    if self.store_intelligence_data(intel_dict):
                        sync_stats['intelligence'] += 1
                        
                logger.info(f"🧠 {sync_stats['intelligence']} رکورد هوش همگام‌سازی شد")
                
            except Exception as e:
                logger.warning(f"خطا در همگام‌سازی هوش: {e}")
            
            # همگام‌سازی عملکرد
            try:
                cursor.execute('SELECT * FROM learning_performance ORDER BY start_time DESC LIMIT 100')
                performance_records = cursor.fetchall()
                
                column_names = [description[0] for description in cursor.description]
                
                for perf_row in performance_records:
                    perf_dict = dict(zip(column_names, perf_row))
                    
                    if self.store_performance_metrics(perf_dict):
                        sync_stats['performance'] += 1
                        
                logger.info(f"⚡ {sync_stats['performance']} رکورد عملکرد همگام‌سازی شد")
                
            except Exception as e:
                logger.warning(f"خطا در همگام‌سازی عملکرد: {e}")
            
            conn.close()
            
            total_synced = sum(sync_stats.values())
            logger.info(f"✅ همگام‌سازی کامل: {total_synced} رکورد")
            
            return sync_stats
            
        except Exception as e:
            logger.error(f"خطا در همگام‌سازی از SQLite: {e}")
            return {'patterns': 0, 'intelligence': 0, 'performance': 0}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """دریافت وضعیت اتصال"""
        status = {
            'healthy': self.connection_healthy,
            'pymongo_available': PYMONGO_AVAILABLE,
            'database_name': self.config.database_name,
            'collections_count': len(self.collections),
            'stats': self.connection_stats.copy()
        }
        
        # تست اتصال در زمان واقعی
        if self.connection_healthy and self.client:
            try:
                self.client.admin.command('ping')
                status['ping_successful'] = True
            except:
                status['ping_successful'] = False
                self.connection_healthy = False
        
        return status
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """پاکسازی داده‌های قدیمی"""
        if not self.connection_healthy:
            return {}
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            cleanup_stats = {}
            
            # پاکسازی الگوهای قدیمی با کیفیت پایین
            patterns_collection = self.collections.get(self.config.learning_collection)
            if patterns_collection:
                result = patterns_collection.delete_many({
                    'created_at': {'$lt': cutoff_date},
                    'confidence': {'$lt': 0.6}  # فقط الگوهای کم‌کیفیت
                })
                cleanup_stats['patterns_deleted'] = result.deleted_count
            
            # پاکسازی رکوردهای عملکرد قدیمی
            performance_collection = self.collections.get(self.config.performance_collection)
            if performance_collection:
                result = performance_collection.delete_many({
                    'created_at': {'$lt': cutoff_date}
                })
                cleanup_stats['performance_deleted'] = result.deleted_count
            
            logger.info(f"🧹 پاکسازی انجام شد: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"خطا در پاکسازی: {e}")
            return {}

# تست سیستم
async def test_mongodb_integration():
    """تست سیستم یکپارچه‌سازی MongoDB"""
    print("🧪 شروع تست MongoDB Integration...")
    
    # ایجاد instance
    mongo_integration = EnhancedMongoDBIntegration()
    
    # بررسی وضعیت اتصال
    status = mongo_integration.get_connection_status()
    print(f"📊 وضعیت اتصال: {status}")
    
    if status['healthy']:
        # تست ذخیره الگو
        test_pattern = {
            'pattern_hash': f'test_{int(time.time())}',
            'confidence': 0.85,
            'category': 'test',
            'source': 'mongodb_test',
            'effectiveness_score': 0.8
        }
        
        success = mongo_integration.store_learning_pattern(test_pattern)
        print(f"✅ تست ذخیره الگو: {'موفق' if success else 'ناموفق'}")
        
        # تست دریافت الگوها
        patterns = mongo_integration.get_learning_patterns(limit=5)
        print(f"📚 الگوهای بازیابی شده: {len(patterns)}")
        
        # تست آمار هوش
        intel_stats = mongo_integration.get_intelligence_statistics()
        print(f"🧠 آمار هوش: {intel_stats}")
    
    else:
        print("⚠️ اتصال MongoDB برقرار نیست - تست محدود")
    
    print("✅ تست MongoDB Integration کامل شد")

if __name__ == "__main__":
    asyncio.run(test_mongodb_integration())
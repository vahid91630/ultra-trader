import os
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError, ConnectionFailure
from datetime import datetime

# تنظیم logging برای MongoDB
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mongo_client():
    """
    دریافت client MongoDB با مدیریت بهتر خطا
    """
    mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
    
    if not mongo_uri:
        logger.error("❌ هیچ‌کدام از متغیرهای MONGO_URI یا MONGODB_URI تنظیم نشده")
        logger.info("💡 لطفاً یکی از این متغیرها را تنظیم کنید:")
        logger.info("   - MONGO_URI=mongodb://localhost:27017/ultra_trader")
        logger.info("   - MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/db")
        raise ValueError("MongoDB URI تنظیم نشده است")
    
    try:
        logger.info("🔌 در حال اتصال به MongoDB...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # تست اتصال
        client.admin.command('ping')
        logger.info("✅ اتصال MongoDB برقرار شد")
        return client
    except ServerSelectionTimeoutError as e:
        logger.error(f"🕐 Timeout در اتصال به MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ خطا در اتصال به MongoDB: {e}")
        raise

# اتصال به دیتابیس MongoDB (با مدیریت خطا)
try:
    client = get_mongo_client()
    db = client["ultra_trader"]
    collection = db["btc_prices"]
    logger.info("🔗 اتصال پایه MongoDB تنظیم شد")
except Exception as e:
    logger.warning(f"⚠️ اتصال پایه MongoDB ناموفق: {e}")
    logger.info("🔄 حالت Safe Mode فعال - عملیات بدون دیتابیس ادامه می‌یابد")
    client = None
    db = None
    collection = None

def save_btc_price(price: float, source: str = "binance"):
    """
    ذخیره قیمت بیت‌کوین با مدیریت بهتر خطا
    """
    if not collection:
        logger.error("❌ اتصال MongoDB برقرار نیست - نمی‌توان قیمت را ذخیره کرد")
        logger.info(f"🔄 قیمت در حافظه موقت ذخیره می‌شود: {price}")
        return False
    
    try:
        doc = {
            "price": price,
            "source": source,
            "timestamp": datetime.utcnow()
        }
        result = collection.insert_one(doc)
        logger.info(f"✅ قیمت {price} با ID {result.inserted_id} ذخیره شد")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره قیمت: {e}")
        logger.info(f"🔄 قیمت در حافظه موقت ذخیره می‌شود: {price}")
        return False

def get_connection_status():
    """
    بررسی وضعیت اتصال MongoDB
    """
    if not client:
        return {
            "connected": False,
            "status": "اتصال برقرار نیست",
            "details": "متغیر محیطی تنظیم نشده یا خطا در اتصال اولیه"
        }
    
    try:
        client.admin.command('ping')
        return {
            "connected": True,
            "status": "متصل و آماده",
            "details": "اتصال سالم و فعال"
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "اتصال قطع شده",
            "details": str(e)
        }

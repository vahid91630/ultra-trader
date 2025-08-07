from pymongo import MongoClient
from datetime import datetime
import os

def connect_to_mongodb():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("⚠️ MONGO_URI not set – Running in Safe Mode")
        return None
    try:
        client = MongoClient(uri)
        return client
    except Exception as e:
        print("❌ اتصال به دیتابیس ناموفق بود:", str(e))
        return None

def save_btc_price(price: float, source="binance"):
    client = connect_to_mongodb()
    if not client:
        return

    db = client["ultra_trader"]
    collection = db["btc_prices"]
    document = {
        "price": price,
        "timestamp": datetime.utcnow(),
        "source": source
    }

    result = collection.insert_one(document)
    print(f"✅ قیمت ذخیره شد (ID: {result.inserted_id})")

from pymongo import MongoClient
from datetime import datetime
import os

# اتصال به دیتابیس MongoDB (اطمینان حاصل کن که URI رو درست تنظیم کردی)
client = MongoClient(os.getenv("MONGO_URI"))
db = client["ultra_trader"]
collection = db["btc_prices"]

def save_btc_price(price: float, source: str = "binance"):
    doc = {
        "price": price,
        "source": source,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(doc)
    print(f"✅ قیمت {price} ذخیره شد.")

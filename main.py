import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

def get_fallback_data():
    print("⚠️ استفاده از دیتای شبیه‌سازی شده (Safe Mode)")
    fake_data = [
        {"symbol": "BTCUSDT", "price": 28750.0},
        {"symbol": "ETHUSDT", "price": 1850.5},
        {"symbol": "SOLUSDT", "price": 25.43},
    ]
    for doc in fake_data:
        print(f"{doc['symbol']} → {doc['price']}")
    return fake_data

def connect_to_mongo():
    try:
        uri = os.getenv("MONGODB_URI")

        if not uri:
            raise Exception("⛔ Mongo URI not found!")

        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("✅ اتصال موفق به MongoDB!")
        db_name = uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        collection = db["prices"]
        results = list(collection.find().limit(10))
        for item in results:
            print(item)
        return results
    except Exception as e:
        print("❌ اتصال واقعی ممکن نیست، سوییچ به حالت Safe Mode")
        return get_fallback_data()

if __name__ == "__main__":
    connect_to_mongo()

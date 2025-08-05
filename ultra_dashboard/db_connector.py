import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def get_data():
    try:
        uri = os.getenv("MONGODB_URI")
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        db_name = uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        collection = db["prices"]
        return list(collection.find().limit(100))
    except Exception as e:
        print("❌ MongoDB connection failed. Using safe mode.")
        return [
            {"symbol": "BTCUSDT", "price": 29200, "timestamp": "2025-08-01"},
            {"symbol": "BTCUSDT", "price": 29450, "timestamp": "2025-08-02"},
            {"symbol": "BTCUSDT", "price": 29700, "timestamp": "2025-08-03"},
        ]

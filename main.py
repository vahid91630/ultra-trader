import os
from pymongo import MongoClient

def connect_to_mongodb():
    # گرفتن URI از محیط
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise Exception("❌ MongoDB URI not found in environment variables!")

    # اتصال
    client = MongoClient(mongo_uri)
    db = client.get_database()
    print("✅ Connected to MongoDB!")
    return db

def show_collections(db):
    collections = db.list_collection_names()
    print("📦 Available Collections:")
    for col in collections:
        print(f" - {col}")

if __name__ == "__main__":
    print("✅ Ultra Trader Booted")

    # اتصال به Mongo
    db = connect_to_mongodb()

    # نمایش کالکشن‌ها
    show_collections(db)

    # نگه‌داشتن اسکریپت
    input("✅ Ultra Trader is running. Press Enter to stop.")

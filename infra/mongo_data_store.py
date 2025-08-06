import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def connect_to_mongodb():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("⚠️ MONGO_URI not set – Running in Safe Mode")
        return None
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("✅ Connected to MongoDB:", uri.split("/")[-1].split("?")[0])
        return client
    except Exception as e:
        print("❌ MongoDB connection failed:", e)
        return None

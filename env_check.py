import os
from pymongo import MongoClient

print("✅ Checking environment variables...")

api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")
mongo_uri = os.getenv("MONGODB_URI")

print("API_KEY:", api_key)
print("SECRET_KEY:", secret_key)
print("MONGODB_URI:", mongo_uri)

try:
    client = MongoClient(mongo_uri)
    client.admin.command("ping")
    print("✅ MongoDB connection successful!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

input("⏳ Press Enter to exit...")

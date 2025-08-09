# /infra/mongo_data_store.py
from __future__ import annotations
import os
from typing import Optional, Tuple
from pymongo import MongoClient

def _pick_env(*names: str) -> Optional[str]:
    for n in names:
        v = os.getenv(n)
        if v and str(v).strip():
            return v
    return None

def _extract_db_name(uri: str) -> Optional[str]:
    try:
        tail = uri.rsplit("/", 1)[-1]
        return tail.split("?", 1)[0] if tail else None
    except Exception:
        return None

def connect_to_mongodb() -> Tuple[Optional[MongoClient], Optional[str]]:
    uri = _pick_env("MONGODB_URI", "MONGO_URI")
    if not uri:
        print("⚠️ Neither MONGODB_URI nor MONGO_URI is set.")
        return None, None
    dbname = _extract_db_name(uri) or os.getenv("MONGODB_DB") or "ultra_trader"
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        client.admin.command("ping")
        return client, dbname
    except Exception as exc:
        print(f"❌ Mongo connection failed: {exc}")
        return None, None


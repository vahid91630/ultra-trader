# -*- coding: utf-8 -*-
"""
ماژول مانیتورینگ وضعیت - بازنویسی ساده و ایمن
"""
import os
import json
import time
from datetime import datetime
import psutil
import pytz

START_TIME = time.time()
TEHRAN_TZ = pytz.timezone("Asia/Tehran")


def _fmt_bytes(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def get_uptime() -> dict:
    seconds = int(time.time() - START_TIME)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return {
        "seconds": seconds,
        "human": f"{days}روز {hours}ساعت {minutes}دقیقه {secs}ثانیه",
        "started_at": datetime.fromtimestamp(START_TIME, TEHRAN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_system_resources() -> dict:
    try:
        cpu = psutil.cpu_percent(interval=0.2)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu_percent": cpu,
            "memory": {
                "percent": mem.percent,
                "used": _fmt_bytes(mem.used),
                "total": _fmt_bytes(mem.total),
            },
            "disk": {
                "percent": disk.percent,
                "used": _fmt_bytes(disk.used),
                "total": _fmt_bytes(disk.total),
            },
        }
    except Exception:
        return {
            "cpu_percent": 0.0,
            "memory": {"percent": 0.0, "used": "0 B", "total": "0 B"},
            "disk": {"percent": 0.0, "used": "0 B", "total": "0 B"},
        }


def get_exchange_status() -> dict:
    """
    مقادیر پیشفرض ایمن. بعداً به سیستم واقعی متصل کنید.
    """
    return {
        "connected": False,
        "exchange": None,
        "balance_usdt": None,
        "symbols_tracked": 0,
        "last_update": datetime.now(TEHRAN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_learning_progress() -> dict:
    """
    تلاش میکند از فایل learning_status.json بخواند، در غیر اینصورت مقادیر پیشفرض برمیگرداند.
    """
    path = os.getenv("LEARNING_STATUS_PATH", "learning_status.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "active": bool(data.get("active", False)),
                "progress_percent": float(data.get("progress_percent", 0.0)),
                "workers": int(data.get("workers", 0)),
                "last_update": data.get("last_update"),
            }
        except Exception:
            pass
    # fallback
    return {"active": False, "progress_percent": 0.0, "workers": 0, "last_update": None}


def get_news_status() -> dict:
    """
    تلاش میکند از فایل news_monitoring_status.json بخواند، در غیر اینصورت مقادیر پیشفرض برمیگرداند.
    """
    path = os.getenv("NEWS_STATUS_PATH", "news_monitoring_status.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "active": bool(data.get("active", False)),
                "crypto_sentiment": float(data.get("crypto_sentiment", 0.0)),
                "stock_sentiment": float(data.get("stock_sentiment", 0.0)),
                "news_analyzed": int(data.get("news_analyzed", 0)),
                "last_update": data.get("last_update"),
            }
        except Exception:
            pass
    # fallback
    return {
        "active": False,
        "crypto_sentiment": 0.0,
        "stock_sentiment": 0.0,
        "news_analyzed": 0,
        "last_update": None,
    }
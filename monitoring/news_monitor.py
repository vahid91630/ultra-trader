# -*- coding: utf-8 -*-
"""
سرویس مانیتور اخبار - نسخه ساده (Mock)
- هر N ثانیه یکبار وضعیت ساختگی تولید و در news_monitoring_status.json ذخیره میکند.
- بعداً میتوانید به NewsAPI/منابع واقعی متصل کنید.
"""
import json
import time
from datetime import datetime
import pytz
import random

TEHRAN_TZ = pytz.timezone("Asia/Tehran")


def run_mock(interval_seconds: int = 60):
    while True:
        now = datetime.now(TEHRAN_TZ).strftime("%Y-%m-%d %H:%M:%S")
        status = {
            "active": True,
            "crypto_sentiment": round(random.uniform(0.3, 0.7), 2),
            "stock_sentiment": round(random.uniform(0.3, 0.7), 2),
            "news_analyzed": random.randint(10, 80),
            "last_update": now,
        }
        with open("news_monitoring_status.json", "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_mock(60)
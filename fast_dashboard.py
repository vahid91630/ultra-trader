#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
داشبورد سریع و سبک (Flask) - بازنویسی کامل
"""
import os
import logging
from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz

# منابع وضعیت از ماژول مانیتورینگ
from monitoring.status_provider import (
    get_system_resources,
    get_exchange_status,
    get_learning_progress,
    get_news_status,
    get_uptime,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fast_dashboard")

app = Flask(__name__, template_folder="templates")

TEHRAN_TZ = pytz.timezone("Asia/Tehran")


@app.route("/")
def index():
    return render_template("fast_dashboard.html")


@app.route("/api/data")
def api_data():
    try:
        now_tehran = datetime.now(TEHRAN_TZ)
        data = {
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "tehran_time": now_tehran.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": get_uptime(),
            "system_resources": get_system_resources(),
            "exchange_status": get_exchange_status(),
            "learning_progress": get_learning_progress(),
            "news_status": get_news_status(),
            "status": "active",
        }
        return jsonify(data)
    except Exception as e:
        logger.exception("خطا در /api/data: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
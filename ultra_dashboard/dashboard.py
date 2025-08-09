# /ultra_dashboard/dashboard.py
from __future__ import annotations
import os
from typing import Dict, Optional
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from infra.mongo_data_store import connect_to_mongodb

load_dotenv()
st.set_page_config(page_title="Ultra Trader – Live Dashboard", layout="wide")
st.title("📊 Ultra Trader – داشبورد آنلاین")
REFRESH_SEC = int(os.getenv("DASHBOARD_REFRESH_SEC", "15"))
st.caption(f"⏱️ رفرش پیشنهادی: {REFRESH_SEC}s")

client, DBNAME = connect_to_mongodb()
ONLINE = bool(client and DBNAME)

def df_from_collection(coll: str, limit: int = 3000,
                       sort: Optional[Dict[str,int]] = None,
                       projection: Optional[Dict[str,int]] = None) -> pd.DataFrame:
    if not ONLINE:
        return pd.DataFrame()
    try:
        _sort = list((sort or {"timestamp": -1}).items())
        cur = client[DBNAME][coll].find({}, projection or {}).sort(_sort).limit(limit)
        rows = list(cur)
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        return df
    except Exception as exc:
        st.warning(f"⚠️ خطا در `{coll}`: {exc}")
        return pd.DataFrame()

def show_table(df: pd.DataFrame, title: str, rows: int = 200):
    st.subheader(title)
    if df.empty:
        st.info("داده‌ای یافت نشد.")
    else:
        st.dataframe(df.head(rows), use_container_width=True)

def show_ts(df: pd.DataFrame, x: str, y: str, title: str):
    if {x, y}.issubset(df.columns) and not df.empty:
        fig = px.line(df.sort_values(x), x=x, y=y, title=title, markers=True)
        st.plotly_chart(fig, use_container_width=True)

with st.sidebar:
    st.header("Navigation")
    page = st.radio("صفحه", ["Overview","Financial Reports","Educational Reports","Monitoring"], index=0)
    st.divider()
    if ONLINE: st.success(f"🟢 Online • DB: {DBNAME}")
    else:
        st.error("🟡 Safe Mode: اتصال Mongo برقرار نیست.")
        st.code("export MONGODB_URI='mongodb+srv://USER:PASS@HOST/DB?retryWrites=true&w=majority'")

if page == "Overview":
    prices = df_from_collection("prices", 3000)
    signals = df_from_collection("signals", 1000)
    pnl = df_from_collection("pnl", 3000)
    c1,c2,c3 = st.columns(3)
    c1.metric("prices", len(prices)); c2.metric("signals", len(signals)); c3.metric("pnl", len(pnl))
    show_ts(prices, "timestamp", "price", "قیمت – زنده")
    if not signals.empty: show_table(signals, "آخرین سیگنال‌ها (۱۰۰)", 100)
    if not pnl.empty: show_ts(pnl, "timestamp", "pnl", "PnL – عملکرد")

elif page == "Financial Reports":
    prices = df_from_collection("prices", 5000)
    signals = df_from_collection("signals", 2000)
    pnl = df_from_collection("pnl", 5000)
    equity = df_from_collection("equity_curve", 5000)
    show_ts(prices, "timestamp", "price", "قیمت زنده")
    if not signals.empty: show_table(signals, "سیگنال‌ها", 200)
    if not pnl.empty: show_ts(pnl, "timestamp", "pnl", "PnL")
    if not equity.empty: show_ts(equity, "timestamp", "equity", "Equity Curve")

elif page == "Educational Reports":
    le = df_from_collection("learning_events", 2000)
    lm = df_from_collection("learning_metrics", 5000)
    if not le.empty: show_table(le, "رویدادهای یادگیری", 200)
    if not lm.empty:
        for y in ["loss","accuracy","reward","score"]:
            if y in lm.columns: show_ts(lm, "timestamp", y, f"روند {y}")
        show_table(lm, "شاخص‌های یادگیری", 200)

else:  # Monitoring
    telemetry = df_from_collection("telemetry", 2000)
    services = df_from_collection("services_health", 500)
    if not telemetry.empty:
        show_table(telemetry, "Telemetry", 200)
        if "cpu" in telemetry.columns: show_ts(telemetry, "timestamp", "cpu", "CPU%")
        if "memory" in telemetry.columns: show_ts(telemetry, "timestamp", "memory", "Memory%")
    if not services.empty: show_table(services, "وضعیت سرویس‌ها", 200)

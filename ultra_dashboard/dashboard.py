import os
import streamlit as st
import pandas as pd
import plotly.express as px
from infra.mongo_data_store import connect_to_mongodb

st.set_page_config(
    page_title="Ultra Trader Dashboard", 
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# Add custom HTML with proper icon meta tags
icon_html = """
<head>
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/icons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/icons/favicon-16x16.png">
    <meta name="theme-color" content="#1e3c72">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Ultra Trader">
</head>
"""
st.markdown(icon_html, unsafe_allow_html=True)
st.title("📊 Ultra+ Trading Dashboard")

client = connect_to_mongodb()
if client:
    dbname = os.getenv("MONGODB_URI").split("/")[-1].split("?")[0]
    df = pd.DataFrame(list(client[dbname]["signals"].find().sort("timestamp", -1).limit(100)))
    st.subheader("Latest Signals")
    st.dataframe(df)
    if "price" in df.columns and "timestamp" in df.columns:
        fig = px.line(df, x="timestamp", y="price", title="📉 Price History", markers=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("🔒 Safe Mode: fallback data")
    fallback = pd.DataFrame([{"timestamp": i, "price": 30000 + i * 10} for i in range(50)])
    fig = px.line(fallback, x="timestamp", y="price", title="📉 Price (Fallback Mode)", markers=True)
    st.plotly_chart(fig, use_container_width=True)

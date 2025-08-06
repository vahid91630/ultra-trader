import os
import streamlit as st
import pandas as pd
import plotly.express as px
from infra.mongo_data_store import connect_to_mongodb

st.set_page_config(page_title="Ultra Trader Dashboard", layout="wide")
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

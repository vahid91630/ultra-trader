import streamlit as st
from db_connector import connect_to_mongo

st.set_page_config(page_title="📊 Ultra Trader Dashboard", layout="wide")

st.title("📈 داشبورد ربات معامله‌گر")

data = connect_to_mongo()

if data:
    st.success("✅ اتصال به MongoDB موفقیت‌آمیز بود!")
    st.dataframe(data)
else:
    st.warning("⚠️ اتصال به دیتابیس برقرار نشد. داده شبیه‌سازی شده استفاده می‌شود.")

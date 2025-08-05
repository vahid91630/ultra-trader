import streamlit as st
import pandas as pd
import plotly.express as px
from db_connector import get_data
from analysis import analyze

st.set_page_config(page_title="📊 Ultra+ Dashboard", layout="wide")

st.title("📈 Ultra+ Trading Dashboard")
st.markdown("مرکز نظارت و تحلیل خودکار بازار بیت‌کوین")

# گرفتن دیتا
data = get_data()

if not data:
    st.warning("❗ هیچ دیتایی در دسترس نیست.")
else:
    df, stats = analyze(data)

    # آمار کلیدی
    st.subheader("📌 آمار کلی")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("قیمت میانگین", f"${stats['average']}")
    col2.metric("بیشترین قیمت", f"${stats['max']}")
    col3.metric("کمترین قیمت", f"${stats['min']}")
    col4.metric("درصد تغییر", f"{stats['change']}%")

    # نمودار قیمت
    st.subheader("📉 نمودار قیمت")
    if "timestamp" in df.columns:
        fig = px.line(df, x="timestamp", y="price", title="نمودار قیمت روزانه", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("❗ ستون زمان موجود نیست، فقط جدول نمایش داده می‌شود.")

    # جدول کامل دیتا
    st.subheader("📋 دیتای کامل")
    st.dataframe(df)

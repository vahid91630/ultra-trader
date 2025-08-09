"""
Deprecated root-level dashboard.
Why: avoid running the old/experimental UI on Railway.
"""
import streamlit as st

st.set_page_config(page_title="Ultra Trader – Redirect", layout="centered")
st.title("ℹ️ این داشبورد قدیمی/آزمایشی است")
st.info(
    "لطفاً داشبورد اصلی را اجرا کنید:\n\n"
    "`streamlit run ultra_dashboard/dashboard.py`\n\n"
    "روی Railway هم با Procfile همین مسیر اجرا می‌شود."
)

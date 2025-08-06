from binance_connector import get_live_price
import streamlit as st

st.title("💹 قیمت لحظه‌ای")

price_data = get_live_price("BTCUSDT")
st.metric("BTC/USDT", f"${price_data['price']}")

import streamlit as st
from db_connector import connect_to_mongo

st.set_page_config(page_title="ULTRA PLUS Dashboard", layout="wide")

st.title("📈 Ultra Plus Crypto Dashboard")

data = connect_to_mongo()

st.subheader("📊 Market Data")
st.dataframe(data)

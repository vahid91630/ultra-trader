import streamlit as st
import plotly.express as px
from infra.mongo_data_store import connect_to_mongodb
from infra.api_manager import APIManager

st.set_page_config(page_title="Ultra Trader Dashboard", layout="wide")
st.title("📈 Ultra+ Monitoring & Analytics")

# Connection and API key check
client = connect_to_mongodb()
api = APIManager()
api.check_keys()

if client:
    dbname = os.getenv("MONGODB_URI").split("/")[-1].split("?")[0]
    df = list(client[dbname]["signals"].find().sort("timestamp", -1).limit(50))
    df = px.data.frame(df)
    st.subheader("Latest Signals")
    st.dataframe(df)
    if "price" in df.columns:
        fig = px.line(df, x="timestamp", y="price", title="📉 Price History", markers=True)
        st.plotly_chart(fig)
else:
    st.warning("🔒 Running in Safe Mode – using fallback data")
    fallback = [{"timestamp": i, "price": 30000 + i*10} for i in range(50)]
    df = px.data.frame(fallback)
    fig = px.line(df, x="timestamp", y="price", title="📉 Price (Fallback Data)", markers=True)
    st.plotly_chart(fig)

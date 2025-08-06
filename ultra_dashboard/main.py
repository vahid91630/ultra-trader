import os

if __name__ == "__main__":
    print("✅ Ultra Trader Dashboard Booted")
    os.system("streamlit run ultra_dashboard/dashboard.py --server.enableCORS false --server.port $PORT")

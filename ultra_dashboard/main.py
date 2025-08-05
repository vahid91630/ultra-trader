import os
import streamlit as st
from infra.api_manager import APIManager

if __name__ == "__main__":
    print("✅ Ultra Trader Dashboard Booted")
    os.system("streamlit run ultra_dashboard/dashboard.py")

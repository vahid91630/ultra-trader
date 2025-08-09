"""
Some platforms auto-run streamlit_app.py.
Why: ensure it launches the new unified dashboard.
"""
import runpy
runpy.run_module("ultra_dashboard.dashboard", run_name="__main__")

"""
Ultra Trader – unified, online Streamlit dashboard for Railway.
Tabs:
- Overview
- Financial Reports
- Educational Reports
- Monitoring
Why: replace old/experimental dashboards and always show live reports.
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from infra.mongo_data_store import connect_to_mongodb

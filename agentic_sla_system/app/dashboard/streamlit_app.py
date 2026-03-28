import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import sqlite3
import pandas as pd
from app.utils.logger import get_logger

logger = get_logger()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DB_PATH = os.path.join(BASE_DIR, "tickets.db")

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_conn()

def load_data():
    logger.info("Loading tickets for dashboard")
    return pd.read_sql_query("SELECT * FROM tickets", conn)

def stars(p):
    return "★"*p + "☆"*(3-p)

st.set_page_config(layout="wide")
st.title("Agentic SLA Dashboard")

df = load_data()

if df.empty:
    st.warning("No tickets available")
else:
    for _, row in df.iterrows():
        st.markdown(f"""
        ### {row['subject']} (#{row['ticket_id']})
        
        **Helpdesk Team:** {row['helpdesk_team']}  
        **Assigned to:** {row['assigned_to']}  
        **Customer:** {row['customer']}  
        **Phone:** {row['phone']}  
        **Priority:** {stars(row['priority'])}
        
        **Description:**  
        {row['description']}
        
        ---
        """)
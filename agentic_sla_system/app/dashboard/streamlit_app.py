import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st

st.set_page_config(
    page_title="Agentic SLA Dashboard",
    layout="wide"
)

import sqlite3
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tickets.db"))

conn = sqlite3.connect(DB_PATH, check_same_thread=False)

def load_data():
    return pd.read_sql_query("SELECT * FROM tickets ORDER BY updated_at DESC", conn)

def stars(p):
    try:
        p = int(p)
    except:
        p = 0
    return "★" * p + "☆" * (3 - p)

st.title("Agentic SLA Dashboard")

df = load_data()

if df.empty:
    st.warning("No tickets available")
else:
    for _, row in df.iterrows():
        st.markdown(f"""
### {row.get('subject')} (#{row.get('ticket_id')})

**Helpdesk Team:** {row.get('helpdesk_team')}  
**Assigned to:** {row.get('assigned_to')}  
**Customer:** {row.get('customer')}  
**Phone:** {row.get('phone')}  
**Priority:** {stars(row.get('priority'))}  
**Tags:** {row.get('tags')}

**Description:**  
{row.get('description')}
        )""")
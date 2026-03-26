import sqlite3
import os
from app.utils.config import config

def get_connection():
    db_dir = config.get("paths", "database", default="data/db/")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "tickets.db")
    return sqlite3.connect(db_path)
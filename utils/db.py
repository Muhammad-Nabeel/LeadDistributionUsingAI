# File: utils/db.py

import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

# Load DB connection details from .env
DB_CONFIG = {
    'server': os.getenv("DB_SERVER"),
    'database': os.getenv("DB_NAME"),
    'username': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD")
}

def get_connection():
    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        connection = pyodbc.connect(conn_str)
        return connection
    except Exception as e:
        print(f"❌ Error connecting to SQL Server: {e}")
        return None

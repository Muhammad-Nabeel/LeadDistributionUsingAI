# File: test_db_connection.py

from utils.db import get_connection

def test_connection():
    conn = get_connection()
    if conn:
        print("✅ Database connection successful!")
        conn.close()
    else:
        print("❌ Failed to connect to the database.")

if __name__ == "__main__":
    test_connection()


import sys
import sqlite3
from pathlib import Path

# Fix import path
sys.path.append(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
from backend.migrations.annotation import schema_mig as mig

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
mig.upgrade(conn)
conn.close()

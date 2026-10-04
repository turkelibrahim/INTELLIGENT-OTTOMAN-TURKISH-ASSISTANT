import sqlite3
import os

db_path = r'backend\ottoman_assistant.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE processing_jobs SET status = 'QUEUED', error_message = NULL, retry_count = 0 WHERE status = 'FAILED' OR status = 'OCR_RUNNING' OR status = 'PREPROCESSING'")
    print(f"Updated {c.rowcount} jobs.")
    conn.commit()
    conn.close()

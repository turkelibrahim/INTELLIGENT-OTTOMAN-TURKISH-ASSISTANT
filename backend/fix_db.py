import sqlite3

try:
    conn = sqlite3.connect('ottoman_assistant.db')
    cur = conn.cursor()
    cur.execute("UPDATE processing_jobs SET status = 'QUEUED', error_message = NULL, progress = 0 WHERE status = 'FAILED' OR status = 'retrying'")
    print(f'Updated {cur.rowcount} jobs from FAILED to QUEUED.')
    conn.commit()
    conn.close()
except Exception as e:
    print(f"Error: {e}")

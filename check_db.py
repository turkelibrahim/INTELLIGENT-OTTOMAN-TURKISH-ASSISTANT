import sqlite3

conn = sqlite3.connect('backend/ottoman_assistant.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print('Tables:', tables)

cur.execute("PRAGMA table_info(ground_truth_lines);")
print('ground_truth_lines info:', cur.fetchall())

import sqlite3
c = sqlite3.connect('backend/ottoman_assistant.db')
for row in c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('annotation_datasets')").fetchall():
    print(row[0])

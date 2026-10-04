import sqlite3
import sys

conn = sqlite3.connect(r'c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\backend\ottoman_assistant.db')
cur = conn.cursor()

try:
    cur.execute("SELECT id FROM datasets WHERE id=2")
    row = cur.fetchone()
    print("dataset_id=2 exists in datasets:", row is not None)
    
    cur.execute("SELECT COUNT(*) FROM documents WHERE dataset_id=2")
    docs = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM pages WHERE document_id IN (SELECT id FROM documents WHERE dataset_id=2)")
    pages = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lines WHERE page_id IN (SELECT id FROM pages WHERE document_id IN (SELECT id FROM documents WHERE dataset_id=2))")
    lines = cur.fetchone()[0]
    
    print(f"Legacy dataset_id=2 -> docs: {docs}, pages: {pages}, lines: {lines}")
except Exception as e:
    print("Error:", e)
    for t in ["datasets", "documents", "pages", "lines"]:
        try:
            sql = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{t}'").fetchone()
            if sql: print(t, sql[0])
        except: pass

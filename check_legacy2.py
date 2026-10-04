import sqlite3
conn = sqlite3.connect(r'c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\backend\ottoman_assistant.db')
for row in conn.execute('SELECT name, sql FROM sqlite_master WHERE type="table"'):
    if row[1] and 'dataset_id' in row[1]:
        print(f'Found dataset_id in table: {row[0]}')

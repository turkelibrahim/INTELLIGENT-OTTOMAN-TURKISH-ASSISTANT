import os
import sys
import sqlite3
from passlib.context import CryptContext
import datetime

evidence_dir = r'c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\evidence\annotation_fastapi_authenticated_repair'
test_db_dir = os.path.join(evidence_dir, 'test_db')
os.makedirs(test_db_dir, exist_ok=True)
db_path = os.path.join(test_db_dir, 'annotation_authenticated_http.db')

os.environ['ANNOTATION_DATABASE_URL'] = f'sqlite:///{db_path}'
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

# We will just copy the schema from the production DB to the test DB directly to ensure exact match!
prod_db_path = r'c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\backend\ottoman_assistant.db'

print(f"Copying schema from {prod_db_path} to {db_path}...")
prod_conn = sqlite3.connect(prod_db_path)
test_conn = sqlite3.connect(db_path)

test_conn.execute("PRAGMA foreign_keys = OFF")

for row in prod_conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND type IN ('table', 'index', 'trigger', 'view')"):
    try:
        test_conn.execute(row[0])
    except Exception as e:
        print("Error creating schema:", e)

# Add users
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)

cur = test_conn.cursor()

# Make sure users table exists
try:
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        is_active BOOLEAN DEFAULT 1,
        is_superuser BOOLEAN DEFAULT 0,
        role VARCHAR(50) DEFAULT 'user'
    )''')
except Exception as e:
    print("User table check:", e)

now = datetime.datetime.now().isoformat()
pw_hash_1 = get_password_hash("testpass")
try:
    now = datetime.datetime.now().isoformat()
    cur.execute(
        "INSERT INTO users (email, username, password_hash, full_name, role, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("reviewer_one@test.com", "reviewer_one", pw_hash_1, "Reviewer One", "admin", "active", now, now)
    )
    user1_id = cur.lastrowid

    pw_hash_2 = get_password_hash("testpass")
    cur.execute(
        "INSERT INTO users (email, username, password_hash, full_name, role, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("reviewer_two@test.com", "reviewer_two", pw_hash_2, "Reviewer Two", "expert", "active", now, now)
    )
    user2_id = cur.lastrowid
    print(f"Created Test DB with users: ID1={user1_id}, ID2={user2_id}")
except Exception as e:
    print("User insert error:", e)

test_conn.commit()
test_conn.close()
prod_conn.close()

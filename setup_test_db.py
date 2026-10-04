import os, sqlite3
from passlib.context import CryptContext
import uuid
import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)

evidence_dir = r'c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\evidence\annotation_fastapi_authenticated_repair'
test_db_dir = os.path.join(evidence_dir, 'test_db')
os.makedirs(test_db_dir, exist_ok=True)
db_path = os.path.join(test_db_dir, 'annotation_authenticated_http.db')

if os.path.exists(db_path):
    os.remove(db_path)

# Let's run migrations first by setting the ANNOTATION_DATABASE_URL and DATABASE_URL
os.environ['ANNOTATION_DATABASE_URL'] = f'sqlite:///{db_path}'
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

# Also need to run create_all on models since user tables might not be in alembic or we can just use alembic.
import sys
sys.path.insert(0, r'c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\backend')

from app.db.session import engine, Base
from app.models.user import User

print("Creating tables...")
Base.metadata.create_all(bind=engine)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

now = datetime.datetime.now().isoformat()
# Create user 1
pw_hash_1 = get_password_hash("testpass")
cur.execute(
    "INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser) VALUES (?, ?, ?, ?, ?)",
    ("reviewer_one@test.com", pw_hash_1, "Reviewer One", 1, 0)
)
user1_id = cur.lastrowid

# Create user 2
pw_hash_2 = get_password_hash("testpass")
cur.execute(
    "INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser) VALUES (?, ?, ?, ?, ?)",
    ("reviewer_two@test.com", pw_hash_2, "Reviewer Two", 1, 0)
)
user2_id = cur.lastrowid

conn.commit()
conn.close()

print(f"Created Test DB with users: ID1={user1_id}, ID2={user2_id}")

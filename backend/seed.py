# backend/seed.py
from database import init_db, SessionLocal
from models import User
from auth import hash_password

init_db()
db = SessionLocal()
for username, password, role in [("teacher1", "pass123", "teacher"), ("student1", "pass456", "student")]:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"User {username} already exists")
        continue
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    print(f"Created {role}: {username}")
db.commit()
db.close()
print("Seed done")

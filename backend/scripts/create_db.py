# backend/scripts/create_db.py
import sys
from pathlib import Path

# Allow running this file directly: add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.db import Base, engine, SessionLocal

# 关键：一定要导入 models，让 Base 注册所有表
from backend.core.db.models import User  # Season/Team/TeamSeasonStats 也会被加载进来

def init_db():
    Base.metadata.create_all(bind=engine)

    # （可选）初始化 admin 账号：如果不存在就创建
    session = SessionLocal()
    try:
        admin_email = "admin@local.com"
        existing = session.query(User).filter_by(email=admin_email).first()
        if not existing:
            admin = User(
                name="admin",
                email=admin_email,
                password="admin123",  # 你后面可以改成 hash
                role="admin"
            )
            session.add(admin)
            session.commit()
            print("✅ Admin user created:", admin_email, "password=admin123")
        else:
            print("ℹ️ Admin user already exists:", admin_email)
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database and tables created.")

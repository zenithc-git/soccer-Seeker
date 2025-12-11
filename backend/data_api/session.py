# backend/data_api/session.py
from contextlib import contextmanager
from core.db import SessionLocal  # 这里 core.db.__init__ 里 re-export 了 SessionLocal

@contextmanager
def get_session():
    """统一的 Session 管理，所有 DAL 函数都用它。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
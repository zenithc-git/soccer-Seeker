"""Service-layer access to shared database objects."""

from backend.core.db import Base, SessionLocal, engine

__all__ = ["Base", "SessionLocal", "engine"]

"""SQLite via SQLAlchemy. Schema auto-created on first import."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker, relationship

DB_PATH = os.environ.get("CODING_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "coding.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def _fk_on(conn, _rec):
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(40), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(16), nullable=False)
    email = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    submissions = relationship("Submission", back_populates="user")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(Integer, nullable=False, index=True)
    language = Column(String(20), nullable=False, default="python")
    code = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    verdict = Column(String(200), nullable=False, default="")
    passed = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    time_ms = Column(Integer, nullable=False, default=0)
    memory_kb = Column(Integer, nullable=False, default=0)
    detail = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="submissions")

def init_db():
    Base.metadata.create_all(engine)

def get_session() -> Session:
    return sessionmaker(bind=engine)()

init_db()

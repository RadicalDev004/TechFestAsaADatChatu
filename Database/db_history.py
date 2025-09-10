# conversations_repo.py
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from Database.db_register import Base
from sqlalchemy import (
    create_engine, Column, String, DateTime, func, Index, BigInteger,
    Sequence, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

# ---------- Types ----------
Role = Literal["user", "assistant"]

@dataclass
class ConversationDTO:
    id: int
    clinic_id: str
    title: str
    created_at: datetime
    messages: List[Dict[str, Any]]

# ---------- DB setup ----------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/postgres"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# ---------- Model ----------
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(BigInteger, Sequence("conversations_seq"), primary_key=True)
    clinic_id = Column(String(6), ForeignKey("clinics.clinic_id"), nullable=False)
    title = Column(Text, nullable=False, server_default="New conversation")
    # ✅ store messages as JSONB (list of {"role":..., "content":...})
    messages = Column(MutableList.as_mutable(JSONB), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_conversations_clinic", "clinic_id"),
        Index("idx_conversations_created", "created_at"),
    )

# ---------- Init ----------
def init_db(max_retries: int = 30, delay_seconds: float = 1.0) -> None:
    import time
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            if attempt == max_retries:
                raise
            time.sleep(delay_seconds)

# ---------- CRUD ----------
def list_messages(conversation_id: int) -> list[dict]:
    with SessionLocal() as session:
        row = (
            session.query(
                Conversation.id,
                Conversation.messages,
                Conversation.created_at,
            )
            .filter(Conversation.id == conversation_id)
            .one_or_none()
        )
        if not row:
            return []

        msgs = row.messages or []
        return [
            {
                "id": i,  # synthetic index
                "conversation_id": conversation_id,
                "role": m.get("role"),
                "content": m.get("content", ""),
                "created_at": row.created_at,
            }
            for i, m in enumerate(msgs, start=1)
        ]

def create_conversation(clinic_id: str, title: str = "New conversation") -> int:
    safe_title = (title or "").strip() or "New conversation"
    with SessionLocal.begin() as session:
        obj = Conversation(clinic_id=clinic_id, title=safe_title, messages=[])
        session.add(obj)
        session.flush()  # assigns PK
        return obj.id

def list_conversations(clinic_id: str) -> List[ConversationDTO]:
    with SessionLocal() as session:
        rows = (
            session.query(Conversation)
            .filter(Conversation.clinic_id == clinic_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )
        return [
            ConversationDTO(
                id=r.id,
                clinic_id=r.clinic_id,
                title=r.title,
                created_at=r.created_at,
                messages=r.messages or [],
            )
            for r in rows
        ]

def get_conversation(conversation_id: int, clinic_id: str) -> Optional[ConversationDTO]:
    with SessionLocal() as session:
        r = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.clinic_id == clinic_id)
            .one_or_none()
        )
        if not r:
            return None
        return ConversationDTO(
            id=r.id,
            clinic_id=r.clinic_id,
            title=r.title,
            created_at=r.created_at,
            messages=r.messages or [],
        )

def rename_conversation(conversation_id: int, clinic_id: str, new_title: str) -> None:
    safe_title = (new_title or "").strip() or "New conversation"
    with SessionLocal.begin() as session:
        r = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.clinic_id == clinic_id)
            .one_or_none()
        )
        if r:
            r.title = safe_title

def delete_conversation(conversation_id: int, clinic_id: str) -> None:
    with SessionLocal.begin() as session:
        session.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.clinic_id == clinic_id
        ).delete()

def add_message(conversation_id: int, clinic_id: str, role: Role, content: str) -> None:
    if role not in ("user", "assistant"):
        raise ValueError("role must be 'user' or 'assistant'")
    with SessionLocal.begin() as session:
        r = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.clinic_id == clinic_id)
            .one_or_none()
        )
        if not r:
            return
        msgs = r.messages or []
        msgs.append({"role": role, "content": content})
        r.messages = msgs  # reassign to mark dirty (MutableList also tracks append)

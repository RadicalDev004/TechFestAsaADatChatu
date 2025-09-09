from dataclasses import dataclass
from typing import Literal
import duckdb
from Database.db_register import DB  # DB = Path("./data/clinic.duckdb")

Role = Literal["user", "assistant"]

@dataclass(frozen=True)
class ConversationDTO:
    id: int
    clinic_id: str
    title: str
    created_at: str

@dataclass(frozen=True)
class MessageDTO:
    id: int
    conversation_id: int
    role: Role
    content: str
    created_at: str

def ensure_tables() -> None:
    con = duckdb.connect(str(DB))
    try:
        con.execute("CREATE SEQUENCE IF NOT EXISTS conversations_seq;")
        con.execute("CREATE SEQUENCE IF NOT EXISTS messages_seq;")

        con.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id BIGINT PRIMARY KEY DEFAULT nextval('conversations_seq'),
            clinic_id TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'New conversation',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_conversations_clinic
                FOREIGN KEY (clinic_id) REFERENCES clinics(clinic_id)
        );
        """)

        con.execute("CREATE INDEX IF NOT EXISTS idx_conversations_clinic ON conversations(clinic_id);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);")

        con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id BIGINT PRIMARY KEY DEFAULT nextval('messages_seq'),
            conversation_id BIGINT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user','assistant')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_messages_conversation
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );
        """)

        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_convo ON messages(conversation_id);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);")
    finally:
        con.close()


def create_conversation(clinic_id: str, title: str = "New conversation") -> int:
    ensure_tables()
    con = duckdb.connect(str(DB))
    try:
        row = con.execute(
            "INSERT INTO conversations (clinic_id, title) VALUES (?, ?) RETURNING id;",
            [clinic_id, title.strip() or "New conversation"],
        ).fetchone()
        return int(row[0])
    finally:
        con.close()

def list_conversations(clinic_id: str) -> list[ConversationDTO]:
    con = duckdb.connect(str(DB))
    try:
        rows = con.execute("""
            SELECT id, clinic_id, title, created_at
            FROM conversations
            WHERE clinic_id = ?
            ORDER BY created_at DESC;
        """, [clinic_id]).fetchall()
        return [ConversationDTO(*r) for r in rows]
    finally:
        con.close()

def get_conversation(conversation_id: int, clinic_id: str) -> ConversationDTO | None:
    con = duckdb.connect(str(DB))
    try:
        row = con.execute("""
            SELECT id, clinic_id, title, created_at
            FROM conversations
            WHERE id = ? AND clinic_id = ?
            LIMIT 1;
        """, [conversation_id, clinic_id]).fetchone()
        return ConversationDTO(*row) if row else None
    finally:
        con.close()

def rename_conversation(conversation_id: int, clinic_id: str, new_title: str) -> None:
    con = duckdb.connect(str(DB))
    try:
        con.execute("""
            UPDATE conversations
            SET title = ?
            WHERE id = ? AND clinic_id = ?;
        """, [new_title.strip() or "New conversation", conversation_id, clinic_id])
    finally:
        con.close()

def delete_conversation(conversation_id: int, clinic_id: str) -> None:
    con = duckdb.connect(str(DB))
    try:
        con.execute("DELETE FROM messages WHERE conversation_id = ?;", [conversation_id])
        con.execute("DELETE FROM conversations WHERE id = ? AND clinic_id = ?;", [conversation_id, clinic_id])
    finally:
        con.close()

def add_message(conversation_id: int, role: Role, content: str) -> int:
    if role not in ("user", "assistant"):
        raise ValueError("role must be 'user' or 'assistant'")
    con = duckdb.connect(str(DB))
    try:
        row = con.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            RETURNING id;
        """, [conversation_id, role, content]).fetchone()
        return int(row[0])
    finally:
        con.close()

def list_messages(conversation_id: int) -> list[MessageDTO]:
    con = duckdb.connect(str(DB))
    try:
        rows = con.execute("""
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC;
        """, [conversation_id]).fetchall()
        return [MessageDTO(*r) for r in rows]
    finally:
        con.close()

def title_from_text(text: str, max_words: int = 8) -> str:
    words = (text or "").strip().split()
    return " ".join(words[:max_words]) if words else "New conversation"
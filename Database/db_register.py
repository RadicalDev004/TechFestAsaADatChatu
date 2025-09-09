# Database/clinics.py
import duckdb, secrets
from pathlib import Path
from typing import Optional
from Backend.core.security import hash_secret, verify_secret

DB = Path("./data/clinic.duckdb")


def _new_id() -> str:
    # 6 hex chars, lowercase (e.g., "70b5bd")
    return secrets.token_hex(3)


def ensure_table() -> None:
    con = duckdb.connect(str(DB))
    con.execute("""
    CREATE TABLE IF NOT EXISTS clinics (
      clinic_id VARCHAR(6) PRIMARY KEY,
      name TEXT,
      password_hash TEXT NOT NULL,
      conversation_history_id TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      CHECK (length(clinic_id)=6),
      CHECK (regexp_full_match(clinic_id, '^[0-9a-f]{6}$'))
    );
    """)
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_clinics_id ON clinics(clinic_id);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_clinics_convo ON clinics(conversation_history_id);")
    con.close()


def register_clinic(name: str, password_plain: str, conversation_history_id: Optional[str] = None) -> str:
    """Generate a unique clinic_id and insert with bcrypt hash."""
    ensure_table()
    con = duckdb.connect(str(DB))
    # generate an ID not present in DB
    for _ in range(20):
        cid = _new_id()
        exists = con.execute("SELECT 1 FROM clinics WHERE clinic_id = ? LIMIT 1;", [cid]).fetchone()
        if not exists:
            break
    else:
        con.close()
        raise RuntimeError("Could not generate unique clinic_id")

    pwd_hash = hash_secret(password_plain)

    con.execute(
        "INSERT INTO clinics (clinic_id, name, password_hash, conversation_history_id) VALUES (?, ?, ?, ?);",
        [cid, name, pwd_hash, conversation_history_id],
    )
    con.close()
    return cid


def get_clinic_name(clinic_id: str) -> Optional[str]:
    ensure_table()
    con = duckdb.connect(str(DB))
    row = con.execute("SELECT name FROM clinics WHERE clinic_id = ? LIMIT 1;", [clinic_id]).fetchone()
    con.close()
    return row[0] if row else None


def authenticate(clinic_id: str, password_plain: str) -> bool:
    """Read stored bcrypt hash and verify the plain password."""
    ensure_table()
    con = duckdb.connect(str(DB))
    row = con.execute(
        "SELECT password_hash FROM clinics WHERE clinic_id = ? LIMIT 1;",
        [clinic_id],
    ).fetchone()
    con.close()
    if not row:
        return False
    return verify_secret(password_plain, row[0])

def set_conversation_history_id(clinic_id: str, conversation_history_id: Optional[str]) -> None:
    ensure_table()
    con = duckdb.connect(str(DB))
    con.execute("UPDATE clinics SET conversation_history_id=? WHERE clinic_id=?;", [conversation_history_id, clinic_id])
    con.close()


if __name__ == "__main__":
    ensure_table()
    cid = register_clinic("Demo Clinic", "demo_password", None)
    print("Registered clinic_id:", cid)
    print("Auth OK?:", authenticate(cid, "demo_password"))

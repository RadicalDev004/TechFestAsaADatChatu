from pathlib import Path
from sqlalchemy import create_engine
import duckdb

DB_PATH = str(Path("./data/mydb.duckdb").resolve())

CANONICAL_CFG = {
    "threads": "4",
    "memory_limit": "4GB",
    "temp_directory": "/tmp/duckdb",
}
READ_ONLY = False

# --- SQLAlchemy engine for LangChain / SQL tools ---
def get_engine():
    # SAME DSN + SAME connect_args everywhere
    return create_engine(
        f"duckdb:///{DB_PATH}",
        connect_args={"config": CANONICAL_CFG, "read_only": READ_ONLY},
        pool_pre_ping=True,  # helps detect dead conns
    )

# --- Raw duckdb connection (only if needed) ---
_singleton_con = None
def get_duckdb_connection():
    global _singleton_con
    if _singleton_con is None:
        _singleton_con = duckdb.connect(DB_PATH, config=CANONICAL_CFG, read_only=READ_ONLY)
    return _singleton_con

def close_duckdb_connection():
    global _singleton_con
    if _singleton_con is not None:
        try:
            _singleton_con.close()
        finally:
            _singleton_con = None

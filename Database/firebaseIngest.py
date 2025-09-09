# Database/firebaseIngest.py
import duckdb
import pandas as pd
from pathlib import Path
import shutil
import re

from Database.firebaseActions import download_all_from_firebase

# project root = parent of Database/
ROOT_DIR = Path(__file__).resolve().parent.parent
DB = ROOT_DIR / "data" / "clinic.duckdb"
DB.parent.mkdir(parents=True, exist_ok=True)

# CSVs live next to this file: Database/clinicCSV/<clinic_id>/
CSV_DIR = Path(__file__).resolve().parent / "clinicCSV"
CSV_DIR.mkdir(parents=True, exist_ok=True)

# -------- utils --------
_SNAKE = re.compile(r"[^0-9a-zA-Z]+")
def _to_snake(s: str) -> str:
    s = s.strip()
    s = _SNAKE.sub("_", s).strip("_").lower()
    if not s:
        s = "col"
    if s[0].isdigit():
        s = "_" + s
    return s

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    seen, new_cols = {}, []
    for c in df.columns:
        base = _to_snake(str(c))
        name, i = base, 2
        while name in seen:
            name = f"{base}_{i}"; i += 1
        seen[name] = True
        new_cols.append(name)
    df.columns = new_cols
    return df

def _quote_identifier(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'

def _table_name_for(clinic_id: str, csv_path: Path) -> str:
    return f"{clinic_id} {csv_path.stem}"

def _ingest_one(con: duckdb.DuckDBPyConnection, table_name: str, csv_path: Path) -> int:
    try:
        df = pd.read_csv(csv_path)
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")
    except pd.errors.EmptyDataError:
        qname = _quote_identifier(table_name)
        con.execute(f"CREATE OR REPLACE TABLE {qname} AS SELECT NULL AS _empty WHERE 1=0;")
        return 0

    qname = _quote_identifier(table_name)
    if df.empty:
        df = _normalize_columns(df)
        con.register("df0", df.head(0))
        con.execute(f"CREATE OR REPLACE TABLE {qname} AS SELECT * FROM df0;")
        con.unregister("df0")
        return 0

    df = _normalize_columns(df)
    con.register("df", df)
    con.execute(f"CREATE OR REPLACE TABLE {qname} AS SELECT * FROM df;")
    con.unregister("df")
    return int(con.execute(f"SELECT COUNT(*) FROM {qname};").fetchone()[0])

# -------- main ingest -------- this is used after the person uploads their CSV
def ingest_clinic_from_firebase(clinic_id: str) -> None:
    clinic_dir = CSV_DIR / clinic_id
    if clinic_dir.exists():
        shutil.rmtree(clinic_dir)
    clinic_dir.mkdir(parents=True, exist_ok=True)

    downloaded = download_all_from_firebase(clinic_id, clinic_dir)
    if not downloaded:
        print(f"No CSV files found under '{clinic_id}/'")
        return

    csvs = sorted(p for p in clinic_dir.iterdir() if p.suffix.lower() == ".csv")
    if not csvs:
        print(f"No CSV files for clinic '{clinic_id}'.")
        return

    con = duckdb.connect(str(DB))
    try:
        for csv_path in csvs:
            tname = _table_name_for(clinic_id, csv_path)
            rows = _ingest_one(con, tname, csv_path)
            print(f"Ingested {rows} rows into table: {tname}")
    finally:
        con.close()

if __name__ == "__main__":
    ingest_clinic_from_firebase("test_id")

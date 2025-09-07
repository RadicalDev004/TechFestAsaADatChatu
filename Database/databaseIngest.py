# Database/databaseIngest.py
import duckdb, pandas as pd, unicodedata
from pathlib import Path

CSV = Path("./healthcare_dataset.csv")  # adjust if needed
DB = Path("./data/clinic.duckdb")
DB.parent.mkdir(parents=True, exist_ok=True)

def _norm_name(s):
    if pd.isna(s):
        return None, None
    s = " ".join(str(s).strip().split())
    disp = s.title()
    key = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
    return disp, key

def ingestion():
    df = pd.read_csv(CSV)

    # normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # parse dates and billing
    df["date_of_admission"] = pd.to_datetime(df["date_of_admission"], errors="coerce").dt.date
    df["discharge_date"]    = pd.to_datetime(df["discharge_date"], errors="coerce").dt.date
    df["billing_amount"]    = pd.to_numeric(df["billing_amount"], errors="coerce")

    # normalize names
    if "name" not in df.columns:
        raise SystemExit("Expected 'name' column in CSV")

    disp, key = zip(*df["name"].map(_norm_name))
    df["patient_name"] = list(disp)
    df["patient_name_key"] = list(key)
    df.drop(columns=["name"], inplace=True)

    # drop duplicate names entirely (keep only unique patient names)
    counts = df["patient_name"].value_counts()
    dupes = counts[counts > 1].index
    before = len(df)
    df = df[~df["patient_name"].isin(dupes)].copy()
    after = len(df)

    print(f"Dropped {before - after} rows due to duplicate patient names.")

    # load into DuckDB
    con = duckdb.connect(str(DB))
    con.register("df", df)
    con.execute("DROP VIEW IF EXISTS vw_entries;")
    con.execute("DROP TABLE IF EXISTS entries;")
    con.execute("CREATE TABLE entries AS SELECT * FROM df;")
    con.execute("CREATE OR REPLACE VIEW vw_entries AS SELECT * FROM entries;")
    con.execute("CREATE INDEX IF NOT EXISTS idx_entries_namekey ON entries(patient_name_key);")

    total = con.execute("SELECT COUNT(*) FROM vw_entries;").fetchone()[0]
    print(f"Rows kept: {total}")
    con.close()

if __name__ == "__main__":
    ingestion()

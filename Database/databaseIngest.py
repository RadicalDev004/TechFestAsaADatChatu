# Database/databaseIngest.py
import duckdb, pandas as pd, unicodedata, hashlib, re
from pathlib import Path

CSV = Path("./healthcare_dataset.csv")  # adjust if needed
DB = Path("./data/clinic.duckdb")
DB.parent.mkdir(parents=True, exist_ok=True)

def _norm_name(s):
    """
    Normalizes:
      - compresses spaces
      - disp: display form (Title Case, preserves diacritics)
      - key : ASCII without diacritics, lowercase (for hashing/keys)
    """
    if pd.isna(s):
        return None, None
    s = " ".join(str(s).strip().split())
    disp = s.title()
    key = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
    return disp, key

def _gen_id_from_name(name_key: str | None, length: int = 16) -> str | None:
    """
    Generates a stable ID from the normalized key (without diacritics, lowercase).
    Uses SHA-256 and truncates to 'length' hex chars (default 16).
    For None -> None.
    """
    if not name_key:
        return None
    return hashlib.sha256(name_key.encode("utf-8")).hexdigest()[:length]

# ── only the first token up to ANY common separator: space, comma, ';', '-', tab, etc.
_SEP_PATTERN = re.compile(r"[,\;\-\s]+")

def _first_token_until_any_sep(s: str | None) -> str | None:
    """
    Returns the initial substring up to the first separator (space, ',', ';', '-', tab...).
    Ex.: 'Regina Maria - Policlinica' -> 'Regina'
         'Sanador-Centrul'            -> 'Sanador'
         'Spitalul, Sectia 1'         -> 'Spitalul'
    """
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s).strip()
    if not s:
        return None
    # split once on the first separator encountered
    return _SEP_PATTERN.split(s, maxsplit=1)[0]

def ingestion():
    df = pd.read_csv(CSV)

    # normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # parse dates and billing
    if "date_of_admission" in df.columns:
        df["date_of_admission"] = pd.to_datetime(df["date_of_admission"], errors="coerce").dt.date
    if "discharge_date" in df.columns:
        df["discharge_date"]    = pd.to_datetime(df["discharge_date"], errors="coerce").dt.date
    if "billing_amount" in df.columns:
        df["billing_amount"]    = pd.to_numeric(df["billing_amount"], errors="coerce")

    # normalize names (obligatoriu 'name')
    if "name" not in df.columns:
        raise SystemExit("Expected 'name' column in CSV")

    disp, key = zip(*df["name"].map(_norm_name))
    df["patient_name"] = list(disp)
    # key generated after the normalized name (without diacritics)
    df["patient_id"] = [_gen_id_from_name(k) for k in key]
    # we no longer keep the 'name' column
    df.drop(columns=["name"], inplace=True)

    # ── clinic from 'hospital': retain only the first word up to the separator + generate clinic_id
    if "hospital" in df.columns:
        # draw the first token
        hospital_first = df["hospital"].map(_first_token_until_any_sep)
        # normalize (disp/key)
        cdisp, ckey = zip(*hospital_first.map(_norm_name))
        df["clinic_name"] = list(cdisp)
        # shorter clinic_id (12 hex), from the key without diacritics
        df["clinic_id"] = [_gen_id_from_name(k, length=12) for k in ckey]
        # optionally, we remove the original 'hospital' column so as not to duplicate the information
        df.drop(columns=["hospital"], inplace=True)
    else:
        # if there is no 'hospital', we still add the columns as None, so that the schema remains stable
        df["clinic_name"] = None
        df["clinic_id"] = None

    # drop duplicate names entirely (keep only unique patient names)
    counts = df["patient_name"].value_counts(dropna=True)
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
    # index on generated keys
    con.execute("CREATE INDEX IF NOT EXISTS idx_entries_patientid ON entries(patient_id);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_entries_clinicid  ON entries(clinic_id);")

    total = con.execute("SELECT COUNT(*) FROM vw_entries;").fetchone()[0]
    print(f"Rows kept: {total}")
    con.close()

if __name__ == "__main__":
    ingestion()



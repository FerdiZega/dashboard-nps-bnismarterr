# uploader.py
import os
import pandas as pd
import tempfile
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extras import execute_values

DB_CONN = os.getenv("DB_CONN")
if not DB_CONN:
    raise RuntimeError("DB_CONN env var tidak ditemukan.")

# helper: fastest bulk load using COPY FROM STDIN
def copy_csv_to_table(csv_path, table_name="nps_data", conn_string=DB_CONN):
    # conn_string is full postgres URI
    import psycopg2
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        # Assumes CSV header names match table column names
        cur.copy_expert(sql=f"COPY {table_name} FROM STDIN WITH CSV HEADER DELIMITER ','", file=f)
    conn.commit()
    cur.close()
    conn.close()

def process_upload_file(filepath, table_name="nps_data", chunksize=200_000):
    """
    filepath can be .csv or .xlsx
    For xlsx, convert to csv in chunks (pandas read_excel chunking not supported directly),
    so we read via pandas.read_csv after saving temp csv.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext in [".xls", ".xlsx"]:
        # convert to csv temporary (streaming by reading with pandas in chunks via engine openpyxl -> to_csv in parts)
        # simpler: read in chunks by sheets/rows using pandas (may require memory). For huge xlsx, prefer csv input.
        df = pd.read_excel(filepath, engine="openpyxl")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df.to_csv(tmp.name, index=False)
        tmp.close()
        copy_csv_to_table(tmp.name, table_name)
        os.unlink(tmp.name)
    elif ext == ".csv":
        # for large csv, we can do direct COPY
        copy_csv_to_table(filepath, table_name)
    else:
        raise ValueError("Unsupported file format. Use .csv or .xlsx")

# Example usage for CLI:
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python uploader.py path_to_file.csv")
        sys.exit(1)
    path = sys.argv[1]
    print("Start uploading:", path)
    process_upload_file(path)
    print("Done.")

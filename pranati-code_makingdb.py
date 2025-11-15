import os
import pandas as pd
from sqlalchemy import create_engine

DATA_DIR = "imf_tables"
DB_PATH = "imf_data.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

def clean(col):
    col = col.strip().lower()
    col = col.replace(" ", "_").replace("-", "_").replace("/", "_").replace(".", "_")

    if col and col[0].isdigit():
        col = "col_" + col

    return col

for file in os.listdir(DATA_DIR):
    if file.endswith(".csv"):
        table_name = os.path.splitext(file)[0].lower()
        csv_path = os.path.join(DATA_DIR, file)

        print(f"Loading {file} → table `{table_name}`")

        df = pd.read_csv(csv_path)
        df.columns = [clean(c) for c in df.columns]

        df.to_sql(table_name, engine, index=False, if_exists="replace")

print("All  of te IMF tables imported successfully into imf_data.db")
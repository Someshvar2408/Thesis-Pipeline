
from sqlalchemy import inspect, text
from app.ingest import ingest_csv
from app.queries import fetch_all_data
from app.db import engine
from app.config import TABLE_NAME
from app.db_utils import table_exists, create_flow_table
import pandas as pd
def ingest_csv(csv_path: str):
    df = pd.read_csv(csv_path)

    # Enforce numeric types
    df["HighFlow"] = df["HighFlow"].astype(float)
    df["HighFlowRAW"] = df["HighFlowRAW"].astype(float)
    df["LowFlow"] = df["LowFlow"].astype(float)
    df["LowFlowRAW"] = df["LowFlowRAW"].astype(float)
    df["ArgonFlow"] = df["ArgonFlow"].astype(float)
    df["ArgonFlowRAW"] = df["ArgonFlowRAW"].astype(float)
    df["Energy_kWh"] = df["Energy_kWh"].astype(float)
    df["Power_W"] = df["Power_W"].astype(float)

    # NEW: explicit table control
    if not table_exists(TABLE_NAME):
        create_flow_table()

    df.to_sql(TABLE_NAME, engine, if_exists="append", index=False)

    return len(df)
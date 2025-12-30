import pandas as pd
from app.db import engine
from app.config import TABLE_NAME

def fetch_all_data():
    query = f"""
    SELECT *
    FROM {TABLE_NAME}
    ORDER BY Timestamp
    """
    return pd.read_sql(query, engine)


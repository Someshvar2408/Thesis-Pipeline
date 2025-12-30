from sqlalchemy import inspect, Table, Column, MetaData, Float, String
from app.db import engine
from app.config import TABLE_NAME

def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_flow_table():
    metadata = MetaData()

    Table(
        "DoERun",
        metadata,
        Column("Timestamp", String),
        Column("HighFlow", Float),
        Column("HighFlowRAW", Float),
        Column("LowFlow", Float),
        Column("LowFlowRAW", Float),
        Column("ArgonFlow", Float),
        Column("ArgonFlowRAW", Float),
        Column("Energy_kWh", Float),
        Column("Power_W", Float),
    )

    metadata.create_all(engine)

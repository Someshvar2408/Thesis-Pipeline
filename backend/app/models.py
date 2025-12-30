from sqlalchemy import Table, Column, MetaData, Float, String
from app.config import TABLE_NAME
from app.db import engine

metadata = MetaData()

DoERun = Table(
    TABLE_NAME,
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

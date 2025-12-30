
from sqlalchemy import create_engine
from app.config import DB_FILE

engine = create_engine(
    f"sqlite:///{DB_FILE}",
    connect_args={"check_same_thread": False},
    echo=False
)


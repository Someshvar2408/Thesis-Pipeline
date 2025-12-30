from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
import uuid, shutil, os

from app.ingest import ingest_csv
from app.queries import fetch_all_data
from app.db import engine, TABLE_NAME  # Add this import

app = FastAPI(title="Flow & Power Analytics Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "..", "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open(os.path.join(FRONTEND_DIR, "index.html")) as f:
        return f.read()

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    temp_path = f"/tmp/{uuid.uuid4()}.csv"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rows = ingest_csv(temp_path)
    return {"rows_inserted": rows}

@app.get("/timeseries")
def get_timeseries():
    df = fetch_all_data()
    
    # Handle empty dataframe
    if df.empty:
        return {
            "Timestamp": [],
            "HighFlowRAW": [],
            "LowFlowRAW": [],
            "ArgonFlowRAW": [],
            "Power_W": [],
        }
    
    # Convert timestamps to ISO format strings for proper JSON serialization
    return {
        "Timestamp": df["Timestamp"].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist(),
        "HighFlowRAW": df["HighFlowRAW"].fillna(0).tolist(),  # Replace NaN with 0
        "LowFlowRAW": df["LowFlowRAW"].fillna(0).tolist(),
        "ArgonFlowRAW": df["ArgonFlowRAW"].fillna(0).tolist(),
        "Power_W": df["Power_W"].fillna(0).tolist(),
    }

@app.get("/db-status")
def db_status():
    inspector = inspect(engine)
    table_exists = TABLE_NAME in inspector.get_table_names()

    row_count = 0
    if table_exists:
        with engine.connect() as conn:
            row_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            ).scalar()

    return {
        "table_exists": table_exists,
        "row_count": row_count
    }
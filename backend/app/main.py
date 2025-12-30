
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uuid, shutil

from app.ingest import ingest_csv
from app.queries import fetch_all_data

app = FastAPI(title="Flow & Power Analytics Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    return {
        "Timestamp": df["Timestamp"].tolist(),
        "HighFlowRAW": df["HighFlowRAW"].tolist(),
        "LowFlowRAW": df["LowFlowRAW"].tolist(),
        "ArgonFlowRAW": df["ArgonFlowRAW"].tolist(),
        "Power_W": df["Power_W"].tolist(),
    }

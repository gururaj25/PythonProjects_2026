from fastapi import FastAPI, UploadFile, File
from backend.parser_engine import extract_files_from_text
from backend.reconstructor import reconstruct_project

app = FastAPI(title="AI Project Source Downloader")

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/parse")
async def parse_ai_response(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    parsed = extract_files_from_text(content)
    return {"files": parsed}

@app.post("/reconstruct")
async def reconstruct(data: dict):
    output = reconstruct_project(data)
    return output
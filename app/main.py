# app/main.py
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from app.agent import run_topic_agent, run_pdf_agent
from app.tools.pdf_extract import extract_pdf_text
from app.tools.tracing import read_trace

app = FastAPI(title="Research Assistant Agent", version="0.1.0")

class TopicRequest(BaseModel):
    topic: str

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/run/topic")
def run_topic(req: TopicRequest):
    return run_topic_agent(req.topic)

@app.post("/run/pdf")
async def run_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    full_text, _page_texts = extract_pdf_text(pdf_bytes, max_pages=30)
    return run_pdf_agent(file.filename, full_text)

@app.get("/trace/{trace_id}")
def get_trace(trace_id: str):
    txt = read_trace(trace_id)
    return {"trace_id": trace_id, "trace": txt}

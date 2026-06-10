import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.pipeline import load_and_index_pdfs, load_vectorstore, get_rag_chain, ask_question

app = FastAPI(
    title="Australian Legal Case Analyser",
    description="RAG-powered legal case analysis using Gemini AI",
    version="1.0.0"
)

UPLOAD_DIR = "data/cases"
os.makedirs(UPLOAD_DIR, exist_ok=True)

rag_chain = None

class QuestionInput(BaseModel):
    question: str

@app.get("/")
def root():
    return {
        "message": "Australian Legal Case Analyser API",
        "version": "1.0.0",
        "docs": "/docs",
        "author": "Abhay Singh Wazir"
    }

@app.post("/ingest")
async def ingest_pdfs(files: List[UploadFile] = File(...)):
    global rag_chain
    saved_paths = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF")
        path = os.path.join(UPLOAD_DIR, file.filename)
        with open(path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_paths.append(path)

    try:
        num_chunks = load_and_index_pdfs(saved_paths)
        vectorstore = load_vectorstore()
        rag_chain = get_rag_chain(vectorstore)
        return {
            "message": f"Successfully ingested {len(saved_paths)} PDF(s)",
            "chunks_created": num_chunks,
            "files": [file.filename for file in files]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask(input: QuestionInput):
    global rag_chain
    if rag_chain is None:
        try:
            vectorstore = load_vectorstore()
            rag_chain = get_rag_chain(vectorstore)
        except:
            raise HTTPException(
                status_code=400,
                detail="No documents indexed yet. Please upload PDFs first via /ingest"
            )
    try:
        result = ask_question(rag_chain, input.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "Gemini 1.5 Flash",
        "index_exists": os.path.exists("faiss_index")
    }
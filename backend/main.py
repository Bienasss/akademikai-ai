#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from pathlib import Path

from backend.config import settings
from backend.services.pdf_processor import PDFProcessor
from backend.services.vectorizer import Vectorizer
from backend.services.rag_service import RAGService

app = FastAPI(title="Akademikai AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pdf_processor = PDFProcessor()
vectorizer = Vectorizer()
rag_service = RAGService()


class VectorizeRequest(BaseModel):
    file_path: Optional[str] = None
    directory: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_by: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_by: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    return {"message": "Akademikai AI Backend API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/vectorize")
async def vectorize_documents(request: VectorizeRequest):
    try:
        if request.file_path:
            result = await pdf_processor.process_file(request.file_path)
            if result:
                await vectorizer.add_documents(result)
                return {"status": "success", "message": f"Processed {request.file_path}", "chunks": len(result)}
        elif request.directory:
            results = await pdf_processor.process_directory(request.directory)
            if results:
                await vectorizer.add_documents(results)
                return {"status": "success", "message": f"Processed {len(results)} chunks from {request.directory}", "chunks": len(results)}
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Either file_path or directory must be provided"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/search")
async def search_documents(request: SearchRequest):
    try:
        results = await rag_service.search(
            query=request.query,
            top_k=request.top_k,
            filter_by=request.filter_by
        )
        return {"status": "success", "results": results}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/query")
async def query_documents(request: QueryRequest):
    try:
        results = await rag_service.query(
            query=request.query,
            top_k=request.top_k,
            filter_by=request.filter_by
        )
        return {"status": "success", "context": results["context"], "sources": results["sources"]}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/documents")
async def list_documents():
    try:
        documents = await vectorizer.list_documents()
        return {"status": "success", "documents": documents}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

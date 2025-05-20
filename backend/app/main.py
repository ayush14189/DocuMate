from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from typing import List
import httpx
from dotenv import load_dotenv

from . import models, db
from .pdf_utils import extract_text_from_pdf, split_text_into_chunks, create_vector_store, search_vector_store

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("vector_stores", exist_ok=True)

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(db.get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save file
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Extract text and create vector store
    text = extract_text_from_pdf(file_path)
    chunks = split_text_into_chunks(text)
    
    # Create vector store
    vector_store_path = os.path.join("vector_stores", f"{file.filename}.pkl")
    create_vector_store(chunks, vector_store_path)
    
    # Save to database
    db_document = models.PDFDocument(
        filename=file.filename,
        file_path=file_path,
        vector_store_path=vector_store_path
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return {"message": "PDF uploaded successfully", "document_id": db_document.id}

@app.get("/ask-question")
async def ask_question(
    question: str = Query(..., description="The question to ask about the PDF"),
    document_id: int = Query(..., description="ID of the uploaded PDF document"),
    db: Session = Depends(db.get_db)
):
    # Get document from database
    document = db.query(models.PDFDocument).filter(models.PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Search for relevant chunks
    relevant_chunks = search_vector_store(question, document.vector_store_path)
    
    # Create context from relevant chunks
    context = "\n".join(relevant_chunks)
    
    # Generate answer using Groq
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on the provided context of the pdf."
                        },
                        {
                            "role": "user",
                            "content": f"Context: {context}\n\nQuestion: {question}"
                        }
                    ]
                }
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")
    
    return {"answer": answer} 
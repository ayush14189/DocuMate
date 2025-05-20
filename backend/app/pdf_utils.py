import PyPDF2
from typing import List
import os
import pickle
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

def create_vector_store(chunks: List[str], store_path: str):
    """Create vector store from text chunks using TF-IDF."""
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    
    # Generate TF-IDF vectors
    tfidf_matrix = vectorizer.fit_transform(chunks)
    
    # Save vectorizer and matrix
    store_data = {
        'vectorizer': vectorizer,
        'tfidf_matrix': tfidf_matrix,
        'chunks': chunks
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    
    # Save to file
    with open(store_path, 'wb') as f:
        pickle.dump(store_data, f)
    
    return store_data

def search_vector_store(query: str, store_path: str, top_k: int = 3) -> List[str]:
    """Search vector store for relevant chunks using TF-IDF similarity."""
    # Load store data
    with open(store_path, 'rb') as f:
        store_data = pickle.load(f)
    
    # Transform query using saved vectorizer
    query_vector = store_data['vectorizer'].transform([query])
    
    # Calculate similarities
    similarities = cosine_similarity(query_vector, store_data['tfidf_matrix'])[0]
    
    # Get top k indices
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    # Return relevant chunks
    return [store_data['chunks'][i] for i in top_indices] 
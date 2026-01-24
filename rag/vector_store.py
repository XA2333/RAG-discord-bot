import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import shutil

VECTOR_DB_PATH = "chroma_db"

def get_embedding_function():
    # Using a lightweight local embedding model
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def create_vector_db(chunks):
    # Clear existing DB if needed (optional strategy)
    if os.path.exists(VECTOR_DB_PATH):
        shutil.rmtree(VECTOR_DB_PATH)

    embedding_fn = get_embedding_function()
    
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_fn,
        persist_directory=VECTOR_DB_PATH
    )
    print(f"Vector DB created at {VECTOR_DB_PATH}")
    return db

def load_vector_db():
    embedding_fn = get_embedding_function()
    if not os.path.exists(VECTOR_DB_PATH):
        return None
        
    db = Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embedding_fn
    )
    return db

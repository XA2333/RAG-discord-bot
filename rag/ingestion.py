import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.vector_store import create_vector_db

def load_documents(data_dir: str):
    documents = []
    # Load PDFs
    for file in glob.glob(os.path.join(data_dir, "*.pdf")):
        try:
            loader = PyPDFLoader(file)
            documents.extend(loader.load())
            print(f"Loaded PDF: {file}")
        except Exception as e:
            print(f"Failed to load PDF {file}: {e}")

    # Load Text files
    for file in glob.glob(os.path.join(data_dir, "*.txt")):
        try:
            loader = TextLoader(file, encoding='utf-8')
            documents.extend(loader.load())
            print(f"Loaded Text: {file}")
        except Exception as e:
            print(f"Failed to load Text {file}: {e}")
            
    return documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

if __name__ == "__main__":
    # Assuming script is run from root or rag package
    # Adjust path to data folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_path = os.path.join(project_root, "data")
    
    print(f"Loading documents from {data_path}...")
    docs = load_documents(data_path)
    if docs:
        chunks = split_documents(docs)
        create_vector_db(chunks)
        print("Ingestion complete.")
    else:
        print("No documents found.")

import sys
import traceback

try:
    from rag import ingestion
    print("Import successful")
    # Simulate the main block
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming this script is in project root
    data_path = os.path.join(current_dir, "data")
    print(f"Loading documents from {data_path}...")
    docs = ingestion.load_documents(data_path)
    if docs:
        chunks = ingestion.split_documents(docs)
        ingestion.create_vector_db(chunks)
        print("Ingestion complete.")
except Exception:
    with open("error_log.txt", "w") as f:
        traceback.print_exc(file=f)
    traceback.print_exc()

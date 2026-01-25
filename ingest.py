import os
import glob
from backend.ingestion_service import IngestionService

def run_ingestion():
    print("🚀 Starting Ingestion (Using Service)...")
    service = IngestionService()
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    
    print(f"Found {len(pdf_files)} PDFs in {data_dir}")
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"\nProcessing {filename}...")
        count = service.process_local_file(pdf_path)
        print(f"✅ Ingested {count} chunks.")

if __name__ == "__main__":
    run_ingestion()

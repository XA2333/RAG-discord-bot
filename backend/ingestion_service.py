import os
import io
import pypdf
import time
from backend.azure_client import AzureAIClient
from backend.mongo_store import MongoVectorStore

BATCH_SIZE = 10
CHUNK_SIZE = 1000
OVERLAP = 200

class IngestionService:
    def __init__(self):
        self.azure = AzureAIClient()
        self.store = MongoVectorStore()

    def _chunk_text(self, text):
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + CHUNK_SIZE, text_len)
            chunk = text[start:end]
            chunks.append(chunk)
            if end == text_len:
                break
            start = end - OVERLAP
        return chunks

    def _clean_text(self, text):
        return " ".join(text.split())

    def process_file_bytes(self, file_bytes: bytes, filename: str) -> int:
        """
        Ingest a file from bytes (Discord Attachment)
        Returns: Number of chunks ingested.
        """
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_file)
            return self._process_reader(reader, filename)
        except Exception as e:
            raise ValueError(f"Failed to process PDF bytes: {e}")

    def process_local_file(self, file_path: str) -> int:
        """
        Ingest a local file path (CLI).
        Returns: Number of chunks ingested.
        """
        try:
            reader = pypdf.PdfReader(file_path)
            filename = os.path.basename(file_path)
            return self._process_reader(reader, filename)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return 0

    def _process_reader(self, reader, filename: str) -> int:
        buffer = []
        total_chunks = 0
        
        for page_idx, page in enumerate(reader.pages):
            raw_text = page.extract_text()
            if not raw_text: continue
            
            text = self._clean_text(raw_text)
            chunks = self._chunk_text(text)
            
            for chunk_idx, chunk_str in enumerate(chunks):
                chunk_id = f"{filename}:p{page_idx+1:03d}:c{chunk_idx:03d}"
                doc = {
                    "chunk_id": chunk_id,
                    "text": chunk_str,
                    "source": filename,
                    "metadata": {"page": page_idx+1}
                }
                buffer.append(doc)
                
                if len(buffer) >= BATCH_SIZE:
                    self._upload_batch(buffer)
                    total_chunks += len(buffer)
                    buffer = []
        
        if buffer:
            self._upload_batch(buffer)
            total_chunks += len(buffer)
            
        return total_chunks

    def _upload_batch(self, batch):
        texts = [d["text"] for d in batch]
        embeddings = self.azure.generate_embeddings(texts)
        
        for i, doc in enumerate(batch):
            doc["embedding"] = embeddings[i]
            
        self.store.upload_chunks_batch(batch)

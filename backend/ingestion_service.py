import io
import time
import os
from backend.azure_client import AzureAIClient
from backend.mongo_store import MongoVectorStore
from backend.pdf_parser import PDFParser

BATCH_SIZE = 10

class IngestionService:
    def __init__(self):
        self.azure = AzureAIClient()
        self.store = MongoVectorStore()

    def process_stream(self, file_stream, filename: str):
        """
        Generator that yields progress strings.
        """
        chunks_buffer = []
        total_chunks = 0
        pages_processed = set()
        
        # Generator yields chunks one by one from parser
        parser_gen = PDFParser.parse_and_chunk(file_stream, filename)
        
        for doc in parser_gen:
            pages_processed.add(doc["metadata"]["page"])
            chunks_buffer.append(doc)
            
            if len(chunks_buffer) >= BATCH_SIZE:
                yield f"   embedding batch ({len(chunks_buffer)} items)..."
                self._upload_batch(chunks_buffer)
                total_chunks += len(chunks_buffer)
                chunks_buffer = []
        
        # Flush remaining
        if chunks_buffer:
            yield f"   embedding final batch ({len(chunks_buffer)} items)..."
            self._upload_batch(chunks_buffer)
            total_chunks += len(chunks_buffer)
            
        yield f"✅ Finished: {total_chunks} chunks from {len(pages_processed)} pages."

    def _upload_batch(self, batch):
        try:
            texts = [d["text"] for d in batch]
            embeddings = self.azure.generate_embeddings(texts)
            
            for i, doc in enumerate(batch):
                doc["embedding"] = embeddings[i]
                
            self.store.upload_chunks_batch(batch)
            time.sleep(0.2) # Rate limit politeness
        except Exception as e:
            print(f"Batch upload failed: {e}")
            raise

    # CLI Compat
    def ingest_file_sync(self, filepath: str):
        print(f"Processing {filepath}...")
        with open(filepath, 'rb') as f:
            for status in self.process_stream(f, filename=os.path.basename(filepath)):
                print(status)

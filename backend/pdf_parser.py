import io
import pypdf

class PDFParser:
    @staticmethod
    def parse_and_chunk(file_stream, filename: str, chunk_size=1000, overlap=200):
        """
        Parses a PDF stream (bytes or file object) and yields chunk dictionaries.
        """
        try:
            reader = pypdf.PdfReader(file_stream)
        except Exception as e:
            raise ValueError(f"Invalid PDF file: {e}")

        for page_idx, page in enumerate(reader.pages):
            raw_text = page.extract_text()
            if not raw_text:
                continue

            # Clean text
            clean_text = " ".join(raw_text.split())
            if not clean_text:
                continue

            # Chunking logic
            start = 0
            text_len = len(clean_text)
            
            chunk_indices = []
            
            # If text is shorter than chunk size, take it all
            if text_len <= chunk_size:
                 chunk_indices.append((0, text_len))
            else:
                while start < text_len:
                    end = min(start + chunk_size, text_len)
                    chunk_indices.append((start, end))
                    
                    if end == text_len:
                        break
                        
                    start = end - overlap

            for i, (s, e) in enumerate(chunk_indices):
                chunk_text = clean_text[s:e]
                
                # Stable ID
                chunk_id = f"{filename}:p{page_idx+1:03d}:c{i:03d}"
                
                yield {
                    "text": chunk_text,
                    "source": filename,
                    "chunk_id": chunk_id,
                    "metadata": {"page": page_idx+1}
                }

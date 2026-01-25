from backend.azure_client import AzureAIClient
from backend.mongo_store import MongoVectorStore

class RAGPipeline:
    def __init__(self):
        self.azure = AzureAIClient()
        self.store = MongoVectorStore()

    def answer_question(self, question: str) -> str:
        try:
            # 1. Embed
            query_vec = self.azure.generate_embeddings([question])[0]
            
            # 2. Search
            results = self.store.search(query_vec, limit=6)
            
            # DEBUG: Print scores to console
            print(f"Query: {question}")
            for r in results:
                print(f" - Hit: {r['chunk_id']} | Score: {r.get('score', 0):.4f}")

            # 3. Filter
            # Lowered threshold to 0.5 for debugging (was 0.65)
            context_docs = [r for r in results if r.get('score', 0) > 0.5]
            
            if not context_docs:
                return "The answer was not found in the documents."
            
            # 4. Format Context & Citations
            seen_source_pages = set()
            context_text_list = []
            citations = []
            
            for doc in context_docs:
                # Deduplicate roughly by page to avoid redundant text
                source_identifier = f"{doc['source']}:p{doc['chunk_id'].split(':p')[1].split(':')[0]}"
                
                if source_identifier not in seen_source_pages:
                    seen_source_pages.add(source_identifier)
                    context_text_list.append(f"Content from {doc['source']}:\n{doc['text']}")
                    
                # Always add citation for transparency
                citations.append(f"({doc['source']}#{doc['chunk_id'].split(':c')[-1]})")

            full_context = "\n\n".join(context_text_list)
            citation_str = ", ".join(list(set(citations))) # Unique citations

            # 5. Prompt
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Answer the user's question using ONLY the provided context. If the answer is not present, explicitly state that you cannot find it."},
                {"role": "user", "content": f"Context:\n{full_context}\n\nQuestion: {question}"}
            ]
            
            # 6. Generate
            answer = self.azure.chat_completion(messages)
            
            return f"{answer}\n\n**Sources:** {citation_str}"

        except Exception as e:
            return f"Error encountered: {str(e)}"

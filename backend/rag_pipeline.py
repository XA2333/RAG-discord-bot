import time
from backend.azure_client import AzureAIClient
from backend.mongo_store import MongoVectorStore
from backend.observability import ObservabilityLogger
import hashlib

def hash_user(user_id: str) -> str:
    if not user_id:
        return "anon"
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:12]

class RAGPipeline:
    def __init__(self):
        self.azure = AzureAIClient()
        self.store = MongoVectorStore()
        self.logger = ObservabilityLogger()

    def answer_question(self, question: str, user_id: str = None) -> str:
        t0 = time.time()
        start_time = t0
        hashed_id = hash_user(user_id)
        
        # Sanitize for logging (truncate to 50 chars)
        q_snip = (question[:47] + "...") if len(question) > 50 else question
        
        try:
            # 1. Embed
            t_embed_start = time.time()
            query_vec = self.azure.generate_embeddings([question])[0]
            dur_embed = (time.time() - t_embed_start) * 1000
            
            # 2. Search
            t_search_start = time.time()
            results = self.store.search(query_vec, limit=6)
            dur_search = (time.time() - t_search_start) * 1000
            
            # DEBUG: Print scores to console
            print(f"Query: {question}")
            for r in results:
                print(f" - Hit: {r['chunk_id']} | Score: {r.get('score', 0):.4f}")

            # 3. Filter
            # Lowered threshold to 0.5 for debugging (was 0.65)
            context_docs = [r for r in results if r.get('score', 0) > 0.5]
            
            if not context_docs:
                self.logger.log_event("query", "ok", (time.time() - t0)*1000, 
                                      meta={"result": "no_context", "full_question": question},
                                      question_snip=q_snip, hashed_user_id=hashed_id)
                return "The answer was not found in the documents."
            
            # 4. Format Context & Citations
            seen_source_pages = set()
            context_text_list = []
            citations = []
            
            for doc in context_docs:
                source_identifier = f"{doc['source']}:p{doc['chunk_id'].split(':p')[1].split(':')[0]}"
                
                if source_identifier not in seen_source_pages:
                    seen_source_pages.add(source_identifier)
                    context_text_list.append(f"Content from {doc['source']}:\n{doc['text']}")
                    
                citations.append(f"({doc['source']}#{doc['chunk_id'].split(':c')[-1]})")

            full_context = "\n\n".join(context_text_list)
            citation_str = ", ".join(list(set(citations))) # Unique citations

            # 5. Prompt
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Answer the user's question using ONLY the provided context. If the answer is not present, explicitly state that you cannot find it."},
                {"role": "user", "content": f"Context:\n{full_context}\n\nQuestion: {question}"}
            ]
            
            # 6. Generate
            t_chat_start = time.time()
            answer, usage = self.azure.chat_completion(messages)
            dur_chat = (time.time() - t_chat_start) * 1000
            
            total_dur = (time.time() - t0) * 1000
            
            # Log Success
            a_snip = (answer[:47] + "...") if len(answer) > 50 else answer
            
            self.logger.log_event("query", "ok", total_dur, meta={
                "embed_ms": round(dur_embed),
                "search_ms": round(dur_search),
                "chat_ms": round(dur_chat),
                "sources_count": len(context_docs),
                "full_question": question,
                "full_answer": answer,
                "citations": citations,
                "usage": usage
            }, question_snip=q_snip, answer_snip=a_snip, hashed_user_id=hashed_id)

            return f"{answer}\n\n**Sources:** {citation_str}"

        except Exception as e:
            total_dur = (time.time() - t0) * 1000
            self.logger.log_event("query", "fail", total_dur, error_type=type(e).__name__, 
                                  meta={"error_msg": str(e), "full_question": question},
                                  question_snip=q_snip if 'q_snip' in locals() else None,
                                  hashed_user_id=hashed_id if 'hashed_id' in locals() else None)
            return f"Error encountered: {str(e)}"

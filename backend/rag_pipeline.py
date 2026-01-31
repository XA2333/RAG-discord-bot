"""
RAG Pipeline Module

This module implements the core Retrieval-Augmented Generation (RAG) pipeline.
It handles:
- Query embedding generation
- Vector similarity search
- Context filtering based on configurable threshold
- LLM response generation with conversation memory

Configuration (via .env):
- RAG_THRESHOLD: Similarity score threshold for context filtering (default: 0.5)
- RAG_MAX_HISTORY: Maximum conversation turns to remember per user (default: 5)
- RAG_TOP_K: Number of chunks to retrieve from vector search (default: 6)
"""

import os
import time
import hashlib
from collections import defaultdict
from dotenv import load_dotenv
from backend.azure_client import AzureAIClient
from backend.mongo_store import MongoVectorStore
from backend.observability import ObservabilityLogger

load_dotenv()

# =============================================================================
# CONFIGURATION - These can be adjusted in .env file
# =============================================================================

# Similarity threshold for filtering search results.
# Higher values (0.7+) = stricter matching, may miss relevant content
# Lower values (0.3-0.5) = more lenient, may include less relevant content
# Recommended: Start with 0.5, adjust based on your document corpus
RAG_THRESHOLD = float(os.getenv("RAG_THRESHOLD", "0.5"))

# Maximum number of conversation turns to remember per user session.
# Each turn = one question + one answer
# Higher values provide more context but increase token usage
RAG_MAX_HISTORY = int(os.getenv("RAG_MAX_HISTORY", "5"))

# Number of document chunks to retrieve from vector search
# More chunks = more context but higher latency and token usage
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))


def hash_user(user_id: str) -> str:
    """Hash user ID for privacy in logs."""
    if not user_id:
        return "anon"
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:12]


class RAGPipeline:
    """
    Main RAG Pipeline class with conversation memory support.
    
    Features:
    - Per-user conversation history (stored in memory)
    - Configurable similarity threshold
    - Source citations in responses
    - Observability logging
    
    Usage:
        pipeline = RAGPipeline()
        response = pipeline.answer_question("What is AI?", user_id="user123")
    """
    
    def __init__(self):
        self.azure = AzureAIClient()
        self.store = MongoVectorStore()
        self.logger = ObservabilityLogger()
        
        # Session memory: stores conversation history per user
        # Format: {user_id: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        self.conversation_history = defaultdict(list)
        
        print(f"[RAGPipeline] Initialized with threshold={RAG_THRESHOLD}, "
              f"max_history={RAG_MAX_HISTORY}, top_k={RAG_TOP_K}")

    def _get_history_context(self, user_id: str) -> str:
        """
        Get formatted conversation history for a user.
        Returns a string summarizing recent Q&A pairs.
        """
        history = self.conversation_history.get(user_id, [])
        if not history:
            return ""
        
        # Format history as readable context
        history_text = "Previous conversation:\n"
        for i in range(0, len(history), 2):
            if i + 1 < len(history):
                q = history[i]["content"]
                a = history[i + 1]["content"]
                # Truncate long entries
                q = q[:200] + "..." if len(q) > 200 else q
                a = a[:300] + "..." if len(a) > 300 else a
                history_text += f"User: {q}\nAssistant: {a}\n\n"
        
        return history_text

    def _add_to_history(self, user_id: str, question: str, answer: str):
        """
        Add a Q&A pair to the user's conversation history.
        Maintains a sliding window of RAG_MAX_HISTORY turns.
        """
        if not user_id:
            return
        
        self.conversation_history[user_id].append({"role": "user", "content": question})
        self.conversation_history[user_id].append({"role": "assistant", "content": answer})
        
        # Keep only the last N turns (each turn = 2 messages)
        max_messages = RAG_MAX_HISTORY * 2
        if len(self.conversation_history[user_id]) > max_messages:
            self.conversation_history[user_id] = self.conversation_history[user_id][-max_messages:]

    def clear_history(self, user_id: str):
        """Clear conversation history for a specific user."""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]

    def answer_question(self, question: str, user_id: str = None) -> str:
        """
        Answer a question using RAG with conversation memory.
        
        Args:
            question: The user's question
            user_id: Optional user identifier for session memory
            
        Returns:
            Answer string with source citations, or error message
        """
        t0 = time.time()
        hashed_id = hash_user(user_id)
        
        # Sanitize for logging (truncate to 50 chars)
        q_snip = (question[:47] + "...") if len(question) > 50 else question
        
        try:
            # 1. Generate query embedding
            t_embed_start = time.time()
            query_vec = self.azure.generate_embeddings([question])[0]
            dur_embed = (time.time() - t_embed_start) * 1000
            
            # 2. Vector similarity search
            t_search_start = time.time()
            results = self.store.search(query_vec, limit=RAG_TOP_K)
            dur_search = (time.time() - t_search_start) * 1000
            
            # DEBUG: Print scores to console
            print(f"Query: {question}")
            for r in results:
                print(f" - Hit: {r['chunk_id']} | Score: {r.get('score', 0):.4f}")

            # 3. Filter results by similarity threshold
            # Only include chunks with score above RAG_THRESHOLD
            context_docs = [r for r in results if r.get('score', 0) > RAG_THRESHOLD]
            
            if not context_docs:
                self.logger.log_event("query", "ok", (time.time() - t0)*1000, 
                                      meta={"result": "no_context", "full_question": question},
                                      question_snip=q_snip, hashed_user_id=hashed_id)
                return "The answer was not found in the documents."
            
            # 4. Format context and citations
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
            citation_str = ", ".join(list(set(citations)))  # Unique citations
            
            # 5. Get conversation history for context
            history_context = self._get_history_context(user_id)

            # 6. Build prompt with history and context
            system_prompt = """You are a helpful assistant. Answer the user's question using ONLY the provided context. 
If the answer is not present in the context, explicitly state that you cannot find it.
If the user refers to something from the previous conversation, use that context to understand their question."""

            user_prompt = ""
            if history_context:
                user_prompt += f"{history_context}\n---\n\n"
            user_prompt += f"Context from documents:\n{full_context}\n\nQuestion: {question}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 7. Generate response
            t_chat_start = time.time()
            answer, usage = self.azure.chat_completion(messages)
            dur_chat = (time.time() - t_chat_start) * 1000
            
            total_dur = (time.time() - t0) * 1000
            
            # 8. Save to conversation history
            self._add_to_history(user_id, question, answer)
            
            # Log success
            a_snip = (answer[:47] + "...") if len(answer) > 50 else answer
            
            self.logger.log_event("query", "ok", total_dur, meta={
                "embed_ms": round(dur_embed),
                "search_ms": round(dur_search),
                "chat_ms": round(dur_chat),
                "sources_count": len(context_docs),
                "full_question": question,
                "full_answer": answer,
                "citations": citations,
                "usage": usage,
                "history_turns": len(self.conversation_history.get(user_id, [])) // 2
            }, question_snip=q_snip, answer_snip=a_snip, hashed_user_id=hashed_id)

            return f"{answer}\n\n**Sources:** {citation_str}"

        except Exception as e:
            total_dur = (time.time() - t0) * 1000
            self.logger.log_event("query", "fail", total_dur, error_type=type(e).__name__, 
                                  meta={"error_msg": str(e), "full_question": question},
                                  question_snip=q_snip if 'q_snip' in locals() else None,
                                  hashed_user_id=hashed_id if 'hashed_id' in locals() else None)
            return f"Error encountered: {str(e)}"


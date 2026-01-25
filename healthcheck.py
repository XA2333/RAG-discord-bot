import sys
import re
from backend.azure_client import AzureAIClient
from backend.mongo_store import MongoVectorStore

def run_healthcheck():
    print("🏥 Starting RAG Bot Healthcheck (Strict Mode)...\n")
    
    # Init Clients
    try:
        azure = AzureAIClient()
        store = MongoVectorStore()
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        sys.exit(1)
        
    # 1. Embedding Check
    print("[1/3] Testing Azure Embeddings (ping)...")
    try:
        # Generate one embedding
        vec = azure.generate_embeddings(["ping"])[0]
        dim = len(vec)
        print(f"   ✅ HTTP 200 OK. Dimension: {dim}")
    except Exception as e:
        print(f"   ❌ Embedding Failed: {e}")
        sys.exit(1)

    # 2. Chat Check
    print("\n[2/3] Testing Azure Chat (DeepSeek)...")
    try:
        # Specific system prompt validation
        messages = [
            {"role": "system", "content": "Return ONLY the exact string: ok"},
            {"role": "user", "content": "hello"}
        ]
        response = azure.chat_completion(messages)
        print(f"   Response (Raw): '{response}'")
        
        # Already cleaned by client, but double check logic here implies we trust the client
        # or we verify the client's cleaning. 
        # Since I updated the client to return clean content, 'response' should just be 'ok'.
        
        if response == "ok":
            print("   ✅ Chat Response Verified (Strict Match).")
        else:
            print(f"   ❌ Chat Failed: Expected 'ok', got '{response}'")
            sys.exit(1)
    except Exception as e:
        print(f"   ❌ Chat Failed: {e}")
        sys.exit(1)

    # 3. Real Mongo Check
    print("\n[3/3] Testing MongoDB $vectorSearch (Real Query)...")
    try:
        # Use the generated vector from Step 1 to query
        results = store.search(vec, limit=1)
        # We don't care if we find results, we care if the command SUCCEEDS.
        # If index is missing or dim mismatch, Atlas throws error.
        print("   ✅ $vectorSearch execution successful.")
    except Exception as e:
        print(f"   ❌ MongoDB Search Failed: {e}")
        print("   -> Check if 'vector_index' exists in Atlas.")
        print(f"   -> Check if index dimensions match {dim}.")
        sys.exit(1)

    print("\n✨ HEALTHCHECK PASSED. Deployment Ready.")

if __name__ == "__main__":
    run_healthcheck()

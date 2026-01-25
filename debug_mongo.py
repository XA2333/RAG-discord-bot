import os
import pymongo
from dotenv import load_dotenv
import dns.resolver

# FIX DNS
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

load_dotenv()

def debug_mongo():
    uri = os.getenv("MONGO_URI")
    client = pymongo.MongoClient(uri)
    db = client["rag_db"]
    collection = db["chunks"]
    
    print("--- MONGO DEBUG ---")
    
    # 1. Count
    count = collection.count_documents({})
    print(f"Total Documents: {count}")
    
    if count == 0:
        print("❌ Collection is empty! Ingestion failed silently?")
        return

    # 2. Inspect one
    doc = collection.find_one({})
    if "embedding" in doc:
        dim = len(doc["embedding"])
        print(f"Sample Embedding Dimension: {dim}")
        print(f"Sample Source: {doc.get('source')}")
        
        # 3. Check Index
        print("\nChecking Indexes...")
        indexes = list(collection.list_search_indexes())
        if not indexes:
            print("⚠️ No Search Indexes found via driver (might need Atlas UI to see them).")
        else:
            for idx in indexes:
                print(f"Found Index: {idx.get('name')}")
                print(f"Def: {idx}")
    else:
        print("❌ Sample document HAS NO EMBEDDING field!")

if __name__ == "__main__":
    debug_mongo()

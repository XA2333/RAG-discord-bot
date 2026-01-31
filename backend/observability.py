import os
import time
import uuid
import datetime
import pymongo
from dotenv import load_dotenv

load_dotenv()

class ObservabilityLogger:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI")
        if not self.uri:
            print("⚠️ Observability disabled: MONGO_URI missing.")
            self.collection = None
            return

        try:
            # Re-use existing client if possible, but here we create new for safety/isolation
            import dns.resolver
            dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
            dns.resolver.default_resolver.nameservers = ['8.8.8.8']

            self.client = pymongo.MongoClient(self.uri)
            self.db = self.client["rag_db"]
            self.collection = self.db["observability_events"]
            
            # Ensure TTL index (7 days)
            self.collection.create_index("ts", expireAfterSeconds=7 * 24 * 3600)
            # Index for faster dashboard queries
            self.collection.create_index([("ts", -1)])
            self.collection.create_index("event")
            self.collection.create_index("hashed_user_id")
            self.collection.create_index("status")
        except Exception as e:
            print(f"⚠️ Observability init failed: {e}")
            self.collection = None

    def log_event(self, event_type: str, status: str, duration_ms: float = 0, error_type: str = None, 
                  meta: dict = None, question_snip: str = None, answer_snip: str = None, hashed_user_id: str = None):
        if self.collection is None:
            return

        try:
            entry = {
                "ts": datetime.datetime.utcnow(),
                "event": event_type,
                "status": status,
                "duration_ms": duration_ms,
                "error_type": error_type,
                "meta": meta or {},
                "question_snip": question_snip,
                "answer_snip": answer_snip,
                "hashed_user_id": hashed_user_id,
                "correlation_id": str(uuid.uuid4())
            }
            self.collection.insert_one(entry)
        except Exception as e:
            print(f"Failed to log event: {e}")

    def get_metrics_summary(self):
        """Aggregate stats for dashboard."""
        if self.collection is None:
            return {}

        now = datetime.datetime.utcnow()
        last_24h = now - datetime.timedelta(hours=24)

        pipeline = [
            {"$match": {"ts": {"$gte": last_24h}}},
            {"$group": {
                "_id": "$event",
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_ms"},
                "errors": {"$sum": {"$cond": [{"$eq": ["$status", "fail"]}, 1, 0]}},
                "total_tokens": {"$sum": {"$ifNull": ["$meta.usage.total_tokens", 0]}},
                "completion_tokens": {"$sum": {"$ifNull": ["$meta.usage.completion_tokens", 0]}}
            }}
        ]
        
        try:
            results = list(self.collection.aggregate(pipeline))
            
            # Simple aggregations
            metrics = {
                "total_queries_24h": 0,
                "error_rate_24h": 0,
                "latency_p50": 0,
                "latency_p95": 0,
                "breakdown": {}
            }
            
            total_ops = 0
            total_errors = 0
            
            for r in results:
                evt = r["_id"]
                count = r["count"]
                metrics["breakdown"][evt] = {
                    "count": count,
                    "avg_ms": round(r["avg_duration"] or 0, 1),
                    "errors": r["errors"]
                }
                if evt == "query":
                    metrics["total_queries_24h"] = count
                
                total_ops += count
                total_errors += r["errors"]

            if total_ops > 0:
                metrics["error_rate_24h"] = round((total_errors / total_ops) * 100, 1)

            # Calculate token velocity (approximate)
            # We don't have exact time windows for every request in this loop, but we can Average it
            total_tokens = sum(d.get("total_tokens", 0) for d in results if d["_id"] == "query")
            completion_tokens = sum(d.get("completion_tokens", 0) for d in results if d["_id"] == "query")
            
            metrics["token_stats"] = {
                "total_24h": total_tokens,
                "completion_24h": completion_tokens
            }

            return metrics
        except Exception as e:
            print(f"Metrics aggregation failed: {e}")
            return {}
    
    def get_logs(self, limit=50, status=None, event_type=None) -> list[dict]:
        """
        Fetch logs with optional filtering.
        """
        if self.collection is None:
            return []
        
        query = {}
        if status:
            query["status"] = status
        if event_type:
            query["event"] = event_type
            
        try:
            cursor = self.collection.find(query, {"_id": 0}).sort("ts", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            return []

    def get_db_stats(self):
        """Get chunk/source counts."""
        try:
           chunks_col = self.db["chunks"]
           return {
               "total_chunks": chunks_col.count_documents({}),
               "total_sources": len(chunks_col.distinct("source"))
           }
        except:
            return {"total_chunks": 0, "total_sources": 0}

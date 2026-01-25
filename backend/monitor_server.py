import os
import io
from functools import wraps
from flask import Flask, jsonify, render_template, request, Response, abort
from dotenv import load_dotenv
from backend.observability import ObservabilityLogger
from backend.mongo_store import MongoVectorStore
from backend.ingestion_service import IngestionService

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv("MAX_UPLOAD_MB", 10)) * 1024 * 1024

# Services
logger = ObservabilityLogger()
store = MongoVectorStore()
ingestion_service = IngestionService()



# --- WEB UI ROUTES ---

@app.route('/')
def index():
    return render_template('overview.html', active_page='overview')

@app.route('/documents')
def documents():
    return render_template('documents.html', active_page='documents')

@app.route('/logs')
def logs():
    return render_template('logs.html', active_page='logs')

# --- API ENDPOINTS ---

@app.route('/api/stats')
def get_stats():
    metrics = logger.get_metrics_summary()
    logs = logger.get_logs(limit=20)
    db_stats = logger.get_db_stats()
    return jsonify({
        "metrics": metrics,
        "logs": logs,
        "db_stats": db_stats
    })

@app.route('/api/logs')
def get_logs():
    limit = int(request.args.get('limit', 50))
    status = request.args.get('status')
    logs = logger.get_logs(limit=limit, status=status)
    return jsonify(logs)

@app.route('/api/docs/list')
def list_docs():
    docs = store.list_sources()
    return jsonify(docs)

@app.route('/api/docs/preview')
def preview_doc():
    source = request.args.get('source')
    if not source:
        return jsonify({"error": "source required"}), 400
    
    chunks = store.get_preview(source)
    return jsonify({"content": "\n\n...[Snippet]...\n\n".join(chunks)})

@app.route('/api/upload/pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF allowed"}), 400

    try:
        # Read file into memory (Flask spooled file)
        # IngestionService expects a file-like object
        stream = io.BytesIO(file.read())
        
        # Run ingestion (blocking for now)
        logs = []
        for status in ingestion_service.process_stream(stream, file.filename):
            logs.append(status)
            
        return jsonify({"message": "Upload successful", "logs": logs})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete/pdf', methods=['POST'])
def delete_pdf():
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({"error": "filename required"}), 400
    
    try:
        count = store.delete_by_source(filename)
        return jsonify({"message": "Deleted", "chunks_removed": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print(f"🚀 Monitor running on http://localhost:5000 (Open Access)")
    app.run(host='0.0.0.0', port=5000, debug=False)

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

@app.route('/settings')
def settings():
    return render_template('settings.html', active_page='settings')

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

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    KEYS_TO_MANAGE = ["AZURE_AI_ENDPOINT", "AZURE_AI_KEY", "MONGO_URI", "DISCORD_TOKEN"]

    if request.method == 'GET':
        # Read .env manually to assume latest values on disk
        current_vals = {}
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, 'r') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        if k in KEYS_TO_MANAGE:
                            current_vals[k] = v
        return jsonify(current_vals)

    if request.method == 'POST':
        data = request.json
        new_lines = []
        
        # Read existing
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        # Update or Append
        updated_keys = set()
        for line in lines:
            key_part = line.split('=')[0].strip()
            if key_part in KEYS_TO_MANAGE and key_part in data:
                new_lines.append(f"{key_part}={data[key_part]}\n")
                updated_keys.add(key_part)
            else:
                new_lines.append(line)
        
        # Append missing keys
        for k in KEYS_TO_MANAGE:
            if k in data and k not in updated_keys:
                new_lines.append(f"{k}={data[k]}\n")

        # Write back
        start_marker = "# --- AUTO MANAGED SETTINGS ---\n"
        final_content = "".join(new_lines)
        
        with open(ENV_PATH, 'w') as f:
            f.write(final_content)
            
        return jsonify({"message": "Settings saved to .env. Please RESTART the application."})

if __name__ == "__main__":
    print(f"🚀 Monitor running on http://localhost:5000 (Open Access)")
    app.run(host='0.0.0.0', port=5000, debug=False)

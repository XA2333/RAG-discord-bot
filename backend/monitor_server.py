"""
RAG Bot Monitor Server

A Flask dashboard for monitoring and managing the RAG Discord Bot.
Features:
- Session-based authentication (first user to register becomes admin)
- View query logs and statistics
- Manage documents (upload/delete PDFs)
- Configure settings

Authentication:
- User credentials stored in backend/dashboard_users.json
- Passwords hashed with werkzeug.security
- Session-based login with Flask secret key
"""

import os
import io
import json
import secrets
from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from backend.observability import ObservabilityLogger
from backend.mongo_store import MongoVectorStore
from backend.ingestion_service import IngestionService

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv("MAX_UPLOAD_MB", 10)) * 1024 * 1024
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

# User storage file path
USERS_FILE = os.path.join(os.path.dirname(__file__), 'dashboard_users.json')

# Services (lazy init to handle import errors gracefully)
logger = None
store = None
ingestion_service = None


def init_services():
    """Initialize backend services."""
    global logger, store, ingestion_service
    try:
        logger = ObservabilityLogger()
        store = MongoVectorStore()
        ingestion_service = IngestionService()
        print("[Monitor] Backend services initialized.")
    except Exception as e:
        print(f"[Monitor] Warning: Could not init services: {e}")


# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================

def load_users() -> dict:
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    """Save users to JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def login_required(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# AUTH ROUTES
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    users = load_users()
    
    # If no users exist, redirect to register
    if not users:
        return redirect(url_for('register'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password."
    
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page."""
    users = load_users()
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 4:
            error = "Password must be at least 4 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif username in users:
            error = "Username already exists."
        else:
            # Create user
            users[username] = {
                'password': generate_password_hash(password),
                'is_first_user': len(users) == 0  # First user is admin
            }
            save_users(users)
            
            # Auto-login
            session['user'] = username
            return redirect(url_for('index'))
    
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """Logout and redirect to login."""
    session.pop('user', None)
    return redirect(url_for('login'))


# =============================================================================
# WEB UI ROUTES (PROTECTED)
# =============================================================================

@app.route('/')
@login_required
def index():
    return render_template('overview.html', active_page='overview', user=session.get('user'))


@app.route('/documents')
@login_required
def documents():
    return render_template('documents.html', active_page='documents', user=session.get('user'))


@app.route('/logs')
@login_required
def logs():
    return render_template('logs.html', active_page='logs', user=session.get('user'))


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', active_page='settings', user=session.get('user'))


# =============================================================================
# API TEST ENDPOINTS (PROTECTED)
# =============================================================================

@app.route('/api/test/azure')
@login_required
def test_azure():
    """Test Azure AI connection by generating a simple embedding."""
    try:
        from backend.azure_client import AzureAIClient
        client = AzureAIClient()
        vec = client.generate_embeddings(["test"])
        if vec and len(vec) > 0 and len(vec[0]) > 0:
            return jsonify({
                "success": True,
                "message": f"Connected successfully. Embedding dimension: {len(vec[0])}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Empty response from Azure AI"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/test/mongo')
@login_required
def test_mongo():
    """Test MongoDB connection by pinging the database."""
    try:
        from backend.mongo_store import MongoVectorStore
        test_store = MongoVectorStore()
        # Try to list sources as a simple query
        sources = test_store.list_sources()
        return jsonify({
            "success": True,
            "message": f"Connected successfully. Documents in KB: {len(sources)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


# =============================================================================
# API ENDPOINTS (PROTECTED)
# =============================================================================

@app.route('/api/stats')
@login_required
def get_stats():
    if not logger:
        return jsonify({"error": "Services not initialized"}), 500
    metrics = logger.get_metrics_summary()
    logs_data = logger.get_logs(limit=20)
    db_stats = logger.get_db_stats()
    return jsonify({
        "metrics": metrics,
        "logs": logs_data,
        "db_stats": db_stats
    })


@app.route('/api/logs')
@login_required
def get_logs():
    if not logger:
        return jsonify({"error": "Services not initialized"}), 500
    limit = int(request.args.get('limit', 50))
    status = request.args.get('status')
    logs_data = logger.get_logs(limit=limit, status=status)
    return jsonify(logs_data)


@app.route('/api/docs/list')
@login_required
def list_docs():
    if not store:
        return jsonify({"error": "Services not initialized"}), 500
    docs = store.list_sources()
    return jsonify(docs)


@app.route('/api/docs/preview')
@login_required
def preview_doc():
    if not store:
        return jsonify({"error": "Services not initialized"}), 500
    source = request.args.get('source')
    if not source:
        return jsonify({"error": "source required"}), 400
    
    chunks = store.get_preview(source)
    return jsonify({"content": "\n\n...[Snippet]...\n\n".join(chunks)})


@app.route('/api/upload/pdf', methods=['POST'])
@login_required
def upload_pdf():
    if not ingestion_service:
        return jsonify({"error": "Services not initialized"}), 500
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF allowed"}), 400

    try:
        stream = io.BytesIO(file.read())
        
        upload_logs = []
        for status in ingestion_service.process_stream(stream, file.filename):
            upload_logs.append(status)
            
        return jsonify({"message": "Upload successful", "logs": upload_logs})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete/pdf', methods=['POST'])
@login_required
def delete_pdf():
    if not store:
        return jsonify({"error": "Services not initialized"}), 500
    
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
@login_required
def manage_settings():
    ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    KEYS_TO_MANAGE = ["AZURE_AI_ENDPOINT", "AZURE_AI_KEY", "MONGO_URI", "DISCORD_TOKEN", 
                      "RAG_THRESHOLD", "RAG_MAX_HISTORY", "RAG_TOP_K"]

    if request.method == 'GET':
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
        
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        updated_keys = set()
        for line in lines:
            key_part = line.split('=')[0].strip()
            if key_part in KEYS_TO_MANAGE and key_part in data:
                new_lines.append(f"{key_part}={data[key_part]}\n")
                updated_keys.add(key_part)
            else:
                new_lines.append(line)
        
        for k in KEYS_TO_MANAGE:
            if k in data and k not in updated_keys:
                new_lines.append(f"{k}={data[k]}\n")

        final_content = "".join(new_lines)
        
        with open(ENV_PATH, 'w') as f:
            f.write(final_content)
            
        return jsonify({"message": "Settings saved to .env. Please RESTART the application."})


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    init_services()
    
    users = load_users()
    if not users:
        print("🔐 No users found. First visitor will be prompted to register.")
    else:
        print(f"🔐 {len(users)} user(s) registered.")
    
    print(f"🚀 Monitor running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)


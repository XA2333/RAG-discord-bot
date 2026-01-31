# Discord RAG Bot (Strict Azure/Mongo/No-LangChain)

A production-ready Discord Bot that uses **Azure AI Foundry** (DeepSeek R1 + Embeddings) and **MongoDB Atlas** ($vectorSearch) to answer questions based on your PDF documents.

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+** (Recommend Miniconda)
- **MongoDB Atlas** Cluster (Basic Tier is fine)
- **Azure AI Foundry** Endpoint (`/models`) & Key

### 2. Configuration

Create a `.env` file (see `.env.example`):

```ini
DISCORD_TOKEN=...
AZURE_AI_ENDPOINT=https://<your-res>.services.ai.azure.com/models
AZURE_AI_KEY=...
MONGO_URI=mongodb+srv://...
DEEPSEEK_MODEL=DeepSeek-R1
EMBED_MODEL=text-embedding-3-small
MAX_UPLOAD_MB=10
```

> ⚠️ **Security**: The `.env` file is in `.gitignore` and will NOT be pushed to GitHub.

### 3. MongoDB Setup

Create a **Search Index** on `rag_db.chunks`:

- **Name**: `vector_index`
- **Definition**:

```json
{
  "fields": [
    {
      "numDimensions": 1536,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    },
    {
      "path": "source",
      "type": "filter"
    }
  ]
}
```

*(Check your embedding model dimensions! text-embedding-3-small is usually 1536)*

### 4. Installation

```powershell
pip install -r requirements.txt
```

### 5. Running

#### Option A: Easy Launchers (Recommended)

| Script | Description |
|--------|-------------|
| `start.bat` | Start the Discord Bot (double-click) |
| `start_db.bat` | Start the Monitoring Dashboard (double-click) |

#### Option B: PowerShell Scripts

```powershell
.\run_healthcheck.ps1   # Validate connections
.\run_ingest.ps1        # Load PDFs from data/ folder
.\run_bot.ps1           # Start bot
.\run_monitor.ps1       # Start dashboard
```

#### Option C: Direct Python

```powershell
python healthcheck.py      # Validate
python ingest.py           # Ingest PDFs
python main_bot.py         # Start bot
python backend/monitor_server.py  # Start dashboard
```

## 🤖 Bot Commands

| Command | Description |
| :--- | :--- |
| `!ask <query>` | Ask a question based on uploaded docs. |
| `@Bot <query>` | Mention the bot to ask quickly. |
| `!upload` | Attach a PDF to upload it to the knowledge base. |
| `!delete <name>` | Delete a document (e.g., `!delete report.pdf`). |
| `!sources` | List all documents in the database. |
| `!help` | Show an interactive command menu. |

## 🖥️ Monitoring Dashboard

Access the web dashboard at `http://localhost:5000` after running `start_db.bat`.

Features:

- View query logs and statistics
- Upload/delete documents
- Manage settings

## 🛠️ Tech Stack

- **Framework**: `discord.py` (No LangChain/LlamaIndex)
- **Client**: Raw `requests` to Azure AI Foundry REST API
- **DB**: `pymongo` with Atlas `$vectorSearch`
- **Dashboard**: Flask
- **Safety**: `<think>` tag suppression, rate limits, size limits.

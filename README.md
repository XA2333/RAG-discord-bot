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

We provide PowerShell helpers to ensure the correct environment:

**A. Healthcheck (Run First)**
Validates connections and dimension match.

```powershell
.\run_healthcheck.ps1
```

**B. Ingestion (Load Data)**
Loads PDFs from `data/` folder.

```powershell
.\run_ingest.ps1
```

**C. Start Bot**

```powershell
.\run_bot.ps1
```

## 🤖 Bot Commands

| Command | Description |
| :--- | :--- |
| `!ask <query>` | Ask a question based on uploaded docs. |
| `@Bot <query>` | Mention the bot to ask quickly. |
| `!upload` | **(Admin)** Attach a PDF to upload it instantly. |
| `!delete <name>` | **(Admin)** Delete a document (e.g., `!delete report.pdf`). |
| `!sources` | List all documents in the database. |
| `!help` | Show an interactive command button. |

## 🛠️ Tech Stack

- **Framework**: `discord.py` (No LangChain/LlamaIndex)
- **Client**: Raw `requests` to Azure AI Foundry REST API
- **DB**: `pymongo` with Atlas `$vectorSearch`
- **Safety**: `<think>` tag suppression, rate limits, size limits.

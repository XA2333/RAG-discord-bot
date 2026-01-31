# Production RAG Bot - Walkthrough

## Overview

This is a production-ready Discord RAG Bot integrated with Azure AI Foundry (DeepSeek via Serverless) and MongoDB Atlas. It features strict privacy controls, a robust RAG pipeline with citations, and a real-time monitoring dashboard.

## Features

- **DeepSeek Integration**: Uses Azure Serverless REST API with raw `requests` (no LangChain).
- **Vector Search**: MongoDB Atlas `$vectorSearch` with 1536-dim embeddings.
- **Strict Privacy**: No user content is logged. Only metrics and anonymized events.
- **Admin Tools**: `!upload` (PDFs only) and `!delete`.
- **User Interaction**: Supports `@Bot <question>` and intuitive `!help`.
- **Monitoring**: Web dashboard showing latency, error rates, and system health.

## 🚀 Getting Started

### 1. Requirements

Ensure you have the correct `.env` file with:

- `AZURE_AI_ENDPOINT` (ending in `/models`)
- `AZURE_AI_KEY`
- `MONGO_URI`
- `DISCORD_TOKEN`

### 2. Running the Bot & Dashboard

Open a terminal and run:

```powershell
.\run_bot.ps1
```

This script will:

1. Run a system Healthcheck.
2. Start the **Monitoring Dashboard** in a background window.
3. Automatically open `http://localhost:5000` in your browser.
4. Start the **Discord Bot** in the current terminal.

(To stop, press Ctrl+C in the main terminal. The dashboard window can be closed separately).

Access the dashboard at: [http://localhost:5000](http://localhost:5000)
(Open access, no login required)

## Web Dashboard Features

- **Overview**:
  - Real-time stats, latency charts, and system status.
  - **Token Usage**: Track Total Tokens (24h) and Avg/Request to monitor costs.
- **Documents**:
  - 📤 **Upload**: Drag & drop PDF upload via web UI.
  - 🗑️ **Management**: View chunk counts and delete files.
  - 👁️ **Preview**: Click "Preview" to see extracted text chunks.
- **User Logs**:
  - View user queries with **hashed User IDs** (Privacy).
  - See truncated Questions & Answers.
  - Filter by Status (OK/Fail).
  - **Details**: Click "Details" to view full question/answer and metadata.
- **Settings**:
  - View and Update API Keys/Tokens.
  - Requires application restart to apply changes.

## API Endpoints (Localhost Only)

- `POST /api/upload/pdf`: Multipart file upload.
- `POST /api/delete/pdf`: JSON `{ "filename": "x.pdf" }`.
- `GET /api/logs`: Query logs.

## Admin Commands

- `!upload`: Attach a PDF file to add it to the knowledge base.
- `!delete <filename>`: Remove a document and its chunks.
- `!sources`: List all available documents.

## Troubleshooting

- **Healthcheck Fails**: Check `healthcheck.py` output. Ensure Azure endpoint ends in `/models`.
- **No Answers**: Verify MongoDB Index is configured for `1536` dimensions and named `vector_index`.

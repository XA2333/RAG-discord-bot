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

### 2. Running the Bot

Open a terminal and run:

```powershell
.\run_bot.ps1
```

This script automatically runs a healthcheck before starting the bot.

### 3. Running the Dashboard

Open a **second** terminal and run:

```powershell
.\run_monitor.ps1
```

Access the dashboard at: [http://localhost:5000](http://localhost:5000)

## Dashboard Metrics

The dashboard auto-refreshes every 5 seconds and displays:

- **Total Queries (24h)**: Volume of questions asked.
- **Avg Latency**: Performance of the RAG pipeline.
- **Error Rate**: Percentage of failed requests.
- **Recent Events**: Live log of queries (status only, no content) and errors.

## Admin Commands

- `!upload`: Attach a PDF file to add it to the knowledge base.
- `!delete <filename>`: Remove a document and its chunks.
- `!sources`: List all available documents.

## Troubleshooting

- **Healthcheck Fails**: Check `healthcheck.py` output. Ensure Azure endpoint ends in `/models`.
- **No Answers**: Verify MongoDB Index is configured for `1536` dimensions and named `vector_index`.

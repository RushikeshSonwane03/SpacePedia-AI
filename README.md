---
title: SpacePedia AI
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

<div align="center">

# 🚀 SpacePedia AI

### Your Intelligent Companion for Exploring the Cosmos

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000.svg?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

[![LangChain](https://img.shields.io/badge/LangChain-0.1+-blue.svg?style=flat&logo=langchain&logoColor=white)](https://python.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-RAG-purple.svg)](https://github.com/langchain-ai/langgraph)

[![LLM](https://img.shields.io/badge/LLM-Groq%20Llama3-orange.svg)](https://groq.com/)
[![Embeddings](https://img.shields.io/badge/Embeddings-Google%20Gemini-blue.svg)](https://ai.google.dev/)

[![Evaluation](https://img.shields.io/badge/Evaluation-Ragas%20%2B%20Gemini-ff69b4.svg)](https://docs.ragas.io/)
[![Tests](https://img.shields.io/badge/Tests-10%2F10%20Passing-brightgreen.svg)](#testing)

<img src="images/landing_page.png" alt="SpacePedia Landing Page" width="800"/>

*A production-ready RAG-based chatbot powered by LangGraph, Groq LLM, and Google Gemini embeddings.*

[**Live Demo**](#screenshots) • [**Features**](#features) • [**Quick Start**](#quick-start) • [**Architecture**](#architecture) • [**API Docs**](#api-reference)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **3D Interactive UI** | Stunning Three.js Earth visualization with glassmorphism design |
| 🧠 **Hybrid RAG Engine** | LangGraph-powered retrieval with multi-context reasoning |
| ⚡ **500+ tokens/sec** | Groq's `llama-3.3-70b-versatile` for blazing-fast responses |
| 📚 **244 Wikipedia Sources** | Curated knowledge base with 14,000+ vector chunks |
| 💬 **Multi-turn Context** | Full conversation history with PostgreSQL persistence |
| 🔒 **Rate Limiting** | Built-in API protection with SlowAPI |
| 📊 **Ragas Evaluation** | Automated quality scoring with Gemini Flash judge |

---

## 📸 Screenshots

### Landing Page
<img src="images/landing_page.png" alt="Landing Page" width="700"/>

*Immersive 3D Earth visualization with the "Start Journey" call-to-action.*

### Chat Interface
<img src="images/chat_interface.png" alt="Chat Interface" width="700"/>

*AI-powered responses grounded in verified Wikipedia sources.*

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 15+
- API Keys: [Groq](https://console.groq.com/) and [Google AI Studio](https://aistudio.google.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/RushikeshSonwane03/SpacePedia-AI.git
cd SpacePedia

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run the Application

```bash
# Start Backend (FastAPI)
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Start Frontend (Flask + PyScript)
python -m app.web.app
```

Open **http://localhost:5000** in your browser.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Flask)                       │
│           PyScript + Three.js + Glassmorphism UI            │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│        /api/v1/query  │  /api/v1/chats  │  /api/v1/meta     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Engine                         │
│    ┌──────────┐     ┌───────────┐    ┌─────────────┐        │
│    │ Retrieve │───▶│  Reason   │───▶│  Validate   │        │
│    └──────────┘     └───────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 │  ChromaDB   │    │  Groq LLM   │    │ PostgreSQL  │
 │   (Vectors) │    │ (Llama 70B) │    │  (History)  │
 └─────────────┘    └─────────────┘    └─────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Groq `llama-3.3-70b-versatile` |
| **Embeddings** | Google Gemini `text-embedding-004` (768-dim) |
| **Vector DB** | ChromaDB with cosine similarity |
| **Orchestration** | LangGraph with typed state |
| **Backend** | FastAPI + Pydantic v2 |
| **Frontend** | Flask + PyScript + Three.js |
| **Database** | PostgreSQL + SQLAlchemy |
| **Evaluation** | Ragas with Gemini Flash judge |

---

## 📁 Project Structure

```
SpacePedia/
├── app/
│   ├── api/                    # FastAPI Backend
│   │   ├── main.py             # App entry point
│   │   ├── dependencies.py     # Rate limiting
│   │   └── routes/
│   │       ├── chat.py         # Chat endpoints
│   │       ├── query.py        # RAG query endpoint
│   │       └── meta.py         # Knowledge metadata
│   │
│   ├── core/                   # Core Configuration
│   │   ├── config.py           # Settings (API keys, DB)
│   │   ├── schemas.py          # Pydantic models
│   │   ├── logger.py           # Logging setup
│   │   └── errors.py           # Error handlers
│   │
│   ├── db/                     # Database Layer
│   │   ├── models.py           # Chat, Message models
│   │   └── session.py          # SQLAlchemy session
│   │
│   ├── ingestion/              # Data Ingestion Pipeline
│   │   ├── pipeline.py         # Main ingestion flow
│   │   ├── crawler.py          # Wikipedia scraper
│   │   ├── parser.py           # HTML parser
│   │   ├── normalizer.py       # Text normalization
│   │   ├── discovery.py        # Page discovery
│   │   ├── batch_processor.py  # Batch ingestion
│   │   ├── models.py           # Document models
│   │   └── candidates.json     # 244 curated pages
│   │
│   ├── orchestration/          # LangGraph Engine
│   │   ├── graph.py            # Graph definition
│   │   ├── nodes.py            # Retrieve, Grade, Generate
│   │   ├── state.py            # Typed state
│   │   └── memory.py           # History formatting
│   │
│   ├── rag/                    # RAG Components
│   │   ├── embedder.py         # Embedder factory
│   │   ├── embedder_gemini.py  # Gemini embeddings
│   │   ├── llm.py              # Groq/Gemini LLM client
│   │   ├── retriever.py        # Vector retrieval
│   │   ├── vector_store.py     # ChromaDB interface
│   │   ├── chunker.py          # Text chunking
│   │   ├── validator.py        # Response validation
│   │   └── engine.py           # RAG orchestration
│   │
│   └── web/                    # Flask Frontend
│       ├── app.py              # Flask app
│       ├── templates/          # HTML templates
│       └── static/             # CSS, JS, PyScript
│
├── scripts/
│   ├── ingest_data.py        # Dynamic data ingestion tool
│   ├── migrate_embeddings.py # Embedding migration utility
│   ├── verify_migration.py   # System verification
│   ├── curate_wiki_pages.py  # Wikipedia curation
│   └── generate_testset.py   # Ragas testset generator
├── tests/
│   ├── test_runner.py          # Unified test suite (10 tests)
│   ├── run_eval.py             # Ragas evaluation
│   ├── test_api_full.py        # API integration tests
│   └── verify_all.py           # System verification
│
├── images/                     # Screenshots
├── chroma_db/                  # Vector storage (14,323 chunks)
├── k8s/                        # Kubernetes configs
├── .env.example                # Environment template
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container build
├── SETUP_DB.md                 # Postgres Database Setup
└── README.md
```

---

## 🧪 Testing

Run the unified test suite:

```bash
# Interactive mode
python tests/test_runner.py

# Run all tests
python tests/test_runner.py --all

# Run specific test
python tests/test_runner.py --test 2
```

### Latest Test Results

| Test | Status | Duration |
|------|--------|----------|
| Health Check | ✅ PASS | 2.05s |
| RAG Query | ✅ PASS | 3.72s |
| Chat Flow | ✅ PASS | 8.33s |
| Multi-turn Context | ✅ PASS | 9.74s |
| Rate Limiting | ✅ PASS | 24.44s |
| Metadata API | ✅ PASS | 2.78s |
| Graph Invocation | ✅ PASS | 15.05s |
| Ingestion Pipeline | ✅ PASS | 33.30s |
| Frontend Check | ✅ PASS | 2.06s |
| Full System | ✅ PASS | 16.52s |

**Pass Rate: 100%** (10/10 tests)

---

## � Data Management

Use the dynamic ingestion tool to update the knowledge base:

```bash
# Interactive mode
python scripts/ingest_data.py

# Single URL ingestion
python scripts/ingest_data.py --url https://en.wikipedia.org/wiki/Mars --category Solar_System

# Batch ingestion from JSON
python scripts/ingest_data.py --file my_sources.json

# Refresh entire knowledge base
python scripts/ingest_data.py --refresh
```

### Knowledge Base Stats
- **244 Wikipedia articles** across 12 categories
- **14,323 vector chunks** with 768-dimensional Gemini embeddings
- Categories: Space Agencies, Commercial Space, Missions, Spacecraft, Observatories, etc.

---

## �📡 API Reference

### Query Endpoint
```bash
POST /api/v1/query
Content-Type: application/json

{
  "query": "What is the Hubble Space Telescope?"
}
```

### Response
```json
{
  "query": "What is the Hubble Space Telescope?",
  "answer": "The Hubble Space Telescope is a space-based observatory...",
  "confidence": "High",
  "reasoning": "Retrieved 3 relevant documents about Hubble...",
  "sources": [
    {"title": "Hubble Space Telescope", "url": "..."}
  ]
}
```

### Other Endpoints
- `GET /health` - Health check
- `POST /api/v1/chats` - Create chat session
- `POST /api/v1/chats/{id}/messages` - Send message
- `GET /api/v1/meta/knowledge` - List knowledge sources

---

## ⚙️ Configuration

```ini
# .env file
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile

GEMINI_API_KEY=your_gemini_key
GEMINI_EMBEDDING_MODEL=text-embedding-004

POSTGRES_SERVER=localhost
POSTGRES_DB=spacepedia
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for Space Enthusiasts**

[⬆ Back to Top](#)

</div>

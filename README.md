# 🤖 KnowledgeBot — AI-Powered Chatbot with Knowledge Base

A full-stack, production-ready chatbot that uses **local HuggingFace models** (no paid APIs) to answer questions from a **custom knowledge base** you upload.

---

## ✨ Features

| Feature | Status |
|---|---|
| Custom knowledge base (PDF, DOCX, TXT, MD, HTML, URLs) | ✅ |
| Semantic search with ChromaDB + Sentence Transformers | ✅ |
| Local LLM answer generation (HuggingFace Phi-2) | ✅ |
| Graceful out-of-scope fallback | ✅ |
| Conversation memory (per-session) | ✅ |
| JWT authentication (User + Admin roles) | ✅ |
| REST API with OpenAPI docs | ✅ |
| Structured logging (Loguru) | ✅ |
| Knowledge base updates without retraining | ✅ |
| React frontend with dark UI | ✅ |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│   Login / Chat / Admin Panel (Vite + React Router)      │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (JWT Bearer)
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│  /api/v1/auth  /api/v1/chat  /api/v1/knowledge          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Auth Service│  │ Chat Service │  │  KB Service  │  │
│  │  JWT + bcrypt│  │  RAG Pipeline│  │  Doc Parser  │  │
│  └──────────────┘  └──────┬───────┘  └──────┬───────┘  │
│                           │                 │          │
│                    ┌──────▼─────────────────▼──────┐   │
│                    │         Vector Store           │   │
│                    │   ChromaDB (local disk)        │   │
│                    │   Embeddings: all-MiniLM-L6-v2 │   │
│                    └───────────────────────────────┘   │
│                           │                            │
│                    ┌──────▼──────┐                     │
│                    │  Local LLM  │                     │
│                    │  Phi-2 (HF) │                     │
│                    └─────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- ~5GB disk space (for models)

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd knowledge-chatbot
```

### 2. Backend setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (defaults work out of the box)

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**On first startup**, the embedding model (`all-MiniLM-L6-v2`) is downloaded from HuggingFace (~90MB).  
The LLM (`microsoft/phi-2`) is downloaded **on first chat request** (~5.5GB).

### 3. Frontend setup
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Default credentials
| Username | Password | Role |
|---|---|---|
| `admin` | `admin1234` | Admin |

---

## 📖 API Documentation

After starting the backend, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | None | Register user |
| POST | `/api/v1/auth/login` | None | Login, get tokens |
| GET | `/api/v1/auth/me` | User | Current user info |
| POST | `/api/v1/chat` | User | Send a message |
| DELETE | `/api/v1/chat/session/{id}` | User | Clear session |
| POST | `/api/v1/knowledge/upload` | Admin | Upload document |
| POST | `/api/v1/knowledge/ingest-url` | Admin | Ingest web URL |
| GET | `/api/v1/knowledge/documents` | User | List documents |
| DELETE | `/api/v1/knowledge/documents/{id}` | Admin | Delete document |
| GET | `/api/v1/knowledge/stats` | User | KB statistics |
| GET | `/api/v1/admin/users` | Admin | List users |

---

## 🔧 Configuration

Edit `backend/.env` to change:

| Variable | Default | Description |
|---|---|---|
| `LLM_MODEL_ID` | `microsoft/phi-2` | HuggingFace model ID |
| `EMBEDDING_MODEL_ID` | `all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `512` | Words per chunk |
| `TOP_K_RESULTS` | `5` | Retrieved chunks per query |
| `SIMILARITY_THRESHOLD` | `0.35` | Min similarity score |

### Lighter / faster model alternatives
```
# Ultra-light (CPU-friendly):
LLM_MODEL_ID=TinyLlama/TinyLlama-1.1B-Chat-v1.0

# Medium (good quality):
LLM_MODEL_ID=microsoft/phi-2

# High quality (needs GPU):
LLM_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.2
```

---

## 📁 Project Structure

```
knowledge-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── core/         # Config, security, logger
│   │   ├── models/       # Schemas, user store
│   │   └── services/     # LLM, vector store, parser, sessions
│   ├── knowledge_base/   # ChromaDB persistence (auto-created)
│   ├── logs/             # Log files (auto-created)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/   # Layout
│       ├── pages/        # Login, Register, Chat, Admin
│       ├── services/     # API client
│       └── store/        # Zustand auth store
└── README.md
```

---

## 🐳 Docker (optional)

```yaml
# docker-compose.yml (add to project root)
version: '3.9'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./backend/knowledge_base:/app/knowledge_base
      - ./backend/logs:/app/logs
    environment:
      - FRONTEND_ORIGIN=http://localhost:5173

  frontend:
    build: ./frontend
    ports: ["5173:80"]
```

---

## 📜 License
MIT

# Akademikai AI

Scientific work based question answering AI and document analysis toolkit with RAG (Retrieval Augmented Generation) capabilities.

## Overview

This project combines a Next.js chatbot frontend with a Python FastAPI backend for document processing, vectorization, and semantic search. The system can answer questions based on a large collection of PDF documents using RAG technology.

## Architecture

- **Frontend**: Next.js 15 with TypeScript, React, and AI SDK
- **Backend**: Python FastAPI with sentence-transformers and ChromaDB
- **Database**: PostgreSQL (chat history) + ChromaDB (vector embeddings)
- **AI Model**: OpenAI GPT-4o-mini with RAG context injection

## Features

- PDF Document Processing - Extract and analyze text from PDF documents
- Vector Search - Semantic search across document collection using embeddings
- RAG Integration - Retrieval Augmented Generation for context-aware responses
- Machine Learning Models - Train classifiers for text analysis
- Web Scraping - Extract content and files from websites
- RSS Feed Processing - Parse and analyze news headlines
- Chat Interface - Interactive chatbot with document-based answers

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL database (for chat history)

### 1. Clone and Install Dependencies

```bash
# Install all dependencies
npm run install:all

# Or install separately:
# Python dependencies
source venv/bin/activate
pip install -r python/requirements.txt
pip install -r python/backend/requirements.txt

# Node.js dependencies
cd frontend && npm install
```

### 2. Environment Configuration

Create `.env.local` file in the root directory:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Python Backend URL
PYTHON_BACKEND_URL=http://localhost:8000

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 3. Database Setup

```bash
# Generate database migrations
npm run db:generate

# Push schema to database
npm run db:push
```

### 4. Process Documents

Before using the RAG system, process all PDF documents:

```bash
# Activate virtual environment
source venv/bin/activate

# Process all PDFs in data/ and scraped_files/ directories
cd python && PYTHONPATH=. python backend/scripts/process_documents.py
```

This will:
- Extract text from all PDF files
- Chunk text into manageable segments
- Generate embeddings using multilingual sentence-transformers
- Store in ChromaDB vector database

### 5. Start Development Servers

**Terminal 1 - Python Backend:**
```bash
source venv/bin/activate
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Next.js Frontend:**
```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

### Chat Interface

1. Open http://localhost:3000
2. Start a new chat session
3. Ask questions about the documents
4. The system will automatically retrieve relevant context from PDFs and provide answers with source citations

### API Endpoints

#### Python Backend

- `GET /` - API information
- `GET /health` - Health check
- `POST /api/vectorize` - Process and vectorize documents
  ```json
  {
    "directory": "/path/to/pdfs"
  }
  ```
- `POST /api/search` - Semantic search
  ```json
  {
    "query": "your search query",
    "top_k": 5
  }
  ```
- `POST /api/query` - RAG query with formatted context
  ```json
  {
    "query": "your question",
    "top_k": 5
  }
  ```
- `GET /api/documents` - List all indexed documents

#### Next.js API Routes

- `POST /api/rag` - Proxy to Python backend RAG query
- `GET /api/documents` - List available documents
- `POST /api/chat` - Chat endpoint with RAG integration

## Project Structure

```
akademikai_ai/
├── python/                  # Python backend and scripts
│   ├── backend/            # FastAPI backend
│   │   ├── main.py         # FastAPI application
│   │   ├── config.py       # Configuration
│   │   ├── requirements.txt # Backend dependencies
│   │   ├── services/       # Core services
│   │   │   ├── pdf_processor.py
│   │   │   ├── vectorizer.py
│   │   │   └── rag_service.py
│   │   └── scripts/        # Utility scripts
│   │       ├── process_documents.py
│   │       └── rebuild_index.py
│   ├── scripts/            # Standalone scripts
│   │   └── website_scraper.py
│   └── requirements.txt    # Main Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/                # Source code
│   │   └── app/
│   │       ├── api/        # API routes
│   │       │   ├── chat/   # Chat endpoint
│   │       │   ├── rag/    # RAG proxy
│   │       │   └── documents/ # Documents list
│   │       └── ui/         # React components
│   ├── public/             # Static assets
│   ├── package.json        # Node.js dependencies
│   └── [config files]      # Next.js config files
├── data/                   # PDF documents (400+ files)
├── scraped_files/          # Scraped documents
├── chroma_db/             # Vector database (generated)
└── package.json           # Root package.json with scripts
```

## Data Directory

The `data/` directory contains various document collections:
- `ass/` - ASS organization documents (57 PDFs)
- `llhs/` - LLHS organization documents (33 PDFs)
- `ls/` - LS organization documents (265 PDFs)
- `lss/` - LSS organization documents (49 PDFs)
- `zso/` - ZSO organization documents (24 PDFs)
- `raw/` - Raw source documents and archives

Total: **428+ PDF documents** ready for analysis.

## Development Scripts

```bash
# Process all documents
cd python && PYTHONPATH=. python backend/scripts/process_documents.py

# Rebuild vector index from scratch
cd python && PYTHONPATH=. python backend/scripts/rebuild_index.py

# Run Python backend
npm run backend

# Run Next.js dev server
npm run dev

# Database operations
npm run db:push
npm run db:generate
npm run db:studio
```

## Deployment

### Python Backend

Deploy to Railway, Render, Fly.io, or similar:

```bash
# Install dependencies
pip install -r python/requirements.txt
pip install -r python/backend/requirements.txt

# Run with uvicorn
cd python && PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Next.js Frontend

Deploy to Vercel:

```bash
# Build
npm run build

# Deploy
vercel
```

Update `PYTHON_BACKEND_URL` in Vercel environment variables to point to your deployed Python backend.

## Configuration

Key configuration options in `backend/config.py`:

- `CHUNK_SIZE`: Text chunk size (default: 800 characters)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 150 characters)
- `EMBEDDING_MODEL`: Sentence transformer model (multilingual support)
- `TOP_K_DEFAULT`: Default number of results (default: 5)

## Troubleshooting

### Vector Database Issues

If the vector database becomes corrupted:

```bash
python backend/scripts/rebuild_index.py
```

### PDF Processing Errors

Some PDFs may fail to process. Check logs for specific errors. The system will continue processing other files.

### Backend Connection Issues

Ensure the Python backend is running on port 8000 and `PYTHON_BACKEND_URL` is correctly set in `.env.local`.

## License

See LICENSE file for details.
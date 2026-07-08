<div align="center">

# Nova

### AI NEET Tutor Grounded in Your Own Books

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square&logo=fastapi&logoColor=white)](https://console.groq.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Vercel-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com)

**Live Demo → add your Vercel URL here after deploying**

An AI chatbot for NEET aspirants that answers Physics, Chemistry, and Biology questions using *only* the PDF books you give it — and cites the exact book and page every answer came from.

<br/>

![Nova — Chat Interface](docs/screenshot.png)

</div>

---

## Features

| Feature | Description |
|---------|-------------|
| Book-Grounded Answers | Every response is retrieved from your own PDF books, not the model's general knowledge |
| Page Citations | Each answer shows exactly which book and page it came from, so you can verify it |
| Subject Filter | Narrow retrieval to Physics, Chemistry, Biology, or search across all of them |
| Session Memory | Remembers recent chat context within a session |
| No Vector DB / Embedding API Needed | Uses TF-IDF search (scikit-learn) — fast, free, fully offline at request time |
| Dark UI | Distraction-free chat interface built for late-night revision sessions |
| Serverless-Ready | Ships as a prebuilt search index, deploys cleanly to Vercel |

---

## Tech Stack

<table>
<tr>
<td><strong>Backend</strong></td>
<td>Python 3.11+, FastAPI, Uvicorn</td>
</tr>
<tr>
<td><strong>Frontend</strong></td>
<td>HTML5, CSS3, Vanilla JS</td>
</tr>
<tr>
<td><strong>LLM</strong></td>
<td><code>openai/gpt-oss-120b</code> via Groq (fallback: <code>openai/gpt-oss-20b</code>)</td>
</tr>
<tr>
<td><strong>Retrieval</strong></td>
<td>TF-IDF + cosine similarity (scikit-learn) over chunked book text</td>
</tr>
<tr>
<td><strong>PDF Parsing</strong></td>
<td>PyMuPDF (ingestion-only, not shipped to production)</td>
</tr>
<tr>
<td><strong>Memory</strong></td>
<td>In-memory per-session store, backed by client-side history for serverless reliability</td>
</tr>
<tr>
<td><strong>Deploy</strong></td>
<td>Vercel (serverless Python functions)</td>
</tr>
</table>

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **[Groq API key](https://console.groq.com/keys)** (free tier available)

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd neet-chatbot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-ingest.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ_API_KEY=gsk_your_key_here
```

### 3. Add your books & build the index

```bash
# drop PDFs into data/books/<subject>/, e.g.:
#   data/books/physics/hc-verma-vol1.pdf
#   data/books/chemistry/ncert-chemistry-class12.pdf
#   data/books/biology/ncert-biology-class12.pdf

python scripts/ingest_pdfs.py
```

### 4. Run

```bash
python run.py
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Your Groq API key ([get one](https://console.groq.com/keys)) |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Primary chat model |
| `GROQ_FALLBACK_MODEL` | No | `openai/gpt-oss-20b` | Used automatically if the primary model fails |
| `PORT` | No | `8000` | Local dev server port |

---

## Project Structure

```
neet-chatbot/
├── api/
│   └── index.py                 # Vercel entrypoint (re-exports the FastAPI app)
├── app/
│   ├── main.py                  # App factory: static files, templates, routes
│   ├── routes/
│   │   └── chat.py              # /api/chat, /api/chat/reset, /api/subjects
│   └── services/
│       ├── llm_service.py       # Groq chat completions
│       ├── memory_service.py    # Session-scoped conversation memory
│       ├── prompt_manager.py    # System prompt + RAG prompt building
│       └── retrieval_service.py # Loads the TF-IDF index, runs the search
├── scripts/
│   └── ingest_pdfs.py           # Run locally: PDFs -> chunks -> TF-IDF index
├── data/
│   ├── books/                   # Your NEET PDF books (physics/chemistry/biology)
│   └── processed/               # Generated index.pkl lands here
├── static/
│   ├── css/style.css            # Chat UI styling
│   └── js/chat.js               # Chat logic, session + subject state
├── templates/
│   └── index.html               # Main chat page
├── docs/
│   └── screenshot.png           # README screenshot
├── .env.example                 # Environment template
├── requirements.txt             # Runtime dependencies (deployed to Vercel)
├── requirements-ingest.txt      # Extra dependency for scripts/ingest_pdfs.py
├── vercel.json                  # Vercel build + routing config
└── run.py                       # Dev entry point
```

---

## Deployment

### Vercel (Recommended)

1. Build the search index locally first — Vercel's filesystem is read-only at
   request time, so `data/processed/index.pkl` must be committed, not
   generated on the server:
   ```bash
   python scripts/ingest_pdfs.py
   ```
2. Push your code (including `data/processed/index.pkl`) to GitHub
3. Install the CLI and deploy:
   ```bash
   npm i -g vercel
   vercel login
   vercel            # first deploy
   vercel --prod     # promote to production
   ```
4. In the Vercel dashboard → your project → **Settings → Environment
   Variables**, add `GROQ_API_KEY`
5. Redeploy so the function picks up the new env var

### Updating your books later

Re-run `python scripts/ingest_pdfs.py` locally whenever you add or remove a
PDF, then redeploy — the index ships as a static file with the build, it
isn't rebuilt on the server.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Chat interface |
| `POST` | `/api/chat` | Send a message — returns an answer + source citations |
| `POST` | `/api/chat/reset` | Clear a session's conversation memory |
| `GET` | `/api/subjects` | List indexed subjects and index readiness |
| `GET` | `/api/health` | Health check |

---

## How It Works

```
Student asks a question
        │
        ▼
┌───────────────────────────────────────────┐
│  FastAPI Backend                          │
│  ├── TF-IDF search over indexed books     │
│  │     (data/processed/index.pkl)          │
│  ├── Top passages inserted into prompt     │
│  │     (app/services/prompt_manager.py)    │
│  └── Groq LLM (openai/gpt-oss-120b)        │
│        answers using only that context     │
│                                             │
│  Memory: per-session history (client +     │
│           server-side, serverless-safe)    │
└───────────────────────────────────────────┘
        │
        ▼
Answer + book/page citations
```

---

## Contributing

Contributions welcome!

```bash
git checkout -b feature/your-feature
pip install -r requirements.txt -r requirements-ingest.txt
# make changes
git commit -m "Add your feature"
git push origin feature/your-feature
```

---

## License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

**Built for NEET aspirants**

</div>

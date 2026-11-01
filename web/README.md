# MisconAI Studio — web frontend

Next.js (App Router, TypeScript, Tailwind CSS v4) frontend for MisconAI.

All `/api/*` requests are proxied to the Python API (`src/server.py`, default `http://127.0.0.1:8000`).
Override the target with `MISCONAI_API_URL`.

```bash
# 1. In the project root: start the API
python src/server.py

# 2. In web/: start the frontend
npm install
npm run dev        # http://localhost:3000
```

## Structure

```text
src/
├── app/
│   ├── layout.tsx         # Header, engine provider, footer, fonts
│   ├── globals.css        # Palette tokens (navy / royal blue / gold) + markdown styles
│   ├── page.tsx           # Overview
│   ├── lab/page.tsx       # Mining lab — analyze student code
│   ├── tutor/page.tsx     # Concept tutor — chat over 75 questions
│   ├── results/page.tsx   # Evaluation scorecards and charts
│   └── taxonomy/page.tsx  # Searchable misconception bank
├── components/            # UI primitives, header, engine picker, diagnosis view
└── lib/                   # Typed API client and fetch hook
```

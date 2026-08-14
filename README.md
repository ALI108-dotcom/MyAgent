# Personal AI Coding Agent

Production-ready foundation for an autonomous Personal AI Coding Agent featuring a modular **FastAPI** backend, **Next.js** (TypeScript + Tailwind CSS) frontend, **MongoDB** integration, and automated quality tooling (`pytest`, `ruff`, `mypy`, `eslint`, strict `tsc`).

---

## System Architecture

```text
AgentAI/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # REST API route handlers
│   │   ├── agent/             # Modular agent capabilities (LLM, reasoning, tools, memory, RAG)
│   │   ├── core/              # Config, async database, exception handlers, logging
│   │   ├── models/            # Pydantic schemas & data models
│   │   ├── services/          # Business logic layer
│   │   └── main.py            # FastAPI entry point
│   ├── tests/                 # Automated Pytest test suite
│   ├── pyproject.toml         # Ruff, Mypy & Pytest configurations
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router (pages & layouts)
│   │   ├── components/        # Reusable UI components
│   │   ├── lib/               # Typed API client
│   │   └── types/             # TypeScript type definitions
│   ├── package.json           # Node.js dependencies
│   ├── tsconfig.json          # Strict TypeScript configuration
│   └── .env.example           # Frontend environment template
└── README.md                  # Project documentation
```

---

## Tech Stack

* **Backend**: Python 3.10+, FastAPI, Motor (Async MongoDB), Pydantic v2, Uvicorn
* **Frontend**: Next.js 15, React 19, TypeScript (Strict Mode), Tailwind CSS
* **Database**: MongoDB (Async connection with graceful fallback)
* **Code Quality & Testing**: Pytest, Ruff, Mypy, ESLint, TypeScript Compiler

---

## Setup & Local Development

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run FastAPI Dev Server
uvicorn app.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000` (Health Check: `http://localhost:8000/api/v1/health`).

### 2. Frontend Setup

```bash
cd frontend
npm install

# Copy environment variables
cp .env.example .env.local

# Run Next.js Dev Server
npm run dev
```
Frontend will be running at `http://localhost:3000`.

---

## Code Quality & Testing

### Backend Commands
* **Run Tests**: `pytest`
* **Run Linter & Formatter**: `ruff check .`
* **Run Type Checks**: `mypy app`

### Frontend Commands
* **Run Linter**: `npm run lint`
* **Run Type Checks**: `npm run type-check`
* **Production Build**: `npm run build`

---

## Security Principles

1. **No Hardcoded Secrets**: All sensitive values are loaded via environment variables (`.env`).
2. **CORS Safeguards**: Explicitly configured allowed origins for API security.
3. **Internal Error Masking**: Exception handlers suppress internal tracebacks in production responses.

# bugtrace
Local AI triage prototype: React/Vite frontend, FastAPI backend, PostgreSQL, local embeddings, Gemini JSON analysis, mock fallback.

## Local Running Guide
Prereqs: PostgreSQL running, Python 3.12+, Node/npm.
Create DB in pgAdmin: database name `bugtrace`, owner `postgres` or your chosen user.
Copy env template: keep `.env` local and never commit it.
Required `.env`:
```env
APP_NAME=bugtrace
DATABASE_URL=postgresql+psycopg://postgres:your_password_here@localhost:5432/bugtrace
GEMINI_API_KEY=your_google_ai_studio_key
SEED_RECORD_COUNT=50
ENABLE_MOCK_FALLBACK=true
EMBEDDING_ALLOW_DOWNLOAD=false
VITE_API_BASE_URL=http://localhost:8000
```

## First Run
Terminal 1, backend:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m backend.seed_mock_data --reset
uvicorn backend.app.main:app --reload
```
Backend URL: `http://localhost:8000`
Health check: `http://localhost:8000/health`

Terminal 2, frontend:
```powershell
npm install
npm run dev
```
Frontend URL: `http://localhost:5173`

## Normal Daily Run
Terminal 1:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```
Terminal 2:
```powershell
npm run dev
```
Open `http://localhost:5173`, click `Sample`, then `Submit and analyze`.

## Reset Seed Data
```powershell
.\.venv\Scripts\Activate.ps1
python -m backend.seed_mock_data --reset
```
Default count comes from `SEED_RECORD_COUNT=50`.

## API Cheatsheet
`GET /health` - app, database, fallback status.
`POST /bugs` - submit bug and receive analysis.
`GET /bugs` - recent submitted bugs.
`GET /bugs/{id}` - bug detail, analysis, matches.

## Notes
Tables are created automatically by backend startup or the seed script.
Gemini is used when available; `ENABLE_MOCK_FALLBACK=true` keeps the app usable if Gemini fails.
Embeddings use cached `all-MiniLM-L6-v2` only when present. Set `EMBEDDING_ALLOW_DOWNLOAD=true` to allow Hugging Face download.
If `/health` says `database=false`, check PostgreSQL is running, DB name is `bugtrace`, port is `5432`, and `DATABASE_URL` password is correct.
If npm/Node hits sandbox or permission errors inside Codex, run the same command in your own terminal.
If Git reports dubious ownership, optional fix: `git config --global --add safe.directory D:/Proj/Work/bugtrace`.

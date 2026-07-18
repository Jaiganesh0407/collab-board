# CollabBoard

A real-time collaborative task board (like a mini Trello/Jira) built with FastAPI, PostgreSQL,
WebSockets, and server-rendered HTML. Built as a portfolio project to demonstrate backend
system design: auth, relational data modeling, concurrency handling, and real-time sync.

## Features

- **JWT authentication** — signup/login with bcrypt-hashed passwords
- **Workspaces & boards** — multi-tenant structure: users → workspaces → boards → columns → cards
- **Real-time sync** — WebSocket broadcast so all connected users see card moves instantly
- **Optimistic locking** — each card has a `version`; concurrent edits are detected and rejected
  with `409 Conflict` instead of silently overwriting a teammate's change
- **Drag-and-drop UI** — vanilla JS, no frontend framework/build step required
- **Dockerized** — one command to run the full stack (API + Postgres)
- **Tested** — pytest suite covering auth, board creation, and the optimistic-locking conflict path
- **CI** — GitHub Actions runs the test suite on every push

## Architecture

```
Browser (HTML/JS, Tailwind via CDN)
        │  REST (fetch) + WebSocket
        ▼
FastAPI app  ──────────────►  PostgreSQL
  ├─ /api/auth        (JWT issuing/validation)
  ├─ /api/workspaces
  ├─ /api/boards
  ├─ /api/cards        (optimistic locking on move)
  └─ /ws/boards/{id}   (broadcasts card events to all connected clients)
```

## Run it locally (Docker — recommended)

```bash
git clone <your-repo-url>
cd collabboard
cp .env.example .env        # edit SECRET_KEY if you like
docker compose up --build
```

Open **http://localhost:8000** — register an account, create a workspace, create a board, and
start dragging cards. Open the same board in two browser tabs to see the real-time sync.

## Run it locally without Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export USE_SQLITE=1        # skips Postgres, uses a local SQLite file instead
uvicorn app.main:app --reload
```

## Run the tests

```bash
pip install -r requirements.txt
USE_SQLITE=1 pytest -v
```

## Pushing this to your own GitHub

```bash
cd collabboard
git init
git add .
git commit -m "Initial commit: CollabBoard"
git branch -M main
git remote add origin https://github.com/<your-username>/collabboard.git
git push -u origin main
```

The included `.github/workflows/ci.yml` will automatically run the test suite on every push.

## Deploying it live (free options)

Any host that runs Docker or a plain Python web service works. Two easy free-tier options:

**Render.com**
1. New → Web Service → connect your GitHub repo
2. Environment: Docker (it will detect the `Dockerfile`)
3. Add a free PostgreSQL instance from Render, copy its `DATABASE_URL` into your web service's
   environment variables, along with a `SECRET_KEY`
4. Deploy — you'll get a public URL like `collabboard.onrender.com`

**Railway.app**
1. New Project → Deploy from GitHub repo
2. Add a PostgreSQL plugin (Railway sets `DATABASE_URL` automatically)
3. Add a `SECRET_KEY` variable
4. Deploy — Railway builds from the `Dockerfile` automatically

Put the live URL and repo link at the top of your resume/portfolio.

## Project structure

```
app/
  main.py             FastAPI app, page routes
  database.py         SQLAlchemy engine/session
  models.py           ORM models (User, Workspace, Board, Column, Card, ActivityLog)
  schemas.py          Pydantic request/response models
  auth.py             JWT + password hashing
  ws_manager.py        WebSocket connection manager
  routers/
    auth.py           /api/auth/*
    workspaces.py     /api/workspaces/*
    boards.py         /api/boards/*
    cards.py          /api/cards/* (optimistic locking + broadcast)
    ws.py             /ws/boards/{id}
  templates/          Jinja2 pages (login, register, dashboard, board)
  static/             CSS + vanilla JS (drag-and-drop, WebSocket client)
tests/                pytest suite (SQLite in-memory-style, isolated per test)
.github/workflows/    CI pipeline
Dockerfile
docker-compose.yml
```

## What to highlight in interviews / on your resume

- **Concurrency handling**: the optimistic-locking design on `PATCH /api/cards/{id}/move` — why
  it's needed, what happens without it, and the tradeoff vs. pessimistic locking or CRDTs
- **Real-time architecture**: how the WebSocket broadcast layer stays decoupled from the REST
  layer (all state changes go through REST, which then broadcasts — single source of truth)
- **Auth design**: JWT vs. session cookies, why bcrypt, token expiry tradeoffs
- **Data modeling**: the many-to-many `workspace_members` table and why workspace-scoped
  permissions matter for multi-tenant apps

Suggested resume bullet:

> Built CollabBoard, a real-time collaborative task-management platform (FastAPI, PostgreSQL,
> WebSockets); implemented JWT auth and optimistic locking to safely handle concurrent card
> edits across clients; containerized with Docker and wired up CI via GitHub Actions.

## Next features to add (good for a v2 commit / talking about growth)

- Redis pub/sub instead of in-memory `ConnectionManager` (needed once you run >1 app instance)
- Celery + Redis for background email notifications
- Full-text search on cards (Postgres `tsvector`)
- File attachments on cards (S3-compatible storage)
- Per-workspace roles (owner/admin/member) enforced on write endpoints

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.database import Base, engine
from app import models  # noqa: F401 (registers models with Base)
from app.routers import auth as auth_router
from app.routers import workspaces as workspaces_router
from app.routers import boards as boards_router
from app.routers import cards as cards_router
from app.routers import ws as ws_router

app = FastAPI(title="CollabBoard", version="1.0.0")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_router.router)
app.include_router(workspaces_router.router)
app.include_router(boards_router.router)
app.include_router(cards_router.router)
app.include_router(ws_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- Server-rendered pages (frontend) ----

@app.get("/")
def index(request: Request):
    return RedirectResponse(url="/login")


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/boards/{board_id}")
def board_page(request: Request, board_id: str):
    return templates.TemplateResponse("board.html", {"request": request, "board_id": board_id})

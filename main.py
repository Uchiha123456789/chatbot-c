"""FastAPI app — thay thế Streamlit (app.py cũ).

Giai đoạn 1: thêm CSDL SQLite (SQLAlchemy), đăng ký/đăng nhập (session cookie),
lưu hội thoại + tin nhắn vào DB. Giao diện đầy đủ sẽ hoàn thiện ở giai đoạn 2.
"""
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import models  # noqa: F401 — import để đăng ký toàn bộ model với Base.metadata
from config import settings
from database import Base, engine
from routers import auth as auth_router
from routers import chat as chat_router
from routers import feedback as feedback_router
from routers import progress as progress_router
from routers import quiz as quiz_router
from services.csrf_service import has_valid_csrf_header, requires_csrf_header

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chatbot dạy lập trình C")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=settings.session_https_only,
    same_site="lax",
)


@app.middleware("http")
async def enforce_csrf_header(request: Request, call_next):
    """Chặn CSRF cổ điển: yêu cầu header X-Requested-With trên mọi request
    làm thay đổi trạng thái (POST/PUT/PATCH/DELETE) tới /api/* và /auth/*.
    Xem services/csrf_service.py để biết lý do header tuỳ chỉnh chặn được CSRF."""
    if requires_csrf_header(request.method, request.url.path) and not has_valid_csrf_header(request.headers):
        return JSONResponse(
            status_code=403,
            content={"detail": "Thiếu header xác thực yêu cầu — vui lòng gửi qua giao diện ứng dụng"},
        )
    return await call_next(request)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(feedback_router.router)
app.include_router(progress_router.router)
app.include_router(quiz_router.router)


@app.get("/")
def index(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/chat")
    return RedirectResponse(url="/login")


@app.get("/login")
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/chat")
    return templates.TemplateResponse(request, "login.html", {})


@app.get("/register")
def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/chat")
    return templates.TemplateResponse(request, "register.html", {})


@app.get("/chat")
def chat_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "chat.html", {})


@app.get("/quiz")
def quiz_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "quiz.html", {})


@app.get("/dashboard")
def dashboard_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "dashboard.html", {})

from __future__ import annotations

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.seed import bootstrap
from app.resp import AppError
from app.routers import auth, overview, projects, requirements, users, public, audit

app = FastAPI(title="需求智能工作台 v2", version="2.0.0")

FRONTEND_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:8012", "http://127.0.0.1:8012",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    bootstrap()


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.http, content={"code": exc.code, "data": None, "message": exc.message})


@app.exception_handler(HTTPException)
def handle_http(request: Request, exc: HTTPException):
    code_map = {401: 1001, 403: 1003, 404: 2001, 409: 2002, 422: 3001}
    code = code_map.get(exc.status_code, 5000)
    return JSONResponse(status_code=exc.status_code, content={"code": code, "data": None, "message": str(exc.detail)})


@app.exception_handler(RequestValidationError)
def handle_validation(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"code": 3001, "data": None, "message": "参数校验失败", "errors": exc.errors()})


@app.get("/api/healthz")
def healthz():
    return {"code": 0, "data": {"service": "需求智能工作台 v2", "status": "ok"}, "message": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(overview.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(requirements.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(audit.router, prefix="/api")

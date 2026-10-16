from __future__ import annotations
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: int, message: str, http: int = 400):
        self.code = code
        self.message = message
        self.http = http


def ok(data=None, message: str = "ok"):
    return JSONResponse(status_code=200, content={"code": 0, "data": data, "message": message})


def fail(code: int, message: str, http: int = 400, data=None):
    return JSONResponse(status_code=http, content={"code": code, "data": data, "message": message})

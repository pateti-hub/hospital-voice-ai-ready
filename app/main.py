from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from app.api import router
from app.config import get_settings
from app.logging import configure_logging, new_request_id

s = get_settings()
configure_logging(s.log_level)
app = FastAPI(title=s.app_name, version="0.1.0", docs_url="/docs")
app.include_router(router)
app.mount("/metrics", make_asgi_app())
static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static), name="static")


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = new_request_id(request.headers.get("x-request-id"))
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["referrer-policy"] = "no-referrer"
    return response


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(static / "index.html")

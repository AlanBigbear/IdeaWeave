import asyncio
import logging
import traceback
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, db_info, engine, migrate_schema
from app.services.trial import reset_all_trial_accounts

logger = logging.getLogger("bstar.errors")


async def _reset_trial_periodically() -> None:
    while True:
        await asyncio.sleep(max(settings.trial_reset_minutes, 1) * 60)
        try:
            await asyncio.to_thread(reset_all_trial_accounts)
            logger.info("试用空间已恢复为默认模板")
        except Exception:
            logger.exception("定时恢复试用空间失败")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_schema()
    task = None
    if settings.trial_enabled:
        try:
            await asyncio.to_thread(reset_all_trial_accounts)
        except Exception:
            logger.exception("初始化试用空间失败，服务将继续启动")
        task = asyncio.create_task(_reset_trial_periodically())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="B-Star 虚拟编导工作台", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.ngrok-free\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def catch_unhandled(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.error("未处理异常 %s %s\n%s", request.method, request.url.path, traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": "服务器开小差了，请看服务端日志"})


@app.get("/api/health")
def health():
    return {"ok": True, "name": settings.app_name, "database": db_info()}


class HashedAssetStaticFiles(StaticFiles):
    """Vite 产物文件名带 hash，可长期缓存。"""

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


# 生产模式：托管 frontend/dist。ngrok 指向 8000 即可，不必再走 Vite :5173
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_API_PREFIXES = ("api/", "docs", "redoc", "openapi.json")
if _DIST.is_dir():
    app.mount("/assets", HashedAssetStaticFiles(directory=_DIST / "assets"), name="static-assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    def spa_fallback(full_path: str):
        if full_path.startswith(_API_PREFIXES):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        candidate = (_DIST / full_path).resolve()
        if full_path and candidate.is_file() and str(candidate).startswith(str(_DIST.resolve())):
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
else:
    logger.warning("未找到 frontend/dist，外网请先执行: cd frontend && npm run build")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, db_info, engine, migrate_schema

Base.metadata.create_all(bind=engine)
migrate_schema()

app = FastAPI(title="B-Star 虚拟编导工作台", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/api/health")
def health():
    return {"ok": True, "name": settings.app_name, "database": db_info()}

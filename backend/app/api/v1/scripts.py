import json
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import ExpandScriptIn, ScriptOut
from app.services import script as script_service

router = APIRouter(prefix="/scripts", tags=["scripts"])

_STREAM_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="bstar-stream")


@router.post("/expand", response_model=ScriptOut)
def expand(
    payload: ExpandScriptIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return script_service.expand(db, user, payload)


@router.post("/expand/stream")
def expand_stream(
    payload: ExpandScriptIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    def events():
        yield "event: status\ndata: 编导娘正在结合人设与评论写稿，稍等一下下…\n\n"
        # 用独立会话在后台线程跑 LLM：即使客户端断开，生成结果也会保存
        session = SessionLocal()
        future = _STREAM_POOL.submit(
            script_service.expand, session, user, payload
        )
        waited = 0
        try:
            while not future.done():
                # 心跳：每 6 秒给前端阶段感，避免长连接期间毫无反馈
                time.sleep(1)
                waited += 1
                if waited % 6 == 0:
                    if waited <= 30:
                        yield "event: status\ndata: 编导娘在搭脚本骨架…\n\n"
                    elif waited <= 90:
                        yield "event: status\ndata: 正在逐镜写台词和互动…\n\n"
                    else:
                        yield f"event: status\ndata: 快收尾了，已写 {waited} 秒…\n\n"
            result = future.result()
            yield f"event: done\ndata: {result.model_dump_json()}\n\n"
        except Exception as exc:
            detail = getattr(exc, "detail", str(exc))
            yield f"event: error\ndata: {json.dumps({'detail': detail}, ensure_ascii=False)}\n\n"
        finally:
            session.close()

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("", response_model=list[ScriptOut])
def list_scripts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return script_service.list_scripts(db, user)


@router.get("/{script_id}", response_model=ScriptOut)
def get_script(
    script_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return script_service.get_script(db, user, script_id)

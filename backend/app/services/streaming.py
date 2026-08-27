"""把 AI 生成过程包装成 SSE（Server-Sent Events）流。

前端拿到的不是「转圈等待」，而是一条条「编导娘正在…」的实时进度，
最后用 `done` 事件把结构化结果送回。即使客户端中途断开，生成也会在
后台线程里跑完并落库，切页面不打断。
"""

import json
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.core.database import SessionLocal

# 全局共享线程池：SSE 请求很快会占住一个连接，但真正在跑 LLM 的任务数量
# 需要被限制，避免无脑并发把模型服务打挂。
_STREAM_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="bstar-stream")


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


def sse_stream(fn, *, serialize, statuses, interval: int = 4):
    """把一个 AI 生成调用包成 SSE 事件流（进度心跳版，用于热点日历等无需展示思考的场景）。

    Args:
        fn: callable() -> result。会在独立线程执行，内部自行创建并关闭 DB 会话，
            客户端断开也会照常完成并保存。
        serialize: callable(result) -> str。把结果转成 JSON 字符串（`done` 事件体）。
        statuses: 依次播报的进度文案；第一条会立刻发出。
        interval: 每隔多少秒换下一条 status（心跳），给前端阶段感。
    """
    statuses = list(statuses) or ["编导娘正在努力…"]
    yield _sse("status", statuses[0])

    future = _STREAM_POOL.submit(fn)
    waited = 0
    try:
        while not future.done():
            time.sleep(1)
            waited += 1
            if waited % interval == 0:
                idx = min(waited // interval, len(statuses) - 1)
                yield _sse("status", statuses[idx])
        yield _sse("done", serialize(future.result()))
    except Exception as exc:
        detail = getattr(exc, "detail", str(exc))
        yield _sse("error", json.dumps({"detail": detail}, ensure_ascii=False))


def sse_token_stream(fn, *, serialize):
    """把一个 AI 生成调用包成 SSE 事件流（真·逐字流式版）。

    fn(session, on_delta) -> result 会在独立线程里执行：LLM 每吐出一段增量，
    on_delta("thinking"|"content", text) 就会被回调，这里实时转成 `token` 事件推给前端；
    生成结束后 `done` 带回结构化结果。因为跑在独立线程，客户端中途断开也会照常落库。

    Args:
        fn: callable(session, on_delta) -> result。on_delta(kind, text) 见上。
        serialize: callable(result) -> str。把结果转成 JSON 字符串（`done` 事件体）。
    """
    q: queue.Queue = queue.Queue()

    def on_delta(kind: str, text: str) -> None:
        q.put(("token", kind, text))

    def worker() -> None:
        session = SessionLocal()
        try:
            result = fn(session, on_delta)
            q.put(("done", result))
        except Exception as exc:
            q.put(("error", exc))
        finally:
            session.close()

    threading.Thread(target=worker, daemon=True).start()

    while True:
        item = q.get()
        tag = item[0]
        if tag == "token":
            kind, text = item[1], item[2]
            yield _sse("token", json.dumps({"kind": kind, "text": text}, ensure_ascii=False))
        elif tag == "done":
            yield _sse("done", serialize(item[1]))
            return
        else:
            detail = getattr(item[1], "detail", str(item[1]))
            yield _sse("error", json.dumps({"detail": detail}, ensure_ascii=False))
            return

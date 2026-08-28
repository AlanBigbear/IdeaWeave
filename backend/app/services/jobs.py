import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_MAX_JOBS = 100


@dataclass
class Job:
    id: str
    status: str = "running"  # running | done | error
    error: str = ""
    result: dict = field(default_factory=dict)


_lock = threading.Lock()
_jobs: dict[str, Job] = {}
_running_keys: dict[str, str] = {}
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bstar-job")


def _evict_done() -> None:
    done_ids = [jid for jid, job in _jobs.items() if job.status != "running"]
    while len(_jobs) > _MAX_JOBS and done_ids:
        _jobs.pop(done_ids.pop(0), None)


def submit(key: str | None, fn) -> tuple[str, bool]:
    """提交后台任务；返回任务 ID 及本次是否真正创建了任务。"""
    with _lock:
        if key and key in _running_keys:
            return _running_keys[key], False
        job = Job(id=uuid.uuid4().hex[:12])
        _jobs[job.id] = job
        if key:
            _running_keys[key] = job.id
        _evict_done()

    def _run():
        try:
            job.result = fn() or {}
            job.status = "done"
        except Exception as exc:
            logger.exception("后台任务 %s 失败", job.id)
            job.status = "error"
            job.error = str(exc) or exc.__class__.__name__
        finally:
            with _lock:
                if key and _running_keys.get(key) == job.id:
                    _running_keys.pop(key, None)

    _pool.submit(_run)
    return job.id, True


def get(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)

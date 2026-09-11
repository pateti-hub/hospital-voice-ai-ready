import contextvars
import logging
import sys
import uuid

from pythonjsonlogger.json import JsonFormatter

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s")
    )
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def new_request_id(value: str | None = None) -> str:
    rid = value or str(uuid.uuid4())
    request_id_ctx.set(rid)
    return rid

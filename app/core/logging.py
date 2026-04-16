import contextvars
from loguru import logger
import sys
import logging
from app.core.config import settings

# Context variable to store the request ID for the duration of a request
request_id_ctx = contextvars.ContextVar("request_id", default="n/a")


class InterceptHandler(logging.Handler):
    """
    Default handler from dev.to/guiseopapa/loguru-fastapi-404i
    and official loguru documentation.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    logger.remove()

    # Determine log format based on request context availability
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "[RID: <yellow>{extra[request_id]}</yellow>] - <level>{message}</level>"
    )

    # Add standard output handler - Choose format based on environment
    if settings.ENVIRONMENT == "production":
        # Structured JSON logs for machine ingestion (Datadog, CloudWatch, ELK)
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
    else:
        # High-visibility colorized logs for human readability
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            format=log_format,
            colorize=True,
            backtrace=True,
            diagnose=True if settings.ENVIRONMENT == "development" else False,
        )

    # Intercept all logs from the standard logging library
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Update uvicorn loggers to use our InterceptHandler
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False

    # Patch all logs with the request_id from contextvars
    def patcher(record):
        record["extra"]["request_id"] = request_id_ctx.get()

    logger.configure(patcher=patcher)

    return logger

import sys
import os
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


def setup_logger():
    """Configure loguru logger with file rotation and structured output."""
    os.makedirs(settings.log_dir, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Console handler — colored, human-readable
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Rotating file handler — JSON structured logs
    logger.add(
        os.path.join(settings.log_dir, "app_{time:YYYY-MM-DD}.log"),
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="gz",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        ),
        enqueue=True,
    )

    # Error-only file
    logger.add(
        os.path.join(settings.log_dir, "errors_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="gz",
        enqueue=True,
    )

    return logger


# Singleton logger instance
log = setup_logger()

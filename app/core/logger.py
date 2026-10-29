"""Dosyaya loglama ve yakalanmayan istisna kancaları.

Konsolsuz (windowed) exe'de stderr yoktur; log dosyası olmadan hata kaybolur.
`setup_logging` idempotenttir: tekrar çağrılınca çift handler eklemez.
"""

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler

from app.core import paths

LOGGER_NAME = "namaz_takip"
LOG_FILE_NAME = "namaz_takip.log"
LOG_LEVEL_ENV = "NAMAZ_TAKIP_LOG_LEVEL"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 3
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

logger = logging.getLogger(LOGGER_NAME)


def _resolve_level(level) -> int:
    value = level if level is not None else os.environ.get(LOG_LEVEL_ENV, "INFO")
    if isinstance(value, int):
        return value
    resolved = logging.getLevelName(str(value).upper())
    return resolved if isinstance(resolved, int) else logging.INFO


def _is_ours(handler: logging.Handler) -> bool:
    return getattr(handler, "_namaz_takip", False)


def setup_logging(level=None) -> logging.Logger:
    """Log dosyasını kurar. Düzey: argüman, yoksa ortam değişkeni, yoksa INFO."""
    resolved = _resolve_level(level)
    logger.setLevel(resolved)
    logger.propagate = False

    if not any(_is_ours(h) for h in logger.handlers):
        handler = RotatingFileHandler(
            paths.logs_dir() / LOG_FILE_NAME,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(_FORMAT))
        handler._namaz_takip = True
        logger.addHandler(handler)

    _install_excepthooks()
    return logger


def shutdown_logging() -> None:
    """Handler'ları kapatır ve çıkarır (testlerde dosya kilidini bırakmak için)."""
    for handler in [h for h in logger.handlers if _is_ours(h)]:
        logger.removeHandler(handler)
        handler.close()


def _install_excepthooks() -> None:
    if getattr(sys.excepthook, "_namaz_takip", False):
        return

    def _sys_hook(exc_type, exc, tb):
        logger.critical("Yakalanmayan istisna", exc_info=(exc_type, exc, tb))

    def _thread_hook(args):
        logger.critical(
            "Yakalanmayan istisna (iş parçacığı: %s)",
            args.thread.name if args.thread else "?",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    _sys_hook._namaz_takip = True
    _thread_hook._namaz_takip = True
    sys.excepthook = _sys_hook
    threading.excepthook = _thread_hook

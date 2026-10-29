import logging
import sys
import threading

import pytest

from app.core import logger as log_module
from app.core import paths


@pytest.fixture(autouse=True)
def restore_hooks(monkeypatch):
    # Kanca kurulumu testler arasında sızmasın.
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    monkeypatch.delenv(log_module.LOG_LEVEL_ENV, raising=False)


def _log_text() -> str:
    return (paths.logs_dir() / log_module.LOG_FILE_NAME).read_text(encoding="utf-8")


def test_log_dosyaya_yazilir_ve_turkce_karakter_korunur(isolated_data_dir):
    log_module.setup_logging()
    log_module.logger.info("Işık şehir ğüzel İstanbul")
    assert "Işık şehir ğüzel İstanbul" in _log_text()
    assert (isolated_data_dir / "logs" / log_module.LOG_FILE_NAME).exists()


def test_kurulum_idempotent():
    log_module.setup_logging()
    log_module.setup_logging()
    ours = [h for h in log_module.logger.handlers if getattr(h, "_namaz_takip", False)]
    assert len(ours) == 1


def test_duzey_ortam_degiskeninden_ve_arguman_onceliklidir(monkeypatch):
    monkeypatch.setenv(log_module.LOG_LEVEL_ENV, "DEBUG")
    log_module.setup_logging()
    assert log_module.logger.level == logging.DEBUG
    log_module.setup_logging("WARNING")
    assert log_module.logger.level == logging.WARNING


def test_gecersiz_duzey_info_olur(monkeypatch):
    monkeypatch.setenv(log_module.LOG_LEVEL_ENV, "yanlis")
    log_module.setup_logging()
    assert log_module.logger.level == logging.INFO


def test_yakalanmayan_istisna_loglanir():
    log_module.setup_logging()
    try:
        raise ValueError("deneme hatası")
    except ValueError:
        sys.excepthook(*sys.exc_info())
    text = _log_text()
    assert "Yakalanmayan istisna" in text
    assert "deneme hatası" in text

"""Kullanıcı verisinin yazıldığı klasörler.

Testler gerçek kullanıcı klasörüne yazmasın diye `NAMAZ_TAKIP_DATA_DIR` ortam değişkeni
varsa onu kullanır (bkz. tests/conftest.py).
"""

import os
from pathlib import Path

DATA_DIR_ENV = "NAMAZ_TAKIP_DATA_DIR"
APP_DIR_NAME = "NamazTakip"


def app_data_dir() -> Path:
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        path = Path(override)
    else:
        base = os.environ.get("APPDATA") or str(Path.home())
        path = Path(base) / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_dir() -> Path:
    path = app_data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return app_data_dir() / "namaz_takip.db"

"""Günlük veritabanı yedeği: açılışta günde bir kez, son 7 yedek tutulur.

Neden: kaza borcu ve işaretler tek dosyada yıllarca birikir; bozulmada yalnızca "bozuk dosya yedeği" yetmez
(docs/wiki/veri-katmani.md). SQL ve `sqlite3` `AppDatabase.backup_to` içindedir; burada yalnızca politika vardır.
"""

from datetime import date
from pathlib import Path

from app.core import paths
from app.core.database import AppDatabase
from app.core.logger import logger

BACKUP_PREFIX = "namaz_takip-"
BACKUP_SUFFIX = ".db"
BACKUP_KEEP = 7


def backup_path(folder: Path, day: date) -> Path:
    return folder / f"{BACKUP_PREFIX}{day:%Y%m%d}{BACKUP_SUFFIX}"


def run_daily_backup(
    database: AppDatabase, today: date, folder: "Path | None" = None, keep: int = BACKUP_KEEP
) -> "Path | None":
    """Bugünün yedeğini alır. Yeni yedek yazıldıysa yolunu, atlandıysa veya başarısızsa None döner.

    Bellek içi veritabanında ve bugün zaten yedek varsa atlanır. Hata uygulamayı durdurmaz, loglanır.
    """
    if database.path is None:
        return None
    folder = folder if folder is not None else paths.backups_dir()
    target = backup_path(folder, today)
    if target.exists():
        return None
    try:
        folder.mkdir(parents=True, exist_ok=True)
        database.backup_to(target)
    except Exception:
        logger.exception("Günlük yedek alınamadı: %s", target)
        return None
    _prune(folder, keep)
    logger.info("Günlük yedek alındı: %s", target)
    return target


def _prune(folder: Path, keep: int) -> None:
    """Ada göre (tarih sıralı) en yeni `keep` yedek kalır, eskileri silinir."""
    backups = sorted(
        p for p in folder.iterdir() if p.is_file() and p.name.startswith(BACKUP_PREFIX) and p.name.endswith(BACKUP_SUFFIX)
    )
    for old in backups[:-keep] if keep > 0 else backups:
        try:
            old.unlink()
        except OSError:
            logger.exception("Eski yedek silinemedi: %s", old)
